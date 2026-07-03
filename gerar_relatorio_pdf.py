# -*- coding: utf-8 -*-
"""
Gera o relatório formal em PDF (entregável do item 5 da especificação),
com as seções mínimas exigidas: introdução (contextualização, fundamentação
teórica, objetivos), materiais e métodos, resultados, discussão e conclusão.

As figuras e os números vêm dos resultados reais dos Experimentos 1 e 2
(pastas resultados/experimento1 e resultados/experimento2).

Uso:  python gerar_relatorio_pdf.py
Saída: Relatorio_Trabalho_Pratico_PDI.pdf
"""

import os

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

RAIZ = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(RAIZ, "Relatorio_Trabalho_Pratico_PDI.pdf")
RES = os.path.join(RAIZ, "resultados")

# ---------------------------------------------------------------- fontes
# Arial cobre os glifos gregos (lambda, sigma, psi, gamma, theta) que as
# 14 fontes padrão do PDF não possuem.
FONTES = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
pdfmetrics.registerFont(TTFont("Arial", os.path.join(FONTES, "arial.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Bold", os.path.join(FONTES, "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Italic", os.path.join(FONTES, "ariali.ttf")))
pdfmetrics.registerFont(TTFont("Arial-BoldItalic", os.path.join(FONTES, "arialbi.ttf")))
registerFontFamily("Arial", normal="Arial", bold="Arial-Bold",
                   italic="Arial-Italic", boldItalic="Arial-BoldItalic")

# ---------------------------------------------------------------- estilos
LARGURA_UTIL = A4[0] - 4 * cm  # margens de 2 cm

est_titulo_capa = ParagraphStyle("TituloCapa", fontName="Arial-Bold",
                                 fontSize=18, leading=24, alignment=TA_CENTER)
est_capa = ParagraphStyle("Capa", fontName="Arial", fontSize=12, leading=18,
                          alignment=TA_CENTER)
est_capa_menor = ParagraphStyle("CapaMenor", fontName="Arial", fontSize=11,
                                leading=16, alignment=TA_CENTER,
                                textColor=colors.HexColor("#333333"))
est_h1 = ParagraphStyle("H1", fontName="Arial-Bold", fontSize=14, leading=18,
                        spaceBefore=18, spaceAfter=8,
                        textColor=colors.HexColor("#111111"))
est_h2 = ParagraphStyle("H2", fontName="Arial-Bold", fontSize=12, leading=16,
                        spaceBefore=12, spaceAfter=6,
                        textColor=colors.HexColor("#222222"))
est_corpo = ParagraphStyle("Corpo", fontName="Arial", fontSize=10.5,
                           leading=14.5, alignment=TA_JUSTIFY, spaceAfter=6)
est_item = ParagraphStyle("Item", parent=est_corpo, leftIndent=0.6 * cm,
                          bulletIndent=0.2 * cm, spaceAfter=3)
est_formula = ParagraphStyle("Formula", fontName="Arial", fontSize=10.5,
                             leading=14, alignment=TA_CENTER, spaceBefore=4,
                             spaceAfter=8)
est_legenda = ParagraphStyle("Legenda", fontName="Arial", fontSize=9,
                             leading=12, alignment=TA_CENTER,
                             textColor=colors.HexColor("#444444"),
                             spaceBefore=4, spaceAfter=12)
est_tab_titulo = ParagraphStyle("TabTitulo", parent=est_legenda, spaceBefore=10,
                                spaceAfter=4)
est_ref = ParagraphStyle("Ref", parent=est_corpo, leftIndent=0.8 * cm,
                         firstLineIndent=-0.8 * cm, spaceAfter=4)

_contador_figura = [0]
_contador_tabela = [0]


def figura(caminho_rel, legenda, largura_max=LARGURA_UTIL, altura_max=15 * cm):
    """Flowable de figura + legenda numerada, mantidos juntos."""
    caminho = os.path.join(RES, caminho_rel)
    if not os.path.exists(caminho):
        raise FileNotFoundError(caminho)
    with PILImage.open(caminho) as im:
        w, h = im.size
    escala = min(largura_max / w, altura_max / h, 1.0 if w > largura_max else largura_max / w)
    largura = w * escala
    altura = h * escala
    _contador_figura[0] += 1
    n = _contador_figura[0]
    return KeepTogether([
        Image(caminho, width=largura, height=altura),
        Paragraph(f"<b>Figura {n}</b> — {legenda}", est_legenda),
    ]), n


def adicionar_figura(historia, caminho_rel, legenda, **kw):
    bloco, n = figura(caminho_rel, legenda, **kw)
    historia.append(bloco)
    return n


def tabela(historia, titulo, cabecalho, linhas, larguras=None, fonte=8.0):
    _contador_tabela[0] += 1
    n = _contador_tabela[0]
    historia.append(Paragraph(f"<b>Tabela {n}</b> — {titulo}", est_tab_titulo))
    dados = [cabecalho] + linhas
    t = Table(dados, colWidths=larguras, repeatRows=1, hAlign="CENTER")
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Arial"),
        ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), fonte),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f5f5f5")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    historia.append(t)
    historia.append(Spacer(1, 10))
    return n


def p(historia, texto, estilo=est_corpo):
    historia.append(Paragraph(texto, estilo))


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Arial", 9)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawCentredString(A4[0] / 2.0, 1.1 * cm, f"{doc.page}")
    canvas.restoreState()


def capa_sem_rodape(canvas, doc):
    pass


# ================================================================ conteúdo
historia = []

# ------------------------------------------------------------------ capa
historia.append(Spacer(1, 3.2 * cm))
p(historia, "UNIVERSIDADE FEDERAL DA PARAÍBA", est_capa)
p(historia, "CENTRO DE INFORMÁTICA", est_capa)
historia.append(Spacer(1, 0.6 * cm))
p(historia, "Introdução ao Processamento Digital de Imagens — Período 2026.1", est_capa_menor)
p(historia, "Professor: Leonardo", est_capa_menor)
historia.append(Spacer(1, 3.4 * cm))
p(historia, "DETECÇÃO DE BORDAS EM IMAGENS COLORIDAS:", est_titulo_capa)
p(historia, "CANNY CLÁSSICO × CANNY MODIFICADO GABOR–DI ZENZO", est_titulo_capa)
historia.append(Spacer(1, 0.8 * cm))
p(historia, "Trabalho Prático da disciplina", est_capa_menor)
historia.append(Spacer(1, 6.0 * cm))
p(historia, "Junho de 2026", est_capa)
historia.append(PageBreak())

