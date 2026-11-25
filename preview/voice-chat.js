// 语音对话：麦克风识别（浏览器 / Confucius4-R2T2 流式 / 服务端 Whisper）、逐句 TTS 播放与口型。
import {downsampleToInt16, estimateDuration, splitSentences} from './voice-text.js?v=voice-1';

const EOS = 'YOUDAO_ONETIME_ASR_STREAM_EOS';
const clamp01 = value => Math.max(0, Math.min(1, value));

function rms(samples) {
  let sum = 0;
  for (let i = 0; i < samples.length; i++) sum += samples[i] * samples[i];
  return Math.sqrt(sum / Math.max(1, samples.length));
}

/** 简单能量 VAD：开口后静音超过 silenceMs 即认为一句话结束。 */
function createEndpointer({threshold = .018, silenceMs = 900, maxMs = 20000, onEnd}) {
  let speaking = false, quietSince = 0, started = performance.now(), done = false;
  return {
    get speaking() { return speaking; },
    push(level) {
      if (done) return;
      const now = performance.now();
      if (level > threshold) { speaking = true; quietSince = 0; }
      else if (speaking && !quietSince) quietSince = now;
      if ((speaking && quietSince && now - quietSince > silenceMs) || now - started > maxMs ||
          (!speaking && now - started > 8000)) { done = true; onEnd(speaking); }
    },
  };
}

async function openMicrophone() {
  if (!navigator.mediaDevices?.getUserMedia) throw new Error('当前浏览器不支持麦克风（需要 localhost 或 HTTPS）');
  const stream = await navigator.mediaDevices.getUserMedia({audio: {echoCancellation: true, noiseSuppression: true}});
  const context = new AudioContext();
  const source = context.createMediaStreamSource(stream);
  return {stream, context, source, close() { stream.getTracks().forEach(track => track.stop()); context.close().catch(() => {}); }};
}

/** 浏览器 Web Speech API（Chrome / Edge 可用，识别由浏览器厂商的服务完成）。 */
export function browserRecognizer({language = 'zh-CN'} = {}) {
  const Recognition = globalThis.SpeechRecognition || globalThis.webkitSpeechRecognition;
  let active = null;
  return {
    name: '浏览器识别',
    supported: !!Recognition,
    listen({onInterim, onLevel} = {}) {
      if (!Recognition) return Promise.reject(new Error('当前浏览器不支持 Web Speech 识别，请换 Chrome/Edge 或选择其他 ASR 后端'));
      return new Promise((resolve, reject) => {
        const recognition = new Recognition(); active = recognition;
        recognition.lang = language; recognition.interimResults = true; recognition.continuous = false;
        let finalText = '', failed = null;
        recognition.onresult = event => {
          let interim = '';
          for (const result of event.results) (result.isFinal ? null : (interim += result[0].transcript));
          finalText = [...event.results].filter(result => result.isFinal).map(result => result[0].transcript).join('');
          onInterim?.(finalText + interim); onLevel?.(.4);
        };
        recognition.onerror = event => { if (!['no-speech', 'aborted'].includes(event.error)) failed = new Error('语音识别失败：' + event.error); };
        recognition.onend = () => { active = null; failed ? reject(failed) : resolve(finalText.trim()); };
        recognition.start();
      });
    },
    stop() { active?.stop(); },
    abort() { active?.abort(); },
  };
}

/**
 * Confucius4-R2T2 流式识别（网易有道开源，最长稳定前缀 LSP：已输出文字不再回改）。
 * 协议来自官方 ws_server.py：先发 JSON 头，再发 16kHz 单声道 int16 PCM 二进制帧（约 160ms 一帧），
 * 结束时发送字符串 YOUDAO_ONETIME_ASR_STREAM_EOS；服务端每条消息的 msg.text 是新增片段，直接拼接即可。
 */
