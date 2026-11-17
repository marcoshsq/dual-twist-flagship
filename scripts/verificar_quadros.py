import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageStat
import numpy as np

folder=Path.cwd()/'Dual Twist - Video Final'
seq=folder/'PNGs'
files=sorted(seq.glob('Quadro_*.png'))
expected=[f'Quadro_{i:04}.png' for i in range(1,481)]
assert [f.name for f in files]==expected
changes=[]
means=[]
dark_frames=[]
previous=None
for i,f in enumerate(files,1):
    with Image.open(f) as im:
        im.verify()
    with Image.open(f) as im:
        assert im.size==(1280,720) and im.mode=='RGB', (f,im.size,im.mode)
        gray=np.asarray(im.convert('L').resize((160,90),Image.Resampling.BILINEAR),dtype=np.float32)
        means.append(float(gray.mean()))
        if (gray<17).mean()>.98:
            dark_frames.append(i)
        if previous is not None:
            changes.append((float(np.abs(gray-previous).mean()),i))
        previous=gray
assert not dark_frames, dark_frames
print('PNG',len(files),'min_luma',round(min(means),2),'largest_frame_deltas',sorted(changes,reverse=True)[:12])
sample=[1,39,85,129,172,208,245,279,312,351,396,431,480]
sample += [frame for _,frame in sorted(changes,reverse=True)[:3]]
sample=sorted(set(sample))
cols=4
c=Image.new('RGB',(1280,math.ceil(len(sample)/cols)*204),'#212225')
d=ImageDraw.Draw(c)
for index,frame in enumerate(sample):
    x=index%cols*320
    y=index//cols*204
    with Image.open(seq/f'Quadro_{frame:04}.png') as im:
        c.paste(im.resize((320,180),Image.Resampling.LANCZOS),(x,y))
    d.text((x+7,y+183),f'{frame:04}  /  {(frame-1)/24:.2f}s',fill='white')
c.save(Path(os.environ['TEMP'])/'dual-v3-video-final-qa.png')
