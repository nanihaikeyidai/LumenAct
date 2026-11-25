# 流明直播间定稿：星空魔法书房

用户从三版草案中选定了 **C. 星空 / 魔法书房**。本目录是定稿 2D 背景 + 透明前景层。未使用 RunningHub，无积分消耗。

生成工具：cursor.studio `GenerateImage`（16:9，原生 1280×720 JPEG）+ 本地 Pillow（chroma key、层叠、Lanczos 放大到 2560×1440）。

配色依据仍与草案相同：公开仓库只有流明独立脸部。肤色桃粉 `#fed8d5`，星空靛紫瞳 `#4f2c6a` / `#556083` / 高光 `#a0a9eb`，预览器象牙米 `#e9e8e3`、珊瑚红 `#da5b48`、深青 `#1d2c33`。主光为左前方暖金，辅以靛蓝、薰衣草粒子与少量 blush 粉。

---

## 相对草案 `bg-starry.png` 改了什么

1. **铜灯从左上角移走。** 不再悬挂在弹幕区（左上约 28%×40%）。改为放在左中柜上，高度低于弹幕区，仍提供左前方暖色主光。左上角改为较安静的书架与墙面。
2. **右侧漂浮书从礼物区移走。** 不再占右上 / 右中。定稿只保留一本较小的书，收在远处拱窗左侧，不进入站位区，也不进入礼物区。
3. **中央与中下方站位保持空旷。** 只有木地板和底部一小条地毯，没有长凳或挡腿的家具。
4. 风格、房间结构、星空拱窗、漂浮光尘、粉花与蜡烛，尽量保持与选定草案一致。

---

## 交付文件

| 文件 | 尺寸 | 说明 |
| --- | --- | --- |
| `bg-starry-final.png` | 2560×1440 RGB | 定稿背景（由 1280×720 Lanczos 2× + 轻度锐化） |
| `bg-starry-final-preview.png` | 2560×1440 RGB | 背景 + 站位剪影占位 + 弹幕/礼物区示意 |
| `fg-desk.png` | 2560×1440 RGBA | 前景桌沿，预摆在画面底部，可 1:1 叠在背景上 |
| `fg-mic.png` | 2560×1440 RGBA | 黄铜桌面麦克风，偏右约 70% 宽度，底座落在桌面上 |
| `fg-props.png` | 2560×1440 RGBA | 打开的书、茶杯、发光小球，在桌面左侧 |
| `composite-preview.png` | 2560×1440 RGB | 背景 + 剪影 + 三张前景层的合成预览 |
| `source/bg-starry-final-1280x720.jpg` | 1280×720 | 定稿背景原生文件 |
| `source/fg-*-green-1280x720.jpg` | 1280×720 | 绿幕原图，便于用其他工具重新抠图 |
| `source/bg-starry-final-3840x2160.png` | 3840×2160 | 仅 3× 插值，没有新增细节，不建议作正式稿 |
| `source/fg-desk-thin-edge-2560.png` | 2560×1440 RGBA | 未加桌面进深的细桌沿版本 |

OBS / three.js 叠加顺序：背景 → 角色 → `fg-desk.png` → `fg-props.png` + `fg-mic.png`。

---

## 定稿背景提示词（实际采用的是第二轮，v2）

第一轮已把铜灯下移、清掉右侧漂浮书；第二轮在几乎同一张图上，把仍停在站位区右侧的大漂浮书收到远处窗边。定稿是第二轮结果。

### 中文（可复用）

请以附图为风格和房间结构的参考：同一间靛蓝魔法书房，同一扇星空拱窗，暖色木地板，高书架，blush 粉色花，蜡烛，金色与薰衣草漂浮光尘，暖铜灯光对上冷星光。保持同一套二次元 VTuber 背景绘制风格和配色（深靛蓝与午夜海军蓝、象牙与蜜桃暖色、黄铜金、浅薰衣草粒子、blush 粉花、少量珊瑚红书脊）。这是同一房间的定稿，不是换地方。

