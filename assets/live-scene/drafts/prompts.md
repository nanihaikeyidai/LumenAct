# 流明直播间 2D 背景草案提示词

用于 LumenAct 虚拟主播「流明 / Lumen」直播间背景风格初稿。用户已选定路线 1：2D 背景图（后续再加透明前景 PNG）。本文件记录三张草案的**实际使用提示词**（中英对照），方便在其他生成器里复用。

> 用户已选定 **C. 星空 / 魔法书房**。定稿背景、透明前景层与最终提示词见：`/workspace/lumenact-scene/final/`（`bg-starry-final.png`、`fg-*.png`、`prompts.md`）。

尚未提交到仓库。

生成信息：

- 工具：cursor.studio `GenerateImage`（免费本地/内置生图，未使用 RunningHub，无积分消耗）
- 画幅：16:9
- 原生输出：1280×720 JPEG
- 交付文件：Lanczos 2× 放大到 2560×1440 PNG，轻度 Unsharp Mask
- 原始 1280×720 JPEG 备份在 `source-1280x720/`

---

## 从仓库里读到的配色依据

公开仓库（`/workspace/lumenact`，分支 `feat/voice-chat-emotion`）**只有独立脸部参考**，没有全身、发型或服装设定，完整流明角色未开源。

从 `assets/reference-face/face_texture_0.png` 采样：

| 部位 | 代表色 |
| --- | --- |
| 肤色高光 / 底色 | `#ffe7e3` `#fed8d5` `#fdd6d3` |
| 腮红 / 唇粉 | `#fd938e` `#e37a89` `#d99ea2` `#ce6874` |
| 虹膜（星空靛紫） | `#4f2c6a` `#556083` `#3c5d80` `#616198` |
| 虹膜高光薰衣草 | `#a0a9eb` |
| 眉色（ Mauve 褐） | `#4c3745` |
| 暗部紺青 | `#151323` `#2e2a4f` |

预览器界面（`preview/preview.css`、`reference-view.js`）补充：

- 渲染清空色象牙米 `#e9e8e3`
- 视口深青 `#1d2c33`
- 强调珊瑚红 `#d75343` / `#da5b48`
- 辅助蓝绿 `#4f98bb` / `#23749c`

角色名「流明」本身有光、微光的意象；脸上还有金色闪光和粉心装饰。三版背景都按这些颜色来配：暖象牙与蜜桃光打主光（左前方），靛紫 / 薰衣草呼应瞳色，珊瑚红只做小点缀。

---

## 三版共用约束（生成时都写进了提示词）

- 二次元 / VTuber 背景插画，赛璐璐或清晰动漫背景风，要能和二次元赛璐璐角色站在一起
- 16:9 横构图，尽量高清
- **画面中禁止出现人物、角色、人体模型、人偶、肖像、人脸、手**
- 机位在站立者胸口高度，镜头平视向前
- 画面正中与中下方留白作为角色站位：可以有地板或最底部一条细桌沿，但中间不能被物体挡住
- 左上角和右侧相对干净、低细节，留给弹幕和礼物特效
- 主光为左前方暖色关键光，方便以后和角色光照统一
- 远处背景轻微景深虚化
- 不要文字、Logo、水印、UI

---

## A. 温馨卧室直播间 / Cozy bedroom

交付：`bg-cozy.png`（预览合成：`bg-cozy-preview.png`）

### 中文

二次元虚拟主播直播间背景插画，16:9 横构图，高精度赛璐璐动漫背景，线条干净，光影柔和偏手绘。房间完全空着：不要人物、不要角色、不要人体模型、不要玩偶人脸、不要肖像、不要脸、不要手，画面里不能出现任何人类或类人形体。

机位在站立者胸口高度，镜头平视，看向一间温馨的动漫卧室直播间。画面正中和中下方必须完全留白，作为角色站位区：只有温暖的木地板，最底部最多保留一条很细的矮桌沿；中间不能被家具、植物或道具挡住。

构图：中央留出充足站位空间。左上角和整条右侧要相对安静、低细节、少杂物，留给以后叠弹幕和礼物特效。有看点的细节放在中景左侧和远处后墙，不要放在正中或 overlay 区域。

主光来自左前方：一盏发光的暖色台灯，以及柔和的金桃色灯光，照亮中央空地，就像在给一个站在那里的人打光。带轻微景深，远处背景略微虚化。

配色要衬托白里透粉的动漫肤色和星空靛紫瞳：象牙奶油色墙壁、暖橡木地板、blush 粉和灰玫瑰床品布艺、雾面靛蓝和periwinkle抱枕与毯子、少量珊瑚红小物件、暖金色小灯串、奶油色和mauve的圆形无脸玩偶。整洁的床放在左中景，薄纱窗帘，远处后墙有略虚的书架和小绿植。灯串可以沿床头或侧墙布置，但不要在左上角堆得太密。夜间室内的温馨感，生活痕迹有，但整体整齐。

