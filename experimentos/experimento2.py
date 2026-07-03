# -*- coding: utf-8 -*-
"""
Experimento 2 — Validação do Afinamento (NMS) e da Histerese.

Para cada imagem fornecida:
  - Pipeline completo do Canny Modificado Gabor–Di Zenzo (banco padrão):
    painel lado a lado com o mapa de magnitudes de Di Zenzo, o resultado
    pós-NMS, a classificação fortes/fracos/suprimidos e as bordas finais.
  - Pipeline completo do Canny clássico (Y manual -> Gaussiana -> Sobel ->
    NMS -> histerese), com os mesmos painéis.
  - Zoom digital (vizinho mais próximo, 8x) na janela com maior densidade
    de bordas, demonstrando a espessura de exatamente 1 pixel.
  - Painel de comparação Canny padrão vs modificado.
  - Métricas para justificar limiares: Thigh/Tlow escolhidos (percentil 90
    pós-NMS + razão 0.4), contagens de fortes/fracos, fração de blocos 2x2
    cheios (verificação quantitativa do afinamento).
  - Para GrayAndMagenta.png: perfil horizontal da linha central da
    magnitude (clássico vs modificado) — gráfico apenas para o relatório.

Saídas: resultados/experimento2/<imagem>/*.png e log_experimento2.json.
Uso:    python experimentos\\experimento2.py
"""

import os
import time

import numpy as np
from PIL import Image, ImageDraw

import comum
from bordas import fracao_blocos_2x2_cheios
from canny_classico import canny_classico
from canny_modificado import canny_modificado
from imagem_io import carregar_imagem_rgb, salvar_imagem
from visualizacao import (binaria_para_uint8, expansao_histograma,
                          janela_mais_densa, lado_a_lado, recorte_centrado,
                          salvar_painel, trimapa_classificacao,
                          zoom_vizinho_mais_proximo)

MEIA_JANELA_ZOOM = 20   # recorte 41x41
FATOR_ZOOM = 8

LOG = []


def fmt_limiar(valor):
    return "inf" if np.isinf(valor) else f"{valor:.1f}"


def marcar_janela(bordas_bool, centro, meia, caminho):
    """Salva as bordas com um retângulo vermelho na janela do zoom."""
    base = binaria_para_uint8(bordas_bool)
    pil = Image.fromarray(np.stack([base] * 3, axis=2))
    desenho = ImageDraw.Draw(pil)
    i, j = centro
    desenho.rectangle([j - meia, i - meia, j + meia, i + meia],
                      outline=(255, 64, 64), width=2)
    pil.save(caminho)


def zooms(pasta, prefixo, magnitude, nms, bordas, centro):
    """Recortes ampliados (8x) de magnitude, pós-NMS e bordas finais."""
    recorte_mag, _ = recorte_centrado(magnitude, centro, MEIA_JANELA_ZOOM)
    recorte_nms, _ = recorte_centrado(nms, centro, MEIA_JANELA_ZOOM)
    recorte_bor, _ = recorte_centrado(bordas, centro, MEIA_JANELA_ZOOM)

    z_mag = zoom_vizinho_mais_proximo(expansao_histograma(recorte_mag), FATOR_ZOOM)
    z_nms = zoom_vizinho_mais_proximo(expansao_histograma(recorte_nms), FATOR_ZOOM)
    z_bor = zoom_vizinho_mais_proximo(binaria_para_uint8(recorte_bor), FATOR_ZOOM)

    salvar_imagem(os.path.join(pasta, f"zoom_{prefixo}_magnitude.png"), z_mag)
    salvar_imagem(os.path.join(pasta, f"zoom_{prefixo}_nms.png"), z_nms)
    salvar_imagem(os.path.join(pasta, f"zoom_{prefixo}_bordas.png"), z_bor)
    salvar_painel(os.path.join(pasta, f"painel_zoom_{prefixo}.png"),
                  [z_mag, z_nms, z_bor],
                  ["magnitude (zoom 8x)", "pos-NMS (zoom 8x)", "bordas finais (zoom 8x)"])


