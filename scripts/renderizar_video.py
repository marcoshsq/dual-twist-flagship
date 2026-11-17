
import bpy, os, struct, time
from pathlib import Path
root=Path(os.environ['DT_FINAL_ROOT'])
folder=root/'Dual Twist - Video Final'
seq=folder/'PNGs'
dest=folder/'Dual_Twist_Flagship_V3_Producao.blend'
s=bpy.context.scene
c=s.camera
assert c and c.name.startswith('Passeio cinematográfico')
assert c.animation_data and c.data.animation_data and c.constraints[0].target.animation_data
assert (s.frame_start,s.frame_end,s.render.fps,s.render.fps_base)==(1,480,24,1.0)
assert s.render.engine=='BLENDER_EEVEE'
assert all(i.packed_file for i in bpy.data.images if i.source=='FILE')
positions=[]
for frame in (1,129,208,351,480):
    s.frame_set(frame)
    positions.append(tuple(round(v,3) for v in c.matrix_world.translation))
assert len(set(positions))==5
print('PASSEIO',c.name,positions,flush=True)
s.frame_set(1)
s.render.resolution_x=1280
s.render.resolution_y=720
s.render.resolution_percentage=100
s.eevee.taa_render_samples=16
s.render.image_settings.file_format='PNG'
s.render.image_settings.color_mode='RGB'
s.render.image_settings.color_depth='8'
s.render.image_settings.compression=28
s.render.film_transparent=False
s.render.filepath='//PNGs/Quadro_'
seq.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath)!=dest:
    assert not dest.exists(), dest
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    print('COPIA',dest,flush=True)

def valid(path):
    try:
        with path.open('rb') as file:
            header=file.read(24)
            if len(header)!=24 or header[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack('>II',header[16:24])!=(1280,720):
                return False
            file.seek(-12,2)
            return file.read()==b'\x00\x00\x00\x00IEND\xaeB`\x82'
    except OSError:
        return False
pending=[i for i in range(1,481) if not valid(seq/f'Quadro_{i:04}.png')]
print('RENDER_START',len(pending),time.time(),flush=True)
start=time.perf_counter()
for frame in pending:
    final=seq/f'Quadro_{frame:04}.png'
    partial=seq/'em_render.png'
    s.frame_set(frame)
    s.render.filepath=str(partial)
    bpy.ops.render.render(write_still=True)
    assert valid(partial), partial
    os.replace(partial,final)
    print('FRAME_OK',frame,round(time.perf_counter()-start,2),flush=True)
assert all(valid(seq/f'Quadro_{frame:04}.png') for frame in range(1,481))
print('RENDER_DONE',round(time.perf_counter()-start,2),time.time(),flush=True)
