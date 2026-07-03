# -*- coding: utf-8 -*-
"""
Módulo B — Gerador Paramétrico de Banco de Filtros de Gabor.

Carrega as propriedades do banco a partir de um arquivo JSON e gera as
máscaras dinamicamente, do zero (sem cv2.getGaborKernel).

Fórmula do filtro de Gabor (parte real), no sistema de coordenadas da
imagem (x = colunas -> direita, y = linhas -> baixo):

    x' =  x*cos(theta) + y*sin(theta)
    y' = -x*sin(theta) + y*cos(theta)
    g(x, y) = exp(-(x'^2 + gamma^2 * y'^2) / (2*sigma^2)) * cos(2*pi*x'/lambda + psi)

theta é a direção da VARIAÇÃO (da portadora senoidal); a borda detectada é
PERPENDICULAR a theta (ex.: theta = 0 -> bordas verticais). Essa mesma
convenção é usada na supressão de não-máximos (módulo bordas).

Parâmetros do JSON (aceita os nomes da especificação, com ou sem acentos,
maiúsculas ou minúsculas):
    tamanho_mascara   — dimensão ímpar do kernel quadrado (ex.: 31)
    sigma             — desvio padrão da envoltória gaussiana (escala espacial)
    lambda            — comprimento de onda do fator senoidal (frequência espacial)
    gamma             — proporção de aspecto espacial (elipsicidade)
    psi               — deslocamento de fase, em RADIANOS
    orientacoes_graus — lista de orientações em graus (ex.: [0, 22.5, ..., 157.5])
"""

import json
import unicodedata

import numpy as np

_CHAVES_OBRIGATORIAS = ("tamanho_mascara", "sigma", "lambda", "gamma",
                        "psi", "orientacoes_graus")


def _normalizar_chave(chave):
    """Remove acentos e baixa a caixa ('Orientações_graus' -> 'orientacoes_graus')."""
    sem_acentos = unicodedata.normalize("NFD", chave)
    sem_acentos = "".join(c for c in sem_acentos if unicodedata.category(c) != "Mn")
    return sem_acentos.strip().lower()


def gerar_kernel_gabor(tamanho_mascara, sigma, lambd, gamma, psi, theta_graus):
    """Gera uma máscara de Gabor (parte real) com os parâmetros dados."""
    tamanho_mascara = int(tamanho_mascara)
    if tamanho_mascara < 3 or tamanho_mascara % 2 == 0:
        raise ValueError(f"tamanho_mascara deve ser ímpar e >= 3 (recebido {tamanho_mascara})")
    if sigma <= 0 or lambd <= 0:
        raise ValueError("sigma e lambda devem ser positivos")

    meia = tamanho_mascara // 2
    # y cresce para baixo (linhas), x cresce para a direita (colunas)
    y, x = np.mgrid[-meia:meia + 1, -meia:meia + 1]
    x = x.astype(np.float64)
    y = y.astype(np.float64)

    theta = np.deg2rad(float(theta_graus))
    x_rot = x * np.cos(theta) + y * np.sin(theta)
    y_rot = -x * np.sin(theta) + y * np.cos(theta)

    envoltoria = np.exp(-(x_rot ** 2 + (gamma ** 2) * (y_rot ** 2)) / (2.0 * sigma ** 2))
    portadora = np.cos(2.0 * np.pi * x_rot / lambd + psi)
    return envoltoria * portadora


def gerar_banco_gabor(parametros):
    """Gera o banco a partir de um dicionário de parâmetros já normalizado.

    Retorna um dicionário com:
        'parametros'        — os parâmetros usados
        'orientacoes_graus' — lista de ângulos
        'kernels'           — lista de máscaras (ndarray), uma por orientação
    """
    faltando = [c for c in _CHAVES_OBRIGATORIAS if c not in parametros]
    if faltando:
        raise ValueError(f"parâmetros obrigatórios ausentes no banco de Gabor: {faltando}")

    orientacoes = [float(t) for t in parametros["orientacoes_graus"]]
    if not orientacoes:
        raise ValueError("a lista de orientações está vazia")

    kernels = [
        gerar_kernel_gabor(
            parametros["tamanho_mascara"],
            float(parametros["sigma"]),
            float(parametros["lambda"]),
            float(parametros["gamma"]),
            float(parametros["psi"]),
            theta,
        )
        for theta in orientacoes
    ]
    return {
        "parametros": dict(parametros),
        "orientacoes_graus": orientacoes,
        "kernels": kernels,
    }


def carregar_banco_gabor(caminho_json):
    """Carrega as propriedades do banco de um arquivo JSON e gera as máscaras."""
    with open(caminho_json, "r", encoding="utf-8") as arq:
        dados = json.load(arq)
    if not isinstance(dados, dict):
        raise ValueError(f"o arquivo de banco de Gabor deve ser um objeto JSON: {caminho_json}")

    parametros = {_normalizar_chave(k): v for k, v in dados.items()}
    return gerar_banco_gabor(parametros)


def salvar_banco_gabor(caminho_json, tamanho_mascara, sigma, lambd, gamma, psi,
                       orientacoes_graus, nome=None, descricao=None):
    """Escreve um arquivo JSON de banco de Gabor (usado pelos experimentos
    para gerar as configurações das varreduras paramétricas)."""
    dados = {}
    if nome:
        dados["nome"] = nome
    if descricao:
        dados["descricao"] = descricao
    dados.update({
        "tamanho_mascara": int(tamanho_mascara),
        "sigma": float(sigma),
        "lambda": float(lambd),
        "gamma": float(gamma),
        "psi": float(psi),
        "orientacoes_graus": list(orientacoes_graus),
    })
    with open(caminho_json, "w", encoding="utf-8") as arq:
        json.dump(dados, arq, ensure_ascii=False, indent=2)
    return caminho_json
