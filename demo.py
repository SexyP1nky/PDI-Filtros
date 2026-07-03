# -*- coding: utf-8 -*-
"""
Demonstração ao vivo (apresentação): processa UMA imagem qualquer com o
Canny clássico e/ou o Canny Modificado Gabor-Di Zenzo e salva os painéis
em resultados/demo/<nome_da_imagem>/.

Exemplos:
  python demo.py GrayAndMagenta.png
  python demo.py Zebra.png --metodo modificado
  python demo.py GrayAndMagenta.png --banco config\\experimentos\\gabor_t31_s4_l16_g0.5_psim1.5708.json
  python demo.py FCBarcelona.png --thigh 5000
  python demo.py C:\\qualquer\\foto.jpg
"""

import argparse
import os
import sys
import time

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(RAIZ, "src"))

import numpy as np

from bordas import fracao_blocos_2x2_cheios
from canny_classico import canny_classico
from canny_modificado import canny_modificado
from imagem_io import carregar_imagem_rgb
from visualizacao import (binaria_para_uint8, expansao_histograma,
                          janela_mais_densa, recorte_centrado, salvar_painel,
                          trimapa_classificacao, zoom_vizinho_mais_proximo)

MEIA_JANELA = 20  # recorte 41x41
FATOR_ZOOM = 8


def fmt(valor):
    return "inf" if np.isinf(valor) else f"{valor:.1f}"


def resumo(rotulo, resultado, duracao):
    frac, n_blocos = fracao_blocos_2x2_cheios(resultado["bordas"])
    print(f"  {rotulo}: Tlow={fmt(resultado['t_low'])}  Thigh={fmt(resultado['t_high'])}  "
          f"bordas={int(resultado['bordas'].sum())} px  "
          f"blocos 2x2 cheios={n_blocos} ({frac:.4%})  [{duracao:.1f}s]")


def painel_zoom(pasta, prefixo, resultado):
    """Zoom 8x (vizinho mais próximo) na janela com mais bordas."""
    if not resultado["bordas"].any():
        print(f"  ({prefixo}: sem bordas — zoom não gerado)")
        return
    centro = janela_mais_densa(resultado["bordas"], 2 * MEIA_JANELA + 1)
    rec_mag, _ = recorte_centrado(resultado["magnitude"], centro, MEIA_JANELA)
    rec_nms, _ = recorte_centrado(resultado["nms"], centro, MEIA_JANELA)
    rec_bor, _ = recorte_centrado(resultado["bordas"], centro, MEIA_JANELA)
    salvar_painel(
        os.path.join(pasta, f"painel_zoom_{prefixo}.png"),
        [zoom_vizinho_mais_proximo(expansao_histograma(rec_mag), FATOR_ZOOM),
         zoom_vizinho_mais_proximo(expansao_histograma(rec_nms), FATOR_ZOOM),
         zoom_vizinho_mais_proximo(binaria_para_uint8(rec_bor), FATOR_ZOOM)],
        [f"magnitude (zoom {FATOR_ZOOM}x)", f"pos-NMS (zoom {FATOR_ZOOM}x)",
         f"bordas finais (zoom {FATOR_ZOOM}x)"])


def principal():
    ap = argparse.ArgumentParser(
        description="Demo: Canny clássico x Canny Modificado Gabor-Di Zenzo em uma imagem.")
    ap.add_argument("imagem", help="caminho da imagem (jpg/png/webp/...)")
    ap.add_argument("--metodo", choices=["ambos", "modificado", "classico"],
                    default="ambos")
    ap.add_argument("--banco",
                    default=os.path.join(RAIZ, "config", "gabor_banco_padrao.json"),
                    help="arquivo JSON do banco de Gabor (Módulo B)")
    ap.add_argument("--tlow", type=float, default=None,
                    help="limiar inferior manual (padrão: automático)")
    ap.add_argument("--thigh", type=float, default=None,
                    help="limiar superior manual (padrão: automático)")
    ap.add_argument("--saida", default=None, help="pasta de saída dos painéis")
    args = ap.parse_args()

    # se só um limiar manual for dado, deriva o outro pela razão padrão 0.4
    t_low, t_high = args.tlow, args.thigh
    if (t_low is None) != (t_high is None):
        if t_high is None:
            t_high = t_low / 0.4
        else:
            t_low = 0.4 * t_high

    rgb = carregar_imagem_rgb(args.imagem)
    nome = os.path.splitext(os.path.basename(args.imagem))[0]
    pasta = args.saida or os.path.join(RAIZ, "resultados", "demo", nome)
    os.makedirs(pasta, exist_ok=True)
    original = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    print(f"Imagem: {args.imagem}  ({rgb.shape[0]}x{rgb.shape[1]})  "
          f"banco: {os.path.basename(args.banco)}")

    res_mod = res_cla = None

    if args.metodo in ("ambos", "modificado"):
        inicio = time.perf_counter()
        res_mod = canny_modificado(rgb, args.banco, t_low=t_low, t_high=t_high)
        resumo("modificado", res_mod, time.perf_counter() - inicio)
        salvar_painel(
            os.path.join(pasta, "painel_modificado.png"),
            [expansao_histograma(res_mod["magnitude"]),
             expansao_histograma(res_mod["nms"]),
             trimapa_classificacao(res_mod["classes"]),
             binaria_para_uint8(res_mod["bordas"])],
            ["magnitude Di Zenzo", "pos-NMS (afinado)",
             f"classes Tl={fmt(res_mod['t_low'])} Th={fmt(res_mod['t_high'])}",
             f"bordas finais ({int(res_mod['bordas'].sum())} px)"])
        painel_zoom(pasta, "mod", res_mod)

    if args.metodo in ("ambos", "classico"):
        cfg = os.path.join(RAIZ, "config")
        inicio = time.perf_counter()
        res_cla = canny_classico(rgb,
                                 os.path.join(cfg, "gaussiana_5x5.json"),
                                 os.path.join(cfg, "sobel_x.txt"),
                                 os.path.join(cfg, "sobel_y.txt"),
                                 t_low=t_low, t_high=t_high)
        resumo("classico  ", res_cla, time.perf_counter() - inicio)
        salvar_painel(
            os.path.join(pasta, "painel_classico.png"),
            [np.clip(np.round(res_cla["cinza"]), 0, 255).astype(np.uint8),
             expansao_histograma(res_cla["magnitude"]),
             expansao_histograma(res_cla["nms"]),
             binaria_para_uint8(res_cla["bordas"])],
            ["Y (cinza manual)", "magnitude Sobel", "pos-NMS",
             f"bordas finais ({int(res_cla['bordas'].sum())} px)"])
        painel_zoom(pasta, "cla", res_cla)

    if res_mod is not None and res_cla is not None:
        salvar_painel(
            os.path.join(pasta, "painel_comparacao.png"),
            [original,
             binaria_para_uint8(res_cla["bordas"]),
             binaria_para_uint8(res_mod["bordas"])],
            ["original",
             f"Canny classico ({int(res_cla['bordas'].sum())} px)",
             f"Canny modificado ({int(res_mod['bordas'].sum())} px)"])

    print(f"Painéis salvos em: {pasta}")


if __name__ == "__main__":
    principal()
