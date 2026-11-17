# Dual Twist Flagship

Projeto acadêmico de Visual Merchandising da Fatec. A proposta apresenta a Dual Twist, uma tintura capilar fictícia, em uma flagship conceitual L’Oréal Men Expert. A loja reúne a ilha de lançamento, a vitrine Pit Stop, gôndolas por categoria e um ponto de atendimento. O passeio de 20 segundos percorre a entrada, a ilha e a vitrine e encerra com um recuo para a fachada.

## Código

| Arquivo | Função |
| --- | --- |
| `scripts/construir_flagship.py` | Cria a arquitetura, o mobiliário, os materiais, a iluminação e quatro câmeras da V3. Reaproveita os modelos de embalagem do projeto-base. |
| `scripts/animar_flagship.py` | Adiciona a câmera do passeio, as marcações de tempo e a verificação de afastamento da geometria. Também gera imagens de avaliação. |
| `scripts/validar_flagship.py` | Ajusta os mapas de sombras do Eevee e gera os quatro renders de apresentação, um teste de desempenho em HD e quadros de prévia. |
| `scripts/renderizar_video.py` | Salva a cópia de produção e renderiza 480 PNGs numerados. Ao retomar, verifica a resolução e a estrutura de cada PNG antes de pular os quadros concluídos. |
| `scripts/verificar_quadros.py` | Verifica a sequência, a resolução e a presença de quadros pretos. Gera uma prancha para revisar as transições visualmente. |
| `historico/` | Scripts das primeiras versões, incluindo dois recuperados dos textos internos do arquivo Blender original. Os scripts históricos de construção limpam a cena ativa. Use-os somente em uma cópia descartável. |

O repositório contém o código Python. Os arquivos Blender, os PNGs, o vídeo e o briefing ficam com o material local da disciplina. A marca e as referências fornecidas no briefing pertencem aos respectivos titulares. O projeto é um exercício acadêmico.

## Renderizar o passeio existente

Requisitos de produção: Blender 5.2.3 LTS com Eevee e FFmpeg no PATH. Para a verificação dos PNGs, use Python com Pillow e NumPy. Os comandos abaixo usam PowerShell e partem da raiz do repositório.

```powershell
$blender = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
$env:DT_FINAL_ROOT = (Get-Location).Path
& $blender --factory-startup -b -Y '.\Dual_Twist_Flagship_V3.blend' --python-exit-code 1 --python '.\scripts\renderizar_video.py'
```

O script usa o `Dual_Twist_Flagship_V3.blend` da versão aprovada como entrada. Depois de criada a cópia, use `Dual Twist - Video Final\Dual_Twist_Flagship_V3_Producao.blend` como entrada para retomar. Os PNGs são gravados em `Dual Twist - Video Final/PNGs/`.

```powershell
python .\scripts\verificar_quadros.py
ffmpeg -framerate 24 -start_number 1 -i 'Dual Twist - Video Final\PNGs\Quadro_%04d.png' -frames:v 480 -vf 'scale=out_color_matrix=bt709:out_range=tv' -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -movflags +faststart 'Dual Twist - Video Final\Dual_Twist_Passeio_Virtual_Final.mp4'
```

## Construção e avaliação da V3

Os scripts de construção e avaliação registram o fluxo usado no Blender em Windows. Eles usam `DT_V3_ROOT` como pasta de trabalho. A construção recebe como entrada o `Dual_Twist_Animacao.blend` com a coleção de embalagens e lê a arte da vitrine em `dual-v3-campaign.png` na pasta temporária do Windows. Crie a subpasta `Dual Twist - Flagship V3` antes de executar. Os scripts de animação e avaliação alteram a V3 usada como entrada. Use uma cópia para essas etapas. A construção usa as fontes Arial instaladas e as incorpora ao arquivo final.
