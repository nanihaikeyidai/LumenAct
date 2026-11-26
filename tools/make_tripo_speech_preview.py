"""Build a speech-ready Tripo copy and render an audio-driven close-up in Blender."""
import argparse
import math
import sys
import wave
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("audio", type=Path, help="Mono 16-bit PCM narration")
parser.add_argument("frames", type=Path)
parser.add_argument("--refine-face", action="store_true")
parser.add_argument("--stills", action="store_true")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
args.frames.mkdir(parents=True, exist_ok=True)

scene = bpy.context.scene
face = bpy.data.objects["tripo_node_449779d7"]
rig = next(obj for obj in scene.objects if obj.type == "ARMATURE")
keys = face.data.shape_keys.key_blocks
basis, mouth, blink = (keys[name] for name in ("Basis", "mouth_a", "eye_close"))
for key in keys:
    key.value = 0

# Landmarks measured on the Tripo front render, in Blender world coordinates.
mouth_x, mouth_z = .027, .7255
world = face.matrix_world.copy()
local = world.inverted()
head_index = face.vertex_groups["Head"].index
for vertex in face.data.vertices:
    i = vertex.index
    point = world @ basis.data[i].co
    x, y, z = point
    mouth.data[i].co = basis.data[i].co
    blink.data[i].co = basis.data[i].co
    head = next((g.weight for g in vertex.groups if g.group == head_index), 0)
    if head < .5 or y > -.057:
        continue
    dx, dz = x - mouth_x, z - mouth_z
    if abs(dx) < .033 and -.036 < dz < .018:
        blend = math.exp(-.5*((dx/.015)**2 + ((dz+.012)/.015)**2))
        # Only tuck the lower lip and chin slightly down.
        lower = min(1, max(0, -dz/.009))
        mouth.data[i].co = local @ (point + Vector((0, .0007*blend*lower, -.007*blend*lower)))
    if .750 < z < .803:
        for eye_x in (-.019, .079):
            u, v = (x-eye_x)/.032, (z-.774)/.027
            if abs(u) < 1 and abs(v) < 1:
                falloff = (1-u**4)**2 * (1-v**6)**2
                blink.data[i].co = local @ (point + Vector((0, 0, (.774-z)*.94*falloff)))
                break

def refine_skin():
    # Derive the retouch mask from the face triangles and their own UV islands.
    # Texels in the eyes, brows, lips and hair retain their original line work.
    material = face.data.materials[0]
    shader = next(n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    tex = shader.inputs["Base Color"].links[0].from_node
    image = tex.image.copy()
    image.name = "Tripo facial skin retouch"
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    pixels = pixels.reshape(height, width, 4)
    uv = face.data.uv_layers.active.data
    mask = np.zeros((height,width), np.float32)
    edge_mask = np.zeros_like(mask)
    coords = np.array([tuple(world @ v.co) for v in face.data.vertices])
    for poly in face.data.polygons:
        pos = coords[list(poly.vertices)]
        x,y,z = pos.mean(axis=0)
        if abs(x-.024) > .103 or y > -.055 or not .700 < z < .827:
            continue
        triangle = np.array([tuple(uv[i].uv) for i in poly.loop_indices])*[width,height]-.5
        lo = np.maximum(0, np.floor(triangle.min(axis=0)).astype(int))
        hi = np.minimum([width-1,height-1],np.ceil(triangle.max(axis=0)).astype(int))
        if np.any(hi<lo):
            continue
        xx, yy = np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1))
        a,b,c = triangle
        v1,v2=b-a,c-a
        det=v1[0]*v2[1]-v2[0]*v1[1]
        if abs(det)<1e-8:
            continue
        v=((xx-a[0])*v2[1]-(yy-a[1])*v2[0])/det
        w=(v1[0]*(yy-a[1])-v1[1]*(xx-a[0]))/det
        inside=(v>=0)&(w>=0)&(v+w<=1)
        mask[yy[inside],xx[inside]]=1
        # Project each UV sample onto the calibrated 720px front portrait.
        px = pos[0,0]+v*(pos[1,0]-pos[0,0])+w*(pos[2,0]-pos[0,0])
        pz = pos[0,2]+v*(pos[1,2]-pos[0,2])+w*(pos[2,2]-pos[0,2])
        sx,sy = 360+(px-.018)*720/.405, 360-(pz-.786)*720/.405
        def band(cx,cy,rx,ry,slope):
            return np.clip((1-((sx-cx)/rx)**4-((sy-cy-slope*(sx-cx))/ry)**4)*1.5,0,1)
        coverage=np.maximum.reduce([band(286,344,45,9,.17),band(474,339,43,10,-.13),
                                    band(506,406,13,15,-.95)])
        edge_mask[yy[inside],xx[inside]]=coverage[inside]

    y,x=np.where(mask>0)
    rgb=pixels[y,x,:3].copy()
    r,g,b=rgb.T
    skin=np.clip((r-g-.012)/.05,0,1)*np.clip((g-b+.012)/.035,0,1)*np.clip((r-.17)/.24,0,1)
    nearby=np.stack([pixels[np.clip(y+dy,0,height-1),np.clip(x+dx,0,width-1),:3]
                     for dy in (-3,0,3) for dx in (-3,0,3)])
    median=np.median(nearby,axis=0)
    filtered=rgb+np.clip(median-rgb,-.09,.09)*.70
    # Soften the baked orange shadows around cheeks while retaining tonal depth.
    filtered+=np.maximum(0,.72-filtered)*np.array([.047,.069,.073])
    pixels[y,x,:3]=np.clip(rgb+(filtered-rgb)*skin[:,None],0,1)
    # Repaint stray warm dark flecks on the skin side of the fringe.
    # Keep near-black lash outlines and cool silver hair pixels.
    weight=edge_mask[y,x]*np.clip((r-b-.018)/.055,0,1)*np.clip((r-.055)/.13,0,1)
    skin_base=np.array([.77,.59,.49])
    cleaned=filtered+(skin_base-filtered)*.38
    pixels[y,x,:3]+=weight[:,None]*(cleaned-pixels[y,x,:3])
    image.pixels.foreach_set(pixels.ravel())
    image.update()
    image.pack()
    tex.image=image
    print("Retouched skin texels:",int((skin>.1).sum()),flush=True)

