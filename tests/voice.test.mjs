// 网页端情绪映射与字幕切分测试：node --test tests/
import assert from 'node:assert/strict';
import {readFileSync, existsSync} from 'node:fs';
import test from 'node:test';
import {detectEmotion, fallbackLabel, listeningReaction, parseReply, resolveLabel, spokenText} from '../preview/emotion-map.js';
import {captionProgress, downsampleToInt16, splitSentences} from '../preview/voice-text.js';

const catalogPath = new URL('../models/expression/catalog.json', import.meta.url);
// 与资源仓库 catalog.json 一致的标签；下载资源后优先使用真实目录。
const LABELS = existsSync(catalogPath) ? JSON.parse(readFileSync(catalogPath, 'utf8')).labels : [
  '卖萌和蔼安详', '厌烦厌恶', '大眼微笑', '头晕目眩', '害羞', '小眼震惊', '尴尬', '开心欢快', '微笑', '微笑_闭眼', '思考专注',
  '惊讶震惊', '意志坚定', '感觉无聊无趣', '担忧担心', '挑眉逗趣', '星星眼', '欣慰宽慰', '爱心眼', '生气愤怒', '痛苦疼痛',
  '睡眼朦胧敷衍', '自然放松', '进入陌生环境担忧左顾右盼', '道歉抱歉', '难过流泪', '震惊疑惑质问', '骄傲自豪'];

test('解析括号标签', () => {
  assert.deepEqual(parseReply('(开心欢快)早上好！'), {tag: '开心欢快', text: '早上好！', format: 'bracket'});
  assert.equal(parseReply('（害羞）别夸啦').tag, '害羞');
  assert.equal(parseReply('【思考专注】让我想想').tag, '思考专注');
  assert.equal(parseReply('[sad] 呜呜').tag, 'sad');
});

test('解析 JSON 回复（含代码围栏）', () => {
  assert.deepEqual(parseReply('{"expression":"星星眼","text":"好期待！"}'), {tag: '星星眼', text: '好期待！', format: 'json'});
  assert.equal(parseReply('```json\n{"emotion": "happy", "reply": "嗨"}\n```').tag, 'happy');
  assert.equal(parseReply('{不是 JSON').format, 'plain');
});

test('无标签时返回空标签与原文', () => {
  const parsed = parseReply('好的，我知道了。');
  assert.equal(parsed.tag, ''); assert.equal(parsed.text, '好的，我知道了。');
});

test('朗读文本去掉括号动作和 emoji', () => {
  assert.equal(spokenText('(微笑)你好😀（挥手）呀'), '你好呀');
});

test('标签对齐表情目录', () => {
  assert.deepEqual(resolveLabel('星星眼', LABELS), {label: '星星眼', method: 'exact'});
  assert.equal(resolveLabel('开心', LABELS).label, '开心欢快');
  assert.equal(resolveLabel('happy', LABELS).label, '开心欢快');
  assert.equal(resolveLabel('Sad', LABELS).label, '难过流泪');
  assert.equal(resolveLabel('有点担心地', LABELS).label, '担忧担心');
  assert.equal(resolveLabel('', LABELS), null);
  assert.equal(resolveLabel('完全无关的词语', LABELS), null);
});

test('目录缺少首选标签时顺延', () => {
  const labels = LABELS.filter(label => label !== '开心欢快');
  assert.equal(resolveLabel('happy', labels).label, '大眼微笑');
});

test('关键词兜底', () => {
  assert.equal(fallbackLabel('你竟然真的做到了？', LABELS).label, '惊讶震惊');
  assert.equal(fallbackLabel('对不起，是我搞错了', LABELS).label, '道歉抱歉');
  assert.equal(fallbackLabel('晚安，好困呀', LABELS).label, '睡眼朦胧敷衍');
  assert.equal(fallbackLabel('今天天气不错。', LABELS), null);
  // “你好”这类温和词权重较低，不会盖过真实情绪。
  assert.equal(detectEmotion('你好，我今天好难过').key, 'sad');
});

test('倾听反应是共情而不是镜像', () => {
  assert.equal(listeningReaction('我今天好难过', LABELS).label, '担忧担心');
  assert.equal(listeningReaction('气死我了', LABELS).label, '担忧担心');
  assert.equal(listeningReaction('我好开心', LABELS).label, '开心欢快');
  assert.equal(listeningReaction('今天天气不错', LABELS), null);
});

test('所有候选表情都来自目录', () => {
  for (const text of ['开心', '爱你', '好厉害', '竟然', '为什么', '让我想想', '难过', '担心', '生气', '恶心', '无聊', '好困',
    '害羞', '尴尬', '对不起', '骄傲', '还好', '加油', '逗你', '好疼', '头晕', '你好']) {
    const result = fallbackLabel(text, LABELS);
    assert.ok(result && LABELS.includes(result.label), text);
  }
});

test('逐句切分与合并短句', () => {
  assert.deepEqual(splitSentences('你好！今天过得怎么样？嗯。'), ['你好！今天过得怎么样？嗯。']);
  const long = '这是一句非常非常长的话，'.repeat(8) + '结束。';
  for (const sentence of splitSentences(long)) assert.ok(sentence.length <= 72, sentence);
  assert.equal(splitSentences(long).join(''), long);
  assert.deepEqual(splitSentences(''), []);
});

test('字幕进度', () => {
  assert.deepEqual(captionProgress('你好呀', .5), {shown: '你好', rest: '呀'});
  assert.deepEqual(captionProgress('你好', 2), {shown: '你好', rest: ''});
});

test('下采样到 16kHz int16', () => {
  const input = new Float32Array(48000).fill(.5);
  const output = downsampleToInt16(input, 48000);
  assert.equal(output.length, 16000);
  assert.ok(Math.abs(output[100] - 16383) <= 1);
});