def metricas(resultado):
    nms = resultado["nms"]
    bordas = resultado["bordas"]
    classes = resultado["classes"]
    frac_2x2, n_2x2 = fracao_blocos_2x2_cheios(bordas)
    return {
        "t_low": float(resultado["t_low"]),
        "t_high": float(resultado["t_high"]),
        "pixels_candidatos_nms": int((nms > 0).sum()),
        "pixels_fortes": int((classes == 2).sum()),
        "pixels_fracos": int((classes == 1).sum()),
        "pixels_borda_final": int(bordas.sum()),
        "fracao_blocos_2x2_cheios": round(frac_2x2, 6),
        "blocos_2x2_cheios": n_2x2,
        "mag_max": float(resultado["magnitude"].max()),
    }


def perfil_gray_and_magenta(pasta, rgb, res_cla, res_mod):
    """Perfil horizontal (linha central) da magnitude: clássico vs modificado."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  matplotlib indisponível — perfil não gerado", flush=True)
        return None
    linha = rgb.shape[0] // 2
    fig, eixos = plt.subplots(1, 2, figsize=(11, 3.5))
    eixos[0].plot(res_cla["magnitude"][linha, :], color="tab:gray")
    eixos[0].set_title(f"Canny clássico — |gradiente| na linha {linha}")
    eixos[0].set_xlabel("coluna")
    eixos[0].set_ylabel("magnitude")
    eixos[1].plot(res_mod["magnitude"][linha, :], color="tab:purple")
    eixos[1].set_title(f"Modificado — magnitude Di Zenzo na linha {linha}")
    eixos[1].set_xlabel("coluna")
    fig.tight_layout()
    caminho = os.path.join(pasta, "perfil_linha_central.png")
    fig.savefig(caminho, dpi=120)
    plt.close(fig)
    return caminho


def processar_imagem(nome_arquivo):
    nome = comum.nome_base(nome_arquivo)
    print(f"== Experimento 2: {nome} ==", flush=True)
    pasta = comum.garantir_pasta(
        os.path.join(comum.PASTA_RESULTADOS, "experimento2", nome))
    rgb = carregar_imagem_rgb(comum.caminho_imagem(nome_arquivo))
    original = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    salvar_imagem(os.path.join(pasta, "01_original.png"), original)

    inicio = time.perf_counter()
    res_mod = canny_modificado(rgb, comum.CAMINHO_BANCO_PADRAO)
    t_mod = time.perf_counter() - inicio
    inicio = time.perf_counter()
    res_cla = canny_classico(rgb, comum.CAMINHO_GAUSSIANA,
                             comum.CAMINHO_SOBEL_X, comum.CAMINHO_SOBEL_Y)
    t_cla = time.perf_counter() - inicio

    # ---- mapas individuais (expansão de histograma para exibição) ----
    salvar_imagem(os.path.join(pasta, "02_mod_magnitude_dizenzo.png"),
                  expansao_histograma(res_mod["magnitude"]))
    salvar_imagem(os.path.join(pasta, "03_mod_nms.png"),
                  expansao_histograma(res_mod["nms"]))
    salvar_imagem(os.path.join(pasta, "04_mod_classes.png"),
                  trimapa_classificacao(res_mod["classes"]))
    salvar_imagem(os.path.join(pasta, "05_mod_bordas.png"),
                  binaria_para_uint8(res_mod["bordas"]))
    salvar_imagem(os.path.join(pasta, "06_cla_cinza.png"),
                  np.clip(np.round(res_cla["cinza"]), 0, 255).astype(np.uint8))
    salvar_imagem(os.path.join(pasta, "07_cla_magnitude_sobel.png"),
                  expansao_histograma(res_cla["magnitude"]))
    salvar_imagem(os.path.join(pasta, "08_cla_nms.png"),
                  expansao_histograma(res_cla["nms"]))
    salvar_imagem(os.path.join(pasta, "09_cla_bordas.png"),
                  binaria_para_uint8(res_cla["bordas"]))

    # ---- painéis lado a lado ----
    met_mod = metricas(res_mod)
    met_cla = metricas(res_cla)
    salvar_painel(
        os.path.join(pasta, "painel_modificado.png"),
        [expansao_histograma(res_mod["magnitude"]),
         expansao_histograma(res_mod["nms"]),
         trimapa_classificacao(res_mod["classes"]),
         binaria_para_uint8(res_mod["bordas"])],
        ["magnitude Di Zenzo",
         "pos-NMS (afinado)",
         f"classes Tl={fmt_limiar(res_mod['t_low'])} Th={fmt_limiar(res_mod['t_high'])}",
         f"bordas finais ({met_mod['pixels_borda_final']} px)"])
    salvar_painel(
        os.path.join(pasta, "painel_classico.png"),
        [np.clip(np.round(res_cla["cinza"]), 0, 255).astype(np.uint8),
         expansao_histograma(res_cla["magnitude"]),
         expansao_histograma(res_cla["nms"]),
         binaria_para_uint8(res_cla["bordas"])],
        ["Y (cinza manual)",
         "magnitude Sobel",
         "pos-NMS",
         f"bordas finais ({met_cla['pixels_borda_final']} px)"])
    salvar_painel(
        os.path.join(pasta, "painel_comparacao.png"),
        [original,
         binaria_para_uint8(res_cla["bordas"]),
         binaria_para_uint8(res_mod["bordas"])],
        ["original",
         f"Canny classico ({met_cla['pixels_borda_final']} px)",
         f"Canny modificado ({met_mod['pixels_borda_final']} px)"])

    # ---- zoom digital provando espessura de 1 pixel ----
    if res_mod["bordas"].any():
        centro = janela_mais_densa(res_mod["bordas"], 2 * MEIA_JANELA_ZOOM + 1)
    else:
        centro = (rgb.shape[0] // 2, rgb.shape[1] // 2)
    marcar_janela(res_mod["bordas"], centro, MEIA_JANELA_ZOOM,
                  os.path.join(pasta, "05b_mod_bordas_janela_zoom.png"))
    zooms(pasta, "mod", res_mod["magnitude"], res_mod["nms"], res_mod["bordas"], centro)
    zooms(pasta, "cla", res_cla["magnitude"], res_cla["nms"], res_cla["bordas"], centro)

    if nome == "GrayAndMagenta":
        perfil_gray_and_magenta(pasta, rgb, res_cla, res_mod)

    registro = {
        "imagem": nome,
        "dimensoes": list(rgb.shape),
        "tempo_modificado_s": round(t_mod, 2),
        "tempo_classico_s": round(t_cla, 2),
        "janela_zoom_centro_ij": [int(centro[0]), int(centro[1])],
        "modificado": met_mod,
        "classico": met_cla,
    }
    LOG.append(registro)
    print(f"  modificado: Th={fmt_limiar(met_mod['t_high'])} "
          f"bordas={met_mod['pixels_borda_final']} px "
          f"2x2 cheios={met_mod['blocos_2x2_cheios']} ({t_mod:.1f}s) | "
          f"classico: Th={fmt_limiar(met_cla['t_high'])} "
          f"bordas={met_cla['pixels_borda_final']} px "
          f"2x2 cheios={met_cla['blocos_2x2_cheios']} ({t_cla:.1f}s)", flush=True)


def principal():
    inicio = time.time()
    for nome_arquivo in comum.IMAGENS:
        processar_imagem(nome_arquivo)
    caminho_log = os.path.join(comum.PASTA_RESULTADOS, "experimento2",
                               "log_experimento2.json")
    comum.salvar_log(caminho_log, LOG)
    print(f"Experimento 2 concluído em {(time.time() - inicio)/60:.1f} min. "
          f"Log: {caminho_log}", flush=True)


if __name__ == "__main__":
    principal()
