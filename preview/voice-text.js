// 朗读文本切分与字幕进度：纯函数，可在 Node 中单元测试。

/**
 * 按句切分回复，用于逐句 TTS（先合成第一句即可开口，后续句子并行预取）与逐句字幕。
 * 句末标点保留在句中；过短的句子并入下一句，过长的句子在逗号处再切。
 */
export function splitSentences(text, {maxLength = 60, minLength = 6} = {}) {
  const source = String(text ?? '').replace(/\s+/g, ' ').trim();
  if (!source) return [];
  const pieces = source.match(/[^。！？!?；;…\n]+[。！？!?；;…]*[”」』"']?|[。！？!?；;…]+/g) || [source];
  const sentences = [];
  for (let piece of pieces.map(item => item.trim()).filter(Boolean)) {
    while (piece.length > maxLength) {
      const cut = Math.max(...['，', ',', '、', ' '].map(mark => piece.lastIndexOf(mark, maxLength)));
      const at = cut > minLength ? cut + 1 : maxLength;
      sentences.push(piece.slice(0, at).trim()); piece = piece.slice(at).trim();
    }
    if (piece) sentences.push(piece);
  }
  const merged = [];
  for (const sentence of sentences) {
    const previous = merged[merged.length - 1];
    const short = previous !== undefined && (previous.length < minLength || sentence.length < minLength);
    if (short && previous.length + sentence.length <= maxLength * 1.2) merged[merged.length - 1] = previous + sentence;
    else merged.push(sentence);
  }
  return merged;
}

/** 字幕逐字显示：progress 为 0–1 的播放进度，返回 {shown, rest}。 */
export function captionProgress(sentence, progress) {
  const characters = [...String(sentence ?? '')];
  const count = Math.round(characters.length * Math.max(0, Math.min(1, Number(progress) || 0)));
  return {shown: characters.slice(0, count).join(''), rest: characters.slice(count).join('')};
}

/** 没有音频时长时（浏览器朗读或无 TTS）按字数估计朗读时长，单位秒。 */
export function estimateDuration(text, charsPerSecond = 4.5) {
  const length = [...String(text ?? '').replace(/\s/g, '')].length;
  return Math.max(1.2, length / charsPerSecond);
}

/** 16 位 PCM 下采样：Float32 任意采样率 → Int16 16kHz（Confucius4-R2T2 流式接口要求）。 */
export function downsampleToInt16(input, inputRate, outputRate = 16000) {
  const ratio = inputRate / outputRate;
  const length = Math.floor(input.length / ratio);
  const output = new Int16Array(length);
  for (let i = 0; i < length; i++) {
    const start = Math.floor(i * ratio), end = Math.min(input.length, Math.floor((i + 1) * ratio));
    let sum = 0;
    for (let j = start; j < end; j++) sum += input[j];
    const value = Math.max(-1, Math.min(1, sum / Math.max(1, end - start)));
    output[i] = value < 0 ? value * 0x8000 : value * 0x7fff;
  }
  return output;
}
