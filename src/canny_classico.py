# -*- coding: utf-8 -*-
"""
Canny clássico (escalar), implementado do zero.

Pipeline:
  1. Conversão manual para tons de cinza: Y = 0.299R + 0.587G + 0.114B.
  2. Suavização gaussiana — máscara estática carregada de arquivo de
     configuração (.json) e aplicada pela correlação própria (Módulo A).
  3. Gradientes por Sobel — máscaras carregadas de arquivos .txt (Módulo A).
  4. Magnitude (norma L2 de gx, gy) e direção do gradiente (atan2).
  5. Supressão de Não-Máximos guiada pela direção do gradiente.
  6. Limiarização por histerese (fortes/fracos/suprimidos + conectividade).
"""

import numpy as np

from bordas import (classificar_bordas, histerese, limiares_por_percentil,
                    supressao_nao_maximos)
from filtragem import aplicar_filtro_de_arquivo
from imagem_io import converter_para_cinza


def canny_classico(rgb, caminho_gaussiana, caminho_sobel_x, caminho_sobel_y,
                   t_low=None, t_high=None,
                   percentil_forte=90.0, razao_fraco=0.4, borda="replicar"):
    """Executa o Canny clássico sobre uma imagem RGB (float, 0..255).

    Se t_low/t_high não forem dados, são escolhidos automaticamente por
    percentil sobre os máximos do NMS (ver bordas.limiares_por_percentil).

    Retorna um dicionário com todos os mapas intermediários e os limiares.
    """
    cinza = converter_para_cinza(rgb)
    suavizada = aplicar_filtro_de_arquivo(cinza, caminho_gaussiana, borda=borda)
    gx = aplicar_filtro_de_arquivo(suavizada, caminho_sobel_x, borda=borda)
    gy = aplicar_filtro_de_arquivo(suavizada, caminho_sobel_y, borda=borda)

    magnitude = np.sqrt(gx.astype(np.float64) ** 2 + gy.astype(np.float64) ** 2)
    magnitude = magnitude.astype(np.float32)
    orientacao = np.rad2deg(np.arctan2(gy, gx))  # direção do gradiente

    nms = supressao_nao_maximos(magnitude, orientacao)

    if t_low is None or t_high is None:
        t_low, t_high = limiares_por_percentil(nms, percentil_forte, razao_fraco)
    classes = classificar_bordas(nms, t_low, t_high)
    bordas_finais = histerese(nms, t_low, t_high)

    return {
        "cinza": cinza,
        "suavizada": suavizada,
        "gx": gx,
        "gy": gy,
        "magnitude": magnitude,
        "orientacao": orientacao,
        "nms": nms,
        "classes": classes,
        "t_low": float(t_low),
        "t_high": float(t_high),
        "bordas": bordas_finais,
    }
