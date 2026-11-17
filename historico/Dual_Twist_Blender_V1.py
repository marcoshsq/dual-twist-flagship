# ============================================================
# DUAL TWIST — LOJA 3D | V1: estrutura e layout
# Blender 5.2 | Script sem dependencias externas
# ============================================================
# ATENCAO: este script APAGA OS OBJETOS DA CENA ATUAL.
# Execute apenas no arquivo de projeto que voce salvou.
# Nao altera arquivos fora do Blender e NAO salva automaticamente.
#
# Referencias do grupo:
# - Planta: entrada na frente; vitrine na frente/esquerda;
#   gondola lateral esquerda e ao fundo; ilha central; caixa ao fundo/direita.
# - Visual: preto, laranja, branco, piso neutro e elementos automotivos.
# - Produto oficial: sera incorporado na V2. Nao inventamos o frasco.
# ============================================================

import bpy
import math
from mathutils import Vector

# ------------------------------------------------------------
# 0. LIMPAR SOMENTE OBJETOS DA CENA ATUAL
# ------------------------------------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ------------------------------------------------------------
# 1. CONFIGURACOES
# ------------------------------------------------------------
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.resolution_percentage = 70
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False

# Colecoes para facilitar a edicao posterior
def colecao(nome):
    c = bpy.data.collections.get(nome)
    if c is None:
        c = bpy.data.collections.new(nome)
        scene.collection.children.link(c)
    return c

ESTRUTURA = colecao('01 | Estrutura da loja')
MOVEIS = colecao('02 | Gondolas e caixa')
ILHA = colecao('03 | Ilha Dual Twist')
VITRINE = colecao('04 | Vitrine Pit Stop')
SINALIZACAO = colecao('05 | Sinalizacao e fluxo')
ILUMINACAO = colecao('06 | Luzes e cameras')

def mover_para_colecao(obj, col):
    for antiga in list(obj.users_collection):
        antiga.objects.unlink(obj)
    col.objects.link(obj)
    return obj

def hex_rgba(c):
    c = c.lstrip('#')
    rgb = [int(c[i:i+2], 16)/255.0 for i in (0,2,4)]
    # Conversao aproximada sRGB -> linear para cores do material
    rgb = [v/12.92 if v <= 0.04045 else ((v+0.055)/1.055)**2.4 for v in rgb]
    return (*rgb, 1.0)

def material(nome, cor, metallic=0.0, roughness=0.55):
    mat = bpy.data.materials.get(nome) or bpy.data.materials.new(nome)
    mat.diffuse_color = hex_rgba(cor)
    mat.use_nodes = True
    principled = mat.node_tree.nodes.get('Principled BSDF')
    if principled:
        principled.inputs['Base Color'].default_value = hex_rgba(cor)
        principled.inputs['Metallic'].default_value = metallic
        principled.inputs['Roughness'].default_value = roughness
    return mat

PRETO = material('Dual Twist | Preto grafite', '#111216', 0.25, 0.44)
PRETO_FOSCO = material('Dual Twist | Preto fosco', '#08090B', 0.0, 0.72)
LARANJA = material('Dual Twist | Laranja', '#FF6B00', 0.12, 0.42)
BRANCO = material('Dual Twist | Branco', '#F5F3EF', 0.0, 0.65)
PISO = material('Dual Twist | Piso cimento claro', '#A8A29B', 0.0, 0.80)
PAREDE = material('Dual Twist | Parede grafite', '#25272B', 0.0, 0.78)
METAL = material('Dual Twist | Metal', '#575A5D', 0.55, 0.33)
PRODUTOS = [
    material('Cenario | Frascos pretos', '#16191C', 0.08, 0.46),
    material('Cenario | Frascos cinza', '#5C6063', 0.0, 0.52),
    material('Cenario | Frascos laranja', '#C94E00', 0.0, 0.54),
    material('Cenario | Frascos claros', '#D5CCC0', 0.0, 0.65),
]

