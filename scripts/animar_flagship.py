
import bpy, os, math, time
from pathlib import Path
from mathutils import Vector
s=bpy.context.scene
root=Path(os.environ['DT_V3_ROOT'])
folder=root/'Dual Twist - Flagship V3'
pre=Path(os.environ['TEMP'])/'dual-v3-film-frames'
pre.mkdir(exist_ok=True)
stills=[o for o in s.objects if o.type=='CAMERA']
cam_collection=bpy.data.collections['06 · Câmeras']
data=bpy.data.cameras.new('Passeio | ótica')
data.clip_start=.05
data.clip_end=150
cam=bpy.data.objects.new('Passeio cinematográfico | 20 s',data)
cam_collection.objects.link(cam)
aim=bpy.data.objects.new('Passeio | alvo',None)
aim.empty_display_size=.15
cam_collection.objects.link(aim)
track=cam.constraints.new('TRACK_TO')
track.target=aim
track.track_axis='TRACK_NEGATIVE_Z'
track.up_axis='UP_Y'

beats=[
 (0,(2.0,-15.2,2.43),(.0,-4.40,1.99),29),
 (1.8,(1.71,-11.5,2.24),(.25,-2.65,1.81),29),
 (3.5,(1.40,-7.34,1.93),(.24,-.25,1.51),27),
 (5.3,(1.39,-4.46,1.82),(.00,.94,1.43),25),
 (7.6,(2.15,-2.75,1.75),(.01,.43,1.42),34),
 (8.65,(2.20,-2.53,1.73),(-.04,.32,1.40),36),
 (9.70,(1.96,-3.11,1.76),(-.06,.34,1.42),34),
 (11.7,(.96,-5.91,1.87),(-1.63,-1.66,1.53),28),
 (13.3,(-1.21,-6.88,1.88),(-3.79,-3.51,1.67),30),
 (14.65,(-2.60,-6.58,1.92),(-4.22,-3.42,1.79),27),
 (15.40,(-2.68,-6.75,1.95),(-4.23,-3.25,1.80),27),
 (16.7,(-2.49,-8.63,2.22),(-3.18,-4.28,1.76),28),
 (18.25,(-.89,-12.55,2.51),(-.80,-4.37,1.96),29),
 (19.958333,(2.38,-18.20,2.75),(.03,-4.85,2.18),31),
]
for seconds,position,target,lens in beats:
    frame=round(seconds*24)+1
    cam.location=position
    aim.location=target
    data.lens=lens
    cam.keyframe_insert(data_path='location',frame=frame)
    aim.keyframe_insert(data_path='location',frame=frame)
    data.keyframe_insert(data_path='lens',frame=frame)
for owner in (cam,aim,data):
    a=owner.animation_data
    for layer in a.action.layers:
        for strip in layer.strips:
            for curve in strip.channelbag(a.action_slot).fcurves:
                for key in curve.keyframe_points:
                    key.handle_left_type='AUTO_CLAMPED'
                    key.handle_right_type='AUTO_CLAMPED'
s.camera=cam
for frame,name in [(1,'Fachada · entrada'),(129,'Ilha de lançamento'),(241,'Transição · Pit Stop'),(373,'Recuo · visão geral')]:
    s.timeline_markers.new(name,frame=frame)
bounds=[]
for group in ('01 · Arquitetura','02 · Mobiliário comercial','03 · Comunicação e campanha'):
    for o in bpy.data.collections[group].objects:
        if o.type not in {'MESH','FONT'}: continue
        pts=[o.matrix_world@Vector(v) for v in o.bound_box]
        bounds.append((o.name,[(min(v[k] for v in pts),max(v[k] for v in pts)) for k in range(3)]))
closest=(999,0,'')
turn_max=0
before=None
for frame in range(1,481):
    s.frame_set(frame)
    m=cam.matrix_world.copy()
    p=m.translation
    q=m.to_quaternion()
    if before is not None:
        turn_max=max(turn_max,math.degrees(2*math.acos(min(abs(q.dot(before)),1)))*24)
    before=q
    for label,b in bounds:
        clearance=math.sqrt(sum(max(lo-p[i],0,p[i]-hi)**2 for i,(lo,hi) in enumerate(b)))
        closest=min(closest,(clearance,frame,label))
print('FILM QA',closest,round(turn_max,2),flush=True)
assert closest[0]>.21
assert len(stills)==4
assert all(im.packed_file for im in bpy.data.images if im.source=='FILE')
assert len(bpy.data.scenes)==1 and s.frame_end==480
s.frame_set(1)
bpy.context.preferences.filepaths.save_version=1
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
for still in sorted(stills,key=lambda o:o.name):
    start=time.perf_counter()
    s.camera=still
    s.render.filepath=str(folder/(still.name+'.png'))
    bpy.ops.render.render(write_still=True)
    print('FULL_HD',still.name,round(time.perf_counter()-start,2),flush=True)
s.camera=cam
s.render.resolution_x=528
s.render.resolution_y=298
s.eevee.taa_render_samples=10
for i,frame in enumerate(range(1,481,12)):
    s.frame_set(frame)
    s.render.filepath=str(pre/f'{i:03}.png')
    bpy.ops.render.render(write_still=True)
