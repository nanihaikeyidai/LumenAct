// 语音对话的情绪解析与表情映射：纯函数，不依赖 DOM，可在 Node 中单元测试。
// 优先级：LLM 输出的表情标签 → 语义模型 → 关键词兜底 → 自然放松。

// 粗粒度情绪 → 关键词与候选表情（按顺序取当前模型目录中第一个存在的标签）。
export const EMOTIONS = {
  joy: {name: '开心', labels: ['开心欢快', '大眼微笑', '微笑'],
    words: ['开心', '高兴', '快乐', '哈哈', '嘻嘻', '太好了', '好耶', '真棒', '太棒', '耶', '愉快', '幸福', '好开心', 'happy', 'glad', 'yay']},
  love: {name: '喜爱', labels: ['爱心眼', '害羞', '卖萌和蔼安详'],
    words: ['爱你', '喜欢你', '最喜欢', '么么', '亲亲', '心动', '好可爱', '抱抱', '贴贴', 'love']},
  admire: {name: '崇拜期待', labels: ['星星眼', '大眼微笑'],
    words: ['好厉害', '太厉害', '太酷', '好酷', '期待', '惊艳', '好美', '漂亮', '好牛', '崇拜', 'amazing', 'wow']},
  surprise: {name: '惊讶', labels: ['惊讶震惊', '小眼震惊'],
    words: ['竟然', '居然', '天哪', '天啊', '我的天', '真的吗', '不会吧', '没想到', '吓我', '吓死', '震惊', '哇', 'surprise']},
  doubt: {name: '疑惑质问', labels: ['震惊疑惑质问', '思考专注'],
    words: ['为什么', '怎么会', '你确定', '凭什么', '什么意思', '真的假的', '？？', '??', '疑惑', '质问']},
  think: {name: '思考', labels: ['思考专注'],
    words: ['让我想想', '想一想', '思考', '分析', '也许', '或许', '可能', '考虑', '琢磨', '研究', 'think', 'maybe']},
  sad: {name: '难过', labels: ['难过流泪', '担忧担心'],
    words: ['难过', '伤心', '哭', '呜呜', '遗憾', '心疼', '失去', '去世', '分手', '失败了', '委屈', '想哭', 'sad', 'cry']},
  worry: {name: '担忧', labels: ['担忧担心', '进入陌生环境担忧左顾右盼'],
    words: ['担心', '害怕', '紧张', '焦虑', '小心', '危险', '不安', '恐怖', '好怕', '陌生', 'worried', 'afraid']},
  angry: {name: '生气', labels: ['生气愤怒', '厌烦厌恶'],
    words: ['生气', '气死', '愤怒', '可恶', '混蛋', '滚', '火大', '过分', '岂有此理', 'angry']},
  disgust: {name: '厌烦', labels: ['厌烦厌恶', '感觉无聊无趣'],
    words: ['恶心', '讨厌', '好烦', '烦死', '嫌弃', '受不了', '恶心死']},
  bored: {name: '无聊', labels: ['感觉无聊无趣', '睡眼朦胧敷衍'],
    words: ['无聊', '没意思', '好闲', '没劲', 'boring']},
  sleepy: {name: '困倦', labels: ['睡眼朦胧敷衍', '感觉无聊无趣'],
    words: ['好困', '困了', '想睡', '睡觉', '晚安', '好累', '累了', '疲惫', '熬夜', 'sleepy', 'tired']},
  shy: {name: '害羞', labels: ['害羞', '尴尬'],
    words: ['害羞', '脸红', '羞', '人家', '讨厌啦', '别夸']},
  awkward: {name: '尴尬', labels: ['尴尬', '害羞'],
    words: ['尴尬', '呃', '额', '那个……', '好像搞错', '社死']},
  apology: {name: '道歉', labels: ['道歉抱歉', '尴尬'],
    words: ['对不起', '抱歉', '不好意思', '是我的错', '原谅', 'sorry']},
  proud: {name: '自豪', labels: ['骄傲自豪', '意志坚定'],
    words: ['骄傲', '自豪', '厉害吧', '搞定', '轻松拿下', '小菜一碟', '交给我', '本小姐']},
  relief: {name: '欣慰', labels: ['欣慰宽慰', '微笑_闭眼', '微笑'],
    words: ['还好', '放心', '幸好', '松了口气', '太好了没事', '安心', '辛苦了', '没关系']},
  determined: {name: '坚定', labels: ['意志坚定'],
    words: ['加油', '一定', '坚持', '相信', '绝不', '决心', '努力']},
  playful: {name: '逗趣', labels: ['挑眉逗趣', '大眼微笑'],
    words: ['逗你', '开玩笑', '调皮', '嘿嘿', '猜猜', '你猜', '坏笑', '捉弄']},
  pain: {name: '痛苦', labels: ['痛苦疼痛', '难过流泪'],
    words: ['好疼', '好痛', '疼死', '痛死', '受伤', '难受', 'hurt', 'pain']},
  dizzy: {name: '头晕', labels: ['头晕目眩', '小眼震惊'],
    words: ['头晕', '晕了', '好晕', '转晕', '眼花', '绕晕']},
  gentle: {name: '温和', labels: ['卖萌和蔼安详', '微笑'],
    words: ['你好', '早上好', '晚上好', '欢迎', '谢谢', '好的', '嗯嗯', '当然', '陪你']},
};