必须遵守的构图修改（与参考图冲突时，以这里为准）：

1. 左上角 overlay 区（大约左侧 28% 宽度、上方 40% 高度）要相对安静、低细节。不要把大铜灯、亮灯或密实装饰放在左上角。那里适合较安静的书架或素净靛蓝墙。
2. 把暖色铜灯光源下移到左中、大约半高或更低：铜灯放在左侧柜子上，或挂得更低、挨着左侧书架，明确低于左上 overlay 区。它仍要从左前方把金色主光打到中央空地面上，就像在给一个站在那里的人打光。
3. 右侧 overlay 区（大约右侧 26% 宽度，尤其是右上和右中）要相对安静、低细节。不要把漂浮的书放在右侧。不要有大件道具伸进这个区域。右侧书架可以保留，但更收、更安静，蜡烛和花要更小或更低。
4. 如果还要漂浮的书，最多一本或两本，放在远处窗边或窗框旁的远景，不要放在右侧 overlay，也不要放在空荡的站位区里。
5. 画面正中和中下方必须完全留白，作为全身角色的站位区。只有木地板，最底部可以有一条细地毯边。不要长凳、桌子或大件道具横切中下方或挡住腿。房间中间不要家具。

机位在站立者胸口高度，镜头平视向前，16:9 横构图。赛璐璐 / VTuber 动漫室内背景，清晰锐利，不要照片级三维写实。不要人物、角色、人体模型、脸、手、文字、字母、Logo、水印、屏幕 UI。

### English（第二轮实际送给 GenerateImage 的原文）

Make a nearly identical copy of the attached indigo magical study background, same camera, same architecture, same lighting, same anime VTuber background-painting style, same colors. Keep the brass lantern sitting on the left cabinet at mid-left (NOT hanging in the top-left). Keep the top-left corner a calm quiet bookshelf. Keep the right side calm, with no floating books in the upper-right gift overlay area. Keep the center and lower-center floor completely empty for a standing character, with only the wooden floor and the thin rug at the very bottom. Keep the starry arched window, bookshelves, pink flowers, candles, and floating gold and lavender motes. Keep the warm golden key light from the front-left lantern.

ONE required change: remove the large floating book that hangs in the open air in the middle-right of the room, near the standing space. Do not leave a book floating in the empty center or beside where a person would stand. If you still want a magical floating book, make it much smaller and tuck it far back against the window or just beside the window frame in the distant background, not in the open floor space.

Do not add a hanging lantern in the top-left. Do not add floating books on the right side. Do not add a bench or table in the lower center. No people, no faces, no hands, no text, no logos, no UI. 16:9 landscape, sharp anime interior background.

参考图：草案 `bg-starry-1280x720.jpg`（第一轮），以及第一轮结果（第二轮）。

---

## 前景：桌沿 `fg-desk.png`

### 中文（可复用）

虚拟主播直播用的单张前景素材，16:9 横构图。画面上半部分是完全平坦的纯绿幕，颜色为 `#00FF00`，不要渐变，绿幕上不要阴影，不要房间、墙、窗或背景家具。

只在画面最底部画一条近景木桌沿，材质和光要贴合附图的书房：同样的暖橡木，左侧受金光、右侧略带冷紫，可以有细黄铜包边或嵌条。机位在站立者胸口高度、镜头平视，所以这张桌子就在镜头正前方：一条很浅的、透视压缩过的桌面，以及底部的桌沿厚度 / 裙板。桌子只占画面底部大约 16% 到 18% 的高度，横向铺满。桌面是空的，不要物体、麦克风、书、杯子、人物、手、文字。干净的赛璐璐动漫背景绘制风格，木纹清晰，不要照片级写实。

重要：桌子以上必须只有纯 `#00FF00` 绿。木头上不要出现纯绿。不要把桌腿伸进绿色里。

### English（实际原文）