if args.refine_face:
    refine_skin()

def cast_surface(x, z):
    found, p, _, _ = face.ray_cast(local @ Vector((x, -1, z)), local.to_3x3() @ Vector((0, 1, 0)))
    if not found:
        raise RuntimeError(f"Unable to find lip surface at {x}, {z}")
    return (world @ p).y

def mouth_material(name, rgb):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    shader = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (*rgb, 1)
    shader.inputs["Roughness"].default_value = .85
    shader.inputs["Specular IOR Level"].default_value = .12
    return mat

# A thin, curved dark inner-mouth surface follows the model's facial depth.
# The neutral shape sits below the skin and is revealed by the same mouth_a key.
closed, opened, polygons, colors = [], [], [], []
rows, cols = 20, 44
for row in range(rows + 1):
    v = row / rows
    for col in range(cols + 1):
        u = 2 * col / cols - 1
        arch = max(.008, 1-u*u)
        x = mouth_x + .0118*u
        seam = mouth_z + .0010*u + .0013*arch
        z = seam + .0014*arch - .0115*arch**.8*v
        depth = cast_surface(x, z)
        closed.append((mouth_x+.009*u, cast_surface(mouth_x+.009*u,seam)+.00035, seam))
        opened.append((x, depth-.0018-.00045*abs(2*v-1), z))
        # A soft tongue highlight tapers out before reaching either mouth corner.
        tongue = math.exp(-((v-.84)/.23)**2-(u/.65)**4)
        shade = .75 + .25*arch
        colors.append(((.044+.135*tongue)*shade, (.010+.034*tongue)*shade,
                       (.016+.040*tongue)*shade, 1))
        if row and col:
            i = row*(cols+1)+col
            polygons.append((i-cols-2, i-1, i, i-cols-1))
inner_data = bpy.data.meshes.new("Tripo mouth interior")
inner_data.from_pydata(closed, [], polygons)
inner_data.update()
inner = bpy.data.objects.new("Tripo mouth interior", inner_data)
scene.collection.objects.link(inner)
color = inner_data.color_attributes.new(name="MouthTint", type="FLOAT_COLOR", domain="POINT")
for item, rgba in zip(color.data, colors):
    item.color = rgba
mat = mouth_material("Oral cavity", (1,1,1))
tint = mat.node_tree.nodes.new("ShaderNodeVertexColor")
tint.layer_name = color.name
shader = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
mat.node_tree.links.new(tint.outputs["Color"], shader.inputs["Base Color"])
inner_data.materials.append(mat)
for poly in inner_data.polygons:
    poly.use_smooth = True
inner.vertex_groups.new(name="Head").add(list(range(len(closed))), 1, "REPLACE")
inner.shape_key_add(name="Basis")
inner_key = inner.shape_key_add(name="mouth_a")
for vertex, p in zip(inner_key.data, opened):
    vertex.co = p

# Merge into the skinned mesh so the same morph also drives the opening in GLB.
bpy.ops.object.select_all(action="DESELECT")
face.select_set(True)
inner.select_set(True)
bpy.context.view_layer.objects.active = face
n_vertices = len(face.data.vertices)
bpy.ops.object.join()
keys = face.data.shape_keys.key_blocks
assert len(face.data.vertices) == n_vertices + len(closed)
assert len(keys) == 30
assert any((keys["mouth_a"].data[i].co-keys["Basis"].data[i].co).length > .001
           for i in range(n_vertices, len(face.data.vertices)))

def aim(obj, point):
    obj.rotation_euler = (Vector(point)-obj.location).to_track_quat("-Z", "Y").to_euler()

