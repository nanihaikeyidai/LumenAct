import bpy, json, math, os, sys
from mathutils import Vector
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
outdir = args[0] if args else os.path.dirname(bpy.data.filepath)
blend_in = bpy.data.filepath
mesh = bpy.data.objects.get('tripo_node_449779d7') or next(o for o in bpy.data.objects if o.type=='MESH')
# Requested first batch and follow-on common visemes/expressions. Names kept verbatim.
keys = {
'eyebrow_up_L': ('brow',-1),'eyebrow_up_R': ('brow',1),
'eye_close': ('close',0),'mouth_smile_1': ('smile',0),
'mouth_a': ('vowel','a'),'mouth_i': ('vowel','i'),'mouth_u': ('vowel','u'),'mouth_e': ('vowel','e'),'mouth_o': ('vowel','o'),
'vrc.v_sil': ('vowel','sil'),'vrc.v_aa': ('vowel','a'),'vrc.v_ou': ('vowel','u'),'vrc.v_ih': ('vowel','i'),'vrc.v_e': ('vowel','e'),
'vrc.v_th': ('vowel','th'),'vrc.v_nn': ('vowel','nn'),'vrc.v_dd': ('vowel','dd'),'vrc.v_kk': ('vowel','kk'),'vrc.v_ff': ('vowel','ff'),'vrc.v_ch': ('vowel','ch'),'vrc.v_rr': ('vowel','rr'),'vrc.v_ss': ('vowel','ss'),
'eye_wink_1_L': ('wink',-1),'eye_wink_1_R': ('wink',1),'sp_cheek': ('cheek',0),
'sp_tear_default': ('tear',0),'sp_tear_cool': ('tear',1),'eye_star': ('eye_symbol',0),'eye_heart': ('eye_symbol',1)
}
# Use head vertex group and facial front surface in world space; deltas are sculpt-like, never copied by vertex index.
vg = mesh.vertex_groups.get('Head')
if not vg: raise RuntimeError('Head vertex group missing')
gidx = vg.index
headw={}
for v in mesh.data.vertices:
    w=next((g.weight for g in v.groups if g.group==gidx),0.0)
    if w>.18:
        p=mesh.matrix_world @ v.co
        x,y,z=p
        # facial midface plane; reject rear head/hair by front-Y and face bounds
        if -0.125 < y < -0.052 and abs(x)<.13 and .685<z<.865:
            headw[v.index]=(x,y,z,w)
if len(headw)<500: raise RuntimeError('Facial selection too small: %d'%len(headw))
# smooth, localized influences based on spatial landmarks, in meters

def g(x,z,cx,cz,sx,sz): return math.exp(-0.5*((x-cx)/sx)**2-0.5*((z-cz)/sz)**2)
def influence(kind, side, xyz, variant=None):
    x,y,z=xyz; front=max(0,min(1,(-y-.052)/.04));
    eyeL=g(x,z,-.052,.778,.030,.017); eyeR=g(x,z,.052,.778,.030,.017)
    mouth=g(x,z,0,.731,.038,.018)
    browL=g(x,z,-.055,.800,.035,.010); browR=g(x,z,.055,.800,.035,.010)
    if kind=='brow': return (browL if side<0 else browR)*front
    if kind=='close': return max(eyeL,eyeR)*front
    if kind=='wink': return (eyeL if side<0 else eyeR)*front
    if kind=='smile': return mouth*front
    if kind=='vowel': return mouth*front
    if kind=='cheek': return (g(x,z,-.083,.757,.018,.017)+g(x,z,.083,.757,.018,.017))*front
    if kind=='tear': return (g(x,z,-.057,.778,.010,.018)+g(x,z,.057,.778,.010,.018))*front
    if kind=='eye_symbol': return max(eyeL,eyeR)*front
    return 0

def delta(name, xyz):
    x,y,z=xyz; kind,arg=keys[name]; w=influence(kind,arg,xyz,arg)
    if kind=='brow': return Vector((0,0,.012*w))
    if kind in ('close','wink'):
        # Compress the textured eye vertically around its center; also slightly bring upper/lower lids forward.
        side=arg
        eye= (math.exp(-.5*((x-(side*.052))/.030)**2) if kind=='wink' else max(math.exp(-.5*((x+.052)/.030)**2),math.exp(-.5*((x-.052)/.030)**2)))
        eye*=math.exp(-.5*((z-.778)/.021)**2)*max(0,min(1,(-y-.052)/.04))
        return Vector((0,-.0015*eye,-(z-.778)*.88*eye))
    if kind=='smile':
        corner=abs(x)/.038
        return Vector((0,-.0015*w,.009*w*corner))
    if kind=='vowel':
        typ=arg
        # For this mesh the face is a textured single surface; shape the lip area only.
        if typ in ('sil',): amp=0
        elif typ in ('a','aa'): amp=.010
        elif typ in ('o','ou','u'): amp=.006
        elif typ in ('i','ih','e','ch','ss','rr','th','nn','dd','kk','ff'): amp=.004
        else: amp=.005
        vertical=math.exp(-.5*((z-.731)/.018)**2)
        width=math.exp(-.5*(x/.045)**2)
        dz=(1 if z>=.731 else -1)*amp*w*vertical*width
        # central mouth surface recesses, emphasizing rounded vowels
        recess=-.003*w*(1 if typ in ('o','ou','u','a','aa') else .4)
        return Vector((0,recess,dz))
    if kind=='cheek': return Vector((0,-.003*w,0))
    if kind=='tear': return Vector((0,-.001*w,0))
    if kind=='eye_symbol': return Vector((0,-.001*w,0))
    return Vector((0,0,0))

basis=mesh.data.shape_keys.key_blocks[0] if mesh.data.shape_keys else mesh.shape_key_add(name='Basis')
created=[]
for name in keys:
    if mesh.data.shape_keys.key_blocks.get(name): continue
    kb=mesh.shape_key_add(name=name,from_mix=False); kb.slider_min=0; kb.slider_max=1
    for idx,(x,y,z,weight) in headw.items():
        # strength feathers at group edges to isolate face region
        fac=min(1,max(0,(weight-.18)/.42))
        d=delta(name,(x,y,z))*fac
        if d.length:
            p=mesh.matrix_world @ basis.data[idx].co
            kb.data[idx].co = mesh.matrix_world.inverted() @ (p+d)
    created.append(name)
# verify deltas stay within selected face-only set and no untouched vertex changed
for kb in mesh.data.shape_keys.key_blocks[1:]:
    if kb.name not in keys: continue
    changed=0; outside=0
    for i in range(len(mesh.data.vertices)):
        if (kb.data[i].co-basis.data[i].co).length>1e-7:
            changed+=1
            if i not in headw: outside+=1
    if outside: raise RuntimeError('%s modified %d vertices outside facial mask'%(kb.name,outside))
print('MORPH_KEYS_ADDED',len(created),'FACE_VERTICES',len(headw),'KEYS',json.dumps(list(keys),ensure_ascii=False))
# save independent working file
outblend=os.path.join(outdir,'lumen-tripo-morph-batch.blend')
bpy.ops.wm.save_as_mainfile(filepath=outblend)