A single foreground asset for a VTuber livestream, 16:9 landscape. The entire upper part of the image is a perfectly flat solid pure chroma-key green, hex #00FF00, no gradients, no shadows on the green, no room, no walls, no window, no background furniture.

Only at the very bottom of the frame, paint a close foreground wooden desk edge that matches the attached study: the same warm oak wood, gold-lit from the left and slightly cooler purple-tinted on the right, optional thin brass inlay or brass-edged trim. Camera is at a standing person's chest height looking straight forward, so the desk is right in front of the camera: a shallow foreshortened desktop surface as a horizontal band, then the front thickness / apron of the desk at the bottom edge. The desk should occupy only about the bottom 16 to 18 percent of the frame height, spanning the full width. The desktop is mostly empty, no objects, no microphone, no books, no cups, no people, no hands, no text. Clean anime / cel-shaded background-painting style, sharp wood grain, not photoreal.

Important: everything above the desk must be pure #00FF00 green only. No green color on the wood itself. No legs sticking up. No bench in the middle. This is only a desk foreground strip.

### 本地后处理

生成结果是一条很干净的细桌沿（几乎看不到桌面进深），道具会显得悬空。定稿 `fg-desk.png` 用同一段木纹，在桌沿上方本地延伸了一条约 132 像素（2560 高度下）的浅桌面，左侧偏暖、右侧偏紫、后缘略压暗。未延伸的细桌沿保存在 `source/fg-desk-thin-edge-2560.png`。绿幕用 `g - max(r, b)` 软抠，并做了去溢色；边缘有轻微 0.6px 模糊，JPEG 绿边基本去干净。

---

## 前景：麦克风 `fg-mic.png`

### 中文（可复用）

虚拟主播直播用的单张前景素材，16:9 横构图。整张画布是完全平坦的纯绿幕 `#00FF00`，不要渐变，绿幕上不要阴影，不要房间，也不要铺满整张画的桌面。

绿幕上只放一件物品：一只二次元风格的小型桌面麦克风，短金属支架，黄铜与暗青铜收尾，贴合魔法书房，胶囊是紧凑的电容或复古播音造型，底部是小圆座，支柱短、可略微倾斜。可以有一颗很小的暖色指示灯。不要 Logo，不要可识别文字，不要大块防喷罩，不要横穿画面的悬臂。

位置：麦克风在画面下部、略偏右（大约在宽度 70% 处），像是立在靠近底部的矮桌上。底座大约在画面 86% 到 90% 高度。整只麦克风要小，不要升到画面中部；顶部留在下三分之一，避免挡住角色躯干。左前方暖光。麦克风本身不要含纯绿。不要人物、手、其他道具或家具。干净赛璐璐物体，边缘清晰。

### English（实际原文）

A single foreground asset for a VTuber livestream, 16:9 landscape. The whole canvas is a perfectly flat solid pure chroma-key green background, hex #00FF00, no gradients, no shadows on the green, no room and no desk surface filling the frame.

On this green, place only one object: a small anime-style table microphone on a short metal stand, brass and dark bronze finish to match a magical study, with a compact condenser or vintage broadcast capsule, a small round stand base, and a short upright or slightly angled stem. Optional tiny warm indicator light, no logo, no readable text, no pop filter covering a huge area, no boom arm crossing the frame.

Position: the mic sits in the lower part of the frame, slightly right of center (about 70 percent across the width), as if it is standing on a low desk near the bottom. The base is near the bottom, around 86 to 90 percent down the frame. The whole microphone is small and should not rise into the middle of the frame; the top of the mic should stay in the lower third, so it will not block a character's torso. Lit by warm light from the left, soft shadow only on the green immediately under the base if needed, preferably no shadow.

No people, no hands, no other props, no furniture. Clean cel-shaded anime object, sharp edges, not photoreal. The microphone itself must not contain pure green.

### 本地后处理

