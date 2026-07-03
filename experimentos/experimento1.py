# -*- coding: utf-8 -*-
"""
Experimento 1 — Análise de Sensibilidade Paramétrica do Gabor tradicional
(escalar, sobre tons de cinza) e do Modificado (vetorial Gabor–Di Zenzo).

Para cada imagem fornecida:
  - Varredura de lambda (comprimento de onda): isolar bordas de alta
    frequência (texturas finas) vs baixa frequência (macrocontornos).
  - Varredura de sigma (escala do filtro), incluindo um sigma EXCESSIVO
    (sigma = 12, máscara 73x73) para responder à pergunta da especificação
    sobre cenários texturizados.
  - Comparação direta Gabor tradicional (cinza) vs modificado (cor).

Demonstrações complementares (parâmetros restantes do banco):
  - Efeito de psi (fase): par vs ímpar -> linha dupla vs linha única.
  - Efeito de gamma (elipsicidade) nas magnitudes.

Cada configuração de banco é ESCRITA em config/experimentos/*.json e
recarregada via Módulo B (carregar_banco_gabor), exercitando o caminho
completo "arquivo de configuração -> máscaras dinâmicas" da especificação.

Saídas: resultados/experimento1/<imagem>/*.png e log_experimento1.json.
Uso:    python experimentos\\experimento1.py
"""

import math
import os
import time

import numpy as np

import comum
from bordas import supressao_nao_maximos
from canny_modificado import resposta_gabor_dizenzo
from gabor import carregar_banco_gabor, gerar_kernel_gabor, salvar_banco_gabor
from imagem_io import carregar_imagem_rgb, converter_para_cinza, salvar_imagem
from visualizacao import (expansao_histograma, lado_a_lado, salvar_painel)

PSI_IMPAR = -math.pi / 2.0
GAMMA_PADRAO = 0.5

# (tamanho_mascara, sigma, lambda) — máscara dimensionada para ~6*sigma
VARREDURA_LAMBDA = [(31, 4.0, 4.0), (31, 4.0, 8.0), (31, 4.0, 16.0)]
VARREDURA_SIGMA = [(13, 2.0, 8.0), (31, 4.0, 8.0), (73, 12.0, 8.0)]

LOG = []


def caminho_config(tam, sigma, lambd, gamma, psi):
    chave = (f"gabor_t{comum.fmt(tam)}_s{comum.fmt(sigma)}_l{comum.fmt(lambd)}"
             f"_g{comum.fmt(gamma)}_psi{comum.fmt(round(psi, 4))}")
    return os.path.join(comum.PASTA_CONFIG_EXP, chave + ".json")


def obter_banco(tam, sigma, lambd, gamma=GAMMA_PADRAO, psi=PSI_IMPAR):
    """Escreve (se preciso) o JSON da configuração e carrega via Módulo B."""
    caminho = caminho_config(tam, sigma, lambd, gamma, psi)
    if not os.path.exists(caminho):
        salvar_banco_gabor(
            caminho, tam, sigma, lambd, gamma, psi, comum.ORIENTACOES_PADRAO,
            nome=os.path.basename(caminho),
            descricao="Configuração gerada pelo Experimento 1 (varredura paramétrica).")
    return carregar_banco_gabor(caminho)