// 英文或常见近义标签的直接别名。
const ALIASES = {
  happy: 'joy', joy: 'joy', smile: 'gentle', love: 'love', excited: 'admire', surprised: 'surprise',
  surprise: 'surprise', confused: 'doubt', thinking: 'think', think: 'think', sad: 'sad', worried: 'worry',
  fear: 'worry', scared: 'worry', angry: 'angry', disgust: 'disgust', bored: 'bored', sleepy: 'sleepy',
  tired: 'sleepy', shy: 'shy', embarrassed: 'awkward', awkward: 'awkward', sorry: 'apology', proud: 'proud',
  relieved: 'relief', determined: 'determined', playful: 'playful', pain: 'pain', dizzy: 'dizzy',
  neutral: 'neutral', calm: 'neutral', 平静: 'neutral', 自然: 'neutral', 微笑: 'gentle', 笑: 'joy',
};

// 用户情绪 → 流明在倾听时的反应（共情，而不是镜像）。
const REACTIONS = {
  joy: 'joy', love: 'shy', admire: 'proud', surprise: 'surprise', doubt: 'think', think: 'think',
  sad: 'worry', worry: 'worry', angry: 'worry', disgust: 'awkward', bored: 'playful', sleepy: 'relief',
  shy: 'gentle', awkward: 'gentle', apology: 'relief', proud: 'admire', relief: 'relief',
  determined: 'determined', playful: 'playful', pain: 'worry', dizzy: 'worry', gentle: 'gentle',
};

const BRACKETS = /^\s*[（(\[【]\s*([^（）()\[\]【】\n]{1,40}?)\s*[）)\]】]/;
const ANY_BRACKET = /[（(\[【]\s*([^（）()\[\]【】\n]{1,40}?)\s*[）)\]】]/;
const TAG_KEYS = ['expression', 'emotion', 'tag', 'label', 'face', 'mood', '表情', '情绪'];
const TEXT_KEYS = ['text', 'reply', 'content', 'say', 'speech', 'answer', '台词', '回复'];

/** 去掉括号动作与 emoji，只保留要朗读的台词。 */
export function spokenText(text) {
  return String(text ?? '')
    .replace(/[（(\[【][^（）()\[\]【】\n]*[）)\]】]/g, '')
    .replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, '')
    .replace(/\s+/g, ' ').trim();
}