模型把麦克风几乎放在了正中央。抠图后把精灵移到宽度约 70% 处，底座落在桌面靠近前缘的位置（约 y=1167 / 1440）。边缘干净，网罩孔隙基本保留。

---

## 前景：道具 `fg-props.png`

第一轮生成多出了灯笼和花瓶，已弃用。定稿用的是下面这一轮。

### 中文（可复用）

虚拟主播直播用的单张前景素材，16:9 横构图。整张画布是完全平坦的纯绿幕 `#00FF00`，不要渐变，绿幕上不要阴影，不要房间、墙或家具。

只在画面左下、像是放在矮桌上，摆这三件小道具的紧凑一组：(1) 一本打开的小书，奶油色书页，封面是深靛蓝或酒红；(2) 一只象牙或 blush 粉色瓷茶杯，带托碟；(3) 一颗很小的魔法发光玻璃球或弹珠，发出浅薰衣草金的光，可以搁在书上或书旁。整组要小、要低：留在左下三分之一，底部大约在画面 85% 到 90% 高度，最高处不要高过约 70% 高度。中央和整条右侧保持空绿幕。

严格禁止：不要灯笼、台灯、蜡烛、花瓶、花、植物、麦克风或其他物体。只要打开的书、茶杯托碟、小发光球。不要人物、手、文字、Logo。干净赛璐璐物体，边缘清晰，左前方暖光，不要照片级写实。道具本身不要含纯绿 `#00FF00`。

### English（实际原文）

A single foreground asset for a VTuber livestream, 16:9 landscape. The entire canvas is a perfectly flat solid pure chroma-key green background, hex #00FF00, no gradients, no shadows on the green, no room, no walls, no furniture.

Place ONLY these three small desk props in a compact cluster in the lower-left of the frame, as if sitting on a low desk: (1) a small open book with cream pages and a dark indigo or maroon cover, (2) a delicate ivory or blush-pink porcelain teacup on a saucer, and (3) a tiny magical glowing glass orb or marble giving off a soft lavender-gold light, maybe resting on the book or just beside it. Keep the whole cluster small and low: it should stay in the lower-left third, with the bottoms of the objects near about 85 to 90 percent down the frame, and the top of the tallest object no higher than about 70 percent down the frame. Leave the center and the entire right side empty green.

STRICT: do NOT include a lantern, lamp, candle, vase, flowers, plant, microphone, or any other object. Only the open book, the teacup with saucer, and the tiny glowing orb. No people, no hands, no text, no logos. Clean cel-shaded anime objects, sharp edges, warm light from the left, not photoreal. The props themselves must not contain pure green #00FF00.

### 本地后处理

抠图后把整组下移，使摊开的书靠近桌面前缘；茶杯和发光球因原图是略俯视的 3/4 视角，会落在桌面偏后的位置。未拆开分组，以避免书页与托碟重叠处出现缺口。

---

## 已知剩余问题

- 背景与前景都是 1280×720 生成后再放大。3840×2160 只是 3× 插值，对比裁切后没有新的细节，正式稿使用 2560×1440。若要真正的 4K，建议用能原生出 1920×1080 或 3840×2160 的生成器重跑同一套提示词。
- 延伸出来的桌面木纹是从桌沿取样纵向拉伸的，透视没有真正向后退，和桌沿交接处有一条水平分缝，可以看成装饰线，但不是完整的三维桌面。若要更自然，可在 Blender 里用同一材质重做近景桌子。
- 茶杯、发光球与摊开的书是略俯视画的，和胸口高度平视的桌沿视角不完全一致；它们贴在桌面后缘，没有接触阴影，会略有“贴纸感”。
- 礼物区仍会叠在星空窗户的一部分上，这是窗的位置决定的，窗本身无法完全留白。右上书架还有一只玻璃瓶，比漂浮书克制，但不是完全素墙。
- 前景物体没有投到桌子上的阴影。
- 站位剪影只是占位，不是流明本人；仓库里没有可合成的全身立绘。