class Executor:
    """Calcula (e memoriza) mapas de magnitude por (configuração, método)."""

    def __init__(self, nome, rgb):
        self.nome = nome
        self.rgb = rgb
        self.cinza = converter_para_cinza(rgb)
        self.pasta = comum.garantir_pasta(
            os.path.join(comum.PASTA_RESULTADOS, "experimento1", nome))
        self.cache = {}

    def magnitude(self, metodo, tam, sigma, lambd, gamma=GAMMA_PADRAO, psi=PSI_IMPAR):
        chave = (metodo, tam, sigma, lambd, gamma, round(psi, 6))
        if chave in self.cache:
            return self.cache[chave]
        banco = obter_banco(tam, sigma, lambd, gamma, psi)
        entrada = self.rgb if metodo == "modificado" else self.cinza
        inicio = time.perf_counter()
        mag, ori = resposta_gabor_dizenzo(entrada, banco)
        duracao = time.perf_counter() - inicio
        nome_mapa = (f"mag_t{comum.fmt(tam)}_s{comum.fmt(sigma)}_l{comum.fmt(lambd)}"
                     f"_g{comum.fmt(gamma)}_psi{comum.fmt(round(psi, 4))}_{metodo}.png")
        salvar_imagem(os.path.join(self.pasta, nome_mapa), expansao_histograma(mag))
        LOG.append({
            "imagem": self.nome, "metodo": metodo,
            "tamanho_mascara": tam, "sigma": sigma, "lambda": lambd,
            "gamma": gamma, "psi": round(psi, 6),
            "mag_min": float(mag.min()), "mag_max": float(mag.max()),
            "mag_media": float(mag.mean()), "tempo_s": round(duracao, 2),
            "mapa": nome_mapa,
        })
        print(f"  [{self.nome}] {metodo:11s} masc={tam:2d} sigma={sigma:g} "
              f"lambda={lambd:g} gamma={gamma:g} psi={round(psi,3):g} "
              f"-> max={mag.max():.1f} ({duracao:.1f}s)", flush=True)
        self.cache[chave] = (mag, ori)
        return self.cache[chave]


def varreduras_principais(executor):
    """Varreduras de lambda e sigma para os dois métodos + painéis."""
    for metodo in ("tradicional", "modificado"):
        mapas = []
        rotulos = []
        for tam, sigma, lambd in VARREDURA_LAMBDA:
            mag, _ = executor.magnitude(metodo, tam, sigma, lambd)
            mapas.append(expansao_histograma(mag))
            rotulos.append(f"lambda={lambd:g} (sigma={sigma:g}) max={mag.max():.0f}")
        salvar_painel(os.path.join(executor.pasta, f"painel_lambda_{metodo}.png"),
                      mapas, rotulos)

        mapas = []
        rotulos = []
        for tam, sigma, lambd in VARREDURA_SIGMA:
            mag, _ = executor.magnitude(metodo, tam, sigma, lambd)
            mapas.append(expansao_histograma(mag))
            rotulos.append(f"sigma={sigma:g} masc={tam} (lambda={lambd:g}) max={mag.max():.0f}")
        salvar_painel(os.path.join(executor.pasta, f"painel_sigma_{metodo}.png"),
                      mapas, rotulos)

    # comparação escalar vs vetorial na configuração padrão (31, 4, 8)
    mag_trad, _ = executor.magnitude("tradicional", 31, 4.0, 8.0)
    mag_mod, _ = executor.magnitude("modificado", 31, 4.0, 8.0)
    original = np.clip(np.round(executor.rgb), 0, 255).astype(np.uint8)
    salvar_painel(
        os.path.join(executor.pasta, "painel_tradicional_vs_modificado.png"),
        [original, expansao_histograma(mag_trad), expansao_histograma(mag_mod)],
        ["original",
         f"Gabor tradicional (cinza) max={mag_trad.max():.0f}",
         f"Gabor-Di Zenzo (cor) max={mag_mod.max():.0f}"])


def demo_psi(executor):
    """Fase par (psi=0) vs ímpar (psi=-pi/2): linha dupla vs linha única."""
    paineis = []
    rotulos = []
    for psi, nome_psi in ((0.0, "psi=0 (par)"), (PSI_IMPAR, "psi=-pi/2 (impar)")):
        mag, ori = executor.magnitude("modificado", 31, 4.0, 8.0, psi=psi)
        nms = supressao_nao_maximos(mag, ori)
        paineis.extend([expansao_histograma(mag), expansao_histograma(nms)])
        rotulos.extend([f"magnitude {nome_psi}", f"pos-NMS {nome_psi}"])
    salvar_painel(os.path.join(executor.pasta, "painel_psi.png"), paineis, rotulos)


