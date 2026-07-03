# -*- coding: utf-8 -*-
"""
Módulo C — Canny Modificado Gabor–Di Zenzo (abordagem vetorial para cor).

Fluxo por pixel (i, j), conforme a especificação:
  1. Filtragem independente por orientação: para cada ângulo theta do banco,
     a máscara de Gabor é aplicada aos canais R, G e B separadamente, via
     correlação própria do Módulo A.
  2. Fusão de canais (norma L2):
         Magn(i, j, theta) = sqrt(R_t(i,j)^2 + G_t(i,j)^2 + B_t(i,j)^2)
  3. Redução por máximo: Magnitude_Final(i, j) = max_theta Magn(i, j, theta);
     a Orientação Final é o ângulo do filtro que gerou esse máximo.
  4. Afinamento (NMS) guiado pela matriz de Orientação Final, comparando o
     pixel com os vizinhos ortogonais à borda (ao longo de theta).
  5. Limiarização por histerese (fortes / fracos / suprimidos +
     análise de conectividade).

A mesma função de resposta serve para o "Gabor tradicional" (escalar): basta
passar a imagem em tons de cinza — a norma L2 de um único canal é o valor
absoluto da resposta. Isso permite comparar diretamente o efeito de
processar a cor de forma vetorial (Experimento 1).
"""

import numpy as np

from bordas import (classificar_bordas, histerese, limiares_por_percentil,
                    supressao_nao_maximos)
from filtragem import correlacao2d
from gabor import carregar_banco_gabor


def resposta_gabor_dizenzo(imagem, banco, borda="replicar"):
    """Etapas 1–3 do Módulo C: filtragem por orientação, fusão L2 e redução
    por máximo.

    'imagem' pode ser (H, W, 3) RGB — fusão vetorial de Di Zenzo — ou (H, W)
    em tons de cinza — versão escalar tradicional. Retorna
    (magnitude_final, orientacao_final_graus).
    """
    img = np.asarray(imagem, dtype=np.float32)
    if img.ndim == 2:
        img = img[:, :, np.newaxis]

    magnitude_final = np.zeros(img.shape[:2], dtype=np.float32)
    orientacao_final = np.zeros(img.shape[:2], dtype=np.float32)

    for theta, kernel in zip(banco["orientacoes_graus"], banco["kernels"]):
        # Etapa 1: mesma máscara aplicada a cada canal separadamente (Módulo A)
        resposta = correlacao2d(img, kernel, borda=borda)
        # Etapa 2: fusão dos canais pela norma Euclidiana
        magn_theta = np.sqrt(np.sum(resposta ** 2, axis=2))
        # Etapa 3: redução por máximo (magnitude e ângulo vencedor)
        vence = magn_theta > magnitude_final
        magnitude_final[vence] = magn_theta[vence]
        orientacao_final[vence] = theta

    return magnitude_final, orientacao_final


def canny_modificado(rgb, banco_ou_caminho, t_low=None, t_high=None,
                     percentil_forte=90.0, razao_fraco=0.4, borda="replicar"):
    """Executa o pipeline completo do Canny Modificado Gabor–Di Zenzo.

    'banco_ou_caminho' pode ser o caminho de um arquivo JSON (Módulo B) ou um
    banco já carregado. Se t_low/t_high não forem dados, são escolhidos por
    percentil sobre os máximos do NMS.
    """
    if isinstance(banco_ou_caminho, (str, bytes)) or hasattr(banco_ou_caminho, "__fspath__"):
        banco = carregar_banco_gabor(banco_ou_caminho)
    else:
        banco = banco_ou_caminho

    magnitude, orientacao = resposta_gabor_dizenzo(rgb, banco, borda=borda)

    # Etapa 4: afinamento guiado pela Orientação Final
    nms = supressao_nao_maximos(magnitude, orientacao)

    # Etapa 5: histerese
    if t_low is None or t_high is None:
        t_low, t_high = limiares_por_percentil(nms, percentil_forte, razao_fraco)
    classes = classificar_bordas(nms, t_low, t_high)
    bordas_finais = histerese(nms, t_low, t_high)

    return {
        "banco": banco,
        "magnitude": magnitude,
        "orientacao": orientacao,
        "nms": nms,
        "classes": classes,
        "t_low": float(t_low),
        "t_high": float(t_high),
        "bordas": bordas_finais,
    }
