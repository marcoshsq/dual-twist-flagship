import bpy, os, time
from pathlib import Path
s=bpy.context.scene
root=Path(os.environ['DT_V3_ROOT'])
folder=root/'Dual Twist - Flagship V3'
pre=Path(os.environ['TEMP'])/'dual-v3-film-frames'
pre.mkdir(exist_ok=True)
cam=s.camera
stills=[o for o in s.objects if o.type=='CAMERA' and o!=cam]
s.eevee.shadow_pool_size='1024'
s.eevee.shadow_resolution_scale=.65
s.eevee.taa_render_samples=32
for light in bpy.data.lights:
    light.shadow_maximum_resolution=.014
bpy.context.preferences.filepaths.save_version=1
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
for still in sorted(stills,key=lambda o:o.name):
    start=time.perf_counter()
    s.camera=still
    s.render.filepath=str(folder/(still.name+'.png'))
    bpy.ops.render.render(write_still=True)
    print('FULL_HD',still.name,round(time.perf_counter()-start,2),flush=True)
s.camera=cam
s.render.resolution_x=1280
s.render.resolution_y=720
s.eevee.taa_render_samples=16
for frame in (35,187,351):
    s.frame_set(frame)
    t=time.perf_counter()
    bpy.ops.render.render()
    print('BENCH_720',frame,round(time.perf_counter()-t,2),flush=True)
s.render.resolution_x=528
s.render.resolution_y=298
s.eevee.taa_render_samples=10
for i,frame in enumerate(range(1,481,12)):
    s.frame_set(frame)
    s.render.filepath=str(pre/f'{i:03}.png')
    bpy.ops.render.render(write_still=True)