def demo_gamma(executor):
    """Efeito da elipsicidade gamma na magnitude (modificado)."""
    mapas = []
    rotulos = []
    for gamma in (0.25, 0.5, 1.0):
        mag, _ = executor.magnitude("modificado", 31, 4.0, 8.0, gamma=gamma)
        mapas.append(expansao_histograma(mag))
        rotulos.append(f"gamma={gamma:g} max={mag.max():.0f}")
    salvar_painel(os.path.join(executor.pasta, "painel_gamma.png"), mapas, rotulos)


def salvar_visualizacao_kernels():
    """Tiras de máscaras para o relatório (expansão de histograma + zoom 4x
    para os rótulos caberem sobre cada máscara)."""
    from visualizacao import zoom_vizinho_mais_proximo
    pasta = comum.garantir_pasta(os.path.join(comum.PASTA_RESULTADOS, "experimento1"))

    def ampliar(kernel):
        return zoom_vizinho_mais_proximo(expansao_histograma(kernel), 4)

    banco = carregar_banco_gabor(comum.CAMINHO_BANCO_PADRAO)
    imgs = [ampliar(k) for k in banco["kernels"]]
    rotulos = [f"theta={t:g}" for t in banco["orientacoes_graus"]]
    salvar_imagem(os.path.join(pasta, "kernels_banco_padrao.png"),
                  lado_a_lado(imgs, rotulos))

    imgs, rotulos = [], []
    for tam, sigma, lambd in VARREDURA_LAMBDA:
        k = gerar_kernel_gabor(tam, sigma, lambd, GAMMA_PADRAO, PSI_IMPAR, 0.0)
        imgs.append(ampliar(k))
        rotulos.append(f"lambda={lambd:g}")
    salvar_imagem(os.path.join(pasta, "kernels_varredura_lambda.png"),
                  lado_a_lado(imgs, rotulos))

    imgs, rotulos = [], []
    for tam, sigma, lambd in VARREDURA_SIGMA:
        k = gerar_kernel_gabor(tam, sigma, lambd, GAMMA_PADRAO, PSI_IMPAR, 0.0)
        imgs.append(ampliar(k))
        rotulos.append(f"sigma={sigma:g} masc={tam}")
    salvar_imagem(os.path.join(pasta, "kernels_varredura_sigma.png"),
                  lado_a_lado(imgs, rotulos))

    imgs = [ampliar(gerar_kernel_gabor(31, 4.0, 8.0, GAMMA_PADRAO, 0.0, 0.0)),
            ampliar(gerar_kernel_gabor(31, 4.0, 8.0, GAMMA_PADRAO, PSI_IMPAR, 0.0))]
    salvar_imagem(os.path.join(pasta, "kernels_psi.png"),
                  lado_a_lado(imgs, ["psi=0 (par)", "psi=-pi/2 (impar)"]))


def principal():
    comum.garantir_pasta(comum.PASTA_CONFIG_EXP)
    inicio_total = time.time()
    salvar_visualizacao_kernels()

    for nome_arquivo in comum.IMAGENS:
        nome = comum.nome_base(nome_arquivo)
        print(f"== Experimento 1: {nome} ==", flush=True)
        executor = Executor(nome, carregar_imagem_rgb(comum.caminho_imagem(nome_arquivo)))
        varreduras_principais(executor)
        if nome in ("GrayAndMagenta", "VintageCar"):
            demo_psi(executor)
        if nome == "FCBarcelona":
            demo_gamma(executor)

    caminho_log = os.path.join(comum.PASTA_RESULTADOS, "experimento1",
                               "log_experimento1.json")
    comum.salvar_log(caminho_log, LOG)
    print(f"Experimento 1 concluído em {(time.time() - inicio_total)/60:.1f} min. "
          f"Log: {caminho_log}", flush=True)


if __name__ == "__main__":
    principal()
