# -*- coding: utf-8 -*-
"""
DUAL TWIST | PIT STOP DO VISUAL - LOJA FINAL
Projeto academico Fatec Sebrae | Blender 5.2

Modo de usar (sem programar):
1) Extrair o ZIP completo, mantendo esta .py junto da pasta assets/.
2) Blender > Scripting > Open > 01_CRIAR_LOJA_FINAL.py > Run Script (Alt+P).
3) O script cria a loja, quatro cameras, animacao e um .blend em saida/.
4) Depois rode 02_GERAR_RENDERS.py, 03_TESTE_VIDEO.py e 04_VIDEO_FINAL.py.

SEGURANCA: apaga os objetos SOMENTE da cena atual e salva em NOVO arquivo.
Nao sobrescreve Dual_Twist_Loja.blend (V1), mas salve-a antes.

Produto: caixa + frasco reconstruidos de modo aproximado usando recortes REAIS
fotograficos da imagem do briefing, nao um novo design de embalagem.
Sem alegacoes de eficacia de minoxidil ou biodegradabilidade comprovada.
"""
import bpy
import math
from mathutils import Vector
from pathlib import Path

NOME_ARQUIVO = '01_CRIAR_LOJA_FINAL.py'

# --------------------------------------------------------------
# 0 - LOCALIZACAO SEGURA DE ARQUIVOS
# --------------------------------------------------------------
def achar_pasta_projeto():
    testes = []
    try:
        testes.append(Path(__file__).resolve().parent)
    except Exception:
        pass
    for txt in bpy.data.texts:
        if txt.name == NOME_ARQUIVO or txt.name.startswith('01_CRIAR_LOJA_FINAL'):
            try:
                if txt.filepath:
                    testes.append(Path(bpy.path.abspath(txt.filepath)).resolve().parent)
            except Exception:
                pass
    if bpy.data.filepath:
        testes.append(Path(bpy.data.filepath).resolve().parent)
    testes.append(Path.cwd())
    for pasta in testes:
        if (pasta / 'assets' / 'caixa_frente.png').is_file() and (pasta / 'assets' / 'frasco_rotulo.png').is_file():
            return pasta
    raise FileNotFoundError(
        '\nDUAL TWIST: nao encontrei as texturas. Extraia TODO o ZIP, '
        'mantenha a pasta assets/ ao lado de 01_CRIAR_LOJA_FINAL.py '
        'e abra o script pelo botao Open do Blender.'
    )

ROOT = achar_pasta_projeto()  # verificar ANTES de apagar a cena
ASSETS = ROOT / 'assets'
SAIDA = ROOT / 'saida'
SAIDA.mkdir(parents=True, exist_ok=True)
ARQUIVO_BLEND = SAIDA / 'Dual_Twist_Loja_Final.blend'
numero_versao = 2
while ARQUIVO_BLEND.exists():
    # Cada nova execucao salva outra copia, sem sobrescrever seus projetos.
    ARQUIVO_BLEND = SAIDA / f'Dual_Twist_Loja_Final_v{numero_versao}.blend'
    numero_versao += 1

# --------------------------------------------------------------
# 1 - NOVA CENA / COLECOES
# --------------------------------------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
# limpar colecoes de uma execucao anterior, se existirem
for old in list(bpy.data.collections):
    if old.name.startswith('DUAL |'):
        try:
            bpy.data.collections.remove(old)
        except Exception:
            pass

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene.render.engine = 'BLENDER_EEVEE'  # Blender 5.0+, confirmado na documentacao
scene.eevee.taa_render_samples = 64
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.media_type = 'IMAGE'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = False
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 480  # 20 s a 24 fps

try:
    scene.view_settings.view_transform = 'AgX'
except Exception:
    pass


def grupo(nome):
    col = bpy.data.collections.new('DUAL | ' + nome)
    scene.collection.children.link(col)
    return col

C_ARQ   = grupo('01 Arquitetura')
C_PISO  = grupo('02 Piso e iluminacao decorativa')
C_MOV   = grupo('03 Gondolas e caixa')
C_ILHA  = grupo('04 Ilha Dual Twist')
C_VIT   = grupo('05 Vitrine Pit Stop')
C_PROD  = grupo('06 Produto oficial')
C_CENA  = grupo('07 Produtos genericos do cenario')
C_TEXT  = grupo('08 Comunicacao visual')
C_LUZ   = grupo('09 Luzes')
C_CAM   = grupo('10 Cameras e animacao')