export function r2t2Recognizer({url = 'ws://127.0.0.1:8272/asr_stream_api_v1', secretKey = 'test0102',
  language = 'zhen', hotwords = ''} = {}) {
  let session = null;
  return {
    name: 'Confucius4-R2T2',
    supported: typeof WebSocket !== 'undefined',
    async listen({onInterim, onLevel} = {}) {
      const mic = await openMicrophone();
      const socket = new WebSocket(url); socket.binaryType = 'arraybuffer';
      let text = '', finished = false, connected = false, pending = new Int16Array(0);
      const frame = 2560; // 160ms @ 16kHz
      const processor = mic.context.createScriptProcessor(4096, 1, 1);
      const silent = mic.context.createGain(); silent.gain.value = 0;
      const result = new Promise((resolve, reject) => {
        const finish = error => {
          if (finished) return; finished = true;
          processor.disconnect(); mic.close(); session = null;
          try { socket.close(); } catch {}
          error ? reject(error) : resolve(text.trim());
        };
        const endpoint = createEndpointer({onEnd: () => sendEos()});
        const sendEos = () => {
          if (socket.readyState === WebSocket.OPEN) {
            if (pending.length) socket.send(pending.buffer.slice(0)), pending = new Int16Array(0);
            socket.send(EOS); setTimeout(() => finish(), 4000);
          } else finish();
        };
        session = {stop: sendEos, abort: () => { text = ''; finish(); }};
        socket.onopen = () => socket.send(JSON.stringify({
          channels: 1, sample_rate: 16000, requestId: crypto.randomUUID(), language,
          use_vad: false, secret_key: secretKey, mode: 'slow', ...(hotwords ? {system_prompt: hotwords} : {}), // 热词 / 上下文提示
        }));
        socket.onmessage = event => {
          let value; try { value = JSON.parse(event.data); } catch { return; }
          if (value.status === 'error') return finish(new Error('R2T2：' + (value.msg || '服务端错误')));
          if (value.status === 'connected') connected = true;
          const piece = value.msg && typeof value.msg === 'object' ? value.msg.text : '';
          if (piece) { text += piece; onInterim?.(text); }
          if (value.msg?.reset) finish();
        };
        socket.onerror = () => finish(new Error('无法连接 Confucius4-R2T2 服务：' + url));
        socket.onclose = event => finish(event.code === 4401 ? new Error('R2T2 secret_key 不正确') : null);
        processor.onaudioprocess = event => {
          const input = event.inputBuffer.getChannelData(0), level = rms(input);
          onLevel?.(clamp01(level * 8)); endpoint.push(level);
          // 连接建立前的录音先缓存（最多 10 秒），避免丢掉开头的字。
          const samples = downsampleToInt16(input, mic.context.sampleRate);
          let merged = new Int16Array(pending.length + samples.length);
          merged.set(pending); merged.set(samples, pending.length);
          if (socket.readyState !== WebSocket.OPEN || !connected) { pending = merged.slice(-160000); return; }
          let offset = 0;
          for (; offset + frame <= merged.length; offset += frame) socket.send(merged.slice(offset, offset + frame).buffer);
          pending = merged.slice(offset);
        };
      });
      mic.source.connect(processor); processor.connect(silent); silent.connect(mic.context.destination);
      return result;
    },
    stop() { session?.stop(); },
    abort() { session?.abort(); },
  };
}

/** 录一句话后上传本地服务：openai（OpenAI 兼容 /audio/transcriptions）或 local（faster-whisper）。 */
export function serverRecognizer({backend = 'openai', settings = () => ({})} = {}) {
  let session = null;
  return {
    name: backend === 'local' ? '本地 Whisper' : '云端 Whisper',
    supported: typeof MediaRecorder !== 'undefined',
    async listen({onInterim, onLevel} = {}) {
      const mic = await openMicrophone();
      const analyser = mic.context.createAnalyser(); analyser.fftSize = 1024; mic.source.connect(analyser);
      const samples = new Float32Array(analyser.fftSize);
      const recorder = new MediaRecorder(mic.stream);
      const chunks = []; let aborted = false, timer = 0;
      recorder.ondataavailable = event => event.data.size && chunks.push(event.data);
      const stopped = new Promise(resolve => { recorder.onstop = resolve; });
      const endpoint = createEndpointer({onEnd: () => recorder.state === 'recording' && recorder.stop()});
      session = {stop: () => recorder.state === 'recording' && recorder.stop(),
        abort: () => { aborted = true; recorder.state === 'recording' && recorder.stop(); }};
      const poll = () => {
        analyser.getFloatTimeDomainData(samples); const level = rms(samples);
        onLevel?.(clamp01(level * 8)); endpoint.push(level);
        if (recorder.state === 'recording') timer = setTimeout(poll, 50);
      };
      recorder.start(); poll(); onInterim?.('（录音中…）');
      await stopped; clearTimeout(timer); mic.close(); session = null;
      if (aborted || !chunks.length) return '';
      const blob = new Blob(chunks, {type: recorder.mimeType || 'audio/webm'});
      onInterim?.('（识别中…）');
      const audio = await blobToBase64(blob);
      const config = settings();
      const response = await fetch('/api/services/transcribe', {method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({backend, audio, mime: blob.type, endpoint: config.asrEndpoint, key: config.asrKey,
          model: config.asrModel, language: config.asrLanguage})});
      const value = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(value.error || '语音识别失败');
      return String(value.text || '').trim();
    },
    stop() { session?.stop(); },
    abort() { session?.abort(); },
  };
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1] || '');
    reader.onerror = () => reject(reader.error); reader.readAsDataURL(blob);
  });
}

