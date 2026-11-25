# 直播场景素材引用说明

本目录是本仓库（[nanihaikeyidai/LumenAct](https://github.com/nanihaikeyidai/LumenAct)）为流明虚拟直播补充的 2D 场景素材，不属于上游 LumenAct 原有发布包，也不列入 `release-manifest.json` 的 Hugging Face 下载清单。

## 来源

- 制作日期：2026-11-25
- 生成工具：图像生成（16:9，原生 1280×720）后用本地工具做绿幕抠图、层叠，并用 Lanczos 放大到 2560×1440
- 未使用 RunningHub，无积分消耗
- 提示词原文见各子目录的 `prompts.md`，便于用其他生图工具重出更高分辨率

配色参考了本仓库流明参考脸的桃粉肤色与靛紫星眼，主光为左前方暖光。参考脸本身的许可见 `assets/reference-face/ASSET_NOTICE.md`，本目录的背景图并不复制参考脸的几何或纹理。

## 采用的定稿

用户从三版草案中选定了 **星空 / 魔法书房**。

| 路径 | 说明 |
| --- | --- |
| `starry-study/bg-starry-final.png` | 定稿背景，2560×1440 |
| `starry-study/fg-desk.png` | 透明前景：底部桌沿 |
| `starry-study/fg-mic.png` | 透明前景：黄铜桌面麦克风（偏右） |
| `starry-study/fg-props.png` | 透明前景：书、茶杯、发光小球（偏左） |
| `starry-study/composite-preview.png` | 背景 + 站位剪影 + 前景的合成预览 |
| `starry-study/bg-starry-final-preview.png` | 背景 + 站位与弹幕/礼物区示意 |
| `starry-study/source/` | 原生 1280×720 与绿幕原图，便于重新抠图 |
| `drafts/bg-cozy.png`、`bg-cyber.png`、`bg-starry.png` | 未采用或作为定稿参考的草案 |

OBS / three.js 叠加顺序：背景 → 角色 → 桌沿 → 摆件和麦克风。

已知瑕疵：桌面中部有一条横向接缝；茶杯和光球几乎没有接触阴影；礼物提示区仍会盖住一部分星空窗户。`source/` 中若曾有 3840×2160 插值图，因没有新增细节，未作为正式稿收录。

## 使用与再分发

这些图是为本项目直播场景制作的生成图像。可在本仓库的虚拟直播中使用；再分发时请保留本声明和对应的 `prompts.md`。它们不改变流明参考脸的 CC BY-NC 4.0 授权。
