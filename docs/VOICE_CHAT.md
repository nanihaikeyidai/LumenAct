# 语音对话与表情联动

LumenAct 预览器可以直接和流明语音对话：**麦克风 → 语音识别（ASR）→ LLM 回复 + 表情标签 → TTS 朗读 + 字幕 → 开口时切换表情、口型随音量开合 → 说完回到自然放松**。用户说话时，流明也会根据听到的内容先做出共情反应。

所有后端都可替换；什么都不配置时，也可以用浏览器自带的识别与朗读体验整条链路（仍需配置 LLM）。

## 快速开始

```sh
python server.py
# 浏览器打开 http://127.0.0.1:8766/preview/
```

1. 在“LLM / TTS 配置”中填写 LLM Endpoint、模型名和 Key（或用环境变量，见下文）。
2. 在“语音对话配置”中选择 ASR 后端与 TTS 后端，点“保存语音配置”。
3. 点聊天区的 **🎙 语音对话**，说一句话；停顿约 0.9 秒自动结束，也可以点“■ 说完了”。勾选 **连续对话** 后，流明说完会自动继续听。说话时再点麦克风可打断朗读。

没有任何密钥时可以用模拟服务把整条链路跑通：

```sh
python tests/mock_services.py --port 9100          # 模拟 LLM / TTS / ASR / RunningHub
LUMENACT_LLM_ENDPOINT=http://127.0.0.1:9100/v1/chat/completions \
LUMENACT_TTS_ENDPOINT=http://127.0.0.1:9100/v1/audio/speech \
LUMENACT_ASR_ENDPOINT=http://127.0.0.1:9100/v1/audio/transcriptions \
python server.py
```

## 语音识别（ASR）后端

| 后端 | 说明 | 需要 |
| --- | --- | --- |
| `browser` 浏览器 Web Speech（默认） | Chrome / Edge 内置识别，边说边出字。识别由浏览器厂商的在线服务完成。 | 无 |
| `r2t2` **Confucius4-R2T2 流式**（推荐本地方案） | 网易有道开源的稳定前缀流式 ASR，已输出的字不会回改，倾听反应不会闪烁。网页直接连接官方 `ws_server.py`。 | NVIDIA GPU；按官方仓库部署 |
| `openai` OpenAI 兼容 Whisper | 录完一句后上传 `/v1/audio/transcriptions`（OpenAI、Groq、SiliconFlow 等兼容服务）。 | Endpoint、Key |
| `local` faster-whisper | 本机离线识别：`pip install -r requirements-voice.txt`，模型名填 `small` / `medium` 等，首次使用自动下载。 | CPU 即可，`small` 以上效果较好 |

### Confucius4-R2T2

- 代码：<https://github.com/netease-youdao/Confucius4-R2T2>（Apache-2.0）；权重：Hugging Face `netease-youdao/Confucius4-R2T2`、GGUF 版 `netease-youdao/Confucius4-R2T2-GGUF`，适用**网易模型使用许可协议**（与代码许可不同，使用前请阅读）。
- 原理：在 Qwen3-ASR-1.7B 上做“最长稳定前缀”（Longest Stable Prefix, LSP）后训练，只提交确定不会再变的前缀，不确定时输出 `Wait` 等待更多音频；解码块可在 80 ms–2 s 之间配置。
- 部署（官方，流式需 vLLM + NVIDIA GPU）：

  ```sh
  git clone https://github.com/netease-youdao/Confucius4-R2T2.git && cd Confucius4-R2T2
  pip install -e .            # 或使用官方推荐的 qwenllm/qwen3-asr Docker 镜像
  hf download FireRedTeam/FireRedVAD --include "Stream-VAD/*" --local-dir checkpoints/vad
  ./run_start_server.sh start --model_path /path/to/Confucius4-R2T2 --port 8272 --gpu 0
  ```

- LumenAct 中选择 “Confucius4-R2T2 流式”，WebSocket 默认 `ws://127.0.0.1:8272/asr_stream_api_v1`。`secret_key` 默认 `test0102`：这是官方 `ws_server.py` 中写死的调试密钥，若你修改了服务端的 `secret_key_list`，在这里同步填写。热词 / 上下文会作为 `system_prompt` 发送。
- 网页端协议与官方 `ws_client.py` 一致：先发 JSON 头（`sample_rate: 16000`、`language: zhen`、`use_vad: false`、`mode: slow`），再发 16 kHz 单声道 int16 PCM（每帧 160 ms），结束时发送 `YOUDAO_ONETIME_ASR_STREAM_EOS`；服务端每条 `msg.text` 是新增片段，直接拼接。
- 没有 GPU：可用 `python tests/mock_r2t2.py`（需 `pip install websockets`）模拟该协议检查网页端。T8star 的 ComfyUI 节点 `confucius4-r2t2-t8`（GGUF Q8，支持 CPU / CUDA）和 Windows 整合包提供另一种运行方式，但它们不提供上述 WebSocket 接口，LumenAct 不能直接连接。

## 语音合成（TTS）后端