function parseJsonReply(answer) {
  const source = String(answer).trim().replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '');
  if (!source.startsWith('{')) return null;
  try {
    const value = JSON.parse(source);
    if (!value || typeof value !== 'object') return null;
    const tag = TAG_KEYS.map(key => value[key]).find(item => typeof item === 'string' && item.trim());
    const text = TEXT_KEYS.map(key => value[key]).find(item => typeof item === 'string');
    if (tag === undefined && text === undefined) return null;
    return {tag: tag ? tag.trim() : '', text: spokenText(text ?? ''), format: 'json'};
  } catch { return null; }
}

/**
 * 解析 LLM 回复。支持：
 *   (标签)台词   （标签）台词   【标签】台词   [标签]台词
 *   {"expression": "标签", "text": "台词"}（也接受 emotion/tag 等键，可带 ```json 围栏）
 * 返回 {tag, text, format}；没有标签时 tag 为空字符串。
 */
export function parseReply(answer) {
  const json = parseJsonReply(answer);
  if (json) return json;
  const source = String(answer ?? '');
  const match = BRACKETS.exec(source) || ANY_BRACKET.exec(source);
  return {tag: match ? match[1].trim() : '', text: spokenText(source), format: match ? 'bracket' : 'plain'};
}

function firstAvailable(candidates, labels) {
  return candidates.find(label => labels.includes(label)) || null;
}

/** 按关键词给文本打分，返回得分最高的粗粒度情绪 {key, score, hits}，没有命中时返回 null。 */
export function detectEmotion(text) {
  const source = String(text ?? '').toLowerCase();
  if (!source.trim()) return null;
  let best = null;
  for (const [key, info] of Object.entries(EMOTIONS)) {
    const hits = info.words.filter(word => source.includes(word.toLowerCase()));
    if (!hits.length) continue;
    // 较长的关键词更具体，权重更高；“你好/好的”这类温和词权重减半，避免盖过真实情绪。
    let score = hits.reduce((sum, word) => sum + Math.min(4, word.length), 0);
    if (key === 'gentle') score *= .5;
    if (!best || score > best.score) best = {key, score, hits};
  }
  return best;
}

/** 粗粒度情绪 → 当前目录中可用的表情标签。 */
export function emotionToLabel(key, labels) {
  if (key === 'neutral') return firstAvailable(['自然放松', '微笑'], labels);
  const info = EMOTIONS[key];
  return info ? firstAvailable(info.labels, labels) : null;
}

/**
 * 把 LLM 给出的标签对齐到表情目录：精确匹配 → 包含关系 → 别名 → 标签内关键词。
 * 返回 {label, method}，无法对齐时返回 null（调用方可再交给语义模型）。
 */
export function resolveLabel(tag, labels) {
  const value = String(tag ?? '').trim();
  if (!value || !labels?.length) return null;
  if (labels.includes(value)) return {label: value, method: 'exact'};
  const contained = labels.filter(label => label.includes(value) || value.includes(label))
    .sort((a, b) => b.length - a.length);
  if (value.length >= 2 && contained.length) return {label: contained[0], method: 'contains'};
  const alias = ALIASES[value.toLowerCase()];
  if (alias) {
    const label = emotionToLabel(alias, labels);
    if (label) return {label, method: 'alias'};
  }
  const detected = detectEmotion(value);
  const label = detected && emotionToLabel(detected.key, labels);
  return label ? {label, method: 'keyword'} : null;
}

/** 关键词兜底：LLM 没给标签时，根据回复内容挑选表情。 */
export function fallbackLabel(text, labels) {
  const detected = detectEmotion(text);
  const label = detected && emotionToLabel(detected.key, labels);
  return label ? {label, method: 'keyword', emotion: detected.key, hits: detected.hits} : null;
}

/** 倾听反应：分析用户这句话的情绪，返回流明边听边做出的表情。 */
export function listeningReaction(userText, labels) {
  const detected = detectEmotion(userText);
  if (!detected) return null;
  const label = emotionToLabel(REACTIONS[detected.key] || detected.key, labels);
  return label ? {label, userEmotion: detected.key, userEmotionName: EMOTIONS[detected.key].name} : null;
}
