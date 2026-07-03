# -*- coding: utf-8 -*-
"""Utilidades compartilhadas pelos scripts de experimentos."""

import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))

PASTA_CONFIG = os.path.join(RAIZ, "config")
PASTA_CONFIG_EXP = os.path.join(PASTA_CONFIG, "experimentos")
PASTA_RESULTADOS = os.path.join(RAIZ, "resultados")

IMAGENS = [
    "Bear.jpg",
    "FCBarcelona.png",
    "GrayAndMagenta.png",
    "PlacaMercosul.webp",
    "VintageCar.png",
    "Zebra.png",
]

CAMINHO_GAUSSIANA = os.path.join(PASTA_CONFIG, "gaussiana_5x5.json")
CAMINHO_SOBEL_X = os.path.join(PASTA_CONFIG, "sobel_x.txt")
CAMINHO_SOBEL_Y = os.path.join(PASTA_CONFIG, "sobel_y.txt")
CAMINHO_BANCO_PADRAO = os.path.join(PASTA_CONFIG, "gabor_banco_padrao.json")

ORIENTACOES_PADRAO = [0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5]


def nome_base(nome_arquivo):
    return os.path.splitext(os.path.basename(nome_arquivo))[0]


def caminho_imagem(nome_arquivo):
    return os.path.join(RAIZ, nome_arquivo)


def garantir_pasta(caminho):
    os.makedirs(caminho, exist_ok=True)
    return caminho


def salvar_log(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as arq:
        json.dump(dados, arq, ensure_ascii=False, indent=2)


def fmt(valor):
    """Formata números para nomes de arquivo (4 -> '4', 22.5 -> '22.5')."""
    return f"{valor:g}".replace("-", "m")
