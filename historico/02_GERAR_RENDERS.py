# -*- coding: utf-8 -*-
"""DUAL TWIST: 4 imagens para a apresentacao. Execute apos 01_CRIAR_LOJA_FINAL.py.
Gera arquivos PNG em saida/renders/. Nao recria nem apaga o projeto.
"""
import bpy
from pathlib import Path

scene=bpy.context.scene
PASTA=Path(bpy.data.filepath).resolve().parent / 'renders'
PASTA.mkdir(parents=True,exist_ok=True)
render=scene.render
render.engine='BLENDER_EEVEE'  # Blender 5.2
render.resolution_x=1920
render.resolution_y=1080
render.resolution_percentage=100   # altere para 50 se quiser testar primeiro
scene.eevee.taa_render_samples=64
render.image_settings.media_type='IMAGE'
render.image_settings.file_format='PNG'
render.image_settings.color_mode='RGBA'
scene.frame_set(1)

plan=[
    ('CAM_01_GERAL','01_Visao_Geral_Loja.png'),
    ('CAM_02_ILHA','02_Ilha_Dual_Twist.png'),
    ('CAM_03_VITRINE','03_Vitrine_Pit_Stop.png'),
    ('CAM_04_PLANTA','04_Layout_Vista_Superior.png'),
]
for nome_cam,nome_arq in plan:
    cam=bpy.data.objects.get(nome_cam)
    if cam is None:
        raise RuntimeError('Camera ausente: '+nome_cam+'. Execute primeiro 01_CRIAR_LOJA_FINAL.py.')
    scene.camera=cam
    render.filepath=str(PASTA / nome_arq)
    print('RENDER DUAL TWIST:',nome_cam,'->',nome_arq)
    bpy.ops.render.render(write_still=True)
scene.camera=bpy.data.objects['CAM_01_GERAL']
print('CONCLUIDO! Quatro imagens em:',PASTA)