def mover(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    return obj


def cor_rgba(hexstr):
    rgb = [int(hexstr.strip('#')[i:i+2], 16)/255 for i in (0,2,4)]
    rgb = [c/12.92 if c<0.04045 else ((c+0.055)/1.055)**2.4 for c in rgb]
    return tuple(rgb)+(1,)


def mat_pbr(nome, hexa, metal=0, rug=0.5):
    m=bpy.data.materials.new(nome)
    m.diffuse_color=cor_rgba(hexa)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=cor_rgba(hexa)
    p.inputs['Metallic'].default_value=metal
    p.inputs['Roughness'].default_value=rug
    return m


def mat_emit(nome, hexa, forca=3.0):
    m=bpy.data.materials.new(nome)
    m.diffuse_color=cor_rgba(hexa)
    m.use_nodes=True
    ns=m.node_tree.nodes
    ns.clear()
    out=ns.new('ShaderNodeOutputMaterial')
    e=ns.new('ShaderNodeEmission')
    e.inputs['Color'].default_value=cor_rgba(hexa)
    e.inputs['Strength'].default_value=forca
    m.node_tree.links.new(e.outputs['Emission'],out.inputs['Surface'])
    return m


def mat_imagem(nome, arquivo):
    img=bpy.data.images.load(str(ASSETS / arquivo), check_existing=True)
    img.colorspace_settings.name='sRGB'
    m=bpy.data.materials.new(nome)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Roughness'].default_value=0.67
    t=m.node_tree.nodes.new('ShaderNodeTexImage')
    t.image=img
    t.extension='EXTEND'
    m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
    return m

PRETO   = mat_pbr('01 Preto fosco', '#0F1013',0.08,0.73)
CARVAO  = mat_pbr('02 Grafite acetinado', '#1B1D21',0.2,0.37)
LARANJA = mat_pbr('03 Laranja Dual Twist', '#FF6B00',0.05,0.4)
CREME   = mat_pbr('04 Branco quente', '#EEEAE3',0.0,0.8)
CIMENTO = mat_pbr('05 Porcelanato cinza', '#BDBAB4',0.04,0.54)
JUNTA   = mat_pbr('06 Rejunte', '#84827E',0.02,0.8)
METAL   = mat_pbr('07 Metal escovado', '#5D6064',0.7,0.25)
VIDRO   = mat_pbr('08 Vidro ambar / detalhe', '#2A1914',0.18,0.1)
BORRACHA= mat_pbr('09 Borracha pneu', '#08090A',0.0,0.94)
LED     = mat_emit('10 LED laranja', '#FF6B00',4.0)
LED_W   = mat_emit('11 LED branco quente', '#FCEAD1',2.5)
PAPEL_F = mat_imagem('12 Original | Caixa frente', 'caixa_frente.png')
PAPEL_L = mat_imagem('13 Original | Caixa lateral', 'caixa_lateral.png')
ROTULO  = mat_imagem('14 Original | Rotulo frasco', 'frasco_rotulo.png')
PAINEL  = mat_imagem('15 Pit Stop | Painel campanha', 'painel_pitstop.png')
MATS_COSMETICOS=[PRETO,CARVAO,CREME,METAL,LARANJA]

# --------------------------------------------------------------
# 2 - FERRAMENTAS GEOMETRICAS
# --------------------------------------------------------------
def caixa(nome, local, dim, mat, col, raio=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=local)
    ob=bpy.context.object
    ob.name=nome
    ob.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(mat)
    mover(ob,col)
    if raio>0:
        b=ob.modifiers.new('Suavizar cantos','BEVEL')
        b.width=min(raio,min(dim)*0.45)
        b.segments=3
        ob.modifiers.new('Normais','WEIGHTED_NORMAL')
    return ob


def cil(nome, local, raio, altura, mat, col, v=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v,radius=raio,depth=altura,location=local)
    ob=bpy.context.object
    ob.name=nome
    ob.data.materials.append(mat)
    mover(ob,col)
    return ob


def toro(nome, local, raio_maior, raio_menor, mat, col, rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=raio_maior,minor_radius=raio_menor,
        major_segments=48,minor_segments=12,
        location=local,rotation=rot)
    ob=bpy.context.object
    ob.name=nome
    ob.data.materials.append(mat)
    mover(ob,col)
    for poly in ob.data.polygons:
        poly.use_smooth=True
    return ob


def letra(nome, mensagem, pos, size, cor, col, rot=(math.pi/2,0,0), align='CENTER'):
    cur=bpy.data.curves.new(nome+'|fonte','FONT')
    cur.body=mensagem
    cur.size=size
    cur.align_x=align
    cur.align_y='CENTER'
    cur.extrude=0.0008
    ob=bpy.data.objects.new(nome,cur)
    col.objects.link(ob)
    ob.location=pos
    ob.rotation_euler=rot
    ob.data.materials.append(cor)
    return ob


def poligono_textura(nome,verts,uvs,mat,col):
    mesh=bpy.data.meshes.new(nome+'Mesh')
    mesh.from_pydata(verts,[],[(0,1,2,3)])
    mesh.update()
    mesh.materials.append(mat)
    uv_layer=mesh.uv_layers.new(name='UV Original')
    for poly in mesh.polygons:
        for loop_id in poly.loop_indices:
            idx=mesh.loops[loop_id].vertex_index
            uv_layer.data[loop_id].uv=uvs[idx]
    ob=bpy.data.objects.new(nome,mesh)
    col.objects.link(ob)
    return ob


def painel_fotografico(nome,centro,largura,altura,mat,depth=0.04,col=None):
    col=col or C_TEXT
    x,y,z=centro
    caixa(nome+'|suporte',(x,y+depth/2,z),(largura,depth,altura),PRETO,col,0.018)
    # Frente -Y, UV foto ocupa plano no eixo X-Z
    verts=[(x-largura/2,y-0.001,z-altura/2),
           (x+largura/2,y-0.001,z-altura/2),
           (x+largura/2,y-0.001,z+altura/2),
           (x-largura/2,y-0.001,z+altura/2)]
    poligono_textura(nome+'|imagem',verts,[(0,0),(1,0),(1,1),(0,1)],mat,col)


def luz_area(nome, pos, power, scale, cor=(1,1,1), alvo=(0,0,1)):
    d=bpy.data.lights.new(nome,'AREA')
    d.energy=power
    d.shape='DISK'
    d.size=scale
    d.color=cor
    ob=bpy.data.objects.new(nome,d)
    C_LUZ.objects.link(ob)
    ob.location=pos
    ob.rotation_euler=(Vector(alvo)-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob


def camera(nome,pos,alvo,ortho=False,scale=15,lente=35):
    cam=bpy.data.cameras.new(nome)
    if ortho:
        cam.type='ORTHO'
        cam.ortho_scale=scale
    else:
        cam.type='PERSP'
        cam.lens=lente
    obj=bpy.data.objects.new(nome,cam)
    C_CAM.objects.link(obj)
    obj.location=pos
    obj.rotation_euler=(Vector(alvo)-obj.location).to_track_quat('-Z','Y').to_euler()
    return obj


def barra_luz(nome,pos,dim,mat=LED):
    return caixa(nome,pos,dim,mat,C_PISO,0.012)

# --------------------------------------------------------------
# 3 - ARQUITETURA / LAYOUT APROVADO 12 x 9 m
# --------------------------------------------------------------
caixa('Piso base', (0,0,-0.15), (12,9,0.3), CIMENTO,C_ARQ)
caixa('Rodape perimetral', (0,0,-0.32),(12.25,9.25,0.1),PRETO,C_ARQ)
# Grade do porcelanato, sem texturas externas
for x in range(-5,6):
    caixa(f'Rejunte vertical {x}',(float(x),0,0.003),(0.012,9,0.003),JUNTA,C_PISO)
for y in range(-4,5):
    caixa(f'Rejunte horizontal {y}',(0,float(y),0.003),(12,0.012,0.003),JUNTA,C_PISO)

caixa('Parede traseira', (0,4.52,1.7),(12.04,0.16,3.4),CARVAO,C_ARQ)
caixa('Parede esquerda', (-6.03,0,1.7),(0.16,9.05,3.4),CARVAO,C_ARQ)
# A direita existe apenas um rodape: perspectiva aberta para a professora.
caixa('Parede direita rebaixada', (6.02,0,0.24),(0.16,9,0.48),CARVAO,C_ARQ)
# Frente possui fachada envidracada sugerida por pilares e vigas, sem vidro obstruindo render
for x in (-5.95,-1.9,1.15,5.95):
    caixa(f'Pilar fachada {x}',(x,-4.51,1.5),(0.10,0.10,3.0),METAL,C_ARQ)
caixa('Friso superior fachada', (0,-4.51,3.03),(12,0.12,0.12),PRETO,C_ARQ)
caixa('Soleira entrada',(-0.4,-4.45,0.035),(3.06,0.26,0.07),LARANJA,C_ARQ)
# Faixas superiores e linhas de LED no fundo
barra_luz('LED topo esquerdo',(-5.8,-0.1,3.22),(0.04,8.8,0.055),LED_W)
barra_luz('LED topo traseiro',(-0.4,4.35,3.22),(10.8,0.05,0.055),LED_W)
letra('Entrada | sinalizacao', 'ENTRADA',(-0.45,-4.03,0.020),0.26,PRETO,C_TEXT,rot=(0,0,0))

# --------------------------------------------------------------
# 4 - GONDOLAS E COSMETICOS GENERICOS (NAO SAO DUAL TWIST)
# --------------------------------------------------------------
def generico(nome, pos, tipo=0, h=0.25):
    mat=MATS_COSMETICOS[tipo%len(MATS_COSMETICOS)]
    cil(nome+' | corpo', (pos[0],pos[1],pos[2]+h/2), 0.060,h,mat,C_CENA,14)
    cil(nome+' | tampa', (pos[0],pos[1],pos[2]+h+0.018),0.064,0.035,PRETO,C_CENA,14)


def gondola_fundo(nome, x, y, largura, altura=2.62):
    caixa(nome+'|costas',(x,y,altura/2),(largura,0.35,altura),PRETO,C_MOV)
    caixa(nome+'|moldura topo',(x,y-0.26,altura-0.10),(largura,0.075,0.20),CARVAO,C_MOV)
    for n,hh in enumerate([0.34,0.91,1.48,2.05]):
        caixa(f'{nome}|prateleira {n}',(x,y-0.32,hh),(largura,0.62,0.07),METAL,C_MOV,0.02)
        barra_luz(f'{nome}|LED {n}',(x,y-0.648,hh-0.045),(largura-0.14,0.02,0.018),LED_W)
        for j in range(int((largura-0.33)/0.23)):
            px=x-largura/2+0.22+j*0.23
            generico(f'{nome}|cenario {n}-{j}',(px,y-0.34,hh+0.05),(j+n)%len(MATS_COSMETICOS),0.20+0.03*((j+n)%3))
    letra(nome+'|letreiro','CUIDADO MASCULINO',(x,y-0.19,altura+0.25),0.25,CREME,C_TEXT)


def gondola_esquerda(nome,x,y,comprimento,altura=2.70):
    caixa(nome+'|costas',(x,y,altura/2),(0.35,comprimento,altura),PRETO,C_MOV)
    for n,hh in enumerate([0.34,0.91,1.48,2.05]):
        caixa(nome+f'|prateleira{n}',(x+0.32,y,hh),(0.55,comprimento,0.065),METAL,C_MOV,0.02)
        barra_luz(nome+f'|led {n}',(x+0.60,y,hh-0.043),(0.018,comprimento-0.15,0.014),LED_W)
        for j in range(int((comprimento-0.2)/0.23)):
            py=y-comprimento/2+0.22+j*0.23
            generico(f'{nome}|cenario {n}-{j}',(x+0.32,py,hh+0.04), (2*j+n)%len(MATS_COSMETICOS),0.20+0.02*(j%4))

# Mantem exata setorizacao da planta da V1
gondola_esquerda('Gondola esquerda',-5.52,0.80,4.75)
gondola_fundo('Gondola de fundo',-0.65,4.00,4.7)

# Caixa com frente orientada ao corredor principal
caixa('Caixa | corpo',(4.45,3.31,0.56),(2.43,1.18,1.12),PRETO,C_MOV,0.07)
caixa('Caixa | painel frontal',(4.45,2.71,0.64),(2.19,0.045,0.55),CARVAO,C_MOV)
caixa('Caixa | tampo',(4.45,3.31,1.14),(2.55,1.29,0.08),METAL,C_MOV,0.05)
caixa('Caixa | detalhe LED',(4.45,2.67,0.31),(2.27,0.026,0.025),LED,C_MOV)
letra('CAIXA | identificacao','CAIXA',(4.45,2.676,0.75),0.28,CREME,C_TEXT)
caixa('Caixa | base monitor',(4.55,3.60,1.24),(0.09,0.12,0.16),METAL,C_MOV)
caixa('Caixa | monitor',(4.55,3.60,1.48),(0.65,0.08,0.42),PRETO,C_MOV,0.04)

# --------------------------------------------------------------
# 5 - PRODUTO OFICIAL: CARTON + FRASCO EM ESCALA
# --------------------------------------------------------------
def caixa_dualtwist(nome, x, y, base, scale=1.0, giro=0):
    """Cartucho com textura fotografica original, dimensoes aprox 14x7x21 cm."""
    w,d,h=0.143*scale,0.076*scale,0.214*scale
    # Controlar geometria inteira via parent vazio, se usuario quiser mover
    parent=bpy.data.objects.new(nome+' | mover conjunto',None)
    C_PROD.objects.link(parent)
    parent.location=(x,y,base)
    parent.rotation_euler[2]=giro
    shell=caixa(nome+' | embalagem', (0,0,h/2),(w,d,h),PRETO,C_PROD,0.0015)
    shell.parent=parent
    # Imagem inteira com a frente da caixa do briefing
    front=poligono_textura(nome+' | FRENTE ORIGINAL',
        [(-w/2,-d/2-0.001,0), (w/2,-d/2-0.001,0),
         (w/2,-d/2-0.001,h),(-w/2,-d/2-0.001,h)],
        [(0,0),(1,0),(1,1),(0,1)],PAPEL_F,C_PROD)
    front.parent=parent
    # Lateral esquerda, imagem lateral tambem do briefing
    side=poligono_textura(nome+' | LATERAL ORIGINAL',
        [(-w/2-0.001,-d/2,0),(-w/2-0.001,d/2,0),
         (-w/2-0.001,d/2,h),(-w/2-0.001,-d/2,h)],
        [(1,0),(0,0),(0,1),(1,1)],PAPEL_L,C_PROD)
    side.parent=parent
    return parent


def frasco_dualtwist(nome,x,y,base,scale=1.0,giro=0):
    """Frasco aproximado com o aplicador LARANJA DE PINOS do original.
    Nenhum pente preto e nenhuma troca de identidade.
    Altura total ~24cm antes do fator de escala (aproximacao academica).
    """
    r=0.052*scale
    parent=bpy.data.objects.new(nome+' | mover conjunto',None)
    C_PROD.objects.link(parent)
    parent.location=(x,y,base)
    parent.rotation_euler[2]=giro
    def ad(ob):
        ob.parent=parent
        return ob
    ad(cil(nome+'|frasco ambar',(0,0,0.058*scale),r,0.116*scale,VIDRO,C_PROD))
    ad(cil(nome+'|base escura',(0,0,0.013*scale),r*0.98,0.025*scale,PRETO,C_PROD))
    ad(cil(nome+'|rotulo laranja base',(0,0,0.064*scale),r+0.0004*scale,0.076*scale,LARANJA,C_PROD,44))
    # UV fotografia real do rotulo original sobre a metade frontal do frasco
    segmentos=32
    ang_inicio=-math.pi/2-1.13
    ang_fim=-math.pi/2+1.13
    zin,zout=0.025*scale,0.103*scale
    verts=[]
    faces=[]
    for i in range(segmentos+1):
        phi=ang_inicio+(ang_fim-ang_inicio)*i/segmentos
        verts.append(((r+0.0015*scale)*math.cos(phi),(r+0.0015*scale)*math.sin(phi),zin))
        verts.append(((r+0.0015*scale)*math.cos(phi),(r+0.0015*scale)*math.sin(phi),zout))
    for i in range(segmentos):
        a=2*i
        faces.append((a,a+2,a+3,a+1))
    mesh=bpy.data.meshes.new(nome+' | papel UV')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    mesh.materials.append(ROTULO)
    uv=mesh.uv_layers.new(name='Foto rotulo original')
    for i,poly in enumerate(mesh.polygons):
        u0=i/segmentos
        u1=(i+1)/segmentos
        for li,coord in zip(poly.loop_indices,[(u0,0),(u1,0),(u1,1),(u0,1)]):
            uv.data[li].uv=coord
    ob=bpy.data.objects.new(nome+' | ROTULO OFICIAL',mesh)
    C_PROD.objects.link(ob)
    ob.parent=parent
    # Aneis/colar preto listrado + detalhe metalico
    ad(cil(nome+'|anel transparente',(0,0,0.124*scale),r*0.92,0.018*scale,METAL,C_PROD))
    ad(cil(nome+'|tampa preta',(0,0,0.150*scale),r*1.055,0.044*scale,PRETO,C_PROD,48))
    for i in range(20):
        a=i*2*math.pi/20
        px=(r*1.065)*math.cos(a)
        py=(r*1.065)*math.sin(a)
        detail=caixa(nome+f'|estria preta {i}',(px,py,0.152*scale),
             (0.006*scale,0.008*scale,0.033*scale),CARVAO,C_PROD,0.001)
        detail.rotation_euler[2]=a
        ad(detail)
    ad(cil(nome+'|base aplicador laranja',(0,0,0.179*scale),r*0.94,0.029*scale,LARANJA,C_PROD,40))
    # Pinos verticais laranja integrados na tampa, conforme briefing.
    # Laranja dos pinos, nao adicionar pente preto.
    for i in range(9):
        for j in range(5):
            xx=(-0.036 + i*0.009)*scale
            yy=(-0.025 + j*0.012)*scale
            if (xx/scale)**2+(yy/scale)**2 <= 0.043**2:
                pin=caixa(nome+f'|pino laranja {i}_{j}',
                    (xx,yy,0.204*scale),(0.006*scale,0.006*scale,0.040*scale),
                    LARANJA,C_PROD,0.0012)
                ad(pin)
    # Pequena alca preta no topo atras dos pinos
    for dx in (-0.018,0.018):
        ad(cil(nome+f'|haste alca {dx}',(dx*scale,0.006*scale,0.229*scale),
           0.004*scale,0.033*scale,PRETO,C_PROD,8))
    ad(caixa(nome+'|topo alca',(0,0.006*scale,0.245*scale),
       (0.040*scale,0.008*scale,0.008*scale),PRETO,C_PROD,0.003))
    return parent

# --------------------------------------------------------------
# 6 - ILHA CENTRAL: PROPORCOES DE VAREJO / PRODUTOS PEQUENOS
# --------------------------------------------------------------
ix,iy=-0.40,-0.16
caixa('Ilha|rodape textura pneu',(ix,iy,0.17),(3.38,2.32,0.34),BORRACHA,C_ILHA,0.11)
# linhas em relevo na frente e laterais, lembram banda de rodagem
for i in range(19):
    xx=ix-1.55+i*0.172
    ob=caixa(f'Ilha|sulco pneu {i}',(xx,iy-1.17,0.168),(0.045,0.016,0.21),CARVAO,C_ILHA,0.006)
    ob.rotation_euler[1]=math.radians(25 if i%2 else -25)
caixa('Ilha|corpo laranja',(ix,iy,0.58),(3.34,2.27,0.71),LARANJA,C_ILHA,0.11)
caixa('Ilha|moldura preta',(ix,iy,0.956),(3.46,2.39,0.105),PRETO,C_ILHA,0.13)
barra_luz('Ilha|led rodape frontal',(ix,iy-1.188,0.34),(3.05,0.020,0.024),LED)
caixa('Ilha|base produtos',(ix,iy-0.18,1.09),(2.70,1.32,0.18),CARVAO,C_ILHA,0.035)
barra_luz('Ilha|led base frontal',(ix,iy-0.855,1.01),(2.58,0.020,0.025),LED)
# cartaz publicitario 2D, sem inventar foto do frasco
painel_fotografico('Ilha|painel Pit Stop',(ix,iy+0.79,2.03),2.73,1.63,PAINEL,0.04,C_ILHA)
# Produto em dimensoes fisicas: caixas cerca de 21cm, frasco ~24cm
for i,xx in enumerate([-0.95,-0.77,-0.59,0.59,0.77,0.95]):
    caixa_dualtwist(f'Ilha|caixa oficial {i+1}',ix+xx,iy-0.18,1.185,1.0,0)
for i,xx in enumerate([-0.28,0.0,0.28]):
    frasco_dualtwist(f'Ilha|frasco original {i+1}',ix+xx,iy-0.52,1.185,0.86,0)
letra('Ilha|logomarca frontal','DUAL TWIST',(ix,iy-1.148,0.66),0.45,PRETO,C_TEXT)

# --------------------------------------------------------------
# 7 - VITRINE: CENOGRAFIA AUTOMOTIVA DO GRUPO
# --------------------------------------------------------------
vx,vy=-4.30,-3.20
caixa('Vitrine|base',(vx,vy,0.20),(2.65,1.62,0.40),PRETO,C_VIT,0.08)
caixa('Vitrine|tampo',(vx,vy,0.43),(2.60,1.58,0.065),LARANJA,C_VIT,0.055)
barra_luz('Vitrine|faixa iluminada',(vx,vy-0.812,0.29),(2.46,0.020,0.03),LED)
# Pneu vertical em dois aros, com miolo escuro e friso
for i,(xx,yy,zz) in enumerate([(-4.96,-3.0,0.97),(-4.66,-2.92,0.91)]):
    toro(f'Vitrine|pneu {i+1}',(xx,yy,zz),0.34,0.15,BORRACHA,C_VIT,(math.pi/2,0,0))
    toro(f'Vitrine|friso metal {i+1}',(xx,yy-0.04,zz),0.23,0.018,METAL,C_VIT,(math.pi/2,0,0))
# pedestal do frasco/cx - compacto e fisico, nao frasco gigante
cil('Vitrine|pedestal de destaque',(-3.66,-3.24,0.66),0.41,0.42,PRETO,C_VIT)
cil('Vitrine|aro laranja',(-3.66,-3.24,0.88),0.416,0.025,LARANJA,C_VIT)
frasco_dualtwist('Vitrine|frasco oficial',-3.67,-3.27,0.90,1.0)
caixa_dualtwist('Vitrine|caixa oficial',-3.20,-3.15,0.46,1.15)
letra('Vitrine|slogan','PIT STOP DO VISUAL',(vx,vy-0.815,0.45),0.165,CREME,C_TEXT)
# Moldura de vitrine (sem vidro opaco que esconda os objetos)
for xx in (-5.74,-2.82):
    caixa(f'Vitrine|barra fachada {xx}',(xx,-4.41,1.18),(0.04,0.04,2.35),METAL,C_VIT)

# --------------------------------------------------------------
# 8 - FLUXO NO PISO: SETAS DE LAYOUT (PAINEL ACADEMICO)
# --------------------------------------------------------------
def seta_fluxo(nome,p1,p2,larg=0.045):
    p1=Vector(p1); p2=Vector(p2)
    d=(p2-p1).normalized()
    mid=(p1+p2)*0.5
    ob=caixa(nome+'|haste',(mid.x,mid.y,0.008),
             ((p2-p1).length-0.18,larg,0.01),LARANJA,C_TEXT)
    ob.rotation_euler.z=math.atan2(d.y,d.x)
    # ponta triangular no chao
    lat=Vector((-d.y,d.x,0))
    tip=Vector((p2.x,p2.y,0.015))
    pback=tip-d*0.24
    verts=[tuple(tip),tuple(pback+lat*0.145),tuple(pback-lat*0.145)]
    me=bpy.data.meshes.new(nome+'|ponta')
    me.from_pydata(verts,[],[(0,1,2)])
    me.materials.append(LARANJA)
    ob2=bpy.data.objects.new(nome+'|seta',me)
    C_TEXT.objects.link(ob2)

seta_fluxo('Fluxo entrada para ilha',(-0.45,-3.96),(-0.45,-1.55))
seta_fluxo('Fluxo ilha para corredor',(1.55,-0.35),(3.27,-0.35))
seta_fluxo('Fluxo corredor para caixa',(4.25,0.22),(4.25,2.20))

# --------------------------------------------------------------
# 9 - LUMINOTECNICA E AMBIENTACAO
# --------------------------------------------------------------
# fonte geral fisica + acentos quentes do merchandising
luz_area('Teto | fill 01',(-3.2,-0.4,5.8),1800,7.0,(1.0,0.93,0.86),(-2.5,0.0,0.8))
luz_area('Teto | fill 02',(3.8,1.5,6.0),1600,7.0,(1.0,0.95,0.89),(2.0,1.2,0.8))
luz_area('Destaque ilha',(0,-1.6,4.5),1100,3.2,(1.0,0.79,0.62),(-0.4,0.0,1.5))
luz_area('Destaque vitrine',(-4.4,-4.0,3.5),650,2.3,(1.0,0.57,0.24),(-4.3,-3.2,0.8))
luz_area('Contorno fundo',(-1.2,3.5,4.6),580,3.0,(1.0,0.80,0.62),(-1.2,3.5,1.5))
if scene.world is None:
    scene.world=bpy.data.worlds.new('Mundo do projeto')
scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get('Background')
if bg:
    bg.inputs['Color'].default_value=(0.22,0.23,0.25,1)
    bg.inputs['Strength'].default_value=0.65

# --------------------------------------------------------------
# 10 - QUATRO CAMERAS DE RENDER + PASSEIO VIRTUAL
# --------------------------------------------------------------
CAM_GERAL=camera('CAM_01_GERAL',(11.7,-13.5,11.5),(0,0,0.8),True,17.8)
CAM_ILHA=camera('CAM_02_ILHA',(4.6,-6.0,3.0),(-0.4,0.05,1.42),False,lente=43)
CAM_VITRINE=camera('CAM_03_VITRINE',(-4.2,-8.6,2.0),(-4.3,-3.2,0.98),False,lente=46)
CAM_PLANTA=camera('CAM_04_PLANTA',(0,-0.1,20),(0,0,0),True,14.3)

# Camera animada sempre olha para um Empty animado -> evita problemas de Euler
cam_data=bpy.data.cameras.new('CAM_05_TOUR_20s')
cam_data.lens=27
CAM_TOUR=bpy.data.objects.new('CAM_05_TOUR_20s',cam_data)
C_CAM.objects.link(CAM_TOUR)
ALVO=bpy.data.objects.new('CAM_05_ALVO_ANIMADO',None)
C_CAM.objects.link(ALVO)
constraint=CAM_TOUR.constraints.new(type='TRACK_TO')
constraint.target=ALVO
constraint.track_axis='TRACK_NEGATIVE_Z'
constraint.up_axis='UP_Y'
# Frente -> ilha -> vitrine -> vista superior da loja
keyframes=[
    (1,   (0.0,-11.7,2.60), (0.0,0.0,1.45)),
    (120, (3.7,-6.9,2.65), (-0.4,0.0,1.52)),
    (240, (1.7,-4.0,2.32), (-0.4,0.15,1.45)),
    (360, (-4.8,-6.7,2.28), (-4.30,-3.20,0.95)),
    (480, (9.6,-10.2,9.3), (0.0,0.0,0.9)),
]
for frame,pos,alvo in keyframes:
    CAM_TOUR.location=pos
    CAM_TOUR.keyframe_insert(data_path='location',frame=frame)
    ALVO.location=alvo
    ALVO.keyframe_insert(data_path='location',frame=frame)
scene.frame_set(1)
scene.camera=CAM_GERAL

# --------------------------------------------------------------
# 11 - FINALIZAR: PACK ASSETS + SALVAR NOVO .BLEND
# --------------------------------------------------------------
# Materiais originais permanecerao mesmo se a pasta mudar.
try:
    bpy.ops.file.pack_all()
    print('Todas as texturas foram incorporadas ao arquivo .blend')
except Exception as e:
    print('Aviso ao incorporar as texturas:',e)

# Mostrar a loja em modo Material no viewport, inclusive cores.
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        try:
            area.spaces.active.shading.type='MATERIAL'
            area.spaces.active.region_3d.view_distance=17.0
        except Exception:
            pass

bpy.ops.object.select_all(action='DESELECT')
scene.render.filepath=str(SAIDA / 'renders' / '01_Geral.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ARQUIVO_BLEND))
print('========================================================')
print('DUAL TWIST FINAL: CENARIO CRIADO')
print('Arquivo salvo em:',ARQUIVO_BLEND)
print('4 cameras prontas + camera animada de 20 segundos.')
print('Frasco e caixa usam imagens do briefing original.')
print('Proximo: abra 02_GERAR_RENDERS.py e clique Run Script.')
print('========================================================')
