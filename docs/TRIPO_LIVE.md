# Tripo 本地直播间

使用 ComfyUI 的 T8 IndexTTS 2.5 节点和本机参考 WAV 生成语音。启动已安装模型的 ComfyUI，再在仓库根目录运行下列命令。

    py -m pip install requests
    py -m tools.live_studio --reference "你的参考音色.wav"

打开 http://127.0.0.1:8794/preview/live.html 。可用 `--comfy` 和 `--port` 指定 ComfyUI 地址与直播页端口。服务把参考音频传给指定的 ComfyUI，并缓存最近 32 条合成结果。首次合成需等待模型加载。个人音色请使用本地服务。

台词以（挥手，微笑）、（点头，眨眼）、（讲解，挑眉）或（摇头）开头时会执行相应动作。无标签时页面按欢迎、同意、讲解等关键词选择动作。动作标签不参与朗读。嘴部开合使用播放音频的实际音量。连续点击播报会排队，停止会清空播放队列。输入可达 500 字。

直播页面加载 `assets/character/tripo/lumen-tripo-face-refined.glb`。相邻的同名 Blender 工程可继续编辑。重建时先用 `tools/create_tripo_morph_batch.py` 从原模型生成首批形态键，再运行 `tools/make_tripo_speech_preview.py` 并传入单声道 PCM16 WAV、输出帧目录和 `--refine-face`。

## 浏览器实测

安装 Python Playwright 及 Chromium 后，启动本地直播服务，再执行：

    py -m tests.live_browser --out live-test-output

脚本从页面录制真实画布和播放音轨，检查连续四次播报、停止和浏览器异常。本机实测通过，使用三句不同的中文台词以及挥手、点头、讲解、摇头、挑眉、微笑、眨眼。页面动画通过平滑插值回到待机。短场景可以用于文字驱动播报。当前支持固定动作词，闭眼时虹膜边缘仍可能可见，长时间直播与推流平台需要另测。