def cubo(nome, pos, escala, mat, col, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o = bpy.context.object
    o.name = nome
    o.dimensions = escala
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    mover_para_colecao(o, col)
    if bevel:
        b = o.modifiers.new('Cantos suavizados', 'BEVEL')
        b.width = bevel
        b.segments = 3
        o.modifiers.new('Normais suavizadas', 'WEIGHTED_NORMAL')
    return o

def cilindro(nome, pos, raio, altura, mat, col, vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=raio, depth=altura, location=pos)
    o = bpy.context.object
    o.name = nome
    o.data.materials.append(mat)
    mover_para_colecao(o, col)
    return o

def texto(nome, conteudo, pos, tamanho, mat, col,
          rotacao=(0,0,0), alinhar='CENTER'):
    fonte = bpy.data.curves.new(nome + ' fonte', 'FONT')
    fonte.body = conteudo
    fonte.size = tamanho
    fonte.align_x = alinhar
    fonte.align_y = 'CENTER'
    fonte.extrude = 0.001
    o = bpy.data.objects.new(nome, fonte)
    col.objects.link(o)
    o.location = pos
    o.rotation_euler = rotacao
    o.data.materials.append(mat)
    return o

def linha(nome, pontos, largura, mat, col):
    cv = bpy.data.curves.new(nome + ' curva', type='CURVE')
    cv.dimensions = '3D'
    cv.bevel_depth = largura
    cv.bevel_resolution = 2
    sp = cv.splines.new('POLY')
    sp.points.add(len(pontos)-1)
    for i,p in enumerate(pontos):
        sp.points[i].co = (*p,1)
    ob = bpy.data.objects.new(nome, cv)
    col.objects.link(ob)
    ob.data.materials.append(mat)
    return ob

def seta_chao(nome, inicio, fim, mat=LARANJA):
    x1,y1 = inicio
    x2,y2 = fim
    z = 0.055
    direcao = Vector((x2-x1, y2-y1))
    direcao.normalize()
    lateral = Vector((-direcao.y, direcao.x))
    # corpo
    fim_corpo = Vector((x2,y2)) - direcao*0.22
    linha(nome+' | corpo', [(x1,y1,z),(fim_corpo.x,fim_corpo.y,z)],0.025,mat,SINALIZACAO)
    # ponta triangular, horizontal no chao
    tip = Vector((x2,y2))
    base = tip - direcao*0.32
    verts = [
        (tip.x,tip.y,z),
        (base.x + lateral.x*0.16,base.y + lateral.y*0.16,z),
        (base.x - lateral.x*0.16,base.y - lateral.y*0.16,z),
    ]
    mesh = bpy.data.meshes.new(nome+' ponta mesh')
    mesh.from_pydata(verts, [], [(0,1,2)])
    mesh.materials.append(mat)
    ob = bpy.data.objects.new(nome+' | ponta',mesh)
    SINALIZACAO.objects.link(ob)

# ------------------------------------------------------------
# 2. LOJA: 12 m de largura x 9 m de profundidade
#    Frente = Y negativo; fundo = Y positivo
# ------------------------------------------------------------
cubo('Piso principal | 12 x 9 m', (0,0,-0.12), (12,9,0.24), PISO, ESTRUTURA)
cubo('Base externa', (0,0,-0.30), (12.4,9.4,0.13), PRETO, ESTRUTURA)
cubo('Parede do fundo', (0,4.51,1.62), (12.0,0.16,3.24), PAREDE, ESTRUTURA)
cubo('Parede esquerda', (-6.02,0,1.62), (0.16,9.0,3.24), PAREDE, ESTRUTURA)
# Paredes baixas no lado direito e na frente: corte esquematico
# para enxergar o interior na vista isometrica.
cubo('Parede direita | corte para visualizacao', (6.02,0,0.26), (0.16,9,0.52), PAREDE, ESTRUTURA)
cubo('Fachada esquerda | mureta vitrine', (-3.95,-4.52,0.20), (4.1,0.14,0.40), PRETO, ESTRUTURA)
cubo('Fachada direita | mureta', (3.55,-4.52,0.20), (4.9,0.14,0.40), PRETO, ESTRUTURA)
# A abertura entre -1.9 e +1.1 no eixo X representa a entrada.
texto('Etiqueta ENTRADA', 'ENTRADA', (-0.4,-4.12,0.025),0.30,PRETO_FOSCO,SINALIZACAO)

# ------------------------------------------------------------
# 3. GONDOLAS (esquerda e fundo) + produtos genericos de cenario
#    ATENCAO: estes itens NAO sao o Dual Twist.
# ------------------------------------------------------------
def gondola(nome, centro, largura, profundidade, orientacao='X'):
    x,y = centro
    cubo(nome+' | fundo', (x,y,1.38), (largura,profundidade,2.76), PRETO, MOVEIS,0.025)
    # Faixas de prateleira projetadas para frente do expositor
    if orientacao == 'X':  # gondola ao fundo
        y_frente = y-profundidade/2-0.08
        for altura in [0.46,1.03,1.60,2.17]:
            cubo(nome+f' | prateleira {altura}',(x,y_frente,altura),
                 (largura,0.28,0.07),METAL,MOVEIS)
            n = int((largura-0.35)/0.27)
            for i in range(n):
                px = x-largura/2+0.24+i*0.27
                cilindro(nome+f' | cenografico {altura:.2f}-{i}',
                         (px,y_frente,altura+0.18),0.085,0.30,
                         PRODUTOS[i%len(PRODUTOS)],MOVEIS,12)
    else:  # gondola lateral esquerda
        x_frente = x+profundidade/2+0.08
        for altura in [0.46,1.03,1.60,2.17]:
            cubo(nome+f' | prateleira {altura}',(x_frente,y,altura),
                 (0.28,largura,0.07),METAL,MOVEIS)
            n = int((largura-0.35)/0.27)
            for i in range(n):
                py = y-largura/2+0.24+i*0.27
                cilindro(nome+f' | cenografico {altura:.2f}-{i}',
                         (x_frente,py,altura+0.18),0.085,0.30,
                         PRODUTOS[i%len(PRODUTOS)],MOVEIS,12)

gondola('Gondola lateral',(-5.52,0.85),4.5,0.54,'Y')
gondola('Gondola do fundo',(-0.55,4.00),4.7,0.54,'X')

texto('Identificacao gondola lateral', 'GONDOLA', (-5.35,0.9,2.85),0.26,LARANJA,SINALIZACAO)
texto('Identificacao gondola fundo', 'GONDOLA', (-0.5,3.97,2.85),0.26,LARANJA,SINALIZACAO)

# Caixa ao fundo, a direita
cubo('Caixa | corpo', (4.28,3.25,0.54), (2.35,1.08,1.08), PRETO, MOVEIS,0.08)
cubo('Caixa | tampo', (4.28,3.25,1.11), (2.47,1.16,0.08), METAL, MOVEIS,0.035)
cubo('Caixa | faixa laranja', (4.28,2.69,0.78), (2.12,0.025,0.14), LARANJA, MOVEIS)
texto('Caixa | identificacao', 'CAIXA', (4.28,2.662,0.70),0.32,BRANCO,SINALIZACAO,
      rotacao=(math.pi/2,0,0))
cubo('Caixa | monitor', (4.65,3.54,1.45), (0.55,0.08,0.52), PRETO_FOSCO, MOVEIS)
cubo('Caixa | suporte monitor', (4.65,3.55,1.19), (0.08,0.08,0.20), METAL, MOVEIS)

# ------------------------------------------------------------
# 4. ILHA CENTRAL DUAL TWIST
# ------------------------------------------------------------
ix,iy = -0.45,-0.15
cubo('Ilha | base preta', (ix,iy,0.17), (3.35,2.25,0.34), PRETO_FOSCO, ILHA,0.10)
cubo('Ilha | corpo laranja', (ix,iy,0.56), (3.32,2.22,0.73), LARANJA, ILHA,0.10)
cubo('Ilha | tampo preto', (ix,iy,0.96), (3.45,2.36,0.11), PRETO, ILHA,0.12)
cubo('Ilha | pedestal de exposicao', (ix,iy-0.15,1.12), (2.65,1.18,0.22), PRETO_FOSCO, ILHA,0.035)
# Backdrop posicionado na parte posterior da ilha
cubo('Ilha | painel de campanha', (ix,iy+0.86,1.93), (2.65,0.09,1.93), PRETO, ILHA,0.07)
cubo('Ilha | detalhe lateral painel', (ix+1.20,iy+0.80,1.93), (0.13,0.04,1.76), LARANJA, ILHA)
texto('Ilha | titulo campanha', 'DUAL TWIST',
      (ix,iy+0.802,2.35),0.33,LARANJA,SINALIZACAO,
      rotacao=(math.pi/2,0,0))
texto('Ilha | texto auxiliar', 'PIT STOP DO VISUAL',
      (ix,iy+0.799,2.04),0.15,BRANCO,SINALIZACAO,
      rotacao=(math.pi/2,0,0))
texto('Ilha | identificacao topo', 'ILHA DUAL TWIST',
      (ix,iy-0.37,1.245),0.18,BRANCO,SINALIZACAO)
# Reservas de posicao para produtos oficiais a inserir na V2
for i,dx in enumerate([-0.7,0.0,0.7],start=1):
    cubo(f'Ilha | suporte para produto oficial {i}',
         (ix+dx,iy-0.25,1.31),(0.48,0.48,0.15),METAL,ILHA,0.04)

# ------------------------------------------------------------
# 5. VITRINE AUTOMOTIVA (frente esquerda)
# ------------------------------------------------------------
vx,vy = -4.2,-3.35
cubo('Vitrine | plataforma', (vx,vy,0.28), (2.65,1.50,0.55), PRETO, VITRINE,0.10)
cubo('Vitrine | superficie laranja', (vx,vy,0.58), (2.52,1.39,0.07), LARANJA, VITRINE,0.04)
cubo('Vitrine | suporte central', (vx+0.30,vy,0.80), (0.72,0.65,0.42), PRETO_FOSCO,VITRINE,0.04)
for i,(dx,dy) in enumerate([(-0.65,0.16),(-0.25,0.33)],start=1):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.38,minor_radius=0.12,
        location=(vx+dx,vy+dy,1.07),
        rotation=(math.pi/2,0,0),
        major_segments=40,minor_segments=12)
    obj=bpy.context.object
    obj.name=f'Vitrine | pneu cenografico {i}'
    obj.data.materials.append(PRETO_FOSCO)
    mover_para_colecao(obj,VITRINE)