# ------------------------------------------------------------ 1 introdução
p(historia, "1. Introdução", est_h1)

p(historia, "1.1 Contextualização e apresentação do tema", est_h2)
p(historia,
  "A detecção de bordas é uma das operações fundamentais do processamento "
  "digital de imagens: bordas delimitam objetos, regiões e texturas, e servem "
  "de insumo para segmentação, reconhecimento e medição. O detector de Canny "
  "(1986) é o algoritmo clássico de referência, combinando suavização, "
  "gradientes, afinamento por supressão de não-máximos (NMS) e limiarização "
  "por histerese.")
p(historia,
  "O Canny tradicional, porém, opera de forma <b>escalar</b>: a imagem RGB é "
  "convertida para tons de cinza antes de qualquer cálculo de gradiente. Essa "
  "conversão, Y = 0,299R + 0,587G + 0,114B, é uma projeção linear de um "
  "espaço tridimensional de cor em um único eixo de luminância. Pares de "
  "cores distintas que recaem no mesmo valor de Y tornam-se indistinguíveis — "
  "e a borda cromática entre elas é destruída <i>antes</i> de o detector "
  "começar a trabalhar. Este trabalho implementa, analisa e compara o Canny "
  "clássico com uma versão modificada — o <b>Canny Modificado Gabor–Di "
  "Zenzo</b> — que processa a cor de forma vetorial e funde a informação dos "
  "canais no domínio das derivadas, preservando bordas invisíveis ao "
  "pipeline escalar.")

p(historia, "1.2 Fundamentação teórica", est_h2)
p(historia,
  "<b>Detector de Canny.</b> O pipeline clássico tem cinco etapas: (i) "
  "suavização gaussiana, que controla a escala e reduz ruído; (ii) estimativa "
  "do gradiente por máscaras de Sobel, produzindo as derivadas g<sub>x</sub> "
  "e g<sub>y</sub>; (iii) magnitude (norma L2) e direção (atan2) do "
  "gradiente; (iv) supressão de não-máximos, que compara cada pixel com os "
  "dois vizinhos ao longo da direção do gradiente — ortogonais à borda — "
  "reduzindo as cristas à espessura de um pixel; e (v) histerese, que "
  "classifica os pixels em fortes (≥ T<sub>high</sub>), fracos "
  "(≥ T<sub>low</sub>) ou suprimidos, promovendo fracos a borda apenas "
  "quando conectados a um forte.")
p(historia,
  "<b>Filtros de Gabor.</b> Um filtro de Gabor é o produto de uma envoltória "
  "gaussiana por uma portadora senoidal orientada. No sistema de coordenadas "
  "da imagem (x = colunas, crescendo para a direita; y = linhas, crescendo "
  "para baixo), com rotação de um ângulo θ:")
p(historia, "x′ = x·cos θ + y·sen θ&nbsp;&nbsp;&nbsp;&nbsp; "
            "y′ = −x·sen θ + y·cos θ", est_formula)
p(historia, "g(x, y) = exp( −(x′² + γ²·y′²) / (2σ²) ) · cos( 2π·x′/λ + ψ )",
  est_formula)
p(historia,
  "O parâmetro σ define a escala espacial da envoltória; λ, o comprimento de "
  "onda da portadora (frequência espacial 1/λ); γ, a elipsicidade da "
  "envoltória; ψ, a fase da portadora; e θ, a direção da <i>variação</i> — a "
  "borda detectada é perpendicular a θ. Um banco com várias orientações "
  "permite capturar transições em qualquer direção, com seletividade "
  "simultânea de frequência e orientação — propriedade que o gradiente de "
  "Sobel, de banda larga, não possui.")
p(historia,
  "<b>Abordagem vetorial de Di Zenzo.</b> Di Zenzo (1986) propôs tratar a "
  "imagem colorida como um campo vetorial e combinar as derivadas dos canais "
  "— em vez de combinar os canais antes de derivar. Na formulação original "
  "isso é feito pelo tensor de estrutura; a variante adotada neste trabalho, "
  "definida pela especificação, preserva o princípio essencial (fusão <i>no "
  "domínio das derivadas</i>) de forma direta: para cada orientação θ do "
  "banco de Gabor, a mesma máscara é aplicada aos canais R, G e B "
  "separadamente e as respostas são fundidas pela norma Euclidiana; em "
  "seguida, uma redução por máximo sobre as orientações define a magnitude e "
  "a orientação finais de cada pixel. Assim, uma transição visível em "
  "qualquer canal — ou repartida entre eles — sobrevive à fusão, ainda que a "
  "luminância seja constante.")

p(historia, "1.3 Objetivos", est_h2)
p(historia,
  "<b>Objetivo geral:</b> implementar do zero, analisar e comparar o "
  "detector de Canny clássico e o Canny Modificado Gabor–Di Zenzo em imagens "
  "coloridas, reportando e discutindo os resultados nas seis imagens de "
  "teste fornecidas.")
p(historia, "<b>Objetivos específicos:</b>")
for item in [
    "implementar uma função própria de correlação bidimensional espacial para "
    "imagens RGB, com leitura de máscaras estáticas (Sobel, gaussianas) de "
    "arquivos de configuração externos .txt e .json (Módulo A);",
    "implementar um gerador paramétrico de banco de filtros de Gabor a partir "
    "de arquivo JSON (Módulo B);",
    "implementar o pipeline vetorial completo — filtragem por orientação, "
    "fusão L2 dos canais, redução por máximo, NMS guiado pela orientação "
    "final e histerese (Módulo C);",
    "analisar a sensibilidade do método aos parâmetros do Gabor "
    "(Experimento 1), incluindo o caso de σ excessivo em cenário texturizado;",
    "validar o afinamento (espessura de exatamente 1 pixel, com zoom digital) "
    "e a histerese, justificando os limiares adotados (Experimento 2);",
    "comparar criticamente os dois detectores, com atenção especial à imagem "
    "GrayAndMagenta.png.",
]:
    p(historia, f"• {item}", est_item)