export function createRecognizer(kind, options) {
  if (kind === 'r2t2') return r2t2Recognizer(options.r2t2);
  if (kind === 'openai' || kind === 'local') return serverRecognizer({backend: kind, settings: options.settings});
  return browserRecognizer({language: options.language});
}

/**
 * 逐句朗读：服务端 TTS（runninghub / indextts-local / openai）或浏览器 speechSynthesis。
 * 第一句合成后立即开口，后续句子并行预取；level 提供 0–1 的音量包络驱动口型。
 */
export function createSpeaker({synthesize}) {
  let context = null, analyser = null, buffer = null, current = null, generation = 0, simulated = 0;
  const ensureAnalyser = () => {
    if (analyser) return;
    context = new AudioContext(); analyser = context.createAnalyser(); analyser.fftSize = 1024;
    buffer = new Float32Array(analyser.fftSize); analyser.connect(context.destination);
  };
  function playBlob(blob, onProgress, token) {
    return new Promise((resolve, reject) => {
      ensureAnalyser(); context.resume?.();
      const url = URL.createObjectURL(blob), audio = new Audio(url);
      const source = context.createMediaElementSource(audio); source.connect(analyser);
      const cleanup = () => { source.disconnect(); URL.revokeObjectURL(url); if (current?.audio === audio) current = null; };
      current = {audio, stop: () => { audio.pause(); cleanup(); resolve(); }};
      audio.ontimeupdate = () => token === generation && onProgress?.(audio.duration ? audio.currentTime / audio.duration : 0);
      audio.onended = () => { onProgress?.(1); cleanup(); resolve(); };
      audio.onerror = () => { cleanup(); reject(new Error('音频无法播放')); };
      audio.play().catch(error => { cleanup(); reject(error); });
    });
  }
  function speakBrowser(text, onProgress, language) {
    return new Promise(resolve => {
      if (!globalThis.speechSynthesis) {
        // 没有任何朗读能力时，按字数估算时长，只播放字幕与口型。
        const duration = estimateDuration(text) * 1000, started = performance.now();
        const tick = () => {
          const t = (performance.now() - started) / duration; onProgress?.(Math.min(1, t)); simulated = t < 1 ? .6 : 0;
          if (t < 1 && current?.timer !== undefined) current.timer = requestAnimationFrame(tick); else { current = null; resolve(); }
        };
        current = {timer: 0, stop: () => { simulated = 0; current = null; resolve(); }}; tick(); return;
      }
      const utterance = new SpeechSynthesisUtterance(text); utterance.lang = language || 'zh-CN';
      const length = Math.max(1, text.length), expected = estimateDuration(text) * 1000, started = performance.now();
      let timer = 0;
      const end = () => { clearTimeout(timer); simulated = 0; onProgress?.(1); current = null; resolve(); };
      utterance.onstart = () => { simulated = .7; };
      utterance.onboundary = event => { onProgress?.(event.charIndex / length); simulated = .9; };
      // 系统没有对应语言的音色时朗读会立刻结束：仍按估算时长保留字幕、表情和模拟口型。
      utterance.onend = utterance.onerror = () => {
        const left = expected * .8 - (performance.now() - started);
        if (left <= 0 || current?.cancelled) return end();
        simulated = .6;
        const tick = () => {
          const t = (performance.now() - started) / expected; onProgress?.(Math.min(1, t));
          if (performance.now() - started >= expected * .8 || current?.cancelled) end(); else timer = setTimeout(tick, 60);
        };
        tick();
      };
      current = {cancelled: false, stop() { this.cancelled = true; speechSynthesis.cancel(); end(); }};
      speechSynthesis.speak(utterance);
    });
  }
  return {
    /** 当前口型强度 0–1。浏览器朗读拿不到音频流，用节奏模拟。 */
    get level() {
      if (current?.audio && analyser) {
        analyser.getFloatTimeDomainData(buffer); return clamp01(rms(buffer) * 5);
      }
      if (!simulated) return 0;
      const t = performance.now() / 1000;
      return clamp01(simulated * (.45 + .35 * Math.sin(t * 17) + .2 * Math.sin(t * 7.3)));
    },
    get speaking() { return !!current; },
    /**
     * 朗读一段回复。backend: runninghub / indextts-local / openai / browser / off。
     * hooks.onSentence(index, sentence, sentences) 在每句开口时调用；hooks.onProgress(index, 0–1)。
     * 服务端合成失败且 fallback 为真时改用浏览器朗读。
     */
    async speak(text, {backend = 'browser', fallback = true, language = 'zh-CN', onSentence, onProgress, onStart, onError} = {}) {
      this.stop();
      const token = ++generation;
      const server = !['browser', 'off'].includes(backend);
      // RunningHub 每个任务都有固定排队开销并按次扣点，整段回复尽量合成一次；其他后端逐句合成，先开口。
      const sentences = splitSentences(text, {maxLength: backend === 'runninghub' ? 300 : 60});
      if (!sentences.length) return;
      // 后续句子并发 2 路预取，服务端缓存命中时立即返回。
      const jobs = [];
      const start = index => {
        if (!server || index >= sentences.length || jobs[index]) return;
        jobs[index] = synthesize(backend, sentences[index]).catch(error => error);
      };
      start(0); start(1);
      let started = false, degraded = !server;
      for (let index = 0; index < sentences.length; index++) {
        if (token !== generation) return;
        start(index + 1); start(index + 2);
        const sentence = sentences[index];
        let blob = server && !degraded ? await jobs[index] : null;
        if (token !== generation) return;
        if (blob instanceof Error) {
          onError?.(blob); if (!fallback) return;
          degraded = true; blob = null;
        }
        if (!started) { started = true; onStart?.(sentences); }
        onSentence?.(index, sentence, sentences);
        const progress = value => onProgress?.(index, value);
        if (blob) await playBlob(blob, progress, token).catch(error => { onError?.(error); return speakBrowser(sentence, progress, language); });
        else if (backend !== 'off') await speakBrowser(sentence, progress, language);
        else await new Promise(resolve => { const timer = setTimeout(resolve, estimateDuration(sentence) * 1000); current = {stop: () => { clearTimeout(timer); current = null; resolve(); }}; });
      }
      current = null; simulated = 0;
    },
    stop() { generation++; current?.stop(); current = null; simulated = 0; globalThis.speechSynthesis?.cancel(); },
  };
}

