
import bpy, math, os
from pathlib import Path
from mathutils import Vector

root=Path(os.environ['DT_V3_ROOT'])
out=root/'Dual Twist - Flagship V3'
original=bpy.context.scene
assets=bpy.data.collections['DUAL | 06 Produto oficial']
bottle=next(o for o in assets.objects if o.name.startswith('Ilha|frasco original 1 | mover'))
package=next(o for o in assets.objects if o.name.startswith('Ilha|caixa oficial 1 | mover'))
s=bpy.data.scenes.new('L’Oréal Men Expert | Dual Twist Flagship')
bpy.context.window.scene=s

def collection(name):
    c=bpy.data.collections.new(name)
    s.collection.children.link(c)
    return c
arch=collection('01 · Arquitetura')
fixtures=collection('02 · Mobiliário comercial')
signs=collection('03 · Comunicação e campanha')
products=collection('04 · Produtos')
lighting=collection('05 · Iluminação')
views=collection('06 · Câmeras')
active=arch

def move(o,c):
    for source in list(o.users_collection):
        source.objects.unlink(o)
    c.objects.link(o)

def rgb(h):
    return tuple((v/255/12.92 if v/255<=.04045 else ((v/255+.055)/1.055)**2.4) for v in bytes.fromhex(h))
def mat(name,color,rough=.45,metal=0,noise=0,em=0,anis=0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*rgb(color),1)
    n=m.node_tree.nodes if m.node_tree else None
    if n is None:
        m.use_nodes=True
        n=m.node_tree.nodes
    link=m.node_tree.links
    p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=m.diffuse_color
    p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metal
    if p.inputs.get('Anisotropic IOR Level'):
        p.inputs['Anisotropic IOR Level'].default_value=anis
    if em:
        p.inputs['Emission Color'].default_value=m.diffuse_color
        p.inputs['Emission Strength'].default_value=em
    if noise:
        tex=n.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value=95
        tex.inputs['Detail'].default_value=2
        uv=n.new('ShaderNodeTexCoord')
        link.new(uv.outputs['Object'],tex.inputs['Vector'])
        bump=n.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value=noise
        bump.inputs['Distance'].default_value=.006
        link.new(tex.outputs['Fac'],bump.inputs['Height'])
        link.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m

black=mat('Grafite acetinado | marcenaria','202023',.38,.19,.10)
dark=mat('Laca carvão | perfis','161719',.31,.36)
cement=mat('Estuque mineral quente','414144',.78,0,.23)
silver=mat('Alumínio anodizado escovado','b5aaa0',.28,.78,.09,anis=.5)
stone=mat('Superfície mineral | cinza quente','888581',.48,.05,.18)
floor_tiles=[mat('Grés porcelânico '+h,h,.43,.08,.15) for h in ('5d5b57','64615d','62615f','65615c','5d5e60')]
orange=mat('Laranja performance | laca','ee5f14',.32,.24)
light_orange=mat('Sinalização laranja','ff681d',.4,0,0,1.1)
cream=mat('Tipografia marfim','eee9e2',.43,0,0,.32)
led=mat('LED opalino · 3500 K','ffe2bc',.3,0,0,4)
cool_led=mat('LED opalino · 4300 K','fff4e4',.3,0,0,3.6)
rubber=mat('Preto fosco | rodapé','131313',.72)
paper=mat('Grafismo técnico','aaa39a',.52,0,0,.15)
glass=mat('Vidro | reflexos discretos','b8c5ca',.16,.12)
glass.use_nodes=True
n=glass.node_tree.nodes
mix=n.new('ShaderNodeMixShader')
mix.inputs[0].default_value=.09
transparent=n.new('ShaderNodeBsdfTransparent')
glass.node_tree.links.new(transparent.outputs[0],mix.inputs[1])
reflect=n.new('ShaderNodeBsdfGlossy')
reflect.inputs['Color'].default_value=(.57,.65,.73,1)
reflect.inputs['Roughness'].default_value=.105
glass.node_tree.links.new(reflect.outputs[0],mix.inputs[2])
glass.node_tree.links.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
if hasattr(glass,'surface_render_method'):
    glass.surface_render_method='BLENDED'