不要文字、字母、Logo、水印、屏幕 UI，正中央不要麦克风。高质量动漫室内背景，清晰、高分辨率。

### English（实际送给 GenerateImage 的原文）

Anime VTuber livestream background illustration, 16:9 landscape, highly detailed cel-shaded anime background art with clean linework and soft painterly lighting. Completely empty room: no people, no characters, no mannequin, no dolls, no portraits, no faces, no hands, no human or humanoid figures anywhere.

Camera is at a standing person's chest height, looking straight forward into a cozy anime bedroom used as a streaming room. The exact center and lower-center of the frame are kept completely clear as a standing zone: only a warm wooden floor and maybe the slim front edge of a low desk at the very bottom; no furniture, plants, or props blocking the middle.

Composition: generous empty standing space in the center. The top-left corner and the entire right side of the frame are relatively calm, uncluttered, low-detail areas reserved for later UI overlays. Put the interesting details in the mid-ground left and the far back wall, not in the center or the overlay zones.

Main key light comes from the front-left: a glowing warm table lamp and soft golden-peach lamplight, illuminating the empty center as if lighting a person standing there. Soft depth of field; the far background is slightly defocused.

Color palette chosen to complement a fair peach-pink skinned anime character with starry indigo-violet eyes: ivory cream walls, warm oak floor, blush-pink and dusty rose bedding and textiles, muted indigo and periwinkle cushions and a throw blanket, a few small coral-red accent objects, warm gold fairy lights, cream and mauve round plush toys without faces. A tidy bed in the left mid-background, sheer curtains, a softly out-of-focus shelf of books and small plants on the far back wall. Fairy lights along a headboard or side wall, but not dense in the top-left corner. Nighttime cozy indoor mood, lived-in but tidy.

No text, no letters, no logos, no watermarks, no on-screen UI, no microphone in the center. Masterpiece anime interior background, sharp and high resolution.

---

## B. 赛博霓虹 / Cyber neon

交付：`bg-cyber.png`（预览合成：`bg-cyber-preview.png`）

### 中文

二次元虚拟主播直播间背景插画，16:9 横构图，高精度赛璐璐动漫背景。夜晚的时尚赛博霓虹公寓。房间完全空着：不要人物、不要角色、不要人体模型、不要带脸的机器人、不要肖像、不要窗里的人影、不要手。

机位在站立者胸口高度，镜头平视向前。画面正中和中下方必须完全留白，作为角色站位区：只有深色抛光地板，最底部最多一条细桌沿；中间不能被物体挡住。

构图：中央留出充足站位空间。左上角和右侧要相对安静、低细节，留给以后叠 UI。霓虹灯带和城市细节放在后窗和中景，不要挤在 overlay 角落。

主光仍然是左前方的暖色实用光（台灯或柔和钨丝聚光），让站在中央的角色会被左前方暖光打亮。品红和青色霓虹只作为窗户和侧墙的辅光、轮廓光，不要压过中央。带轻微景深，远处城市天际线略微虚化。

配色：深青海军蓝墙面，品红与青色霓虹灯带，柔和的紫与靛蓝底调呼应星空靛紫瞳，远处城市微光，宽后窗外是冷静的夜景天际线。少量利落的架子、侧边一棵植物、窗框上的 LED 灯带。干净、略带质感的赛博公寓，整齐不杂乱。中央地板偏暗、简洁，好让角色被看清。地面可有淡淡霓虹倒影，但不要像镜子。

不要可阅读的文字、Logo、水印、屏幕 UI、人物。高质量动漫室内背景，清晰、高分辨率。

### English（实际送给 GenerateImage 的原文）

Anime VTuber livestream background illustration, 16:9 landscape, highly detailed cel-shaded anime background art. A stylish cyber neon apartment room at night. Completely empty room: no people, no characters, no mannequin, no robots with faces, no portraits, no figures in windows, no hands.

Camera is at a standing person's chest height, looking straight forward. The exact center and lower-center of the frame are kept completely clear as a standing zone: only a dark polished floor and maybe a slim low desk edge at the very bottom; nothing blocking the middle.

Composition: generous empty standing space in the center. The top-left corner and the right side of the frame are relatively calm, uncluttered, low-detail areas reserved for later UI overlays. Neon strips and city details live on a large rear window and in the mid-background, not crowded into the overlay corners.

Main key light is still a warm practical light from the front-left (a desk lamp or soft tungsten spotlight) so a character standing in the center would be lit warm from the front-left. Magenta and cyan neon are accent and fill lights from the window and side walls, not overpowering the center. Soft depth of field; the far city skyline is slightly defocused.