/** 口型层：把音量包络叠加到 VRChat 视位形态键（vrc.v_aa / v_ou / v_ih），无该通道时回退 mouth_a。 */
export function createMouthControl(channelNames = []) {
  const names = new Set(channelNames);
  const open = names.has('vrc.v_aa') ? 'vrc.v_aa' : names.has('mouth_a') ? 'mouth_a' : null;
  const round = names.has('vrc.v_ou') ? 'vrc.v_ou' : names.has('mouth_o') ? 'mouth_o' : null;
  const wide = names.has('vrc.v_ih') ? 'vrc.v_ih' : names.has('mouth_i') ? 'mouth_i' : null;
  let value = 0, phase = 0;
  return {
    supported: !!open,
    tick(dt, target) {
      const rate = target > value ? 22 : 9; // 张嘴快、合嘴慢
      value += (target - value) * Math.min(1, rate * dt); phase += dt * 5.5;
    },
    compose(baseline) {
      if (!open || value < .01) return baseline;
      const output = {...baseline}, amount = Math.min(1, value) * 100;
      const mix = (name, weight) => { if (name) output[name] = Math.max(Number(baseline[name]) || 0, amount * weight); };
      mix(open, .85); mix(round, .35 * (.5 + .5 * Math.sin(phase))); mix(wide, .25 * (.5 + .5 * Math.cos(phase * 1.3)));
      return output;
    },
  };
}