def mesh_obj(name,verts,faces,m):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    o=bpy.data.objects.new(name,mesh)
    active.objects.link(o)
    mesh.materials.append(m)
    return o

def box(name,loc,dim,m,bevel=.025):
    x,y,z=[v/2 for v in dim]
    verts=[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    faces=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    o=mesh_obj(name,verts,faces,m)
    o.location=loc
    if bevel:
        b=o.modifiers.new('Arestas usinadas','BEVEL')
        b.width=bevel
        b.segments=3
        o.modifiers.new('Normais ponderadas','WEIGHTED_NORMAL')
    return o

def cyl(name,loc,r,h,m,bevel=.006,vertices=48):
    coords=[(r*math.cos(math.tau*i/vertices),r*math.sin(math.tau*i/vertices),z) for z in (-h/2,h/2) for i in range(vertices)]
    faces=[tuple(reversed(range(vertices))),tuple(range(vertices,2*vertices))]
    faces.extend((i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices))
    o=mesh_obj(name,coords,faces,m)
    o.location=loc
    if bevel:
        b=o.modifiers.new('Filete torneado','BEVEL')
        b.width=bevel
        b.segments=3
    for f in list(o.data.polygons)[2:]:
        f.use_smooth=True
    return o

def rounded(name,xy,z0,z1,width,depth,r,material):
    ring=[]
    for cx,cy,ang in [(width/2-r,depth/2-r,0),(-width/2+r,depth/2-r,90),(-width/2+r,-depth/2+r,180),(width/2-r,-depth/2+r,270)]:
        for k in range(9):
            t=math.radians(ang+k*90/8)
            ring.append((cx+r*math.cos(t),cy+r*math.sin(t)))
    count=len(ring)
    verts=[(x+xy[0],y+xy[1],z) for z in [z0,z1] for x,y in ring]
    faces=[tuple(reversed(range(count))),tuple(range(count,2*count))]
    faces.extend((i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count))
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    o=bpy.data.objects.new(name,mesh)
    active.objects.link(o)
    mesh.materials.append(material)
    b=o.modifiers.new('Borda polida','BEVEL')
    b.width=.018
    b.segments=3
    o.modifiers.new('Normais ponderadas','WEIGHTED_NORMAL')
    return o

fonts={}
for name,file in [('bold','arialbd.ttf'),('regular','arial.ttf'),('black','ariblk.ttf')]:
    f=Path(os.environ['WINDIR'])/'Fonts'/file
    if f.exists():
        fonts[name]=bpy.data.fonts.load(str(f))
def typ(name,body,loc,size,material=cream,face='bold',align='CENTER',rot=(math.pi/2,0,0),extrude=.001,space=1):
    dat=bpy.data.curves.new(name,'FONT')
    dat.body=body
    dat.font=fonts.get(face,bpy.data.fonts.get('Bfont'))
    dat.size=size
    dat.space_character=space
    dat.align_x=align
    dat.align_y='CENTER'
    dat.extrude=extrude
    dat.materials.append(material)
    obj=bpy.data.objects.new(name,dat)
    signs.objects.link(obj)
    obj.location=loc
    obj.rotation_euler=rot
    return obj

def plane_front(name,x,y,z,w,h,m):
    me=bpy.data.meshes.new(name)
    me.from_pydata([(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)],[],[(0,1,2,3)])
    uv=me.uv_layers.new()
    for l,uv_value in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]):
        l.uv=uv_value
    o=bpy.data.objects.new(name,me)
    signs.objects.link(o)
    me.materials.append(m)
    return o

# Envelope de 12 × 10 m, modulação de piso e forro parcial.
box('Base arquitetônica',(0,0,-.26),(12.5,10.55,.45),rubber,.05)
for ix in range(10):
    for iy in range(9):
        box('Placa de grés',(1.2*(ix-4.5),1.11*(iy-4),-.032),(1.196,1.106,.056),floor_tiles[(ix*11+iy*7+ix*iy)%5],.002)