Color palette: deep teal-navy walls, magenta and cyan neon light strips, soft violet and indigo undertones echoing starry indigo-violet eyes, faint distant city glow, cool night skyline through a wide rear window. A few sleek shelves, a plant off to the side, LED strips along the window frame. Clean, slightly luxurious cyber apartment, tidy, not cluttered. The center floor is darker and simple so a standing character will read clearly. Subtle floor reflections of neon, not a mirror-like surface.

No readable text, no logos, no watermarks, no on-screen UI, no people. Masterpiece anime interior background, sharp and high resolution.

---

## C. 星空 / 魔法书房 / Starry magic study

交付：`bg-starry.png`（预览合成：`bg-starry-preview.png`）

### 中文

二次元虚拟主播直播间背景插画，16:9 横构图，高精度赛璐璐动漫背景。夜晚的星空魔法书房，明亮而温和。房间完全空着：不要人物、不要角色、不要女巫、不要使魔、不要肖像、不要带脸的雕像、不要手，不能出现人类或类人形体。

机位在站立者胸口高度，镜头平视向前。画面正中和中下方必须完全留白，作为角色站位区：只有温暖的木地板，最底部最多一条细地毯边或细桌沿；中间不能被家具挡住。

构图：中央留出充足站位空间。左上角和右侧要相对安静、低细节，留给 overlay——可以是装饰更少的书架或夜空窗的安静一段。

主光来自左前方：左侧一盏古董黄铜灯或悬挂的暖色提灯，金色光线打进中央空地，就像在给一个站在那里的人打光。背景有一扇高大拱窗或长窗，窗外是深靛蓝的星空，略微虚化。高书架沿后墙和远端两侧排列，不要挤占中央。空气中飘着金色、浅薰衣草和淡玫瑰色的发光粒子与细小星点，像魔法尘埃。只有远端两侧可以有少量漂浮的书。远处书架和夜空带轻微景深。

配色要衬托白里透粉的肤色、星空靛紫瞳，以及「流明 / 光」的名字意象：深靛蓝与午夜海军蓝、温暖羊皮纸和奶油色、黄铜金、浅薰衣草粒子光、少量blush粉蜡烛或花作为点缀、几本珊瑚红书脊。暖灯光对上冷星光。整齐、好看，不要杂乱。

不要文字、字母、Logo、水印、屏幕 UI。高质量动漫魔法室内背景，清晰、高分辨率。

### English（实际送给 GenerateImage 的原文）

Anime VTuber livestream background illustration, 16:9 landscape, highly detailed cel-shaded anime background art. A magical starry study and library room at night, luminous and gentle. Completely empty room: no people, no characters, no witches, no familiars, no portraits, no statues with faces, no hands, no human or humanoid figures.

Camera is at a standing person's chest height, looking straight forward. The exact center and lower-center of the frame are kept completely clear as a standing zone: only a warm wooden floor and maybe a thin rug edge or slim desk edge at the very bottom; no furniture blocking the middle.

Composition: generous empty standing space in the center. The top-left corner and the right side of the frame are relatively calm, uncluttered, low-detail areas reserved for later UI overlays — quieter stretches of shelf or night-sky window with less ornament.

Main key light comes from the front-left: an antique brass lamp or hanging warm lantern on the left, casting golden light into the empty center as if lighting a person standing there. In the background, a large arched or tall window shows a deep indigo star-filled night sky, softly defocused. Tall bookshelves along the back and far sides, not crowding the center. Floating glowing particles and tiny star-like motes of gold, soft lavender, and faint rose drift in the air like magical dust. A few floating books only far off to the sides. Soft depth of field on the far shelves and sky.

Color palette chosen to complement a fair peach-pink skinned anime character with starry indigo-violet eyes, and a name meaning light: deep indigo and midnight navy, warm parchment and cream, brass gold, soft lavender particle glow, small blush-pink candle or flower accents, a few coral-red book spines. Warm lamp versus cool starlight. Tidy, beautiful, not chaotic.

No text, no letters, no logos, no watermarks, no on-screen UI. Masterpiece anime magical interior background, sharp and high resolution.

---

## 草案里还需要注意的问题

定稿或换生成器复用时，可在提示词里额外强调：

1. **赛博版**：画面底部中央不要放长凳/茶几，角色站位会被挡住；整体更偏三维写实，若要统一成动漫背景风，可加上 “flat anime background painting, not a 3D render”。右侧层架略满，礼物 overlay 会压到霓虹和植物。
2. **星空版**：左上角暖色提灯、右侧漂浮书会和弹幕/礼物区重叠；定稿时可把灯略降、把浮书再往边靠。
3. **温馨版**：左上角有藤蔓和灯串，弹幕区不是完全素墙，但右侧非常干净，站位最好。
4. 三张都是 1280×720 生成后再放大，精细定稿建议用能直接出 1920×1080 或 3840×2160 的生成器重跑同一套提示词。
5. 预览图里的剪影只是站位示意，不是流明本人；仓库里没有可直接合成的全身立绘。