historia.append(PageBreak())

# --------------------------------------------------- 2 materiais e métodos
p(historia, "2. Materiais e Métodos", est_h1)

p(historia, "2.1 Ferramentas, restrições e validação", est_h2)
p(historia,
  "O sistema foi desenvolvido em Python 3.12 com NumPy 2.4 — usado "
  "exclusivamente para álgebra de matrizes e operações elemento a elemento — "
  "e Pillow, usado apenas para abrir e salvar imagens, conforme a "
  "especificação. Nenhuma função pronta de processamento de imagem foi "
  "utilizada (sem cv2.Canny, cv2.filter2D, cv2.getGaborKernel, scipy.ndimage "
  "ou equivalentes); o matplotlib aparece somente na geração de um gráfico "
  "de perfil unidimensional para este relatório. Imagens RGBA com "
  "transparência real (FCBarcelona.png) são compostas manualmente sobre "
  "fundo branco; a conversão para tons de cinza é feita manualmente por "
  "Y = 0,299R + 0,587G + 0,114B, como exige o roteiro. A corretude dos "
  "módulos é coberta por 38 testes automatizados de sanidade — incluindo a "
  "comparação da correlação própria com uma implementação de referência por "
  "laços explícitos — e por um teste de ponta a ponta que valida "
  "configurações, pipelines e artefatos de saída.")

p(historia, "2.2 Módulo A — filtragem espacial genérica", est_h2)
p(historia,
  "A correlação bidimensional espacial foi implementada na definição direta,")
p(historia,
  "saída(i, j) = Σ<sub>u</sub> Σ<sub>v</sub> K(u, v) · I(i + u − p<sub>h</sub>, "
  "j + v − p<sub>w</sub>),", est_formula)
p(historia,
  "por soma deslocada vetorizada, para imagens em tons de cinza (H×W) ou "
  "multicanal (H×W×C) — cada canal é filtrado de forma independente. O "
  "tratamento de borda padrão é a replicação do pixel da margem (preencher "
  "com zeros criaria um degrau artificial no contorno da imagem); o modo "
  "zeros também está disponível. As máscaras estáticas são lidas de arquivos "
  "externos: Sobel X/Y em .txt e a gaussiana 5×5 (σ = 1) em .json com campo "
  "de normalização, que faz o carregador dividir a matriz pela soma dos "
  "coeficientes.")

p(historia, "2.3 Módulo B — gerador paramétrico do banco de Gabor", est_h2)
p(historia,
  "O banco é descrito por um arquivo JSON com os parâmetros da especificação "
  "— tamanho_mascara, sigma, lambda, gamma, psi e orientacoes_graus — e as "
  "máscaras são geradas dinamicamente pela fórmula da Seção 1.2. O banco "
  "padrão usa máscara 31×31, σ = 4, λ = 8, γ = 0,5, ψ = −π/2 e oito "
  "orientações (0° a 157,5°, passo 22,5°). A escolha ψ = −π/2 (portadora "
  "senoidal ímpar, anti-simétrica e de soma exatamente nula) é justificada "
  "experimentalmente na Seção 3.2: filtros pares têm resposta nula no centro "
  "de um degrau e produzem linhas duplas após o afinamento. Cada configuração "
  "usada nos experimentos foi gravada em config/experimentos/*.json e "
  "recarregada pelo Módulo B, exercitando o caminho completo arquivo → "
  "máscaras.")

p(historia, "2.4 Módulo C — Canny Modificado Gabor–Di Zenzo", est_h2)
p(historia, "O fluxo por pixel (i, j) segue a especificação:")
for item in [
    "<b>Filtragem independente por orientação:</b> para cada ângulo θ do "
    "banco, a máscara é aplicada aos canais R, G e B separadamente, via "
    "Módulo A;",
    "<b>Fusão de canais (norma L2):</b> Magn(i, j, θ) = √( R<sub>θ</sub>² + "
    "G<sub>θ</sub>² + B<sub>θ</sub>² );",
    "<b>Redução por máximo:</b> Magnitude_Final(i, j) = max<sub>θ</sub> "
    "Magn(i, j, θ); a Orientação Final é o ângulo do filtro vencedor;",
    "<b>Afinamento (NMS):</b> guiado pela matriz de Orientação Final, "
    "comparando o pixel com os dois vizinhos ortogonais à borda;",
    "<b>Limiarização por histerese:</b> classificação em fortes, fracos e "
    "suprimidos, seguida da análise de conectividade.",
]:
    p(historia, f"• {item}", est_item)
p(historia,
  "A mesma rotina aceita uma imagem em tons de cinza — a fusão L2 de um "
  "único canal equivale ao valor absoluto da resposta — fornecendo o "
  "<i>Gabor tradicional</i> (escalar) usado como contraste no Experimento 1.")

p(historia, "2.5 Canny clássico", est_h2)
p(historia,
  "Pipeline: conversão manual para Y; suavização gaussiana 5×5 (σ = 1) "
  "carregada de arquivo; gradientes por Sobel X/Y carregados de arquivos "
  ".txt; magnitude L2 e direção por atan2(g<sub>y</sub>, g<sub>x</sub>); NMS "
  "e histerese idênticos aos do pipeline modificado — o que torna a "
  "comparação justa: os dois métodos diferem apenas na origem da magnitude e "
  "da orientação.")

p(historia, "2.6 Afinamento com espessura de exatamente 1 pixel e histerese", est_h2)
p(historia,
  "A orientação é quantizada nos quatro eixos da vizinhança discreta (0°, "
  "45°, 90°, 135°) e cada pixel é comparado com os dois vizinhos ao longo da "
  "direção de variação. Em platôs de magnitude constante, um critério de "
  "desempate assimétrico — estritamente maior em um sentido, maior ou igual "
  "no outro — garante espessura final de exatamente um pixel, mesmo em "
  "cristas de topo plano. A histerese realiza busca em largura 8-conexa a "
  "partir dos pixels fortes, incorporando os fracos conectados.")

