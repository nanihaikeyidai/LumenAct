# 角色模型素材引用说明

本目录是本仓库（[nanihaikeyidai/LumenAct](https://github.com/nanihaikeyidai/LumenAct)）为流明虚拟人物补充的角色设定与模型，不属于上游 LumenAct 原有发布包，也不列入 `release-manifest.json` 的 Hugging Face 下载清单。

表情驱动仍以 `assets/reference-face/` 中的流明参考脸和 `channels.json` 的 112 个形态键通道为准。本目录的模型用于全身外观与直播站位，不替代参考脸。

## 1. 角色设定图

- 文件：`reference/lumen-chibi-reference.png`
- 来源：仓库所有者于 2026-11-25 提供的流明角色设定图
- 版权：归提供者所有；本仓库仅作开发参考，不代替原作者授权，也不对第三方再授权

外观要点（Q 版立绘）：银色长发与刘海，蓝色眼睛，黑色高领、长外套、腰带和工装靴，银色十字项链；右手魔杖，左手蓝色书本。直播用人体比例不必做成 Q 版，但发型、配色和服装应与此图一致。

## 2. Tripo 全身模型（当前采用的人物模型）

- 来源：仓库所有者使用 [Tripo](https://www.tripo3d.ai/) 生成并转换，于 2026-11-25 23:46（Asia/Shanghai）导出
- 原始导出：
  - `tripo/tripo_convert_449779d7-ee1f-4192-8bf2-71660a899dfc.fbx`（FBX 7.2 / SDK 2020.3.9）
  - `tripo/tripo_convert_449779d7-ee1f-4192-8bf2-71660a899dfc.fbm/tripo_node_08f10aa1-488c-4c03-810c-2d68a65a2368_Clone_BaseColor.png`（4K 基础色贴图）
- 本仓库转换结果（2026-11-26）：
  - `tripo/lumen-tripo.vrm`：VRM 1.0，已映射 21 块 Humanoid 骨骼，元数据名称为「流明」
  - `tripo/lumen-tripo.glb`：同模型的 glTF 备份
  - `tripo/lumen-tripo.blend`：Blender 工程，便于继续补形态键
  - `tripo/preview-front.png`、`tripo/preview-34.png`：正面与四分之三预览
- 请同时遵守 Tripo 当时的服务条款与输出资源许可。外观与设定图一致：银发、蓝眼、黑色外套，右手魔杖、左手书本，Q 版比例。

技术检查：

| 项目 | 情况 |
| --- | --- |
| 网格 | 单网格，约 25,264 顶点、50,717 三角面，有 UV 与骨骼蒙皮 |
| 骨骼 | 41 块肢体骨骼；VRM 中已对应 hips / spine / chest / neck / head 与四肢、肩、手脚、脚趾 |
| 缺失 | **没有形态键**；没有手指骨、眼球骨；部分顶点超过 4 个骨骼权重，导出时只保留权重最高的 4 个 |
| 格式 | 原始为 FBX，现已提供 VRM 1.0 与 GLB |

它已经可以作为全身直播角色导入，但还不能被 LumenAct 的 112 个表情通道驱动。下一步请在 `lumen-tripo.blend` 里按 `docs/ADAPTING_YOUR_MODEL.md` 对照参考脸补同名形态键。

## 3. 未收录的文件

检查过一份从 VRoid Studio 2.16.0 导出的 `AvatarSample_J.vrm`（pixiv VRoid Project）。该文件元数据为禁止修改、禁止再分发、仅作者可作为化身使用，因此 **没有放入本仓库，也不会在其上改外观或补形态键**。请不要把这份官方示例当作流明角色使用。
