# 本地接口与扩展

服务仅绑定 `127.0.0.1`。以下路径相对当前预览服务。

## GET /api/health

返回语义模型的 `ready`、`error`、`model` 和 `device`。模型缺少依赖时返回明确错误，静态参考预览仍可用。

## POST /api/semantic

```json
{"intent": "开心地打招呼", "text": "早上好！"}
```

返回 `expression`、`confidence`、`context_id`、`context_name`、`speech_style`、`top_labels`、`elapsed_ms` 及模型名称。耗时是一次语义选择处理时间，不包括 LLM、TTS、首轮权重加载或动画播放。

参考客户端按类别与可用上下文选择固定片段。输出不是连续面部控制值，也不是下一帧预测。

## 用户服务代理

`POST /api/services/chat`：

```json
{
  "endpoint": "https://example.com/v1/chat/completions",
  "model": "your-model",
  "key": "your-key",
  "messages": [{"role": "user", "content": "你好"}]
}
```

`POST /api/services/speech`：

```json
{
  "endpoint": "https://example.com/v1/audio/speech",
  "model": "your-tts-model",
  "voice": "your-voice",
  "key": "your-key",
  "text": "你好"
}
```

speech 可加 `"backend"`：`runninghub`（IndexTTS 2.5 RunningHub 工作流）、`indextts-local`（自建 IndexTTS HTTP）、`openai`（缺省，兼容旧请求）。RunningHub / 本地 IndexTTS 的参考音色、节点和密钥只从服务端环境变量或 `--services-profile` 读取，请求体只需 `{"backend": "runninghub", "text": "你好"}`。相同后端、音色和文本的结果会缓存在 `voice-cache/`。

`POST /api/services/transcribe`（请求体上限 24MB）：

```json
{"backend": "openai", "audio": "<base64 录音>", "mime": "audio/webm", "language": "zh",
 "endpoint": "https://example.com/v1/audio/transcriptions", "model": "whisper-1", "key": "your-key"}
```

返回 `{"text": "...", "backend": "openai"}`。`backend: "local"` 使用本机 faster-whisper（`requirements-voice.txt`）。浏览器识别与 Confucius4-R2T2 流式识别在网页内直接完成，不经过此接口。

`GET /api/services/config` 返回非密钥默认值、`ttsBackend` / `asrBackend`，以及 `serverKeys`（各服务是否已在服务端配置密钥，不含密钥本身）。网页请求未填 Endpoint / Key 时使用服务端环境变量 `LUMENACT_LLM_*`、`LUMENACT_TTS_*`、`LUMENACT_ASR_*`；服务端密钥只发往同名 Endpoint。

chat 返回服务商 JSON；speech 返回服务商音频。环境变量与各后端部署见 [语音对话指南](VOICE_CHAT.md)。服务端不保存这些请求，不自带任何账号或服务器配置。

## 网页控制

```js
await window.lumenReference.selectExpression('开心', '早上好');
window.lumenReference.chooseClip('0');
window.lumenReference.setShapes({mouth_a: 50, eyebrow_up_L: 30});
window.lumenReference.clearOverrides();
await window.lumenReference.converse('我今天好开心');   // 走完整对话：LLM → 表情 → 朗读 + 字幕
window.lumenReference.startListening();                // 开始一次语音输入
```

`setShapes` 使用已加载模型的实际形态键名称，数值为 0–100，手动覆盖持续到清除或选择其他片段。它只应用输入值，不生成动作。外部系统可以自行决定这些值如何计算。