texto('Vitrine | etiqueta', 'PIT STOP', (vx,vy-0.35,0.628),0.23,PRETO,SINALIZACAO)

# ------------------------------------------------------------
# 6. FLUXO DO CONSUMIDOR (setas no piso)
# ------------------------------------------------------------
seta_chao('Fluxo | entrada para ilha',(-0.45,-3.88),(-0.45,-1.63))
seta_chao('Fluxo | ilha para caixa',(1.65,-0.45),(3.48,-0.45))
seta_chao('Fluxo | corredor para caixa',(4.25,0.15),(4.25,2.26))

# ------------------------------------------------------------
# 7. ILUMINACAO E CAMERAS
# ------------------------------------------------------------
def area_light(nome, pos, energia, tamanho, cor=(1,1,1)):
    dados=bpy.data.lights.new(nome,type='AREA')
    dados.energy=energia
    dados.shape='DISK'
    dados.size=tamanho
    dados.color=cor
    ob=bpy.data.objects.new(nome,dados)
    ILUMINACAO.objects.link(ob)
    ob.location=pos
    direcao=Vector((0,0,0.7))-ob.location
    ob.rotation_euler=direcao.to_track_quat('-Z','Y').to_euler()
    return ob

area_light('Luz | geral 01',(-3,-2,6),1300,6.0)
area_light('Luz | geral 02',(3,2,6),1150,6.0)
area_light('Luz | laranja vitrine',(-4.2,-3.0,3.8),450,2.5,(1.0,0.48,0.15))
area_light('Luz | ilha',(0,-1.2,5.5),650,3.0,(1.0,0.78,0.56))

