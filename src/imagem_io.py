# -*- coding: utf-8 -*-
"""
Entrada/saída de imagens.

Conforme a especificação, bibliotecas externas (Pillow) são usadas APENAS
para abrir e salvar imagens. Todo o processamento é feito nos módulos
próprios (filtragem, gabor, bordas).

A conversão para tons de cinza é feita manualmente por
Y = 0.299*R + 0.587*G + 0.114*B, como exigido no roteiro de experimentos.
"""

import numpy as np
from PIL import Image


def carregar_imagem_rgb(caminho):
    """Abre uma imagem e devolve um array float32 (H, W, 3) na faixa 0..255.

    Imagens RGBA com transparência real são compostas sobre fundo BRANCO
    (rgb_final = alfa*rgb + (1-alfa)*branco); imagens com alfa totalmente
    opaco apenas descartam o canal alfa. Imagens em escala de cinza ou com
    paleta são convertidas para RGB pelo Pillow (apenas decodificação).
    """
    im = Image.open(caminho)
    if im.mode == "RGBA":
        dados = np.asarray(im, dtype=np.float32)
        rgb = dados[:, :, :3]
        alfa = dados[:, :, 3:4] / 255.0
        return rgb * alfa + 255.0 * (1.0 - alfa)
    if im.mode != "RGB":
        im = im.convert("RGB")
    return np.asarray(im, dtype=np.float32)


def converter_para_cinza(rgb):
    """Conversão manual para tons de cinza: Y = 0.299R + 0.587G + 0.114B."""
    rgb = np.asarray(rgb, dtype=np.float32)
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("esperada imagem RGB com formato (H, W, 3)")
    return (0.299 * rgb[:, :, 0]
            + 0.587 * rgb[:, :, 1]
            + 0.114 * rgb[:, :, 2]).astype(np.float32)


def salvar_imagem(caminho, array_uint8):
    """Salva um array uint8 (H, W) em escala de cinza ou (H, W, 3) RGB."""
    arr = np.asarray(array_uint8)
    if arr.dtype != np.uint8:
        raise ValueError("salvar_imagem espera um array uint8 "
                         "(use visualizacao.expansao_histograma antes)")
    Image.fromarray(arr).save(caminho)
