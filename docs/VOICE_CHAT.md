# 语音对话：本地部署与使用指南

本文一步步说明如何在自己的电脑上部署 LumenAct 预览器，并开启**语音对话与表情联动**：

**麦克风 → 语音识别（ASR）→ LLM 回复（带表情标签）→ 语音合成（TTS）朗读 + 字幕 → 开口时切换表情、口型随音量开合 → 说完平滑回到自然放松。** 用户说话时，流明会根据听到的内容先做出共情表情。

所有后端都可以替换。只想先看效果、手上没有任何密钥时，可以直接跳到 [第 9 节 模拟 / 离线体验](#9-模拟--离线体验)。

目录

1. [准备环境](#1-准备环境)
2. [获取代码](#2-获取代码)
3. [创建虚拟环境并安装依赖](#3-创建虚拟环境并安装依赖)
4. [下载模型资源](#4-下载模型资源)
5. [配置服务（网页 / 环境变量 / 配置文件）](#5-配置服务)
6. [启动并打开预览器](#6-启动并打开预览器)
7. [在网页中使用语音对话](#7-在网页中使用语音对话)
8. [各后端的部署方法](#8-各后端的部署方法)
9. [模拟 / 离线体验](#9-模拟--离线体验)
10. [表情是怎么选出来的](#10-表情是怎么选出来的)
11. [测试](#11-测试)
12. [常见问题](#12-常见问题)

---

## 1. 准备环境

| 项目 | 要求 |
| --- | --- |
| 操作系统 | Windows 10/11、macOS、Linux 桌面版 |
| Python | **3.10 或以上**（Windows 建议 64 位 3.11 / 3.12；本仓库在 Linux 上用 3.13 验证过） |
| 浏览器 | 桌面版 **Chrome 或 Edge**（需要 WebGL2；“浏览器识别”只在 Chrome / Edge 等可用） |
| 网络 | 首次下载资源和依赖需要访问 Hugging Face 与 PyPI |
| 磁盘 | 模型资源约 180 MB；faster-whisper 模型另计（见 [8.1](#81-语音识别asr)） |
| 可选 | NVIDIA GPU：仅 Confucius4-R2T2 流式识别、本机 IndexTTS 需要；Node.js 18+：仅运行网页端单元测试需要 |

Windows 安装 Python 时勾选 **Add Python to PATH**。安装后在 PowerShell 中确认：

```powershell
py -3 --version
```

macOS / Linux：

```sh
python3 --version
```

## 2. 获取代码

```sh
git clone https://github.com/nanihaikeyidai/LumenAct.git
cd LumenAct
```

> 语音对话功能在合并前位于 `feat/voice-chat-emotion` 分支：`git clone -b feat/voice-chat-emotion https://github.com/nanihaikeyidai/LumenAct.git`。

没有 Git 时，也可以在 GitHub 页面点 **Code → Download ZIP**，完整解压后进入能看到 `server.py` 的目录。以下命令都在这个目录中执行。

## 3. 创建虚拟环境并安装依赖

`requirements.txt` 是本地语义模型所需（numpy、onnxruntime、tokenizers）；`requirements-voice.txt` 是**可选**的本机 faster-whisper 识别。只用浏览器识别、Confucius4-R2T2 或云端 Whisper 时，不需要安装后者。

**macOS / Linux**

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-voice.txt   # 可选：本机 faster-whisper
```

**Windows PowerShell**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-voice.txt   # 可选：本机 faster-whisper
```

如果 PowerShell 提示“禁止运行脚本”，先执行一次 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`，或者不激活环境，直接用 `.\.venv\Scripts\python.exe` 代替下文的 `python`。

> 注意：`start_preview.bat`、`install_semantic.bat` 使用的是系统 Python，不是 `.venv`。用了虚拟环境就始终用同一个解释器启动（`python server.py` 或 `.\.venv\Scripts\python.exe server.py`），否则会出现“依赖已安装但语义模型未就绪”。

## 4. 下载模型资源

模型和脸部资源不在 GitHub，而在 Hugging Face [AaBbcoder/LumenAct](https://huggingface.co/AaBbcoder/LumenAct)。下载器会按 `release-manifest.json` 固定的版本下载，并校验大小和 SHA-256：

```sh
python download_assets.py          # 下载并校验，完整文件会跳过
python download_assets.py --check  # 离线检查资源是否完整
```

看到 `Assets downloaded and verified. You can start the preview.` 或 `All public assets are present and verified.` 即成功。资源会放到下列位置（相对项目根目录，与 Hugging Face 仓库内的路径一致）：

| 路径 | 内容 |
| --- | --- |
| `models/semantic/config.json`、`selector.onnx`、`tokenizer/tokenizer.json` | 本地语义模型（约 150 MB） |
| `models/expression/catalog.json`、`curves.f32` | 表情目录（28 个标签、97 段表演）与表演曲线 |
| `assets/reference-face/*.json`、`face_texture_0.png` | 网页预览用的流明参考脸 |
| `assets/reference-face/lumen-reference-face.blend` | Blender 参考脸（角色适配用，预览不需要） |

也可以手动从 Hugging Face 仓库的固定提交 `df8126a2a854735227ec81b7f12ab62d49a6d989` 下载同名文件，放到上表相同的相对路径，再运行 `python download_assets.py --check` 确认。这些文件已被 `.gitignore` 忽略，不要提交到 Git。

## 5. 配置服务

语音对话需要一个 **LLM**（必需），ASR 和 TTS 可以先用浏览器自带的能力。配置有三种方式，可以混用：

| 方式 | 适合 | 优先级 |
| --- | --- | --- |
| 网页面板（第 7 节） | 个人在本机使用；Key 只保存在浏览器里 | 网页里已保存的设置最优先 |
| `--services-profile` 配置文件 | 固定的非密钥默认值（地址、模型名、后端选择、参考音色路径） | 其次 |
| 环境变量 | 密钥、RunningHub 等只应留在服务端的配置 | 最后 |

### 5.1 环境变量

`server.py` **不会自动读取 `.env` 文件**。复制 `.env.example` 为 `.env`，删掉用不到的行、填好需要的值，然后在启动前加载：

macOS / Linux（bash / zsh）：

```sh
cp .env.example .env
# 编辑 .env 后：
set -a; . ./.env; set +a
python server.py
```

Windows PowerShell（当前窗口有效）：

```powershell
Copy-Item .env.example .env
# 编辑 .env 后，把其中的 NAME=VALUE 行载入当前窗口：
Get-Content .env | Where-Object { $_ -match '^\s*[A-Z_]+=' } | ForEach-Object {
  $name, $value = $_ -split '=', 2; Set-Item "env:$($name.Trim())" $value.Trim() }
python server.py
```

也可以逐个设置，例如 `$env:LUMENACT_LLM_KEY = "sk-..."`（PowerShell）或 `export LUMENACT_LLM_KEY=sk-...`（bash）。

> `.env` 里留空的行（如 `RUNNINGHUB_API_KEY=`）会把已有的同名环境变量覆盖为空，不用的行请删除。`.env` 已被 `.gitignore` 忽略。

**服务端密钥只会发往同名环境变量配置的 Endpoint**：网页里填了别的地址时，不会附带服务端密钥；`/api/services/config` 只告诉网页“是否已配置”，不返回密钥本身。

| 变量 | 作用 | 默认值 |
| --- | --- | --- |
| **LLM** | | |
| `LUMENACT_LLM_ENDPOINT` | OpenAI 兼容的 `/v1/chat/completions` 完整地址 | 无 |
| `LUMENACT_LLM_MODEL` | 模型名 | 无 |
| `LUMENACT_LLM_KEY` | API Key | 无 |
| **TTS 选择** | | |
| `LUMENACT_TTS_BACKEND` | 默认 TTS 后端：`runninghub` / `indextts-local` / `openai` / `browser` / `off` | 已配置 RunningHub 密钥和参考音色时为 `runninghub`，否则配置了 `LUMENACT_TTS_ENDPOINT` 时为 `openai`，再否则为 `browser` |
| **IndexTTS 2.5 · RunningHub** | | |
| `RUNNINGHUB_API_KEY` | RunningHub API Key；会取其中第一段 32 位十六进制字符 | 无 |
| `LUMENACT_INDEXTTS_REF` | 参考音色 wav 的本机路径（RunningHub 首次使用时上传；本机 IndexTTS 也用它） | 无 |
| `LUMENACT_RH_REF_FILENAME` | 已上传到 RunningHub 的参考音色 `fileName`（如 `api/xxxx.wav`），填了就不再上传 | 无 |
| `LUMENACT_RH_WORKFLOW_ID` | 工作流 ID | `1970149188463980545` |
| `LUMENACT_RH_TEXT_NODE` / `LUMENACT_RH_TEXT_FIELD` | 台词所在节点与字段 | `47` / `prompt` |
| `LUMENACT_RH_AUDIO_NODE` / `LUMENACT_RH_AUDIO_FIELD` | 参考音色节点与字段 | `46` / `audio` |
| `LUMENACT_RH_BASE` | RunningHub 地址（海外站或测试用模拟服务时修改） | `https://www.runninghub.cn` |
| `LUMENACT_RH_POLL` / `LUMENACT_RH_TIMEOUT` | 轮询间隔 / 单次任务超时（秒） | `3` / `240` |
| **本机 / 自建 IndexTTS** | | |
| `LUMENACT_INDEXTTS_ENDPOINT` | 自建 IndexTTS HTTP 地址，如 `http://127.0.0.1:9880/tts` | 无 |
| **OpenAI 兼容云端 TTS** | | |
| `LUMENACT_TTS_ENDPOINT` | `/v1/audio/speech` 完整地址 | 无 |
| `LUMENACT_TTS_MODEL` / `LUMENACT_TTS_VOICE` | 模型名 / 音色名 | 请求时缺省为 `tts-1` / `alloy` |
| `LUMENACT_TTS_KEY` | API Key | 无 |
| `LUMENACT_TTS_CACHE` | 合成结果缓存目录 | 项目下的 `voice-cache/` |
| **ASR** | | |
| `LUMENACT_ASR_BACKEND` | 默认识别后端：`browser` / `r2t2` / `openai` / `local` | `browser` |
| `LUMENACT_ASR_ENDPOINT` | OpenAI 兼容 `/v1/audio/transcriptions` 地址（`openai` 后端） | 无 |
| `LUMENACT_ASR_MODEL` | `openai` 后端的模型名（缺省 `whisper-1`），或 `local` 后端的 faster-whisper 模型（缺省 `small`） | 无 |
| `LUMENACT_ASR_KEY` | `openai` 后端的 API Key | 无 |
| `LUMENACT_ASR_LANGUAGE` | 识别语言，如 `zh`、`en` | `zh` |

### 5.2 配置文件（非密钥）

```sh
cp services.example.json services.local.json   # Windows：Copy-Item services.example.json services.local.json
python server.py --services-profile services.local.json
```

`services.local.json` 已被 `.gitignore` 忽略（`*.local.json`）。**示例里的 `example.com` 地址和 `/path/to/...` 路径都要改成自己的**，不用的字段可以删除。可用字段：

| 字段 | 对应 |
| --- | --- |
| `llmEndpoint`、`llmModel` | LLM 地址与模型（网页默认值） |
| `ttsEnabled` | 网页“启用 TTS”默认是否勾选 |
| `ttsBackend`、`ttsEndpoint`、`ttsModel`、`ttsVoice` | TTS 后端与 OpenAI 兼容 TTS 参数 |
| `indexttsRefAudio`、`indexttsLocalEndpoint` | 同 `LUMENACT_INDEXTTS_REF`、`LUMENACT_INDEXTTS_ENDPOINT` |
| `runninghubWorkflowId`、`runninghubTextNode`、`runninghubTextField`、`runninghubAudioNode`、`runninghubAudioField`、`runninghubRefFileName`、`runninghubBase` | 同对应的 `LUMENACT_RH_*` |
| `ttsCacheDir` | 同 `LUMENACT_TTS_CACHE` |
| `asrBackend`、`asrEndpoint`、`asrModel`、`asrLanguage` | 同对应的 `LUMENACT_ASR_*` |
| `autoListen`、`lipSync`、`listenReaction`、`captions` | 网页“连续对话 / 口型 / 倾听反应 / 字幕”默认是否勾选 |

**密钥不要写进这个文件**，放环境变量或在网页填写。

## 6. 启动并打开预览器

```sh
python server.py                 # 自动打开浏览器
python server.py --no-browser    # 不自动打开
python server.py --port 8767     # 8766 被占用时换端口
```

终端会打印：

```text
LumenAct reference preview: http://127.0.0.1:8766/preview/
语音对话 TTS 默认后端: browser | ASR 默认后端: browser
```

用 Chrome / Edge 打开 <http://127.0.0.1:8766/preview/>，使用期间保持终端窗口开着，`Ctrl+C` 停止。

- **麦克风权限**：第一次点 🎙 时浏览器会询问麦克风权限，选“允许”。浏览器只在 `localhost` / `127.0.0.1` 或 HTTPS 页面开放麦克风，请用上面的地址打开，不要用局域网 IP。
- 服务只监听 `127.0.0.1`，只能在本机访问。
- 直接双击 `preview/index.html` 无法使用，必须先启动服务。

## 7. 在网页中使用语音对话

1. **确认脸部已加载**：画面里能看到流明，右侧“和流明聊聊”显示“本地 CPU · READY”（语义模型就绪）。
2. **配置 LLM**：展开页面底部 **LLM / TTS 配置**，填写 LLM Endpoint、LLM Model、LLM API Key（服务端已用环境变量配置时可留空）。如果要用 OpenAI 兼容云端 TTS，在这里填 TTS Endpoint / Model / Voice / Key。保持 **启用 TTS** 勾选（取消则只显示字幕、不出声）。需要记住 Key 时勾选“保存密钥”，点 **保存配置**。
3. **配置语音**：展开 **语音对话配置**：
   - **ASR 后端**：浏览器 Web Speech / Confucius4-R2T2 流式 / OpenAI 兼容 Whisper / faster-whisper（本机），各自的部署见第 8 节。
   - **识别语言**：默认 `zh`；英文填 `en`。
   - **R2T2 WebSocket / secret_key / 热词**：仅 Confucius4-R2T2 使用。
   - **ASR Endpoint / Model / Key**：OpenAI 兼容 Whisper 使用；faster-whisper 只看 Model（模型大小）。
   - **TTS 后端**：IndexTTS 2.5 · RunningHub / IndexTTS 本地或自建 HTTP / OpenAI 兼容云端 / 浏览器朗读 / 不朗读。
   - **失败时浏览器朗读**、**口型**、**倾听反应**、**字幕**：默认全部开启。
   - 面板底部的灰字会显示服务端状态，例如“LLM 密钥已在服务端配置 · RunningHub IndexTTS 2.5 已就绪”。
   - 点 **保存语音配置**（保存在本浏览器）。
4. **开始说话**：点聊天区的 **🎙 语音对话**，按钮变红表示正在听，旁边的绿色条显示音量。说完停顿约 0.9 秒会自动结束，也可以点 **■ 说完了**。识别到的文字会实时显示在状态栏和画面字幕上，流明会先做出倾听反应。
5. **流明回复**：状态栏显示“流明思考中…”，然后开始朗读；画面下方显示字幕并逐字点亮，表情在开口时切换，说完回到自然放松。
6. **连续对话**：勾选 **连续对话** 后，流明说完会自动开始下一轮聆听。
7. **打断**：流明说话时再点 🎙，会立即停止朗读并开始听你说。
8. **文字输入**照常可用，同样会朗读、显示字幕和切换表情。
9. 展开 **高层原文 / DIRECTOR TRACE** 可以看到 LLM 原始回复、本次选择的表情及来源、使用的 TTS 后端。

## 8. 各后端的部署方法

### 8.1 语音识别（ASR）

#### 浏览器 Web Speech（默认）

无需安装和配置。识别由 Chrome / Edge 调用浏览器厂商的在线服务完成，需要联网；Firefox 等不支持时会提示换后端。

#### Confucius4-R2T2 流式（推荐的本地方案，需要 NVIDIA GPU）

[Confucius4-R2T2](https://github.com/netease-youdao/Confucius4-R2T2) 是网易有道开源的稳定前缀流式识别模型：在 Qwen3-ASR-1.7B 上用“最长稳定前缀”（Longest Stable Prefix, LSP）后训练，只提交确定不会再变的文字，**已显示的字不会回改**，所以边听边做的倾听反应不会闪烁。代码为 Apache-2.0，权重（Hugging Face `netease-youdao/Confucius4-R2T2`）适用**网易模型使用许可协议**，使用前请阅读。

官方流式服务基于 vLLM，需要 NVIDIA GPU（官方推荐 `qwenllm/qwen3-asr` Docker 镜像，详见其 README）。在**另一个目录**部署：

```sh
git clone https://github.com/netease-youdao/Confucius4-R2T2.git
cd Confucius4-R2T2
pip install -e .
hf download FireRedTeam/FireRedVAD --include "Stream-VAD/*" --local-dir checkpoints/vad
./run_start_server.sh start --model_path /path/to/Confucius4-R2T2 --port 8272 --gpu 0
# 停止：./run_start_server.sh kill
```

然后在 LumenAct 的语音对话配置中：

1. ASR 后端选 **Confucius4-R2T2 流式（本地服务）**。
2. **R2T2 WebSocket** 留空即默认 `ws://127.0.0.1:8272/asr_stream_api_v1`；服务在别的端口或机器时填完整地址。
3. **R2T2 secret_key** 留空即 `test0102`——这是官方 `ws_server.py` 中写死的调试密钥（`secret_key_list`）。如果你修改了服务端的列表，在这里填相同的值；密钥不对时会提示“R2T2 secret_key 不正确”。
4. **R2T2 热词 / 上下文**：可填人名、专有名词（如 `流明, LumenAct`），会作为 `system_prompt` 发给服务端。
5. 识别语言 `zh` 时发送 `zhen`（中英混合自动），`en` 时发送 `English`。

网页端按官方 `ws_client.py` 的协议直连服务：先发 JSON 头（`sample_rate: 16000`、`use_vad: false`、`mode: slow`），再发 16 kHz 单声道 int16 PCM（每帧 160 ms），说完发送 `YOUDAO_ONETIME_ASR_STREAM_EOS`；服务端每条 `msg.text` 是新增片段，直接拼接。

> T8star 的 ComfyUI 节点 `confucius4-r2t2-t8`（GGUF Q8，支持 CPU / CUDA）和 Windows 整合包是另一种运行方式，但不提供这个 WebSocket 接口，LumenAct 不能直接连接。没有 GPU 时，可用 [第 9 节](#9-模拟--离线体验) 的模拟服务检查网页流程。

#### OpenAI 兼容 Whisper（云端）

录完一句话后上传到 `/v1/audio/transcriptions`（multipart，字段 `file`、`model`、`language`）。在面板填 **ASR Endpoint**（完整地址，如 `https://api.openai.com/v1/audio/transcriptions`）、**ASR Model**（缺省 `whisper-1`）、**ASR API Key**；或用 `LUMENACT_ASR_ENDPOINT` / `LUMENACT_ASR_MODEL` / `LUMENACT_ASR_KEY`。其他兼容该接口的服务商同样可用，模型名以服务商文档为准。

#### faster-whisper（本机离线）

```sh
python -m pip install -r requirements-voice.txt
```

ASR 后端选 **faster-whisper（本机）**，**ASR Model** 填模型大小（留空为 `small`）。首次使用会从 Hugging Face 自动下载模型，之后离线可用：

| 模型 | 建议 |
| --- | --- |
| `tiny` / `base` | 只适合检查流程；中文错误较多，可能输出繁体 |
| `small`（默认） | 普通 CPU 的起点，速度与准确率平衡 |
| `medium` | 较强的 CPU，或有 GPU 时 |
| `large-v3` | 有 NVIDIA GPU 时效果最好 |

中文识别会自动附加“以下是普通话的句子。”的提示，让输出倾向简体。`requirements-voice.txt` 固定了 `av<16`：faster-whisper 1.2 与 PyAV 16+ 不兼容。

### 8.2 语音合成（TTS）

#### IndexTTS 2.5 · RunningHub（参考音色克隆）

调用 RunningHub 工作流 [1970149188463980545](https://www.runninghub.cn/post/1970149188463980545)，用你的参考音色朗读：

```sh
export RUNNINGHUB_API_KEY=你的RunningHub密钥
export LUMENACT_INDEXTTS_REF=/path/to/your-voice.wav
python server.py
```

PowerShell：`$env:RUNNINGHUB_API_KEY = "..."`、`$env:LUMENACT_INDEXTTS_REF = "D:\voices\me.wav"`，再 `python server.py`。

- 两个变量都配置后，默认 TTS 后端自动为 RunningHub；网页面板底部会显示“RunningHub IndexTTS 2.5 已就绪”。
- 流程：上传参考音色（`/task/openapi/upload`，按文件内容记录，只传一次）→ 创建任务（节点 `46.audio` = 参考音色，`47.prompt` = 台词）→ 轮询 `/task/openapi/status` → 从 `/task/openapi/outputs` 下载音频。节点号可用 `LUMENACT_RH_*` 修改。
- **延迟与费用**：每次合成都是一个云端任务。实测一句 7 个字（约 1.5 秒音频）**耗时约 39 秒、扣 5.27 点**。因此该后端把整段回复合成一次（不逐句拆分），等待期间状态栏显示“IndexTTS 2.5 合成中”，音频到达后字幕与表情一起开始。
- **缓存**：结果按“后端 + 音色 + 文本”缓存在 `voice-cache/`（或 `LUMENACT_TTS_CACHE`），同一句话不会重复扣点；参考音色的上传记录在 `voice-cache/runninghub-uploads.json`。删除该目录即可清空缓存。
- 参考音色 wav 和 `voice-cache/` 不要提交到 Git（后者已被忽略）。
- 实时聊天建议用本机 IndexTTS 或云端 TTS；RunningHub 适合演示和固定台词。

#### IndexTTS 本机 / 自建 HTTP

LumenAct 向 `LUMENACT_INDEXTTS_ENDPOINT` 发送 `POST {"text": "...", "reference_audio": "<LUMENACT_INDEXTTS_REF 的路径>"}`，接受音频响应，或 JSON 中的 `audio_base64` / `audio_url`。任何满足这个约定的服务都能接入。

仓库附带的 `tools/indextts_http_server.py` 把官方 [index-tts](https://github.com/index-tts/index-tts) 的 `IndexTTS2` Python 接口包装成这个约定。先按 index-tts 的 README 安装并下载 checkpoints（通常需要 NVIDIA GPU），在**装好 index-tts 的 Python 环境**中运行：

```sh
python tools/indextts_http_server.py --model-dir /path/to/index-tts/checkpoints --reference /path/to/your-voice.wav --port 9880
# 另一个终端：
export LUMENACT_INDEXTTS_ENDPOINT=http://127.0.0.1:9880/tts
export LUMENACT_INDEXTTS_REF=/path/to/your-voice.wav
python server.py
```

再在面板把 TTS 后端选为 **IndexTTS 本地 / 自建 HTTP**。该脚本尚未在 GPU 环境实机验证，遇到 index-tts 版本差异请按其接口调整。

#### OpenAI 兼容云端 TTS

在“LLM / TTS 配置”填 TTS Endpoint（完整 `/v1/audio/speech` 地址）、TTS Model、TTS Voice、TTS API Key，或使用 `LUMENACT_TTS_*` 环境变量；TTS 后端选 **OpenAI 兼容云端 TTS**。请求体为 `{"model", "input", "voice", "response_format": "mp3"}`，多数云服务商都兼容。该后端逐句合成：第一句合成完就开口，后续句子并行预取。

#### 浏览器朗读

选 **浏览器朗读**，使用系统自带的 `speechSynthesis`，无需配置，音色取决于操作系统安装的语音包。系统没有中文语音时朗读会很快结束，字幕和表情仍按估算时长显示。勾选“失败时浏览器朗读”后，其他 TTS 出错也会自动改用浏览器朗读。

## 9. 模拟 / 离线体验

`tests/mock_services.py` 在本机模拟 LLM、TTS、Whisper 识别和 RunningHub，**不需要任何密钥、不消耗点数**。回复是固定规则（包含“难过 / 开心 / 生气 / 厉害”等词时给出不同表情标签），只用于体验和测试流程。

终端 1：

```sh
python tests/mock_services.py --port 9100
```

终端 2（macOS / Linux）：

```sh
export LUMENACT_LLM_ENDPOINT=http://127.0.0.1:9100/v1/chat/completions
export LUMENACT_TTS_ENDPOINT=http://127.0.0.1:9100/v1/audio/speech
export LUMENACT_ASR_ENDPOINT=http://127.0.0.1:9100/v1/audio/transcriptions
export LUMENACT_TTS_BACKEND=openai
python server.py
```

终端 2（Windows PowerShell）：

```powershell
$env:LUMENACT_LLM_ENDPOINT = "http://127.0.0.1:9100/v1/chat/completions"
$env:LUMENACT_TTS_ENDPOINT = "http://127.0.0.1:9100/v1/audio/speech"
$env:LUMENACT_ASR_ENDPOINT = "http://127.0.0.1:9100/v1/audio/transcriptions"
$env:LUMENACT_TTS_BACKEND = "openai"
python server.py
```

在聊天框输入“我今天好开心”，流明会以“开心欢快”回复，并朗读一段提示音（模拟 TTS 返回的是音调，不是人声），可以观察表情、口型和字幕。ASR 后端选“OpenAI 兼容 Whisper”时，模拟识别总是返回“我今天有点难过”。

- 模拟 RunningHub：再设置 `LUMENACT_RH_BASE=http://127.0.0.1:9100`、`RUNNINGHUB_API_KEY` 为任意 32 位十六进制、`LUMENACT_INDEXTTS_REF` 为任意 wav，TTS 后端选 RunningHub，即可走完整的上传 / 创建 / 轮询流程。
- 模拟 Confucius4-R2T2（需要 `python -m pip install websockets`）：`python tests/mock_r2t2.py --port 8272 --text 我今天有点难过`，ASR 后端选 Confucius4-R2T2。它按官方协议逐字返回固定文本，并在每次会话结束时打印收到的帧大小，用来检查网页端推流。

## 10. 表情是怎么选出来的

系统提示要求 LLM 回复以 `(标签)台词` 开头，标签取自 `models/expression/catalog.json` 的 28 个表情（如 `开心欢快`、`担忧担心`、`星星眼`、`道歉抱歉`）。也接受 `{"expression": "标签", "text": "台词"}` JSON（可带 ```json 围栏），以及 `（）`、`【】`、`[]` 括号。括号里的动作不会被朗读。

1. 标签与目录**完全一致** → 直接使用；同一标签有多段表演时随机挑一段，避免每次一样。
2. 其他标签（如 `有点担心地`、`happy`）→ 交给本地语义模型（与 `/api/semantic` 相同）；语义模型不可用时，用包含关系、英文别名和关键词近似对齐。
3. **没有标签** → 对台词做关键词兜底（`preview/emotion-map.js` 中约 20 类情绪词表，如“竟然 / 天哪”→ 惊讶震惊，“对不起”→ 道歉抱歉，目录缺少首选表情时按顺序顺延）。
4. 关键词也没命中且语义模型就绪时，按整句台词的语义选择；仍失败则保持自然放松。
5. `右眉上挑`、`左眉上挑` 两个单眉标签沿用原有的单通道控制。

**时机**：表情在音频开始播放的那一刻切换，朗读期间循环保持，最后一句结束后 0.4 秒平滑回到自然放松。

**倾听反应**：识别中的文字会做情绪分析，流明先做出共情表情（不是模仿用户）：难过 / 生气 / 害怕 → 担忧担心，开心 → 开心欢快，表白 → 害羞，夸流明厉害 → 骄傲自豪，道歉 → 欣慰宽慰，提问 → 思考专注。

**口型**：用 Web Audio 读取朗读音频的音量，叠加到参考脸的 `vrc.v_aa` / `vrc.v_ou` / `vrc.v_ih` 形态键（没有时用 `mouth_a`）。浏览器朗读拿不到音频流，口型按节奏模拟。这是音量驱动的开合，不是音素级口型。

**字幕**：回复按句显示在画面下方，随播放进度逐字点亮。

## 11. 测试

```sh
python -m unittest discover -s tests   # 服务端：资源下载器、TTS / ASR / RunningHub 流程、密钥边界（全部用本地模拟，不联网）
node --test tests/voice.test.mjs       # 网页端：标签解析、表情映射、关键词兜底、倾听反应、字幕切分（需要 Node.js 18+）
```

## 12. 常见问题

| 现象 | 处理 |
| --- | --- |
| 点 🎙 没反应 / 提示不支持麦克风 | 用 `http://127.0.0.1:8766/preview/` 打开（不要用局域网 IP）；在地址栏左侧的站点设置中允许麦克风；确认系统设置里浏览器有麦克风权限。 |
| 提示“当前浏览器不支持 Web Speech 识别” | 换 Chrome / Edge，或把 ASR 后端换成 faster-whisper / 云端 Whisper / Confucius4-R2T2。 |
| 一直显示“正在听”但没有文字 | 浏览器识别需要联网；检查麦克风音量条是否在动；使用 faster-whisper / 云端 Whisper / R2T2 时，8 秒内没开口会自动结束，可再点一次。 |
| “无法连接 Confucius4-R2T2 服务” | 确认 R2T2 服务已启动、端口与面板地址一致（默认 8272）；查看其目录下 `nohup_service_ws_*.log`。 |
| “R2T2 secret_key 不正确” | 面板中的 secret_key 要与服务端 `ws_server.py` 的 `secret_key_list` 一致，官方默认 `test0102`。 |
| “未安装 faster-whisper” | 用**启动服务的同一个 Python** 运行 `python -m pip install -r requirements-voice.txt`，然后重启服务。 |
| faster-whisper 报 `open() got an unexpected keyword argument 'metadata_errors'` | PyAV 版本过新：`python -m pip install "av>=11,<16"`。 |
| faster-whisper 识别成繁体或乱字 | 模型太小，把 ASR Model 改为 `small` 或更大。 |
| LLM 没有回复 / “服务返回 HTTP 401/404” | 检查 LLM Endpoint 是否为完整的 `/v1/chat/completions` 地址、模型名和 Key；服务端密钥只对同名环境变量里的地址生效。 |
| “未设置 RUNNINGHUB_API_KEY 环境变量” / “未配置 IndexTTS 参考音色” | 在**启动 server.py 的同一个终端**设置 `RUNNINGHUB_API_KEY` 和 `LUMENACT_INDEXTTS_REF`（或 `LUMENACT_RH_REF_FILENAME`）后重启。 |
| RunningHub 等很久才出声 | 正常现象（每次数十秒排队与生成）。同一句话第二次会命中缓存；需要实时对话请换其他 TTS。 |
| “RunningHub 任务创建失败” | 检查账户点数 / 余额和工作流 ID；节点号改过时同步 `LUMENACT_RH_*_NODE`。 |
| 有字幕和表情但没有声音 | 确认“启用 TTS”已勾选、TTS 后端不是“不朗读”；系统没有中文语音包时浏览器朗读无声，可安装系统中文语音或换 TTS 后端。 |
| 连续对话时流明听到自己的声音 | 戴耳机，或关闭“连续对话”。 |
| 页面能显示脸，但“语义模型未就绪” | 用安装依赖的同一个 Python 启动；运行 `python -m pip install -r requirements.txt` 后重启。 |
| 提示缺少资源 | 在项目目录运行 `python download_assets.py`，再用 `--check` 确认。 |
| 端口 8766 不可用 | `python server.py --port 8767`，访问 `http://127.0.0.1:8767/preview/`。 |
