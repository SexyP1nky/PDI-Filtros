# -*- coding: utf-8 -*-
"""
Diretrizes de exibição e visualização (Seção 3 da especificação).

Máscaras e mapas possuem valores reais negativos ou maiores que 255; para
exibição (relatório/depuração) aplica-se a EXPANSÃO DE HISTOGRAMA para o
intervalo [0, 255]. Também há utilitários de montagem de painéis lado a
lado, zoom digital por vizinho-mais-próximo (np.repeat) e busca da janela
com maior densidade de bordas (para os recortes de zoom do Experimento 2).

O Pillow é usado aqui apenas para salvar imagens e desenhar rótulos de
texto nos painéis do relatório — nunca para processar as imagens.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from imagem_io import salvar_imagem


def expansao_histograma(mapa):
    """Expansão linear de histograma para [0, 255] (apenas para exibição).

    saida = (m - min) / (max - min) * 255. Mapa constante vira tudo 0.
    """
    m = np.asarray(mapa, dtype=np.float64)
    minimo = float(m.min())
    maximo = float(m.max())
    if maximo - minimo < 1e-12:
        return np.zeros(m.shape, dtype=np.uint8)
    return np.round((m - minimo) / (maximo - minimo) * 255.0).astype(np.uint8)


def binaria_para_uint8(mascara_bool):
    """Converte máscara booleana de bordas em imagem 0/255."""
    return np.where(np.asarray(mascara_bool, bool), 255, 0).astype(np.uint8)


def _para_rgb_uint8(img):
    arr = np.asarray(img)
    if arr.dtype == bool:
        arr = binaria_para_uint8(arr)
    if arr.dtype != np.uint8:
        raise ValueError("painéis esperam arrays uint8 (aplique expansao_histograma)"
                         f" — recebido dtype {arr.dtype}")
    if arr.ndim == 2:
        arr = np.stack([arr, arr, arr], axis=2)
    return arr


def _fonte(tamanho=14):
    try:
        return ImageFont.truetype("arial.ttf", tamanho)
    except OSError:
        return ImageFont.load_default()


def lado_a_lado(imagens, rotulos=None, margem=8, altura_rotulo=22, fundo=24):
    """Monta um painel horizontal com as imagens (uint8 cinza/RGB ou bool).

    Se 'rotulos' for fornecido, escreve uma faixa de texto acima de cada
    painel. Retorna um array RGB uint8.
    """
    rgb = [_para_rgb_uint8(im) for im in imagens]
    if rotulos is not None and len(rotulos) != len(rgb):
        raise ValueError("quantidade de rótulos diferente da de imagens")

    faixa = altura_rotulo if rotulos is not None else 0
    alt_max = max(im.shape[0] for im in rgb)
    larg_total = margem + sum(im.shape[1] + margem for im in rgb)
    alt_total = margem + faixa + alt_max + margem

    painel = np.full((alt_total, larg_total, 3), fundo, dtype=np.uint8)
    x = margem
    posicoes = []
    for im in rgb:
        h, w = im.shape[:2]
        painel[margem + faixa:margem + faixa + h, x:x + w] = im
        posicoes.append(x)
        x += w + margem

    if rotulos is not None:
        pil = Image.fromarray(painel)
        desenho = ImageDraw.Draw(pil)
        fonte = _fonte(14)
        for texto, px in zip(rotulos, posicoes):
            desenho.text((px, margem + 2), str(texto), fill=(255, 255, 255), font=fonte)
        painel = np.asarray(pil)
    return painel


def zoom_vizinho_mais_proximo(img, fator):
    """Zoom digital por replicação de pixels (vizinho mais próximo), do zero."""
    arr = np.asarray(img)
    if arr.dtype == bool:
        arr = binaria_para_uint8(arr)
    ampliada = np.repeat(np.repeat(arr, int(fator), axis=0), int(fator), axis=1)
    return ampliada


def recorte_centrado(img, centro_ij, meia_janela):
    """Recorta uma janela quadrada (2*meia_janela+1) centrada em (i, j),
    ajustando para não sair da imagem."""
    arr = np.asarray(img)
    alt, larg = arr.shape[:2]
    lado = 2 * int(meia_janela) + 1
    i0 = min(max(int(centro_ij[0]) - meia_janela, 0), max(alt - lado, 0))
    j0 = min(max(int(centro_ij[1]) - meia_janela, 0), max(larg - lado, 0))
    return arr[i0:i0 + lado, j0:j0 + lado], (i0, j0)


def janela_mais_densa(mascara_bool, lado_janela=41):
    """Encontra o centro (i, j) da janela lado x lado com mais pixels de borda.

    Usa imagem integral (somas acumuladas) — apenas álgebra do NumPy.
    """
    b = np.asarray(mascara_bool, dtype=np.float64)
    alt, larg = b.shape
    lado = min(int(lado_janela), alt, larg)
    integral = np.zeros((alt + 1, larg + 1))
    integral[1:, 1:] = np.cumsum(np.cumsum(b, axis=0), axis=1)
    somas = (integral[lado:, lado:] - integral[:-lado, lado:]
             - integral[lado:, :-lado] + integral[:-lado, :-lado])
    # entre janelas empatadas no máximo, escolhe a mais próxima do centro
    # mediano dos empates (centraliza a estrutura no recorte em vez de
    # encostá-la na borda)
    empates = np.argwhere(somas == somas.max())
    mediana = np.median(empates, axis=0)
    i0, j0 = empates[np.argmin(((empates - mediana) ** 2).sum(axis=1))]
    return int(i0) + lado // 2, int(j0) + lado // 2


def salvar_mapa(caminho, mapa):
    """Expande o histograma de um mapa real e salva como imagem."""
    salvar_imagem(caminho, expansao_histograma(mapa))


def salvar_painel(caminho, imagens, rotulos=None):
    salvar_imagem(caminho, lado_a_lado(imagens, rotulos))


def painel_kernels(kernels, rotulos=None, margem=6):
    """Monta uma tira com as máscaras (expansão de histograma individual)."""
    imgs = [expansao_histograma(k) for k in kernels]
    return lado_a_lado(imgs, rotulos, margem=margem)


def trimapa_classificacao(classes):
    """Visualização da classificação da histerese: forte=branco (255),
    fraco=cinza (128), suprimido=preto (0)."""
    c = np.asarray(classes)
    saida = np.zeros(c.shape, dtype=np.uint8)
    saida[c == 1] = 128
    saida[c == 2] = 255
    return saida