p(historia, "2.7 Seleção e justificativa dos limiares (T<sub>high</sub> e T<sub>low</sub>)", est_h2)
p(historia,
  "Os limiares são escolhidos automaticamente por três regras. (i) "
  "T<sub>high</sub> é o percentil 90 dos valores que <i>sobrevivem</i> ao "
  "NMS: após o afinamento restam apenas picos de crista candidatos, e o "
  "percentil adapta o limiar ao conteúdo de cada imagem. (ii) "
  "T<sub>low</sub> = 0,4 · T<sub>high</sub>, razão de 2,5:1, dentro da faixa "
  "2:1 a 3:1 recomendada por Canny — alta o bastante para não semear ruído e "
  "baixa o bastante para a histerese rastrear continuações fracas. (iii) Um "
  "piso absoluto de 0,5 separa estrutura real de ruído numérico: em dados "
  "0–255, o menor degrau real (1 nível de cinza) produz magnitude Sobel ≥ 4, "
  "enquanto resíduos de arredondamento em ponto flutuante ficam na ordem de "
  "10<super>−4</super>. Sem o piso, uma imagem sem estrutura teria os "
  "percentis adaptados ao ruído de máquina e produziria bordas espúrias — "
  "caso real detectado e corrigido durante o desenvolvimento (Seção 4.1).")

p(historia, "2.8 Exibição e roteiro experimental", est_h2)
p(historia,
  "Máscaras e mapas possuem valores negativos ou maiores que 255; para "
  "exibição aplica-se a expansão de histograma linear para [0, 255] — "
  "apenas para fins de relatório e depuração; o pipeline opera sempre sobre "
  "os valores reais. Como a expansão é individual por mapa, o brilho não é "
  "comparável entre figuras; os máximos reais acompanham os rótulos. As "
  "configurações dos experimentos estão na Tabela 1.")

tabela(historia,
       "Configurações do roteiro experimental (banco com 8 orientações em todos os casos).",
       ["Estudo", "Máscara", "σ", "λ", "γ", "ψ", "Métodos", "Imagens"],
       [
           ["Varredura de λ", "31×31", "4", "4 / 8 / 16", "0,5", "−π/2",
            "escalar e vetorial", "todas (6)"],
           ["Varredura de σ", "13/31/73", "2 / 4 / 12", "8", "0,5", "−π/2",
            "escalar e vetorial", "todas (6)"],
           ["Efeito de ψ", "31×31", "4", "8", "0,5", "0 e −π/2",
            "vetorial", "GrayAndMagenta, VintageCar"],
           ["Efeito de γ", "31×31", "4", "8", "0,25/0,5/1", "−π/2",
            "vetorial", "FCBarcelona"],
           ["Experimento 2", "31×31", "4", "8", "0,5", "−π/2",
            "clássico × modificado", "todas (6)"],
       ],
       larguras=[3.0 * cm, 1.7 * cm, 1.7 * cm, 1.9 * cm, 1.7 * cm, 1.7 * cm,
                 2.7 * cm, 2.6 * cm])

historia.append(PageBreak())

# ------------------------------------------------------------- 3 resultados
p(historia, "3. Resultados", est_h1)

p(historia, "3.1 Banco de Gabor e funcionamento do pipeline vetorial", est_h2)
adicionar_figura(historia, os.path.join("experimento1", "kernels_banco_padrao.png"),
                 "Banco de Gabor padrão (máscara 31×31, σ = 4, λ = 8, γ = 0,5, "
                 "ψ = −π/2), com expansão de histograma e zoom 4×. θ é a direção "
                 "da variação: o filtro de θ = 0 detecta bordas verticais.")
p(historia,
  "A Figura 2 demonstra as etapas 1–3 do Módulo C na imagem GrayAndMagenta "
  "com o filtro de θ = 0, exibindo todas as respostas na <i>mesma</i> escala "
  "de cinza. Os canais respondem individualmente à transição (máximos 1929 "
  "em R, 1768 em G e 4046 em B) e a fusão L2 os combina: "
  "√(1929² + 1768² + 4046²) = 4818 — exatamente o máximo do mapa fundido. A "
  "resposta do mesmo filtro sobre a luminância Y é nula (máximo 2×10"
  "<super>−5</super>, painel preto): a informação da borda morre na projeção "
  "para cinza, não na filtragem.")
adicionar_figura(historia, os.path.join("apresentacao", "gm_resposta_por_canal_theta0.png"),
                 "Respostas do filtro de Gabor (θ = 0) por canal na "
                 "GrayAndMagenta, em escala comum: |R|, |G|, |B|, fusão L2 e "
                 "resposta sobre Y (nula).")

p(historia, "3.2 Experimento 1 — sensibilidade paramétrica", est_h2)
p(historia,
  "<b>Efeito de λ (frequência espacial).</b> Com σ fixo, λ seleciona a banda "
  "de frequência a que o detector responde (Figuras 3 e 4): λ = 4 sintoniza "
  "alta frequência — capim e textura fina respondem, estruturas largas "
  "quase desaparecem; λ = 8 maximiza a resposta das listras da zebra, de "
  "período compatível; λ = 16 privilegia os macrocontornos — silhueta, "
  "horizonte e nuvens — com bordas mais espessas (pior localização) e fusão "
  "das listras finas. A magnitude máxima cresce sistematicamente com λ "
  "(6.361 → 17.622 → 22.503 na Zebra, método vetorial), pois com menos "
  "oscilações sob a envoltória há menos cancelamento ao integrar um degrau.")
adicionar_figura(historia, os.path.join("experimento1", "kernels_varredura_lambda.png"),
                 "Máscaras de θ = 0 da varredura de λ (4, 8, 16) com σ = 4: o "
                 "número de oscilações sob a mesma envoltória diminui com λ.")
adicionar_figura(historia, os.path.join("experimento1", "Zebra", "painel_lambda_modificado.png"),
                 "Zebra, método vetorial: mapas de magnitude para λ = 4, 8 e 16 "
                 "(expansão de histograma individual; máximos nos rótulos).")

