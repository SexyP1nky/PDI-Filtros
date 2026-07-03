# -*- coding: utf-8 -*-
"""
Módulo A — Filtragem Espacial Genérica.

Implementa, do zero, a correlação bidimensional espacial para imagens em
escala de cinza (H, W) ou coloridas (H, W, C), sem usar funções prontas de
processamento de imagem (cv2.filter2D, scipy.ndimage etc.). Apenas álgebra
de matrizes do NumPy é utilizada, conforme permitido pela especificação.

Também carrega matrizes de filtros estáticos (ex.: Sobel, Gaussianas) a
partir de arquivos de configuração externos nos formatos .txt e .json.

Convenções:
  - x = colunas (cresce para a direita); y = linhas (cresce para BAIXO).
  - A operação é CORRELAÇÃO:  saida(i, j) = soma_{u,v} K(u, v) * I(i+u-ph, j+v-pw),
    com ph, pw = metade das dimensões (ímpares) do kernel.
  - Tratamento de borda: 'replicar' (repete o pixel da borda, padrão) ou
    'zeros' (preenche com zero).
"""

import json

import numpy as np


def correlacao2d(imagem, kernel, borda="replicar"):
    """Correlação bidimensional espacial implementada do zero.

    Parâmetros
    ----------
    imagem : ndarray (H, W) ou (H, W, C)
        Imagem em escala de cinza ou multicanal (ex.: RGB).
    kernel : ndarray (kh, kw)
        Máscara de filtro com dimensões ímpares.
    borda : str
        'replicar' (padrão) ou 'zeros'.

    Retorno
    -------
    ndarray float32 com o mesmo formato da imagem de entrada.
    """
    img = np.asarray(imagem, dtype=np.float32)
    k = np.asarray(kernel, dtype=np.float32)

    if k.ndim != 2:
        raise ValueError("o kernel deve ser uma matriz bidimensional")
    kh, kw = k.shape
    if kh % 2 == 0 or kw % 2 == 0:
        raise ValueError(f"as dimensões do kernel devem ser ímpares (recebido {kh}x{kw})")
    if img.ndim == 2:
        entrada_2d = True
        img = img[:, :, np.newaxis]
    elif img.ndim == 3:
        entrada_2d = False
    else:
        raise ValueError("a imagem deve ter formato (H, W) ou (H, W, C)")

    alt, larg, _ = img.shape
    ph, pw = kh // 2, kw // 2

    if borda == "replicar":
        pad = np.pad(img, ((ph, ph), (pw, pw), (0, 0)), mode="edge")
    elif borda == "zeros":
        pad = np.pad(img, ((ph, ph), (pw, pw), (0, 0)), mode="constant")
    else:
        raise ValueError(f"modo de borda desconhecido: {borda!r}")

    saida = np.zeros(img.shape, dtype=np.float32)
    temp = np.empty_like(saida)  # buffer reutilizado (evita realocação por coeficiente)
    # Soma deslocada: percorre os elementos do kernel e acumula a janela
    # correspondente da imagem — é a definição direta da correlação espacial,
    # vetorizada apenas em operações elemento a elemento do NumPy.
    for u in range(kh):
        for v in range(kw):
            coef = k[u, v]
            if coef == 0.0:
                continue
            np.multiply(pad[u:u + alt, v:v + larg, :], coef, out=temp)
            saida += temp

    return saida[:, :, 0] if entrada_2d else saida


def carregar_filtro_txt(caminho):
    """Lê uma matriz de filtro de um arquivo .txt.

    Formato: uma linha da matriz por linha do arquivo, valores separados por
    espaço (ou vírgula). Linhas vazias e linhas iniciadas por '#' são ignoradas.
    """
    linhas = []
    with open(caminho, "r", encoding="utf-8") as arq:
        for linha in arq:
            texto = linha.strip()
            if not texto or texto.startswith("#"):
                continue
            texto = texto.replace(",", " ")
            linhas.append([float(token) for token in texto.split()])
    if not linhas:
        raise ValueError(f"nenhuma linha de matriz encontrada em {caminho}")
    n_colunas = len(linhas[0])
    if any(len(l) != n_colunas for l in linhas):
        raise ValueError(f"linhas com quantidades diferentes de valores em {caminho}")
    return np.array(linhas, dtype=np.float64)


def carregar_filtro_json(caminho):
    """Lê uma matriz de filtro de um arquivo .json.

    Aceita uma lista de listas pura, ou um objeto com a chave "matriz" e a
    chave opcional "normalizar" (true => divide pela soma dos coeficientes,
    útil para núcleos gaussianos de suavização).
    """
    with open(caminho, "r", encoding="utf-8") as arq:
        dados = json.load(arq)

    if isinstance(dados, list):
        matriz = np.array(dados, dtype=np.float64)
        normalizar = False
    elif isinstance(dados, dict):
        if "matriz" not in dados:
            raise ValueError(f"chave 'matriz' ausente em {caminho}")
        matriz = np.array(dados["matriz"], dtype=np.float64)
        normalizar = bool(dados.get("normalizar", False))
    else:
        raise ValueError(f"conteúdo JSON inválido para filtro em {caminho}")

    if matriz.ndim != 2:
        raise ValueError(f"a matriz em {caminho} não é bidimensional")

    if normalizar:
        soma = matriz.sum()
        if abs(soma) < 1e-12:
            raise ValueError(f"não é possível normalizar filtro com soma zero ({caminho})")
        matriz = matriz / soma

    return matriz


def carregar_filtro(caminho):
    """Carrega uma matriz de filtro de arquivo .txt ou .json (pela extensão)."""
    caminho_baixo = str(caminho).lower()
    if caminho_baixo.endswith(".txt"):
        return carregar_filtro_txt(caminho)
    if caminho_baixo.endswith(".json"):
        return carregar_filtro_json(caminho)
    raise ValueError(f"extensão de arquivo de filtro não suportada: {caminho}")


def aplicar_filtro_de_arquivo(imagem, caminho, borda="replicar"):
    """Carrega um filtro estático de arquivo (.txt/.json) e o aplica à imagem."""
    return correlacao2d(imagem, carregar_filtro(caminho), borda=borda)