camera = bpy.data.objects.new("Speech preview", bpy.data.cameras.new("Speech preview"))
scene.collection.objects.link(camera)
camera.location = (.018, -2.4, .786)
aim(camera, (.018, -.02, .786))
camera.data.type = "ORTHO"
camera.data.ortho_scale = .405
scene.camera = camera
for name, loc, energy, size in [
    ("Soft key", (-.47, -1.30, 1.18), 142, 1.25),
    ("Soft fill", (.75, -1.20, .86), 62, 1.6),
    ("Hair rim", (.22, .46, 1.12), 80, 1.2),
]:
    light = bpy.data.lights.new(name, "AREA")
    obj = bpy.data.objects.new(name, light)
    scene.collection.objects.link(obj)
    obj.location = loc
    light.energy = energy
    light.shape = "DISK"
    light.size = size
    aim(obj, (.02, -.03, .79))

scene.world = bpy.data.worlds.new("Speech preview background")
scene.world.use_nodes = True
background = next((node for node in scene.world.node_tree.nodes if node.type == "BACKGROUND"), None)
if background is None:
    nodes = scene.world.node_tree.nodes
    background = nodes.new("ShaderNodeBackground")
    output = next((node for node in nodes if node.type == "OUTPUT_WORLD"), None)
    if output is None:
        output = nodes.new("ShaderNodeOutputWorld")
    scene.world.node_tree.links.new(background.outputs["Background"], output.inputs["Surface"])
background.inputs["Color"].default_value = (.044, .057, .082, 1)
scene.view_settings.view_transform = "AgX"
scene.view_settings.exposure = -.32
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.eevee.taa_render_samples = 16
scene.render.resolution_x = scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"

if args.stills:
    for name, opening, closing in [("neutral",0,0), ("open",.85,0), ("blink",0,1)]:
        keys["mouth_a"].value = opening
        keys["eye_close"].value = closing
        scene.render.filepath = str(args.frames / f"{name}.png")
        bpy.ops.render.render(write_still=True)
    raise SystemExit(0)

for key in keys:
    key.value = 0
source = Path(bpy.data.filepath)
output = source.with_name("lumen-tripo-face-refined" if args.refine_face else "lumen-tripo-speech-v2")
bpy.ops.wm.save_as_mainfile(filepath=str(output.with_suffix(".blend")))
rig.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(output.with_suffix(".glb")), export_format="GLB",
                          use_selection=True, export_morph=True, export_morph_normal=False,
                          export_vertex_color="MATERIAL", export_all_influences=True, export_animations=False)

# glTF multiplies COLOR_0 into every material. Only the mouth uses vertex tint.
import json
import struct
glb = output.with_suffix(".glb")
data = glb.read_bytes()
size = struct.unpack_from("<I", data, 12)[0]
document = json.loads(data[20:20+size])
for material in document["materials"]:
    if material["name"].startswith("tripo_mat_"):
        material["pbrMetallicRoughness"].update(metallicFactor=0, roughnessFactor=.88)
        material["alphaMode"]="MASK"
        material["alphaCutoff"]=.35
for mesh_info in document["meshes"]:
    for primitive in mesh_info["primitives"]:
        if document["materials"][primitive["material"]]["name"] != "Oral cavity":
            primitive["attributes"].pop("COLOR_0", None)
encoded = json.dumps(document, separators=(",", ":")).encode()
encoded += b" " * (-len(encoded) % 4)
binary = data[20+size:]
glb.write_bytes(struct.pack("<4sIIII", b"glTF", 2, 20+len(encoded)+len(binary),
                            len(encoded), 0x4E4F534A) + encoded + binary)

with wave.open(str(args.audio), "rb") as wav:
    if wav.getsampwidth() != 2 or wav.getnchannels() != 1:
        raise ValueError("Expected mono 16-bit PCM WAV")
    rate = wav.getframerate()
    audio = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(float)/32768

fps = scene.render.fps
frame_count = math.ceil(len(audio)/rate*fps)
rms = []
for i in range(frame_count):
    center = (i+.35)/fps
    sample = audio[max(0, int((center-.024)*rate)):int((center+.024)*rate)]
    rms.append(float(np.sqrt(np.mean(sample**2))) if len(sample) else 0)
peak = max(.01, float(np.percentile(rms, 92)))
opening = 0.0
mouth_track = []
for level in rms:
    target = min(1, max(0, (level/peak-.08)/.82))**.65
    opening += (.74 if target > opening else .42)*(target-opening)
    mouth_track.append(.90*opening if opening > .025 else 0)
print(f"SPEECH_QA frames={frame_count} peak_mouth={max(mouth_track):.3f} "
      f"neutral_frames={sum(v == 0 for v in mouth_track)}", flush=True)

scene.frame_start, scene.frame_end = 1, frame_count
for frame, value in enumerate(mouth_track, 1):
    keys["mouth_a"].value = value
    keys["mouth_a"].keyframe_insert(data_path="value", frame=frame)
    # Two short blinks, around the clause and sentence transitions.
    keys["eye_close"].value = max(
        (math.cos(d*math.pi/2)**2 if d < 1 else 0)
        for d in (abs(frame - center)/2.5 for center in (62, 141))
    )
    keys["eye_close"].keyframe_insert(data_path="value", frame=frame)

scene.render.filepath = str(args.frames / "frame_")
bpy.ops.render.render(animation=True)


