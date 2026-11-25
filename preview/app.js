import {createReferenceView} from './reference-view.js?v=gaze-sync-9';
import {httpAssets} from './assets.js?v=workbench-4';
import {loadCurvePlayer} from './curve-player.js?v=gaze-neutral-8';
import {buildChatPrompt, browDirective, createBrowControl} from './chat-director.js?v=face-directives-10';
import {fallbackLabel, listeningReaction, parseReply, resolveLabel, spokenText} from './emotion-map.js?v=voice-1';
import {captionProgress} from './voice-text.js?v=voice-1';
import {createMouthControl, createRecognizer, createSpeaker} from './voice-chat.js?v=voice-1';

const $ = id => document.getElementById(id);
const settingsKey = 'lumenact-reference-services-v2';
const voiceKey = 'lumenact-voice-chat-v1';
let face = null, player = null, last = 0;
let mouth = createMouthControl(), recognizer = null, listening = false, semanticReady = false, captionTimer = 0;
const speaker = createSpeaker({synthesize: (backend, text) => {
  const config = settings();
  return api('services/speech', {backend, text, endpoint: config.ttsEndpoint, key: config.ttsKey, model: config.ttsModel, voice: config.ttsVoice});
}});
let displayedStyleId = null;
const history = [];
const brows = createBrowControl();
let hasSavedTtsSetting = false;
const say = (text, kind = '') => { $('faceStatus').textContent = text; $('faceStatus').dataset.kind = kind; };