p(historia,
  "<b>Efeito de σ (escala) e o caso do σ excessivo.</b> σ = 2 dá excelente "
  "localização e responde a tudo, inclusive ruído fino; σ = 4 é o "
  "compromisso do banco padrão. Com σ = 12 (máscara 73×73) — excessivo para "
  "o cenário texturizado, como pergunta a especificação — o suporte do "
  "filtro (±36 px) engloba vários períodos da textura: respostas de bordas "
  "vizinhas com sinais opostos se sobrepõem dentro da envoltória e se "
  "cancelam parcialmente, e o mapa degenera em manchas borradas de baixa "
  "frequência (Figuras 5–7). As listras da zebra fundem-se em blobs, a "
  "pelagem do urso vira um halo difuso e os máximos se deslocam das posições "
  "reais das bordas — perda de localização que inviabiliza o afinamento. É a "
  "manifestação prática do compromisso de incerteza espaço-frequência.")
adicionar_figura(historia, os.path.join("experimento1", "kernels_varredura_sigma.png"),
                 "Máscaras de θ = 0 da varredura de σ: σ = 2 (13×13), σ = 4 "
                 "(31×31) e σ = 12 (73×73), todas com λ = 8.")
adicionar_figura(historia, os.path.join("experimento1", "Zebra", "painel_sigma_modificado.png"),
                 "Zebra, método vetorial: σ = 2, 4 e 12. Com σ excessivo as "
                 "listras se fundem e a localização é destruída.")
adicionar_figura(historia, os.path.join("experimento1", "Bear", "painel_sigma_modificado.png"),
                 "Bear, método vetorial: o mesmo efeito do σ excessivo sobre a "
                 "pelagem fina (σ = 12, máscara 73×73).")

p(historia,
  "<b>Escalar × vetorial.</b> O mesmo banco foi aplicado de duas formas: "
  "sobre Y (escalar) e sobre R, G, B com fusão L2 (vetorial). Na "
  "GrayAndMagenta o escalar registrou magnitude máxima 0,0 em <i>todas</i> "
  "as cinco configurações testadas, enquanto o vetorial respondeu fortemente "
  "em todas (Tabela 2 e Figura 8): nenhuma escolha de parâmetros salva o "
  "método escalar, porque a informação foi destruída antes do filtro.")
tabela(historia,
       "GrayAndMagenta — magnitude máxima por configuração: Gabor escalar "
       "(sobre Y) × vetorial (Gabor–Di Zenzo sobre RGB).",
       ["Configuração", "Escalar (Y)", "Vetorial (RGB)"],
       [
           ["λ = 4, σ = 4 (máscara 31)", "0,0", "1.766"],
           ["λ = 8, σ = 4 (máscara 31)", "0,0", "4.818"],
           ["λ = 16, σ = 4 (máscara 31)", "0,0", "10.025"],
           ["λ = 8, σ = 2 (máscara 13)", "0,0", "2.293"],
           ["λ = 8, σ = 12 (máscara 73)", "0,0", "11.639"],
       ],
       larguras=[6.5 * cm, 3.5 * cm, 3.5 * cm], fonte=9)
adicionar_figura(historia,
                 os.path.join("experimento1", "GrayAndMagenta",
                              "painel_tradicional_vs_modificado.png"),
                 "GrayAndMagenta: original, Gabor escalar sobre Y (máximo 0 — "
                 "mapa preto) e Gabor–Di Zenzo vetorial (borda encontrada).")

p(historia,
  "<b>Efeito de ψ (fase).</b> Sobre um degrau ideal, o filtro par (ψ = 0, "
  "cossenoidal, simétrico) tem resposta nula exatamente no centro da borda e "
  "dois picos simétricos a ±λ/4 — o NMS devolve duas linhas paralelas "
  "(Figura 9, à esquerda). O filtro ímpar (ψ = −π/2, senoidal, "
  "anti-simétrico, soma nula) tem pico único no centro do degrau; restam "
  "lóbulos laterais fracos a ±λ/2 que a histerese elimina por não estarem "
  "conectados a sementes fortes. Por isso o banco padrão adota ψ = −π/2: é o "
  "detector de degraus adequado a um pipeline que afina para um pixel.")
adicionar_figura(historia, os.path.join("experimento1", "GrayAndMagenta", "painel_psi.png"),
                 "GrayAndMagenta: magnitude e pós-NMS para ψ = 0 (par — vale "
                 "central e linha dupla) e ψ = −π/2 (ímpar — pico único).")

p(historia,
  "<b>Efeito de γ (elipsicidade).</b> γ controla a razão de aspecto da "
  "envoltória (desvio ao longo da borda = σ/γ). γ = 0,25 alonga o filtro na "
  "direção da borda: contornos retos ficam mais contínuos (máximo 21.132 no "
  "escudo), ao custo de borrar cantos e curvas fechadas; γ = 1 (isotrópico) "
  "localiza melhor os detalhes, com respostas mais fracas (máximo 7.915) e "
  "mais fragmentadas. O valor γ = 0,5 foi adotado como meio-termo "
  "(Figura 10).")
adicionar_figura(historia, os.path.join("experimento1", "FCBarcelona", "painel_gamma.png"),
                 "FCBarcelona, método vetorial: efeito de γ (0,25; 0,5; 1,0) "
                 "sobre o mapa de magnitudes.")

historia.append(PageBreak())

p(historia, "3.3 Experimento 2 — afinamento, histerese e comparação final", est_h2)
p(historia,
  "<b>Limiares adotados.</b> A Tabela 3 resume, para cada imagem e método, "
  "os limiares escolhidos pela regra da Seção 2.7 e as contagens de pixels. "
  "Os limiares variam quase 50× entre cenas (T<sub>high</sub> de 184 a "
  "7.951) sem qualquer ajuste manual — é o percentil adaptando-se ao "
  "conteúdo. A coluna de fracos mostra a histerese em ação: na FCBarcelona, "
  "dos 15.916 fracos, apenas cerca de 3 mil entraram no resultado (os "
  "conectados a sementes fortes); na GrayAndMagenta, os 448 fracos — os dois "
  "lóbulos laterais paralelos do filtro ímpar — foram todos rejeitados.")