for ix in range(10):
    for iy in range(3):
        box('Placa da calçada',(1.75*(ix-4.5),-5.98-1.35*iy,-.061),(1.744,1.344,.078),floor_tiles[(ix+iy*3)%5],.003)
box('Parede de fundo',(0,5.03,1.98),(12.35,.24,4),cement,.035)
box('Parede oeste',(-6.1,.06,1.98),(.23,10.18,4),cement,.035)
box('Parede leste',(6.1,.06,1.98),(.23,10.18,4),cement,.035)
for x in (-5.96,5.96):
    box('Rodapé metálico lateral',(x,.12,.12),(.055,9.72,.22),dark,.008)
box('Forro de fundo',(0,3.97,3.93),(12.18,2.18,.19),dark,.025)
for x in (-4.84,4.84):
    box('Sanca perimetral',(x,.37,3.84),(2.33,7.41,.22),black,.035)
    sign=1 if x<0 else -1
    box('Linha de luz perimetral',(x+sign*1.05,.35,3.715),(.045,7.55,.021),led,.006)
for x in (-3.36,-2.4,-1.44,-.48,.48,1.44,2.4,3.36):
    box('Nervura de alumínio no forro',(x,.12,3.97),(.065,7.55,.105),silver,.018)
for y in (-2.6,.42,2.93):
    box('Trilho técnico',(0,y,3.79),(7.2,.09,.10),dark,.012)
    for x in (-3.2,-1.65,0,1.65,3.2):
        cyl('Spot de trilho',(x,y,3.694),.062,.167,black)
        cyl('Aro spot',(x,y,3.61),.054,.009,silver,.002)
        cyl('Óptica opalina',(x,y,3.603),.044,.008,cool_led,.001)
for x in [-3.2,-1.6,0,1.6,3.2,5.1]:
    box('Módulo acústico painel de fundo',(x,4.867,3.37),(1.5,.08,1.03),black,.012)
for i in range(76):
    x=(i-37.5)*.151
    box('Friso vertical no fundo',(x,4.817,3.32),(.029,.061,1.081),dark,.006)

# Pórtico público, duas vitrines e vão livre de entrada.
box('Marquise grafite',(0,-5.04,3.88),(12.62,1.22,.43),black,.065)
box('Friso dianteiro alumínio',(0,-5.678,3.95),(12.50,.052,.071),silver,.01)
box('Linha inferior laranja',(0,-5.647,3.67),(12.38,.053,.025),orange,.007)
for x,w in [(-3.99,4.44),(4.76,2.93)]:
    box('Viga superior de vitrine',(x,-5.05,3.30),(w,.22,.13),silver,.017)
    box('Soleira de vitrine',(x,-5.05,.074),(w,.35,.146),black,.015)
for x in (-6.18,-1.78,3.30,6.18):
    box('Montante estrutural',(x,-5.06,1.68),(.18,.28,3.37),black,.02)
    box('Inserto metálico no montante',(x,-5.21,1.68),(.039,.025,3.27),silver,.007)
for x in (-4.02,4.78):
    box('Montante fino de vitrine',(x,-5.07,1.68),(.045,.10,3.22),dark,.006)
for x,w in [(-5.09,2.09),(-2.90,2.12),(4.04,1.40),(5.48,1.34)]:
    plane_front('Vidro laminado',x,-5.065,1.68,w,3.08,glass)
for x in (-1.73,3.24):
    box('Luz vertical do portal',(x,-5.22,1.66),(.025,.02,3.16),led,.004)
box('Travessa da entrada',(0.75,-5.04,3.30),(4.91,.26,.13),dark,.018)
box('Tapete técnico de entrada',(.75,-4.74,.009),(3.58,.92,.032),rubber,.018)
for i in range(13):
    box('Friso antiderrapante',(.75,-5.13+i*.063,.027),(3.52,.010,.003),silver,.001)