async function api(path, body) {
  const response = await fetch('/api/' + path, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  if (path.endsWith('/speech') && response.ok) return response.blob();
  const value = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(value.error || '本地接口请求失败');
  return value;
}
function shapes() { return mouth.compose(brows.compose(player ? player.sample() : {})); }
function updateFace() { if (face) face.setShapes(shapes()); }
function updateTelemetry() {
  if (!face || !player) return;
  const values = shapes();
  const active = Object.values(values).filter(value => Math.abs(Number(value) || 0) > 2).length;
  const total = face.channels?.length || 166;
  const activeNode = $('activeChannels'), channelNode = $('channelValue'), bar = $('channelBar');
  if (activeNode) activeNode.textContent = String(active);
  if (channelNode) channelNode.textContent = active + ' / ' + total;
  if (bar) bar.style.setProperty('--w', Math.min(100, active / Math.max(1, total) * 100).toFixed(1) + '%');
  const fps = $('fps'), latency = $('latency');
  if (fps) fps.textContent = '60';
  if (latency) latency.textContent = '16 ms';
}
function pickStyle(style) {
  if (!player) return;
  brows.release();
  player.choose(style.id); updateFace();
  $('currentExpression').textContent = style.label;
  displayedStyleId = style.id;
  say('表情已更新', 'ok');
}
function showSemantic(result) {
  $('semanticTime').textContent = result.elapsed_ms.toFixed(2) + ' ms';
  $('semanticTime').title = '';
}
function styleFor(label, contextId = 'auto', vary = false) {
  const options = player?.catalog.styles.filter(style => style.label === label) || [];
  return options.find(style => contextId !== 'auto' && style.context_id === contextId) ||
    (vary ? options[Math.floor(Math.random() * options.length)] : options[0]) || null;
}
// 只计算要用的表情，不立刻切换；语音对话在开口那一刻才应用。
async function planExpression(intent, text = '') {
  const directive = browDirective(intent);
  if (directive) {
    if (!player || !face?.channels.some(channel => channel.name === directive.channel))
      throw new Error('当前脸部没有可用的单眉通道');
    return {directive, label: directive.label, source: '单眉指令'};
  }
  const result = await api('semantic', {intent, text});
  showSemantic(result);
  const style = styleFor(result.expression, result.context_id);
  if (!style) throw new Error('当前无法显示该表情：' + result.expression);
  return {style, label: result.expression, source: '语义模型', result};
}
function applyExpression(plan, hold = false) {
  if (!plan || !player) return;
  if (plan.directive) {
    player.returnToNeutral(); brows.start(plan.directive, player.sample());
    $('semanticTime').textContent = '—';
    $('semanticTime').title = '基础单眉指令直接控制公开形态键，本次未调用语义模型';
    return;
  }
  pickStyle(plan.style); player.setLoop(hold);
}
async function selectExpression(intent, text = '') {
  const plan = await planExpression(intent, text);
  applyExpression(plan);
  return plan.result || {operation: 'reference_brow_control', expression: plan.label};
}
/**
 * 根据 LLM 回复挑选表情：
 * 1. 回复带标签且与表情目录完全一致 → 直接使用；
 * 2. 其他标签 → 交给本地语义模型；语义模型不可用时按别名 / 关键词近似匹配；
 * 3. 没有标签 → 台词关键词兜底；仍无命中且语义模型就绪时，按台词语义选择；
 * 4. 都失败 → 自然放松。
 */
async function chooseExpression(answer) {
  const parsed = parseReply(answer);
  const labels = player?.catalog.labels || [];
  if (parsed.tag) {
    const direct = resolveLabel(parsed.tag, labels);
    if (direct?.method === 'exact') return {style: styleFor(direct.label, 'auto', true), label: direct.label, source: 'LLM 标签'};
    try { return await planExpression(parsed.tag, parsed.text); }
    catch (error) {
      if (browDirective(parsed.tag)) throw error;
      if (direct) return {style: styleFor(direct.label, 'auto', true), label: direct.label, source: 'LLM 标签（近似：' + direct.method + '）'};
    }
  }
  const fallback = fallbackLabel(parsed.text, labels);
  if (fallback) return {style: styleFor(fallback.label, 'auto', true), label: fallback.label, source: '关键词兜底：' + fallback.hits.join('、')};
  if (semanticReady && parsed.text) {
    try { const plan = await planExpression(parsed.text.slice(0, 200), parsed.text); plan.source = '语义模型（按台词）'; return plan; } catch {}
  }
  return null;
}
function addMessage(text, role = 'assistant') {
  const item = document.createElement('div'); item.className = 'message ' + role; item.textContent = text;
  $('messages').append(item); $('messages').scrollTop = $('messages').scrollHeight;
}
const voiceFields = ['asrBackend', 'asrLanguage', 'r2t2Url', 'r2t2Secret', 'r2t2Hotwords', 'asrEndpoint', 'asrModel', 'ttsBackend'];
const voiceChecks = ['ttsFallback', 'lipSync', 'listenReaction', 'captions', 'autoListen'];
function settings() {
  return Object.fromEntries(['llmEndpoint','llmModel','llmKey','ttsEndpoint','ttsModel','ttsVoice','ttsKey','asrKey', ...voiceFields]
    .map(id => [id, $(id).value.trim()]));
}
let hasSavedVoice = false;
function restoreVoice() {
  try {
    const value = JSON.parse(localStorage.getItem(voiceKey) || '{}');
    hasSavedVoice = Object.keys(value).length > 0;
    for (const id of voiceFields) if (typeof value[id] === 'string' && value[id]) $(id).value = value[id];
    for (const id of voiceChecks) if (typeof value[id] === 'boolean') $(id).checked = value[id];
    if (typeof value.asrKey === 'string') $('asrKey').value = value.asrKey;
  } catch {}
}
function saveVoice() {
  const value = Object.fromEntries([...voiceFields.map(id => [id, $(id).value.trim()]), ...voiceChecks.map(id => [id, $(id).checked])]);
  if ($('rememberKeys').checked && $('asrKey').value.trim()) value.asrKey = $('asrKey').value.trim();
  try { localStorage.setItem(voiceKey, JSON.stringify(value)); say('语音配置已保存在此浏览器', 'ok'); }
  catch { say('浏览器不允许保存配置', 'error'); }
}
function restoreSettings() {
  try {
    const value = JSON.parse(localStorage.getItem(settingsKey) || '{}');
    for (const [id, text] of Object.entries(value)) if ($(id) && typeof text === 'string') $(id).value = text;
    $('rememberKeys').checked = !!(value.llmKey || value.ttsKey);
    if (typeof value.ttsEnabled === 'boolean') {
      $('ttsEnabled').checked = value.ttsEnabled;
      hasSavedTtsSetting = true;
    }
  } catch {}
}
async function loadServiceDefaults() {
  try {
    const response = await fetch('/api/services/config');
    if (!response.ok) return;
    const value = await response.json();
    for (const id of ['llmEndpoint', 'llmModel', 'ttsEndpoint', 'ttsModel', 'ttsVoice']) {
      if (!$(id).value.trim() && typeof value[id] === 'string') $(id).value = value[id];
    }
    if (!hasSavedTtsSetting && typeof value.ttsEnabled === 'boolean') $('ttsEnabled').checked = value.ttsEnabled;
    if (!hasSavedVoice) {
      for (const id of ['asrBackend', 'asrLanguage', 'asrEndpoint', 'asrModel', 'ttsBackend', 'r2t2Url'])
        if (typeof value[id] === 'string' && value[id]) $(id).value = value[id];
      for (const id of voiceChecks) if (typeof value[id] === 'boolean') $(id).checked = value[id];
    }
    const keys = value.serverKeys || {};
    const notes = [];
    if (keys.llm) notes.push('LLM 密钥已在服务端配置');
    if (keys.tts) notes.push('TTS 密钥已在服务端配置');
    if (keys.asr) notes.push('ASR 密钥已在服务端配置');
    notes.push(value.runninghubReady ? 'RunningHub IndexTTS 2.5 已就绪' : 'RunningHub 未配置（需 RUNNINGHUB_API_KEY 与参考音色）');
    $('voiceServerInfo').textContent = notes.join(' · ');
    if ((keys.llm || value.llmEndpoint) && !$('llmKey').value) $('chatInput').placeholder = '输入一句话，或点麦克风说话';
  } catch {}
}
async function health() {
  try {
    const response = await fetch('/api/health'); if (!response.ok) throw new Error('请通过 start_preview 启动预览');
    const value = await response.json();
    $('semanticStatus').textContent = value.ready ? '本地 CPU · READY' : value.error ? '语义模型未就绪' : '本地模型预热中';
    $('semanticStatus').dataset.kind = value.ready ? 'ok' : value.error ? 'error' : '';
    $('semanticStatus').title = value.error || value.model;
    semanticReady = !!value.ready;
    if (!value.ready && !value.error) setTimeout(health, 1800);
  } catch (error) { $('semanticStatus').textContent = '语义接口不可用'; $('semanticStatus').dataset.kind = 'error'; $('semanticStatus').title = error.message; }
}
function bind() {
  for (const button of document.querySelectorAll('[data-view]')) button.onclick = () => face?.setView(button.dataset.view);
  $('resetView').onclick = () => face?.setView('front');
  $('saveServices').onclick = () => {
    const value = settings(); if (!$('rememberKeys').checked) { delete value.llmKey; delete value.ttsKey; }
    value.ttsEnabled = $('ttsEnabled').checked;
    try { localStorage.setItem(settingsKey, JSON.stringify(value)); say('配置已保存在此浏览器', 'ok'); }
    catch { say('浏览器不允许保存配置', 'error'); }
  };
  $('saveVoice').onclick = saveVoice;
  $('chatForm').onsubmit = event => {
    event.preventDefault(); const text = $('chatInput').value.trim(); if (!text) return;
    $('chatInput').value = ''; converse(text, 'text');
  };
  $('micButton').onclick = () => listening ? recognizer?.stop() : startListening();
}
function voiceStatus(text) { $('voiceStatus').textContent = text; }
function showCaption(sentence, progress) {
  if (!$('captions').checked) return;
  clearTimeout(captionTimer);
  const {shown, rest} = captionProgress(sentence, progress);
  const node = $('caption'); node.hidden = false;
  node.querySelector('.caption-said').textContent = shown; node.querySelector('.caption-rest').textContent = rest;
}
function hideCaption(delay = 1200) { clearTimeout(captionTimer); captionTimer = setTimeout(() => { $('caption').hidden = true; }, delay); }
function ttsBackend() { return $('ttsEnabled').checked ? $('ttsBackend').value : 'off'; }
let reactionLabel = '';
// 倾听反应：边听边分析用户情绪，流明先做出共情表情（不是镜像用户）。
function react(userText) {
  if (!$('listenReaction').checked || !player) return;
  const reaction = listeningReaction(userText, player.catalog.labels);
  if (!reaction || reaction.label === reactionLabel) return;
  reactionLabel = reaction.label;
  const style = styleFor(reaction.label, 'auto', true);
  if (style) { brows.release(); pickStyle(style); player.setLoop(true); voiceStatus('听到「' + reaction.userEmotionName + '」→ ' + reaction.label); }
}
async function startListening() {
  if (listening) return;
  speaker.stop(); hideCaption(0); // 打断：用户开口时停止朗读
  const config = settings();
  recognizer = createRecognizer(config.asrBackend, {language: config.asrLanguage === 'zh' || !config.asrLanguage ? 'zh-CN' : config.asrLanguage, settings,
    r2t2: {url: config.r2t2Url || undefined, secretKey: config.r2t2Secret || undefined, hotwords: config.r2t2Hotwords,
      language: /^zh/.test(config.asrLanguage || 'zh') ? 'zhen' : /^en/.test(config.asrLanguage) ? 'English' : 'zhen'}});
  listening = true; reactionLabel = '';
  $('micButton').setAttribute('aria-pressed', 'true'); $('micButton').textContent = '■ 说完了';
  voiceStatus('正在听（' + recognizer.name + '）…');
  let text = '';
  try {
    text = await recognizer.listen({
      onInterim: value => {
        if (!value) return;
        if (value.startsWith('（')) { voiceStatus(value); return; } // 录音中 / 识别中 提示，不进字幕
        voiceStatus('听到：' + value); showCaption(value, 1); react(value);
      },
      onLevel: value => { $('micLevel').style.width = (value * 100).toFixed(0) + '%'; },
    });
  } catch (error) { addMessage(error.message, 'error'); voiceStatus('识别失败'); }
  finally {
    listening = false; $('micLevel').style.width = '0%';
    $('micButton').setAttribute('aria-pressed', 'false'); $('micButton').textContent = '🎙 语音对话';
    hideCaption(0);
  }
  if (text) { react(text); converse(text, 'voice'); }
  else { voiceStatus('没有听清，点击麦克风再试'); if (player && reactionLabel) { player.returnToNeutral(); reactionLabel = ''; } }
}
async function converse(text, source = 'text') {
  speaker.stop(); hideCaption(0);
  brows.release();
  if (source !== 'voice') player?.returnToNeutral();
  $('sendChat').disabled = true; addMessage(text, 'user');
  voiceStatus('流明思考中…');
  let finished = false, currentSentence = '';
  try {
    const config = settings();
    const prompt = buildChatPrompt(player?.catalog) + '\n你的回复会被语音朗读并显示为字幕，请口语化、简短（一到三句），标签仍放在句首。';
    const messages = [{role: 'system', content: prompt}, ...history.slice(-12), {role: 'user', content: text}];
    const value = await api('services/chat', {endpoint: config.llmEndpoint, key: config.llmKey, model: config.llmModel, messages});
    const answer = value.choices?.[0]?.message?.content ?? value.output_text ?? value.text;
    if (typeof answer !== 'string' || !answer.trim()) throw new Error('LLM 没有返回文本回复');
    const said = parseReply(answer).text || spokenText(answer) || answer;
    addMessage(said);
    history.push({role: 'user', content: text}, {role: 'assistant', content: answer});
    let plan = null;
    try { plan = await chooseExpression(answer); } catch (error) { addMessage('表情响应：' + error.message, 'error'); }
    $('rawAnswer').textContent = answer + '\n\n表情：' + (plan ? plan.label + '（' + plan.source + '）' : '自然放松（未识别情绪）') +
      '\nTTS：' + ttsBackend();
    const backend = ttsBackend();
    voiceStatus(backend === 'runninghub' ? 'IndexTTS 2.5 合成中（RunningHub 通常需要数十秒）…' : '准备朗读…');
    await speaker.speak(said, {
      backend, fallback: $('ttsFallback').checked,
      onStart: () => { applyExpression(plan, true); if (!plan) player?.returnToNeutral(); voiceStatus('流明：' + (plan?.label || '自然放松')); },
      onSentence: (index, sentence) => { currentSentence = sentence; showCaption(sentence, 0); },
      onProgress: (index, value) => showCaption(currentSentence, value),
      onError: error => addMessage('朗读：' + error.message + ($('ttsFallback').checked ? '，已改用浏览器朗读' : ''), 'error'),
    });
    finished = true;
  } catch (error) { addMessage(error.message, 'error'); }
  finally {
    $('sendChat').disabled = false;
    brows.release(); player?.setLoop(false); player?.returnToNeutral(); hideCaption();
    if (!listening) voiceStatus('点击麦克风开始说话');
  }
  if (finished && source === 'voice' && $('autoListen').checked) startListening();
}
function frame(now) {
  const dt = last ? Math.min(.1, (now - last) / 1000) : 0; last = now;
  player?.tick(dt); brows.tick(dt); mouth.tick(dt, $('lipSync').checked ? speaker.level : 0); updateFace();
  const displayId = brows.label ? 'brow:' + brows.label : player?.style.id;
  if (player && displayedStyleId !== displayId) {
    displayedStyleId = displayId;
    $('currentExpression').textContent = brows.label || player.style.label;
    say(brows.label ? '单眉动作' : '自然放松', 'ok');
  }
  updateTelemetry();
  requestAnimationFrame(frame);
}
async function load() {
  try {
    const assets = httpAssets('../assets/reference-face/');
    const reference = await assets.json('reference.json'); assets.setGeometry(reference.geometry);
    const manifest = await assets.json(reference.avatar);
    face = await createReferenceView({container: $('preview'), manifest, assets});
    say('脸部已就绪', 'ok');
    const curve = await loadCurvePlayer('../models/expression/');
    player = curve;
    mouth = createMouthControl(face.channels.map(channel => channel.name));
    $('curveMeta').textContent = player.catalog.fps.toFixed(0) + ' Hz';
    pickStyle(player.catalog.styles.find(style => style.id === player.catalog.neutral_style) || player.catalog.styles[0]);
  } catch (error) { say(error.message, 'error'); $('runtimeStatus').textContent = '资源加载失败'; }
}
restoreSettings(); restoreVoice(); bind(); loadServiceDefaults(); requestAnimationFrame(frame); health(); load();
window.lumenReference = {selectExpression, converse, startListening, chooseExpression,
  voiceState: () => ({listening, speaking: speaker.speaking, level: speaker.level, expression: $('currentExpression').textContent,
    mouth: face ? shapes()['vrc.v_aa'] || 0 : 0})};