tabela(historia,
       "Experimento 2 — limiares (automáticos) e contagens por imagem e método.",
       ["Imagem", "Método", "T_low", "T_high", "Cand. NMS", "Fortes",
        "Fracos", "Borda final"],
       [
           ["Bear", "modificado", "1.357,8", "3.394,6", "742.745", "74.275", "220.726", "189.751"],
           ["Bear", "clássico", "73,5", "183,7", "715.119", "71.502", "204.176", "191.129"],
           ["FCBarcelona", "modificado", "3.180,5", "7.951,3", "41.206", "4.031", "15.916", "7.036"],
           ["FCBarcelona", "clássico", "256,6", "641,5", "12.579", "1.258", "9.105", "2.603"],
           ["GrayAndMagenta", "modificado", "1.927,3", "4.818,4", "1.324", "224", "448", "224"],
           ["GrayAndMagenta", "clássico", "∞", "∞", "224*", "0", "0", "0"],
           ["PlacaMercosul", "modificado", "1.810,3", "4.525,8", "111.751", "11.170", "15.720", "18.619"],
           ["PlacaMercosul", "clássico", "133,7", "334,3", "83.808", "8.292", "4.774", "11.146"],
           ["VintageCar", "modificado", "1.666,0", "4.165,1", "94.989", "9.491", "17.075", "18.867"],
           ["VintageCar", "clássico", "105,7", "264,2", "75.324", "7.239", "12.524", "13.611"],
           ["Zebra", "modificado", "1.409,0", "3.522,4", "122.627", "12.263", "20.390", "18.633"],
           ["Zebra", "clássico", "80,5", "201,3", "113.419", "11.334", "14.985", "13.928"],
       ],
       larguras=[2.9 * cm, 2.2 * cm, 1.8 * cm, 1.8 * cm, 2.0 * cm, 1.7 * cm,
                 1.8 * cm, 2.1 * cm])
p(historia,
  "* Na GrayAndMagenta em tons de cinza os 224 “candidatos” têm magnitude da "
  "ordem de 10<super>−6</super> — ruído de arredondamento —, todos abaixo do "
  "piso absoluto; o sistema responde corretamente “não há bordas” "
  "(T<sub>low</sub> = T<sub>high</sub> = ∞).", est_legenda)

p(historia,
  "<b>Pipeline lado a lado e prova do afinamento.</b> A Figura 11 mostra os "
  "quatro estágios do método modificado na PlacaMercosul: o mapa de "
  "magnitudes de Di Zenzo, o resultado pós-NMS, a classificação da histerese "
  "(branco = forte, cinza = fraco, preto = suprimido) e as bordas finais. As "
  "Figuras 12 e 13 trazem o zoom digital de 8× (replicação de pixels) na "
  "janela de maior densidade de bordas: a magnitude aparece como faixa "
  "larga, o pós-NMS reduzido a cristas de um pixel e as bordas finais "
  "limpas. Quantitativamente (Tabela 4), a fração de blocos 2×2 totalmente "
  "preenchidos — que deveria ser nula em um mapa de 1 px, exceto junções — "
  "ficou abaixo de 0,3% em todas as imagens; na GrayAndMagenta a verificação "
  "é exata: 224 linhas com exatamente um pixel cada.")
adicionar_figura(historia, os.path.join("experimento2", "PlacaMercosul", "painel_modificado.png"),
                 "PlacaMercosul, método modificado: magnitude Di Zenzo → "
                 "pós-NMS → classificação (fortes/fracos/suprimidos) → bordas "
                 "finais.")
adicionar_figura(historia, os.path.join("experimento2", "GrayAndMagenta", "painel_zoom_mod.png"),
                 "GrayAndMagenta — zoom digital 8×: magnitude, pós-NMS e "
                 "bordas finais com exatamente 1 pixel de largura.")
adicionar_figura(historia, os.path.join("experimento2", "PlacaMercosul", "painel_zoom_mod.png"),
                 "PlacaMercosul — zoom digital 8× na região de maior densidade "
                 "de bordas: cristas de 1 pixel após o NMS.")
tabela(historia,
       "Verificação quantitativa do afinamento: blocos 2×2 totalmente "
       "preenchidos (absoluto e fração dos pixels de borda).",
       ["Imagem", "Modificado", "Clássico"],
       [
           ["Bear", "176 (0,093%)", "904 (0,47%)"],
           ["FCBarcelona", "3 (0,043%)", "0 (0%)"],
           ["GrayAndMagenta", "0 (0%)", "0 (—)"],
           ["PlacaMercosul", "7 (0,038%)", "1 (0,009%)"],
           ["VintageCar", "3 (0,016%)", "19 (0,14%)"],
           ["Zebra", "50 (0,27%)", "43 (0,31%)"],
       ],
       larguras=[4.5 * cm, 4.0 * cm, 4.0 * cm], fonte=9)

historia.append(PageBreak())

p(historia,
  "<b>GrayAndMagenta em detalhe.</b> A imagem possui apenas duas cores: "
  "cinza RGB (100, 100, 100) e magenta RGB (172, 34, 251). Pela fórmula da "
  "luminância: Y<sub>cinza</sub> = 100,0 e Y<sub>magenta</sub> = 0,299·172 + "
  "0,587·34 + 0,114·251 = 100,0. As cores são exatamente isoluminantes: após "
  "a conversão para cinza a imagem é constante e não existe gradiente a "
  "detectar — o Canny clássico falha por impossibilidade matemática, não por "
  "calibração. O perfil da linha central (Figura 14) evidencia: a magnitude "
  "do clássico é uma reta em 7,6×10<super>−6</super> (ruído de "
  "arredondamento; observe a escala 10<super>−6</super>), enquanto o "
  "modificado apresenta pico de 4.818 na coluna da borda — seis ordens de "
  "grandeza acima — com os lóbulos laterais característicos do filtro ímpar "
  "a ±λ/2. No domínio vetorial a transição é enorme: ΔRGB = (72, −66, 151), "
  "norma ≈ 180. Resultado final (Figura 15): clássico, 0 px; modificado, a "
  "linha vertical completa — 224 de 224 linhas com exatamente 1 pixel — sem "
  "falsos positivos.")