typ('Logotipo da fachada',"L’ORÉAL PARIS",(-3.66,-5.714,3.817),.36,cream,'regular',space=1.11)
typ('Assinatura fachada','MEN EXPERT',(-.91,-5.714,3.81),.23,cream,'bold',space=1.13)
typ('Nome na fachada','DUAL TWIST',(3.57,-5.714,3.817),.33,light_orange,'black',space=1.10)
typ('Sinal de entrada','ENTRADA',(.75,-5.193,3.30),.095,cream,'bold',space=1.35)

plaster=mat('Revestimento externo | mineral','4e4945',.78,0,.14)
soffit=mat('Forro central | antracite','272727',.68,0,.09)
box('Forro contínuo do showroom',(0,-.43,4.12),(12.36,9.13,.13),soffit,.028)
box('Alvenaria acima do acesso',(0,-4.975,4.56),(12.62,.37,1.02),plaster,.055)
box('Friso superior externo',(0,-5.175,4.51),(12.62,.052,.039),silver,.007)
for x in (-7.85,7.85):
    box('Alvenaria de entorno',(x,-4.92,2.46),(3.08,.37,4.96),plaster,.05)
    box('Junta vertical de fachada',(x-(.95 if x>0 else -.95),-5.115,2.50),(.024,.021,4.80),dark,.004)
for ix in range(10):
    for iy in range(3,10):
        box('Placa de circulação externa',(1.75*(ix-4.5),-5.98-1.35*iy,-.06),(1.744,1.344,.084),floor_tiles[(ix+iy*3)%5],.003)
# Mobiliário com exposição iluminada e três categorias.
active=fixtures
generic=[
    (mat('Preto cosmético','252426',.3,.16),mat('Rótulo cinza','b5b6b4',.45)),
    (mat('Branco mineral','e1ded6',.34),mat('Rótulo carvão','333436',.55)),
    (mat('Azul ardósia','384a57',.31,.12),mat('Rótulo prata','9eb0ba',.41)),
    (mat('Âmbar escuro','473325',.26,.13),mat('Rótulo cobre','9b6c4a',.48)),
]
def stock(name,x,y,z,kind,style,side=False):
    body,label=generic[style]
    turn=math.pi/2 if side else 0
    if kind==0:
        obj=box(name,(x,y,z+.104),(.115,.072,.208),body,.009)
        obj.rotation_euler.z=turn
        dx,dy=(.037,0) if side else (0,-.037)
        o=box('Rótulo | '+name,(x+dx,y+dy,z+.11),(.092,.002,.095),label,0)
        o.rotation_euler.z=turn
    else:
        rad,height=(.051,.177) if kind==1 else (.060,.124)
        cyl(name,(x,y,z+height/2),rad,height,body,.008,24)
        cyl('Tampa | '+name,(x,y,z+height+.021),rad*.89,.043,dark,.005,24)
        cyl('Faixa impressa | '+name,(x,y,z+height*.48),rad+.001,height*.36,label,.001,24)
        if kind==1:
            cyl('Ombro | '+name,(x,y,z+height),rad*.77,.024,silver,.002,24)