| 后端 | 说明 |
| --- | --- |
| `runninghub` **IndexTTS 2.5 · RunningHub**（配置齐全时默认） | 调用 RunningHub 工作流 [1970149188463980545](https://www.runninghub.cn/post/1970149188463980545)，用你的参考音色克隆。 |
| `indextts-local` IndexTTS 本地 / 自建 HTTP | `POST {"text", "reference_audio"}`，返回音频（或 JSON 的 `audio_base64` / `audio_url`）。`tools/indextts_http_server.py` 是基于官方 index-tts `IndexTTS2` 接口的适配示例。 |
| `openai` OpenAI 兼容云端 TTS | `/v1/audio/speech`，配置 Endpoint / 模型 / 音色 / Key，适用于多数云服务商。 |
| `browser` 浏览器朗读 | `speechSynthesis`，无需配置；音色取决于系统。 |
| `off` | 不出声，只显示字幕和表情。 |

勾选“失败时浏览器朗读”后，服务端 TTS 出错会自动改用浏览器朗读，对话不中断。

### IndexTTS 2.5 · RunningHub

```sh
export RUNNINGHUB_API_KEY=你的RunningHub密钥        # 自动取第一段 32 位十六进制
export LUMENACT_INDEXTTS_REF=/path/to/your-voice.wav  # 参考音色，首次使用自动上传，之后复用
python server.py
```

- 调用流程：`/task/openapi/upload` 上传参考音色（按文件 SHA-256 记录，只传一次）→ `/task/openapi/create`（节点 `46.audio` = 参考音色，`47.prompt` = 台词）→ 轮询 `/task/openapi/status` → `/task/openapi/outputs` 下载音频。节点号和工作流 ID 都可通过环境变量或 `services.example.json` 修改。
- **延迟与费用**：每次合成都是一个云端任务，实测一句 7 个字（约 1.5 秒音频）耗时约 39 秒，扣 5.27 点。因此 RunningHub 后端把整段回复合成一次（不逐句拆分），并在 `voice-cache/` 按“后端 + 音色 + 文本”缓存，同一句话不重复扣点。等待期间界面显示“IndexTTS 2.5 合成中”，字幕与表情在音频到达时一起开始。实时对话建议改用本地 IndexTTS 或云端 TTS。
- 参考音色文件不要提交到仓库；`voice-cache/` 已被 `.gitignore` 忽略。

## 表情如何选择

LLM 的系统提示要求回复以 `(标签)台词` 开头，标签取自当前表情目录（`models/expression/catalog.json` 的 28 个标签，如 `开心欢快`、`担忧担心`、`星星眼`）。也接受 `{"expression": "标签", "text": "台词"}` JSON，以及 `（）`、`【】`、`[]` 括号。

1. 标签与目录**完全一致** → 直接使用（同一标签有多个片段时随机挑一个，避免重复）。
2. 其他标签（如 `有点担心地`、`happy`）→ 交给本地语义模型（与 `/api/semantic` 相同）；语义模型不可用时，用包含关系、英文别名和关键词近似对齐。
3. 没有标签 → 对台词做关键词兜底（`preview/emotion-map.js` 中约 20 类情绪词表，按目录中存在的候选顺延）；仍无命中且语义模型就绪时，按台词语义选择。
4. 都失败 → 自然放松。

“高层原文 / DIRECTOR TRACE”会显示本次表情及来源（LLM 标签 / 语义模型 / 关键词兜底）。

**时机**：表情在**开口那一刻**切换（音频到达后），朗读期间循环保持，最后一句结束后 0.4 秒平滑回到自然放松。

**倾听反应**：识别出的文字（流式识别边听边分析）会做情绪分析，流明先做出共情表情，例如用户说难过/生气 → 担忧担心，开心 → 开心欢快，夸奖 → 害羞。

**口型**：用 Web Audio 读取朗读音频的音量包络，叠加到参考脸的 `vrc.v_aa` / `vrc.v_ou` / `vrc.v_ih` 视位形态键（没有时回退 `mouth_a`）。浏览器朗读拿不到音频流，口型按节奏模拟。这是音量驱动的简单开合，不是音素级口型。

**字幕**：回复文本按句显示在脸部画面下方，随播放进度逐字点亮；浏览器朗读按 `boundary` 事件推进。

## 配置与密钥

- 网页里填写的 Key 只在本机浏览器内，勾选“保存密钥”才写入 localStorage。
- 也可以把 Endpoint 与 Key 放在服务端环境变量（见 `.env.example`）。服务端密钥**只会发往同名环境变量配置的 Endpoint**；网页填了别的地址时不会附带服务端密钥，`/api/services/config` 只返回“是否已配置”。
- 非密钥默认值可写进 JSON，用 `python server.py --services-profile services.local.json` 加载（示例见 `services.example.json`）。

## 测试

```sh
python -m unittest discover -s tests      # 服务端：TTS / ASR / RunningHub 流程、密钥边界（全部使用本地模拟服务）
node --test tests/voice.test.mjs          # 网页端：标签解析、表情映射、关键词兜底、倾听反应、字幕切分
```

## 已知限制

- 浏览器麦克风需要 `localhost` 或 HTTPS；Web Speech 识别仅 Chrome / Edge 等支持，且需联网。
- Confucius4-R2T2 官方流式服务需要 NVIDIA GPU；LumenAct 只验证了与其协议一致的模拟服务。
- RunningHub 合成有数十秒排队延迟并按次扣点。
- 回声消除依赖浏览器；外放时开启“连续对话”可能把流明的声音录进去，建议戴耳机。