adicionar_figura(historia, os.path.join("experimento2", "GrayAndMagenta", "perfil_linha_central.png"),
                 "GrayAndMagenta — perfil da magnitude na linha central: "
                 "clássico (esq., escala 10⁻⁶: ruído numérico) × modificado "
                 "(dir., pico 4.818 na borda).")
adicionar_figura(historia, os.path.join("experimento2", "GrayAndMagenta", "painel_comparacao.png"),
                 "GrayAndMagenta — original, bordas do Canny clássico (0 px) e "
                 "do Canny modificado (224 px, 1 px de largura).")

p(historia,
  "<b>FCBarcelona — o caso real mais revelador.</b> O clássico (2.603 px) "
  "recupera a silhueta do escudo — contraste enorme contra o fundo branco — "
  "mas perde quase toda a estrutura interna (Figura 16). Medindo as cores "
  "das listras inferiores na própria imagem: grená RGB (162, 33, 75) → "
  "Y = 76,4; azul RGB (0, 82, 159) → Y = 66,3. A diferença de luminância é "
  "de apenas ≈ 10 níveis (4% da faixa), abaixo de qualquer limiar útil — uma "
  "versão de mundo real da GrayAndMagenta —, enquanto a distância das mesmas "
  "cores no espaço RGB é ≈ 189. O modificado (7.036 px) recupera as "
  "listras, a divisão dos quartéis superiores, a faixa “FCB” e a bola com "
  "costuras.")
adicionar_figura(historia, os.path.join("experimento2", "FCBarcelona", "painel_comparacao.png"),
                 "FCBarcelona — original, Canny clássico (2.603 px: perde a "
                 "estrutura interna) e modificado (7.036 px).")

p(historia,
  "<b>Demais imagens.</b> Na Bear (Figura 17), cena dominada por textura de "
  "pelagem, ambos os métodos devolvem ≈ 190 mil px de borda; o modificado "
  "produz contornos externos mais contínuos (transição cromática pelo/fundo) "
  "e quintuplica menos blocos 2×2 (0,09% × 0,47%). Na PlacaMercosul "
  "(Figura 18), ambos mantêm os caracteres legíveis: o clássico dá traços "
  "mais finos e econômicos; o modificado resolve as duas bordas de cada "
  "traço (contorno duplo, pois λ = 8 está na escala da largura do traço) e "
  "captura mais da faixa azul superior, onde a transição é também cromática. "
  "Na VintageCar (Figura 19), o modificado segue melhor a lataria vermelha "
  "contra o fundo escuro — transição com forte componente de matiz — com "
  "contornos mais contínuos (18.867 × 13.611 px). Na Zebra (Figura 20), "
  "listras preto-e-brancas são o caso ideal do método escalar e os dois "
  "ficam próximos; o modificado adiciona contornos de céu/nuvens e gramado.")
adicionar_figura(historia, os.path.join("experimento2", "Bear", "painel_comparacao.png"),
                 "Bear — original, Canny clássico (191.129 px) e modificado "
                 "(189.751 px).")
adicionar_figura(historia, os.path.join("experimento2", "PlacaMercosul", "painel_comparacao.png"),
                 "PlacaMercosul — original, Canny clássico (11.146 px) e "
                 "modificado (18.619 px).")
adicionar_figura(historia, os.path.join("experimento2", "VintageCar", "painel_comparacao.png"),
                 "VintageCar — original, Canny clássico (13.611 px) e "
                 "modificado (18.867 px).")
adicionar_figura(historia, os.path.join("experimento2", "Zebra", "painel_comparacao.png"),
                 "Zebra — original, Canny clássico (13.928 px) e modificado "
                 "(18.633 px).")

p(historia,
  "<b>Custo computacional.</b> O método modificado custou de ≈ 8× (imagens "
  "pequenas) a ≈ 40–100× o clássico, conforme a imagem: na Bear "
  "(1920×1273), 63,9 s contra 1,7 s. A complexidade é O(H·W·k²) por canal e "
  "por orientação — 8 orientações × máscara 31×31 × 3 canais, contra uma "
  "gaussiana 5×5 e dois Sobéis 3×3 em um único canal.")

historia.append(PageBreak())

# -------------------------------------------------------------- 4 discussão
p(historia, "4. Discussão", est_h1)

p(historia, "4.1 Problemas e dificuldades encontradas", est_h2)
for item in [
    "<b>Limiar adaptativo enganado por ruído de máquina:</b> na primeira "
    "versão, a GrayAndMagenta em tons de cinza produzia 48 px de “borda” "
    "vindos de resíduos de ponto flutuante da ordem de 10<super>−5</super> — "
    "o percentil se adaptava ao ruído. A solução foi o piso absoluto de "
    "magnitude (Seção 2.7). Lição: limiar relativo sem âncora absoluta é "
    "frágil em imagens sem estrutura.",
    "<b>Platôs no NMS:</b> a regra clássica (≥ dos dois lados) mantém "
    "cristas de 2 px quando o topo é plano; foi necessário o desempate "
    "assimétrico, coberto por teste unitário, para garantir 1 px.",
    "<b>Linhas duplas com ψ = 0:</b> a resposta nula do filtro par no centro "
    "do degrau (Seção 3.2) produzia linhas duplas; o banco padrão passou a "
    "usar ψ = −π/2.",
    "<b>Lóbulos laterais do filtro ímpar:</b> tornam-se linhas paralelas "
    "fracas no NMS; com T<sub>low</sub> = 0,4·T<sub>high</sub> ficam abaixo "
    "do limiar ou desconectados, e a histerese os elimina (verificado na "
    "GrayAndMagenta: 448 fracos, todos rejeitados).",
    "<b>Custo da correlação espacial pura:</b> a máscara 73×73 sobre a Bear "
    "custou 328 s no método vetorial. Mitigações sem sair do domínio "
    "espacial: aritmética em float32, buffer pré-alocado e salto de "
    "coeficientes nulos. O Experimento 1 completo levou 18,2 minutos.",
]:
    p(historia, f"• {item}", est_item)