for i,(x,title) in enumerate([(-4.35,'LIMPEZA'),(-1.83,'BARBA'),(.68,'CUIDADO')]):
    box('Gabinete de fundo | '+title,(x,4.48,.27),(2.26,.67,.54),dark,.035)
    box('Painel recuado | '+title,(x,4.742,1.76),(2.26,.14,2.43),black,.024)
    for side in (-1,1):
        box('Lateral usinada',(x+side*1.115,4.52,1.72),(.105,.70,2.53),silver,.014)
    box('Cabeçalho de categoria',(x,4.464,2.91),(2.2,.64,.18),dark,.016)
    typ(title,title,(x,4.13,2.91),.136,cream,'bold',space=1.23)
    for j,z in enumerate((.70,1.23,1.76,2.29)):
        box('Bandeja flutuante',(x,4.45,z),(2.11,.57,.079),black,.012)
        box('Borda gôndola',(x,4.158,z),(2.08,.022,.057),silver,.004)
        box('Luz de prateleira',(x,4.18,z-.044),(2.03,.038,.010),led,.002)
        for g,off in enumerate((-.74,0,.71)):
            count=(3,4,2)[(g+i+j)%3]
            for k in range(count):
                stock(title,x+off+(k-(count-1)/2)*.133,4.43+(g%2)*.08,z+.042,(g+j+i)%3,(g+i+j//2)%4)
typ('Cabeçalho comercial','MEN EXPERT  /  CUIDADO MASCULINO',(-1.82,4.773,3.48),.209,cream,'bold',space=1.14)

for y,title in [(1.94,'ROTINA DIÁRIA'),(-.50,'ESTILO & COR')]:
    box('Base gôndola oeste',(-5.54,y,.275),(.66,2.2,.55),dark,.027)
    box('Painel gôndola oeste',(-5.855,y,1.68),(.115,2.21,2.42),black,.027)
    for end in (-1,1):
        box('Perfil lateral gôndola',(-5.53,y+end*1.07,1.61),(.69,.076,2.46),silver,.011)
    box('Cabeçalho oeste',(-5.51,y,2.84),(.68,2.2,.20),dark,.02)
    typ(title,title,(-5.16,y,2.84),.135,cream,'bold',rot=(math.pi/2,0,math.pi/2),space=1.18)
    for j,z in enumerate((.68,1.19,1.72,2.26)):
        box('Prateleira oeste',(-5.53,y,z),(.66,2.05,.078),black,.012)
        box('Borda oeste',(-5.19,y,z),(.024,2.05,.052),silver,.006)
        box('LED linear oeste',(-5.21,y,z-.043),(.036,2.01,.010),led,.002)
        for g,off in enumerate((-.69,0,.68)):
            for k in range(2+(g+j)%3):
                stock(title,-5.43,y+off+(k-1)*.139,z+.04,(g+j)%3,(g+j//2)%4,True)

# Atendimento ao lado da saída, com banco de experimentação no lado leste.
rounded('Atendimento | base recuada',(4.63,3.25),.0,.11,2.25,1.02,.20,rubber)
rounded('Atendimento | gabinete',(4.63,3.25),.11,1.00,2.44,1.14,.23,black)
rounded('Atendimento | tampo mineral',(4.63,3.25),1.00,1.075,2.55,1.22,.25,stone)
box('Inserto atendimento',(4.63,2.674,.58),(1.94,.028,.50),dark,.035)
box('Filete atendimento',(4.63,2.649,.34),(1.94,.023,.018),orange,.004)
typ('Atendimento','ATENDIMENTO',(4.63,2.648,.65),.15,cream,'bold',space=1.19)
for x in (4.22,5.04):
    box('Terminal | base',(x,3.35,1.117),(.29,.24,.044),silver,.018)
    o=box('Terminal | tela',(x,3.39,1.27),(.31,.035,.22),dark,.018)
    o.rotation_euler.x=-.22
box('Fundo de atendimento',(4.68,4.80,1.86),(2.51,.13,2.2),black,.033)
for i in range(20):
    box('Aleta atrás do caixa',(3.51+i*.12,4.70,1.89),(.030,.09,2.11),silver,.006)
box('Prateleira lateral atendimento',(4.69,4.48,1.32),(2.13,.49,.074),stone,.014)
for i in range(6):
    stock('Serviço',4.04+i*.22,4.45,1.36,i%3,i%4)
box('Painel de experimentação',(5.93,.03,1.83),(.095,3.2,2.68),black,.04)
for y in (-.77,.77):
    box('Espelho de experimentação',(5.85,y,2.0),(.054,1.1,1.36),silver,.036)
    for off in (-.53,.53):
        box('Luz vertical espelho',(5.81,y+off,2),(.023,.018,1.26),led,.004)
box('Bancada de experimentação',(5.59,0,.96),(.76,3.10,.12),stone,.034)
for y in (-.8,.8):
    cyl('Banco | base',(4.94,y,.036),.18,.052,silver)
    cyl('Banco | coluna',(4.94,y,.30),.045,.57,silver)
    cyl('Banco | assento',(4.94,y,.603),.21,.105,black,.02)
typ('Experimentação','EXPERIMENTE',(5.87,0,2.98),.152,cream,'bold',rot=(math.pi/2,0,-math.pi/2),space=1.15)

# Ilha: pedestal iluminado, plataforma com testeiras e exposição hero central.
rounded('Ilha | rodapé recuado',(0,.44),.02,.16,3.58,1.51,.40,rubber)
rounded('Ilha | corpo grafite',(0,.44),.16,.86,3.84,1.70,.45,black)
rounded('Ilha | junta de alumínio',(0,.44),.86,.895,3.86,1.74,.46,silver)
rounded('Ilha | tampo mineral',(0,.44),.895,.993,3.86,1.74,.46,stone)
for i in range(39):
    x=(i-19)*.076
    box('Ilha | canelura frontal',(x,-.424,.393),(.026,.029,.354),dark,.006)
box('Ilha | faixa frontal',(0,-.448,.66),(3.08,.048,.22),dark,.042)
box('Ilha | luz de contorno',(0,-.479,.544),(2.94,.015,.015),light_orange,.004)
typ('Marca da ilha','DUAL TWIST',(0,-.475,.671),.157,cream,'black',space=1.24)
for x in (-1.26,1.25):
    rounded('Ilha | bandeja',(x,.22),.995,1.061,.90,.70,.13,black)
    box('Ilha | linha de alumínio',(x,-.138,1.042),(.70,.015,.023),silver,.003)
    typ('Ilha | identificação lateral','DUAL TWIST',(x,-.148,1.023),.045,cream,'bold')
rounded('Ilha | pedestal inferior',(0,.30),.995,1.107,1.04,.83,.24,dark)
rounded('Ilha | anel luminoso',(0,.30),1.107,1.128,.92,.72,.22,light_orange)
rounded('Ilha | mesa de produto',(0,.30),1.128,1.26,.89,.69,.20,black)
typ('Ilha | etiqueta hero','LANÇAMENTO',(0,-.054,1.174),.063,cream,'bold',space=1.22)
box('Ilha | plinto de comunicação',(0,1.055,1.105),(2.72,.28,.21),dark,.032)
box('Ilha | placa de destaque',(0,1.145,1.54),(2.84,.105,.95),black,.058)
box('Ilha | moldura inferior',(0,1.08,1.099),(2.63,.019,.023),orange,.005)
typ('Ilha | assinatura','L’ORÉAL MEN EXPERT',(0,1.083,1.85),.102,cream,'bold',space=1.17)
typ('Ilha | mensagem','DUAL TWIST',(0,1.083,1.54),.278,cream,'black',space=1.04)
typ('Ilha | mensagem técnica','TINTURA CAPILAR COM MINOXIDIL',(0,1.081,1.258),.064,light_orange,'bold',space=1.14)

# Vitrine: painel com a foto do briefing e suportes automotivos reinterpretados.
rounded('Vitrine | plataforma',(-3.97,-3.52),.01,.26,3.84,2.30,.28,dark)
rounded('Vitrine | friso refletivo',(-3.97,-3.52),.26,.293,3.78,2.24,.27,silver)
rounded('Vitrine | deck',(-3.97,-3.52),.293,.368,3.80,2.25,.28,stone)
box('Vitrine | moldura da campanha',(-4.60,-2.77,1.92),(1.91,.21,2.91),dark,.057)
box('Vitrine | perfil esquerdo',(-5.58,-2.875,1.93),(.037,.055,2.84),orange,.009)
box('Vitrine | perfil direito',(-3.63,-2.877,1.93),(.032,.055,2.84),silver,.007)
campaign=mat('Campanha Pit Stop | arte e foto','ffffff',.55)
n=campaign.node_tree.nodes
tex=n.new('ShaderNodeTexImage')
tex.image=bpy.data.images.load(str(Path(os.environ['TEMP'])/'dual-v3-campaign.png'))
tex.image.pack()
tex.image.filepath='//Dual Twist - Flagship V3/pit-stop.png'
p=n.get('Principled BSDF')
campaign.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
campaign.node_tree.links.new(tex.outputs['Color'],p.inputs['Emission Color'])
p.inputs['Emission Strength'].default_value=.52
plane_front('Painel da campanha Pit Stop',-4.60,-2.897,1.92,1.77,2.68,campaign)
rounded('Vitrine | pedestal grafite',(-3.12,-3.74),.369,.94,1.27,1.12,.35,black)
rounded('Vitrine | placa de alumínio',(-3.12,-3.74),.94,.987,1.30,1.15,.36,silver)
rounded('Vitrine | topo laranja',(-3.12,-3.74),.987,1.03,1.21,1.07,.33,orange)
box('Vitrine | linha acesa',(-3.12,-4.305,.533),(.97,.02,.025),light_orange,.004)
typ('Vitrine | testeira','PIT STOP DO VISUAL',(-3.12,-4.315,.655),.085,cream,'bold',space=1.04)
for i in range(6):
    ob=box('Vitrine | friso aerodinâmico',(-2.39+i*.045,-2.73,1.29+i*.25),(.92,.086,.044),silver,.011)
    ob.rotation_euler.y=-.19
for i in range(4):
    ob=box('Vitrine | marcação técnica',(-4.82+i*.23,-4.31,.37),(.13,.13,.009),orange,.002)
    ob.rotation_euler.z=-.53

# Seleção e instanciação das embalagens que já foram verificadas com o briefing.
def prototype(source,label):
    proto=bpy.data.collections.new(label)
    anchor=source.copy()
    proto.objects.link(anchor)
    anchor.location=(0,0,0)
    for item in source.children:
        child=item.copy()
        proto.objects.link(child)
        child.parent=anchor
    return proto
bottle_proto=prototype(bottle,'Produto original | frasco')
box_proto=prototype(package,'Produto original | cartucho')
def placed(c,label,position,scale=1,angle=0):
    o=bpy.data.objects.new(label,None)
    products.objects.link(o)
    o.instance_type='COLLECTION'
    o.instance_collection=c
    o.location=position
    o.scale=(scale,)*3
    o.rotation_euler.z=math.radians(angle)
for x in (-1.26,1.25):
    for i in range(3):
        placed(box_proto,'Cartucho na ilha',(x+(i-1)*.196,.29,1.063),1.08,-8 if x<0 else 9)
    placed(bottle_proto,'Frasco para experimentação',(x,.043,1.063),1.02)
placed(bottle_proto,'Frasco protagonista | ilha',(0,.23,1.263),1.9,-8)
placed(box_proto,'Cartucho protagonista | ilha',(.294,.388,1.263),1.6,12)
placed(bottle_proto,'Frasco protagonista | vitrine',(-3.27,-3.797,1.034),2.32,-4)
placed(box_proto,'Cartucho | vitrine',(-2.81,-3.649,1.034),1.94,16)
for x in (-5.0,-4.77,-4.53):
    placed(box_proto,'Cartucho na plataforma',(x,-4.0,.372),1.22,12)

# Iluminação real mais emissores de luminária.
def area(name,pos,aim,power,colour,size,sy=None, spread=180):
    d=bpy.data.lights.new(name,'AREA')
    d.energy=power
    d.color=colour
    d.size=size
    d.spread=math.radians(spread)
    if sy:
        d.shape='RECTANGLE'
        d.size_y=sy
    o=bpy.data.objects.new(name,d)
    lighting.objects.link(o)
    o.location=pos
    o.rotation_euler=(Vector(aim)-o.location).to_track_quat('-Z','Y').to_euler()
for x in (-3.33,0,3.33):
    for y in (-1.8,2.24):
        area('Luz geral neutra',(x,y,3.57),(x,y+.15,.15),240,(1,.95,.88),2.30,1.25,130)
for x in (-4.35,-1.83,.68):
    area('Banho quente para gôndola',(x,3.53,3.26),(x,4.55,1.35),104,(1,.80,.62),2.12,.36,108)
for y in (-.50,1.94):
    area('Banho quente lateral',(-4.54,y,3.42),(-5.50,y,1.31),110,(1,.83,.67),2.03,.52,113)
area('Ilha | luz principal',(-1.20,-1.59,2.98),(0,.32,1.35),168,(1,.9,.78),1.65,1.03,105)
area('Ilha | recorte da embalagem',(1.28,.88,2.85),(0,.28,1.32),136,(1,.59,.29),.94,1.46,105)
area('Vitrine | refletor',(-3.45,-4.34,3.06),(-3.2,-3.74,1.24),162,(1,.83,.62),1.45,.67,100)
area('Vitrine | luz de recorte',(-2.52,-3.08,2.66),(-3.37,-3.79,1.25),84,(1,.68,.42),.7,1.1,105)
area('Fachada | softbox frontal',(-2,-8.41,5.20),(0,-4.96,2.21),1060,(.94,.96,1),7.1,3.5,130)
area('Fachada | preenchimento lateral',(5.8,-6.95,4.46),(2.5,-4.35,1.63),470,(1,.83,.65),4.5,3.5)
area('Atendimento | banho de fundo',(4.2,3.37,3.48),(4.67,4.83,1.99),98,(1,.82,.66),1.88,.75,107)
area('Espelho | luz de área',(4.36,.13,2.55),(5.87,0,1.44),102,(1,.93,.81),2.3,.55,120)

def camera(name,pos,aim,lens,shift=0):
    d=bpy.data.cameras.new(name)
    d.lens=lens
    d.clip_start=.045
    d.clip_end=170
    d.shift_y=shift
    o=bpy.data.objects.new(name,d)
    views.objects.link(o)
    o.location=pos
    o.rotation_euler=(Vector(aim)-o.location).to_track_quat('-Z','Y').to_euler()
    return o
shots=[
 ('01_Visao_Geral',(.84,-4.67,2.61),(.02,2.0,1.57),20,0),
 ('02_Entrada_Fachada',(2.40,-18.22,2.62),(.04,-4.85,2.18),31,0),
 ('03_Ilha_Dual_Twist',(2.6,-2.66,1.77),(-.27,.38,1.36),38,0),
 ('04_Vitrine_Pit_Stop',(-2.60,-6.48,1.89),(-4.22,-3.42,1.79),27,0),
]
cams=[camera(*row) for row in shots]
s.camera=cams[0]
s.world=bpy.data.worlds.new('Ambiente grafite')
s.world.use_nodes=True
bg=s.world.node_tree.nodes.get('Background')
bg.inputs['Color'].default_value=(.085,.093,.110,1)
bg.inputs['Strength'].default_value=.47
s.render.engine='BLENDER_EEVEE'
s.eevee.taa_render_samples=48
s.view_settings.view_transform='AgX'
s.view_settings.look='AgX - Medium High Contrast'
s.view_settings.exposure=.28
s.render.resolution_x=1920
s.render.resolution_y=1080
s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
s.render.image_settings.color_mode='RGB'
s.render.fps=24
s.frame_start=1
s.frame_end=480
s.render.filepath='//Dual Twist - Flagship V3/'
for screen in bpy.data.screens:
    for area_editor in screen.areas:
        if area_editor.type=='VIEW_3D':
            space=area_editor.spaces.active
            space.region_3d.view_perspective='CAMERA'
            space.overlay.show_overlays=False
bpy.data.scenes.remove(original)
bpy.data.orphans_purge(do_recursive=True)
for f in fonts.values():
    if f.users: f.pack()
bpy.context.preferences.filepaths.save_version=1
bpy.ops.wm.save_as_mainfile(filepath=str(root/'Dual_Twist_Flagship_V3.blend'))
s.render.resolution_percentage=45
s.eevee.taa_render_samples=32
for cam in cams:
    if os.environ.get('DT_ONLY') and not cam.name.startswith(os.environ['DT_ONLY']):
        continue
    s.camera=cam
    s.render.filepath=str(out/(cam.name+'_Validacao.png'))
    bpy.ops.render.render(write_still=True)
