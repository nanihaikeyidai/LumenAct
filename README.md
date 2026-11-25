# LumenAct · 本地表情模型预览包

这个包是 **LumenAct 表情模型套组的本地展示页**。它只内置一个流明脸部，用来让使用者看到公开的语义选择和表演曲线效果。页面采用流明当前宣传网页的单角色仪表盘布局，不提供 Unity、Motive 或主工程依赖。

源码仓库：[AaBb-coder/LumenAct](https://github.com/AaBb-coder/LumenAct)。预览器源码和文档已发布；配套资源位于 [Hugging Face 资源仓库](https://huggingface.co/AaBbcoder/LumenAct)。资源仓库包含带 118 个形态键的 `lumen-reference-face.blend`；完整即用包仍会在版本整理后补充。仅下载 GitHub 源码暂不能启动模型预览。

项目作者：**B站 Lumen_流明_**。流明参考脸的基础网格由 **ぷらすわん** 制作，项目已取得相应商业使用许可；参考脸资源仍按 CC BY-NC 4.0 单独授权。

本仓库公开的是可独立运行的核心预览、接口和适配参考部分，便于使用者了解表情模型套组并进行角色适配。完整项目中的部分生产运行时、内部训练流程和持续研发中的实现未纳入本次开源发布，后续会根据整理进度逐步补充公开内容。

## 第一次使用：如何打开 LumenAct

这是在自己电脑上启动的网页预览器：**先启动本地服务，再用浏览器打开页面。** 只看预览不需要安装 Unity、Motive 或 Blender；需要 Python 3.10+ 和支持 WebGL2 的桌面浏览器。Blender 用于后文介绍的角色适配。

**首次使用的顺序是：下载并解压源码 → 下载模型资源 → 安装依赖 → 启动预览。** GitHub 提供代码，Hugging Face 提供配套模型和脸部资源；下面的下载脚本会自动把资源放到正确位置，无需手工拼装两个仓库。

### Windows：按顺序操作

1. **安装 Python。** 前往 [Python 官网](https://www.python.org/downloads/) 安装 Python 3.10 或以上版本，Windows 建议使用 64 位 Python 3.11 / 3.12。安装时勾选 **Add Python to PATH**，并保留 pip。
2. **下载并解压项目。** 打开 [GitHub 仓库](https://github.com/AaBb-coder/LumenAct)，点击绿色 **Code → Download ZIP**，将整个压缩包解压到本地文件夹。进入能看到 `README.md`、`server.py` 和几个 `.bat` 文件的目录；以下操作都在这个目录中进行。请先完整解压，再运行文件。
3. **下载模型资源。** 双击 `download_assets.bat`，等待下载和校验完成。首次需要联网访问 Hugging Face；资源已公开，无需登录或填写 Hugging Face Token。看到 `Assets downloaded and verified. You can start the preview.`，或提示资源已经完整，表示这一步成功。
4. **安装运行依赖。** 双击 `install_semantic.bat`，等待 numpy、onnxruntime、tokenizers 安装完成。首次安装需要联网；如果出现安装错误，先解决错误再继续。
5. **启动预览。** 双击 `start_preview.bat`，浏览器会自动打开 <http://127.0.0.1:8766/preview/>。如果没有自动打开，手动复制该地址到浏览器。**使用期间保持启动的命令窗口打开**，关闭窗口会停止本地服务。
6. **按需开启对话和语音。** 先确认能看到流明参考脸，再展开页面底部的“LLM / TTS 配置”。要聊天，需要填写自己可用的 LLM Endpoint、模型名和 API Key；要播放语音，再配置 TTS。只查看脸部和初始自然表演，无需配置这两项服务。

**以后再次使用：** 资源和依赖安装成功后，通常只需双击 `start_preview.bat`。直接双击 `preview/index.html` 无法完成本地服务的启动。

### 不熟悉部署？可以让 AI 辅助

可以让能访问本机文件并执行终端命令的 AI 编程助手，在解压后的项目目录中协助安装和启动。普通聊天 AI 也可以解释步骤，但需要你自己执行命令。将下面的内容复制给 AI，并填上实际的项目目录和操作系统：

```text
请帮我在本机部署并启动 LumenAct 本地预览器。
项目地址：https://github.com/AaBb-coder/LumenAct
我的项目目录：<填写解压后的绝对路径>
我的操作系统：<Windows / macOS / Linux>

请先阅读项目 README.md、requirements.txt 和 release-manifest.json，
按项目现有方式完成以下步骤：
1. 检查 Python 版本和 pip。项目要求 Python 3.10+；缺少时指导我安装。
2. 运行 download_assets.py，按发布清单下载并校验匹配的公开资源。
3. 用同一个 Python 解释器安装 requirements.txt，并运行 server.py。
   如使用虚拟环境，请始终使用该环境的解释器，避免安装与启动环境不一致。
4. 告诉我本地访问地址，并帮助我确认浏览器能显示流明参考脸。
   保持服务运行，并说明以后如何启动和停止。
5. 如有报错，根据实际报错定位 Python、依赖、资源下载或端口问题，
   保留资源校验，不要为了启动而跳过校验或修改核心模型逻辑。

先完成本地脸部预览，再指导我在网页中配置自己的 LLM / TTS。
如需 API Key，提醒我直接在本地网页中填写。
```

向 AI 求助时，可以提供**操作系统、Python 版本、失败的步骤和完整报错**，注意遮去密钥。仅提供“打不开”较难判断问题出在哪一步。

### macOS / Linux

安装 Python 3.10+ 后，在解压后的项目目录打开终端，依次运行：

```sh
python3 -m venv .venv
. .venv/bin/activate
python download_assets.py
python -m pip install -r requirements.txt
python server.py
```

浏览器访问 <http://127.0.0.1:8766/preview/>。以后重新打开终端时，先进入项目目录并激活 `.venv`，再运行 `python server.py`；在服务终端按 `Ctrl+C` 停止。

### 常见启动问题

| 现象 | 处理方式 |
| --- | --- |
| 提示找不到 `python` 或 `py` | 安装 Python 并启用 PATH；安装后重新打开终端或启动脚本。 |
| 提示缺少资源或资源大小不符 | 在同一个项目目录运行 `download_assets.bat` 或 `python download_assets.py`，等待下载和校验成功。 |
| Hugging Face 下载失败 | 检查本机到 Hugging Face 的网络连接，再重试下载脚本；完整文件会自动跳过。 |
| 页面能显示脸部，但语义模型未就绪 | 安装 `requirements.txt` 中的依赖后重启服务；确认安装依赖与启动服务使用同一个 Python 环境。 |
| 浏览器提示“拒绝连接” | 查看启动窗口中的错误，确认服务仍在运行，并使用窗口打印的访问地址。 |
| 提示端口 8766 不可用 | 在项目目录运行 `python server.py --port 8767`，再访问 `http://127.0.0.1:8767/preview/`。 |
| 能看到脸部，但聊天没有回复或没有语音 | 分别检查自己的 LLM / TTS 服务配置；这两项需要使用者提供可用服务。 |

下载器从 `release-manifest.json` 读取匹配的 Hugging Face 资源版本，默认运行 `python download_assets.py` 即可。当前固定资源提交为 `df8126a2a854735227ec81b7f12ab62d49a6d989`，也可显式指定：

```sh
python download_assets.py --repo AaBbcoder/LumenAct --revision df8126a2a854735227ec81b7f12ab62d49a6d989
```

下载器只使用 Python 标准库，会校验大小和 SHA-256，跳过完整文件；下载失败不会覆盖原文件。`python download_assets.py --check` 可在离线状态检查资源完整性。

## 语音对话

预览器可以和流明直接语音对话，并根据对话内容切换表情：**麦克风识别 → LLM 回复（带表情标签）→ TTS 朗读与字幕 → 开口时切换表情、口型随音量开合 → 说完回到自然放松**；用户说话时，流明会先做出共情反应。

| 环节 | 可选后端 |
| --- | --- |
| 语音识别（ASR） | 浏览器 Web Speech（默认，零配置）· [Confucius4-R2T2](https://github.com/netease-youdao/Confucius4-R2T2) 稳定前缀流式识别（本地 NVIDIA GPU 服务）· OpenAI 兼容 Whisper · 本机 faster-whisper |
| 语音合成（TTS） | IndexTTS 2.5（RunningHub 工作流，参考音色克隆）· 本机 / 自建 IndexTTS HTTP · OpenAI 兼容云端 TTS · 浏览器朗读 |
| 表情 | LLM 给出的标签 → 本地语义模型 → 台词关键词兜底 → 自然放松 |

### 快速开始（本地部署）

需要 Python 3.10+ 和桌面版 Chrome / Edge。

**macOS / Linux**

```sh
git clone https://github.com/nanihaikeyidai/LumenAct.git
cd LumenAct
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-voice.txt   # 可选：本机 faster-whisper 识别
python download_assets.py                         # 从 Hugging Face AaBbcoder/LumenAct 下载并校验模型资源
export LUMENACT_LLM_ENDPOINT=https://你的服务/v1/chat/completions
export LUMENACT_LLM_MODEL=你的模型
export LUMENACT_LLM_KEY=你的Key                    # 也可以不设，直接在网页里填写
python server.py
```

**Windows PowerShell**

```powershell
git clone https://github.com/nanihaikeyidai/LumenAct.git
cd LumenAct
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-voice.txt   # 可选
python download_assets.py
$env:LUMENACT_LLM_ENDPOINT = "https://你的服务/v1/chat/completions"
$env:LUMENACT_LLM_MODEL = "你的模型"
$env:LUMENACT_LLM_KEY = "你的Key"
python server.py
```

> 语音对话功能合并前位于 `feat/voice-chat-emotion` 分支，克隆时加 `-b feat/voice-chat-emotion`。使用虚拟环境时请用 `python server.py` 启动；`start_preview.bat` 使用系统 Python，不会用到 `.venv` 中安装的依赖。

浏览器打开 <http://127.0.0.1:8766/preview/>（麦克风只在 localhost 或 HTTPS 下可用，不要用局域网 IP），然后：

1. 展开底部 **语音对话配置**，选择 ASR 后端和 TTS 后端，点“保存语音配置”。
2. 点聊天区的 **🎙 语音对话**，允许麦克风权限后说话；停顿约 0.9 秒自动结束。
3. 勾选 **连续对话** 可以一轮接一轮地聊；流明说话时再点 🎙 可以打断。

想用自己的声音朗读（IndexTTS 2.5 · RunningHub），启动前再设置：

```sh
export RUNNINGHUB_API_KEY=你的RunningHub密钥
export LUMENACT_INDEXTTS_REF=/path/to/your-voice.wav
```

RunningHub 每次合成约需数十秒并扣点（实测 7 个字约 39 秒、5.27 点），结果会缓存在 `voice-cache/`。

没有任何密钥时，可以先用 `python tests/mock_services.py --port 9100` 模拟 LLM / TTS / 识别体验整条链路。所有环境变量、配置文件字段、各后端（含 Confucius4-R2T2 GPU 服务、faster-whisper 模型大小、自建 IndexTTS）的部署步骤、表情映射规则和常见问题，见 **[语音对话：本地部署与使用指南](docs/VOICE_CHAT.md)**。

### 下一步：B站 AI 虚拟主播（计划）

后续计划把流明做成在 B站直播间读弹幕、回答问题、带表情和身体动作的 AI 虚拟主播，全部组件在本机运行（blivedm / 开放平台弹幕、Ollama 或 vLLM 本地大模型、CosyVoice / 自部署 IndexTTS 2.5 流式语音、OBS 同机推流）。调研、架构、目录规划、分阶段 TODO 与验收标准、硬件要求和合规注意事项见 **[B站 AI 虚拟主播：本地部署调研与开发计划](docs/LIVE_VTUBER_PLAN.md)**。

## 当前阶段

LumenAct 仍处于持续补充表演素材、训练与评估的早期阶段。受当前素材覆盖范围影响，初期版本在部分输入下可能呈现接近 Motion Matching（动作匹配）的观感：相近的情绪描述容易呈现相似的表演，细微语义差异和自由组合的表现还有提升空间。

当前公开预览由语义模型选择情绪类别与上下文，再驱动对应的表演曲线。上面的类比描述的是观看感受，并不表示本包采用了标准 Motion Matching 算法。我们正在持续扩充素材与训练覆盖，也欢迎通过流明表情工坊参与素材制作，一起丰富角色的表达。

## 页面能做什么

1. 页面自动加载唯一的流明脸部。
2. 配置自己的 LLM 后，通过对话回复中的情绪标签触发表情。
3. 主界面不提供独立的情绪解析面板、片段列表、播放进度或循环控制。语义分类和曲线选择在内部执行，详细流程见 [docs/FORMAT.md](docs/FORMAT.md)。
4. 观察语义选择耗时、表演数据规模和浏览器显示状态。
5. 可选配置自己的 LLM / TTS，用对话测试“情绪标签 → 表演片段”的链路。
6. 可旋转脸部视角，便于观看展示。

页面**不提供**形态键滑条、逐通道校准、动作编辑器、用户模型上传或适配向导。

## 如何适配自己的角色

适配在 Blender 中完成，由 AI 通过 MCP 辅助制作，再由人工逐项比较和修正。目标是让自己的角色收到同名通道时，表现出对应的动作含义，不要求相同脸型或相同拓扑。

**本包只提供流明的一份 Blender 参考脸文件。** 推荐用户将自己的 VRM 人形角色导入 Blender 作为适配对象；FBX、MMD（PMX／PMD）、glTF／GLB 等其他格式的导入、转换和形态键保留由用户自行处理。本包不附带这些格式的流明脸部副本，也不提供通用格式转换器。核心要求是最终角色具有可按名称匹配、可由运行时设置权重的形态键网格。

1. 安装并连接 Blender MCP，准备带完整形态键的流明参考脸与目标角色，导入同一场景并保存备份。
2. 完整保留目标角色原有形态键、默认值及绑定，让 AI 分析两张脸的网格、对应部位和参考键的实际顶点位移。
3. 在目标模型工作副本中复用合适的已有键，或添加准确同名的形态键，按目标脸部比例类比制作效果；不同拓扑不能按顶点编号直接复制。
4. 让 AI 为使用者的场景生成双模型联动面板：一条滑条同步驱动两边的同名形态键，提供基线恢复、缺项提示和验收记录。
5. 人工逐键检查不同权重的效果，只修正目标角色；之后检查组合与动态表演，保留形态键导出并接入自己的运行时。

详细步骤与 AI 任务示例见 [Blender＋MCP 适配教程](docs/ADAPTING_YOUR_MODEL.md)。资源仓库中的 `assets/reference-face/lumen-reference-face.blend` 是可直接导入 Blender、保留完整形态键的参考脸文件；网页 JSON 仍只用于网页预览。

面板由使用者自己的 AI 在 Blender 中生成和维护，本包不内置校准插件、自动适配工具或网页校准界面。网页用于公开表情预览。

## 包含什么

| 内容 | 范围 |
| --- | --- |
| 语义模型 | RBT3-Lumen-38M-v6，CPU ONNX 权重及本地分词器 |
| 表演数据 | 97 段表演、166 维原始控制曲线、类别与上下文标签 |
| 展示角色 | 流明独立脸部网格、必要绑定和脸部纹理 |
| 展示页面 | 单脸仪表盘、语义选择、曲线播放和可选对话接口 |
| 服务适配 | 用户自行配置的 OpenAI-compatible LLM / TTS 接口 |

参考页面独立实现了基础相机视线跟随、头部微动和 0.4 秒普通淡入淡出。表演结束或语音播放完毕后回到自然表演，随后循环播放自然曲线；新表演从当前显示的姿态开始过渡。

这不是主项目完整运行时。主项目的复杂眼球限位与闭眼联动、程序化眨眼、动作图调度、惯性过渡、口型合成、头发物理和 Unity 肌肉到骨骼求解没有收录。固定曲线中已经录下的动作不等于包内包含生成这些动作的私有算法。

## LLM / TTS

展开页面底部“LLM / TTS 配置”，填写自己的 Endpoint、模型名和密钥。

- LLM 返回标准 `choices[0].message.content`，也支持 `output_text` / `text`。
- 示例回复：`（微笑）早上好！`。页面把首个括号中的情绪交给本地语义模型，再选择公开表演片段。
- 公开参考提示词在 `preview/chat-director.js` 的 `buildChatPrompt()`，说明虚拟角色身份、可用情绪标签和回复格式，不包含主项目的私有角色提示词。
- `（右眉上挑）好，这样呢？` 和 `（左眉上挑）好，这样呢？` 是额外的基础单眉指令：网页独立控制 `eyebrow_up_R/L` 并平滑回落，不走整脸情绪选择。这是明确规则控制，不代表语义权重学会了任意部位动作。
- TTS 只返回和播放音频，不生成或同步口型。
- 本地代理只转发用户主动发起的请求，不保存密钥和对话内容。
- 配置默认只存在当前页面内存；勾选“在浏览器保存密钥”后才写入当前浏览器的 localStorage。

### 高层 LLM 需要知道什么

高层 LLM 负责生成台词和表情意图，网页负责执行表情。接入自己的角色时，在系统提示词中说明以下信息即可：

1. **角色身份**：它是拥有网页虚拟脸部的角色，标签可以驱动这张脸；面对表情请求，不应误答“没有实体眉毛，只能用文字表演”。
2. **可用范围**：整体情绪标签以 `models/expression/catalog.json` 的 `labels` 为准。优先使用微笑、害羞等已收录的情绪，不要自行编造复杂动作；当前网页另支持 `右眉上挑`、`左眉上挑` 两个基础指令，左右以角色自身为准。
3. **输出格式**：每次回复以一个 `(标签)` 或 `（标签）` 开头，后接自然台词，不需要 JSON、通道数值或复杂动作语法。当前只执行首个括号标签，不支持在一段话中编排多个动作。
4. **能力边界**：整体情绪与单部位指令应分开使用；没有接入的精细动作，不应在台词中声称已经完成。

例如：

```text
(微笑)早上好，今天也一起加油吧。
(右眉上挑)好，这样呢？
```

括号内容用于驱动表情，展示给用户和交给 TTS 的台词会去掉这些标签。页面已通过 `preview/chat-director.js` 自动把角色说明、当前情绪列表和基础指令加入系统提示词；使用内置对话入口时无需再手工配置这套格式。

## 发布边界

本机测试也可使用 `python server.py --services-profile /absolute/path/services.local.json`，从发布目录外加载默认服务配置。JSON 支持 `llmEndpoint`、`llmModel`、`ttsEndpoint`、`ttsModel`、`ttsVoice` 和布尔值 `ttsEnabled`，页面只在相应字段为空时填入默认值。此文件不应包含密钥；密钥由用户填写，或交给自己管理的本地适配服务。默认启动脚本不加载开发机配置。

只打包本目录的文件。不要把上级目录、旧预览器、原工程或开发机配置一起提交。

执行 `python prepare_release.py` 可按显式发布清单在上一级目录生成三个包：`lumenact-local-preview-source.zip` 用于 GitHub 源码，`lumenact-local-preview-huggingface.zip` 用于 Hugging Face 资源仓库，`lumenact-local-preview.zip` 用于 GitHub Releases 的完整即用附件。前两个 ZIP 需要解压后上传对应文件。分仓配置、版本匹配和授权准备见 [docs/RELEASING.md](docs/RELEASING.md)。工具不执行上传。

本包只公开独立脸部展示资产、语义权重、表演曲线和基础页面代码。主项目的面捕映射、视线跟随、口型分层、自然放松、动作图、惯性过渡、微动调度和骨骼求解没有随包发布。详细范围见 [docs/BOUNDARIES.md](docs/BOUNDARIES.md)。

## 本 fork 补充的直播与角色素材

本仓库在上游参考脸之外，还放了直播场景和全身角色模型，方便本地继续开发虚拟直播：

- 直播场景（星空书房背景与透明前景）：[assets/live-scene/](assets/live-scene/)，引用说明见 [素材声明](assets/live-scene/ASSET_NOTICE.md)
- 角色设定图与当前采用的 Tripo 全身模型：[assets/character/](assets/character/)，引用说明见 [素材声明](assets/character/ASSET_NOTICE.md)

Tripo 模型已转换为 VRM 1.0（`assets/character/tripo/lumen-tripo.vrm`），可作全身直播角色使用，但还没有表情形态键，不能直接驱动 LumenAct 的 112 个表情通道。总索引见 [assets/README.md](assets/README.md)。

## 许可证

本项目按内容分别授权：

| 内容 | 许可与范围 |
| --- | --- |
| 新参考代码和文档 | MIT，见 [LICENSE](LICENSE) |
| 语义模型与配套分词器 | RBT3-Lumen-38M-v6 由项目作者自行训练，按 Apache-2.0 发布 |
| 项目有权授权的表演曲线及标签资料 | CC BY 4.0，允许商用、修改和再分发，须署名并说明修改 |
| 项目有权授权的流明参考脸资源 | CC BY-NC 4.0，第三方仅限非商用使用，须署名并说明修改 |

**除原作者／相关权利人自行使用，或另行取得其明确商业授权外，第三方不得将流明参考脸及包含其受保护几何、纹理的改编版本用于商业用途。** 代码的 MIT 许可不覆盖参考脸，修改外观也不会自动免除参考脸的非商用条件。

使用者独立制作、未复制参考脸受保护内容的自有角色，不会仅因采用相同通道或表情数据而受参考脸非商用条件约束；仍需遵守所用模型、数据和自身角色的许可。

授权范围、署名方式和上游核对状态见 [模型及数据声明](models/ASSET_NOTICE.md) 与 [参考脸声明](assets/reference-face/ASSET_NOTICE.md)。完整标准许可文本放在 `licenses/`。本授权不扩展到完整流明角色、项目标识或未发布的主工程，也不取代第三方原有许可。