p(historia, "4.2 Comentários críticos sobre os resultados", est_h2)
p(historia,
  "Os resultados confirmam a tese central nas duas pontas — no caso-limite "
  "construído (GrayAndMagenta: 0 × 224 px) e em imagem real (FCBarcelona: "
  "listras com ΔY ≈ 10 invisíveis ao clássico) —, mas a análise crítica "
  "também registra onde o método modificado <i>não</i> compensa. Primeiro, o "
  "custo: 8–100× mais caro; em cenas onde a luminância já carrega as bordas "
  "(Zebra), o clássico entrega resultado equivalente por uma fração do "
  "tempo. Segundo, a escala do filtro interage com a geometria: na placa, "
  "λ = 8 resolve as duas bordas de cada traço de caractere e produz contorno "
  "duplo onde o clássico dá traço único — para OCR, por exemplo, o clássico "
  "seria preferível. Terceiro, limitações de projeto documentadas: a "
  "orientação é quantizada em 4 eixos no NMS (erro máximo de 22,5°, o mesmo "
  "do Canny clássico); o limiar é global por imagem — em cenas de textura "
  "densa (Bear) mantém-se muita borda de textura, e a extração apenas de "
  "macrocontornos exigiria elevar o percentil ou λ; e a expansão de "
  "histograma individual impede comparação de brilho entre figuras (os "
  "máximos reais acompanham os rótulos). Por fim, a variante implementada "
  "segue a especificação (fusão L2 + máximo) e não o tensor de estrutura do "
  "Di Zenzo original — a propriedade essencial (fusão no domínio das "
  "derivadas) é preservada, como o caso isoluminante demonstra.")

# -------------------------------------------------------------- 5 conclusão
p(historia, "5. Conclusão", est_h1)
p(historia,
  "Todos os módulos exigidos foram implementados do zero — correlação "
  "espacial com filtros carregados de arquivos .txt/.json (Módulo A), banco "
  "de Gabor paramétrico via JSON (Módulo B) e o pipeline vetorial completo "
  "com NMS de 1 pixel e histerese (Módulo C) — e validados por 38 testes de "
  "sanidade e um teste de ponta a ponta. Os experimentos sustentam duas "
  "conclusões. (1) Os parâmetros do Gabor governam o que é “borda”: λ "
  "seleciona a banda de frequência (texturas finas × macrocontornos); σ "
  "controla o compromisso localização × seletividade e, excessivo, destrói a "
  "localização em cenas texturizadas; γ troca continuidade de contornos "
  "retos por sensibilidade a curvas; ψ decide entre detector de linhas (par) "
  "e de degraus (ímpar). (2) Processar a cor vetorialmente, fundindo no "
  "domínio das derivadas, preserva bordas que o pipeline escalar destrói — "
  "de forma absoluta no caso isoluminante e mensurável em imagens reais. O "
  "preço é computacional (8–100×) e de parametrização; onde a luminância já "
  "carrega as bordas, o Canny clássico permanece competitivo. Como trabalhos "
  "futuros, destacam-se a avaliação sob ruído, a implementação do tensor de "
  "estrutura completo de Di Zenzo para comparação, e a paralelização da "
  "correlação.")

# -------------------------------------------------------------- referências
p(historia, "Referências", est_h1)
for ref in [
    "CANNY, J. A computational approach to edge detection. <i>IEEE "
    "Transactions on Pattern Analysis and Machine Intelligence</i>, "
    "v. PAMI-8, n. 6, p. 679–698, 1986.",
    "DI ZENZO, S. A note on the gradient of a multi-image. <i>Computer "
    "Vision, Graphics, and Image Processing</i>, v. 33, n. 1, p. 116–125, "
    "1986.",
    "DAUGMAN, J. G. Uncertainty relation for resolution in space, spatial "
    "frequency, and orientation optimized by two-dimensional visual cortical "
    "filters. <i>Journal of the Optical Society of America A</i>, v. 2, "
    "n. 7, p. 1160–1169, 1985.",
    "GONZALEZ, R. C.; WOODS, R. E. <i>Processamento Digital de Imagens</i>. "
    "3. ed. São Paulo: Pearson, 2010.",
]:
    p(historia, ref, est_ref)

# ------------------------------------------------------------------ anexo
p(historia, "Apêndice A — Reprodução dos resultados", est_h1)
p(historia,
  "O pacote contém o código-fonte completo, os arquivos de configuração "
  "(.txt/.json) e este relatório. Para reproduzir: instalar as dependências "
  "(pip install -r requirements.txt) e executar, na raiz do projeto: "
  "<i>python testes\\testes_sanidade.py</i> (38 testes), "
  "<i>python experimentos\\experimento1.py</i> (≈ 18 min), "
  "<i>python experimentos\\experimento2.py</i> (≈ 2 min) e "
  "<i>python testes\\teste_e2e.py</i> (validação de ponta a ponta). O "
  "utilitário <i>python demo.py &lt;imagem&gt;</i> executa os dois "
  "detectores em qualquer imagem avulsa; os parâmetros do banco podem ser "
  "trocados com <i>--banco &lt;arquivo.json&gt;</i>.")

# ===================================================================== build
doc = SimpleDocTemplate(
    SAIDA, pagesize=A4,
    leftMargin=2 * cm, rightMargin=2 * cm,
    topMargin=2 * cm, bottomMargin=2 * cm,
    title="Detecção de Bordas em Imagens Coloridas: Canny Clássico × Canny "
          "Modificado Gabor–Di Zenzo",
    subject="Trabalho Prático — Introdução ao Processamento Digital de "
            "Imagens, 2026.1",
    creator="Equipe de PDI",
)
doc.build(historia, onFirstPage=capa_sem_rodape, onLaterPages=rodape)
print(f"PDF gerado: {SAIDA}")
print(f"Figuras: {_contador_figura[0]} | Tabelas: {_contador_tabela[0]}")