def camera(nome,pos,alvo,escala):
    dados=bpy.data.cameras.new(nome)
    dados.type='ORTHO'
    dados.ortho_scale=escala
    ob=bpy.data.objects.new(nome,dados)
    ILUMINACAO.objects.link(ob)
    ob.location=pos
    direcao=Vector(alvo)-ob.location
    ob.rotation_euler=direcao.to_track_quat('-Z','Y').to_euler()
    return ob

cam_perspectiva=camera('CAM_01_Perspectiva',(11,-13,11),(0,0,0.7),16.8)
cam_planta=camera('CAM_02_Planta',(0,0,20),(0,0,0),16.8)
scene.camera=cam_perspectiva

if scene.world is None:
    scene.world=bpy.data.worlds.new('Mundo Dual Twist')
scene.world.use_nodes=True
background=scene.world.node_tree.nodes.get('Background')
if background:
    background.inputs['Color'].default_value=(0.20,0.20,0.20,1.0)
    background.inputs['Strength'].default_value=0.6

# Vista de trabalho: cores dos materiais mesmo no modo solido
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.spaces.active.shading.type='SOLID'
        area.spaces.active.shading.color_type='MATERIAL'
        area.spaces.active.region_3d.view_distance=16

# Selecionar ilha para facilitar a localizacao
bpy.ops.object.select_all(action='DESELECT')
ilha=bpy.data.objects.get('Ilha | corpo laranja')
if ilha:
    ilha.select_set(True)
    bpy.context.view_layer.objects.active=ilha

print('--------------------------------------------')
print('DUAL TWIST V1 CRIADA COM SUCESSO!')
print('Vista 3D: pressione HOME para enquadrar tudo.')
print('Camera: Numpad 0. Render: F12.')
print('Nao se esqueca de salvar: Ctrl + S.')
print('Proxima etapa: V2 com texturas e produto oficial.')
print('--------------------------------------------')
