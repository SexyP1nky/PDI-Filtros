# -*- coding: utf-8 -*-
"""
App Streamlit — Detecção de Bordas: Canny Clássico × Canny Modificado Gabor–Di Zenzo

Trabalho Prático — Introdução ao Processamento Digital de Imagens — 2026.1

Uso:
    pip install streamlit
    streamlit run app_streamlit.py
"""

import json
import math
import os
import sys
import time

import numpy as np
from PIL import Image

# ═══════════════════════════════════════════════════════════════════════════════
# Setup de caminhos — adiciona src/ ao sys.path ANTES de qualquer import do
# projeto, porque os módulos usam imports relativos (from bordas import ...)
# ═══════════════════════════════════════════════════════════════════════════════
RAIZ = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(RAIZ, "src")
CFG = os.path.join(RAIZ, "config")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Imports do projeto (só DEPOIS do sys.path)
from bordas import fracao_blocos_2x2_cheios                             # noqa: E402
from canny_classico import canny_classico                               # noqa: E402
from canny_modificado import canny_modificado                           # noqa: E402
from gabor import gerar_banco_gabor                                     # noqa: E402
from visualizacao import (binaria_para_uint8, expansao_histograma,      # noqa: E402
                          trimapa_classificacao, zoom_vizinho_mais_proximo)

# Streamlit importado aqui para garantir que st.set_page_config seja o 1º comando
import streamlit as st                                                  # noqa: E402

# Caminhos absolutos dos filtros estáticos (Canny clássico)
GAUSS_PATH = os.path.join(CFG, "gaussiana_5x5.json")
SOBEL_X_PATH = os.path.join(CFG, "sobel_x.txt")
SOBEL_Y_PATH = os.path.join(CFG, "sobel_y.txt")

# Imagens de teste do enunciado
IMAGENS_TESTE = {
    "GrayAndMagenta.png": "Caso isoluminante (tese central)",
    "FCBarcelona.png":    "Bordas cromáticas em imagem real",
    "Zebra.png":          "Texturas de alta frequência",
    "Bear.jpg":           "Pelagem e textura densa",
    "PlacaMercosul.webp": "Texto e detalhes finos",
    "VintageCar.png":     "Lataria e contornos",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Funções auxiliares
# ═══════════════════════════════════════════════════════════════════════════════
def pil_para_rgb_float(pil_img):
    """Converte PIL Image → float32 (H,W,3) em [0..255].

    Replica a mesma lógica de imagem_io.carregar_imagem_rgb:
    - RGBA: composição alfa sobre fundo branco
    - Outros modos: converte para RGB via Pillow (apenas decodificação)
    """
    if pil_img.mode == "RGBA":
        arr = np.asarray(pil_img, dtype=np.float32)
        rgb = arr[:, :, :3]
        alfa = arr[:, :, 3:4] / 255.0
        return rgb * alfa + 255.0 * (1.0 - alfa)
    return np.asarray(pil_img.convert("RGB"), dtype=np.float32)


def redimensionar(rgb, larg_max):
    """Redimensiona (LANCZOS) mantendo proporção se largura > larg_max."""
    h, w = rgb.shape[:2]
    if w <= larg_max:
        return rgb
    escala = larg_max / w
    novo_w = int(larg_max)
    novo_h = max(1, int(h * escala))
    pil = Image.fromarray(np.clip(np.round(rgb), 0, 255).astype(np.uint8))
    pil = pil.resize((novo_w, novo_h), Image.LANCZOS)
    return np.asarray(pil, dtype=np.float32)


def fmt(v):
    """Formata valor numérico para exibição (limiares, etc.)."""
    if np.isinf(v):
        return "∞"
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    return f"{v:.1f}"


# ═══════════════════════════════════════════════════════════════════════════════
# Configuração da página (DEVE ser o primeiro comando Streamlit)
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Canny × Gabor–Di Zenzo | PDI 2026.1",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    [data-testid="stSidebar"] { min-width: 340px; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Título
# ═══════════════════════════════════════════════════════════════════════════════
st.title("🔬 Detecção de Bordas")
st.markdown(
    "**Canny Clássico × Canny Modificado Gabor–Di Zenzo** · "
    "Trabalho Prático — PDI 2026.1"
)


# ═══════════════════════════════════════════════════════════════════════════════
# Sidebar — Configurações
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # ── Imagem ───────────────────────────────────────────────────────────────
    st.header("📷 Imagem")
    fonte = st.radio(
        "Origem da imagem",
        ["Imagens de teste", "Upload"],
        horizontal=True,
        label_visibility="collapsed",
    )

    pil_img = None
    nome_imagem = ""

    if fonte == "Upload":
        arq = st.file_uploader(
            "Carregar imagem",
            type=["png", "jpg", "jpeg", "webp", "bmp"],
        )
        if arq is not None:
            pil_img = Image.open(arq)
            nome_imagem = arq.name
    else:
        nome_sel = st.selectbox(
            "Selecionar imagem",
            list(IMAGENS_TESTE.keys()),
            format_func=lambda x: f"{x}  —  {IMAGENS_TESTE[x]}",
            label_visibility="collapsed",
        )
        caminho_img = os.path.join(RAIZ, nome_sel)
        if os.path.exists(caminho_img):
            pil_img = Image.open(caminho_img)
            nome_imagem = nome_sel
        else:
            st.error(f"Imagem não encontrada: {nome_sel}")

    # ── Método ───────────────────────────────────────────────────────────────
    st.divider()
    st.header("⚙️ Método")
    metodo = st.radio(
        "Selecione",
        ["Ambos", "Canny Modificado", "Canny Clássico"],
        label_visibility="collapsed",
    )

    # ── Parâmetros do Gabor ──────────────────────────────────────────────────
    st.divider()
    st.header("🎛️ Banco de Gabor")

    # ── Carregar configuração JSON ────────────────────────────────────────
    with st.expander("📂 Carregar configuração JSON", expanded=False):
        json_fonte = st.radio(
            "Origem do JSON",
            ["Arquivo local (config/)", "Upload"],
            horizontal=True,
            label_visibility="collapsed",
            key="json_fonte_radio",
        )

        cfg_json_dados = None

        if json_fonte == "Upload":
            arq_json = st.file_uploader(
                "Carregar JSON de configuração Gabor",
                type=["json"],
                key="gabor_json_upload",
            )
            if arq_json is not None:
                try:
                    cfg_json_dados = json.load(arq_json)
                except Exception as e:
                    st.error(f"Erro ao ler JSON: {e}")
        else:
            arquivos_json = []
            for pasta in [CFG, os.path.join(CFG, "experimentos")]:
                if os.path.isdir(pasta):
                    for f in sorted(os.listdir(pasta)):
                        if f.endswith(".json"):
                            caminho_completo = os.path.join(pasta, f)
                            rel = os.path.relpath(caminho_completo, CFG)
                            arquivos_json.append((rel, caminho_completo))

            if arquivos_json:
                nomes = [rel for rel, _ in arquivos_json]
                sel_json = st.selectbox(
                    "Selecionar configuração",
                    range(len(nomes)),
                    format_func=lambda i: nomes[i],
                    key="json_sel_config",
                )
                caminho_sel = arquivos_json[sel_json][1]
                try:
                    with open(caminho_sel, "r", encoding="utf-8") as fj:
                        cfg_json_dados = json.load(fj)
                except Exception as e:
                    st.error(f"Erro ao ler {nomes[sel_json]}: {e}")
            else:
                st.warning("Nenhum arquivo JSON encontrado em config/.")

        if cfg_json_dados is not None:
            if st.button("✅ Aplicar configuração", key="btn_aplicar_json"):
                st.session_state["gabor_json"] = cfg_json_dados
                st.rerun()

    # ── Defaults: do JSON carregado ou valores padrão ─────────────────────
    gj = st.session_state.get("gabor_json", None)
    def_tam   = int(gj["tamanho_mascara"]) if gj and "tamanho_mascara" in gj else 31
    def_sigma = float(gj["sigma"])         if gj and "sigma" in gj else 4.0
    def_lambd = float(gj["lambda"])        if gj and "lambda" in gj else 8.0
    def_gamma = float(gj["gamma"])         if gj and "gamma" in gj else 0.5
    def_psi   = float(gj["psi"])           if gj and "psi" in gj else -math.pi / 2
    def_n_ori = len(gj["orientacoes_graus"]) if gj and "orientacoes_graus" in gj else 8

    # Clampar nos limites dos sliders
    def_tam   = max(3, min(73, def_tam if def_tam % 2 == 1 else def_tam + 1))
    def_sigma = max(1.0, min(20.0, def_sigma))
    def_lambd = max(2.0, min(32.0, def_lambd))
    def_gamma = max(0.1, min(2.0, def_gamma))
    def_n_ori = max(4, min(16, def_n_ori))

    # Snap para steps dos sliders
    def_sigma = round(def_sigma * 2) / 2      # step 0.5
    def_lambd = round(def_lambd)               # step 1.0
    def_gamma = round(def_gamma * 20) / 20     # step 0.05

    def_psi_opcao_idx = 0 if def_psi < 0 else 1

    if gj:
        st.success(
            f"📄 Configuração JSON carregada: "
            f"{gj.get('nome', 'sem nome')}"
        )
        if st.button("🔄 Limpar configuração JSON", key="btn_limpar_json"):
            del st.session_state["gabor_json"]
            st.rerun()

    with st.expander("Ajustar parâmetros", expanded=False):
        tam = st.slider("Tamanho da máscara", 3, 73, def_tam, step=2)
        sigma = st.slider("σ (escala)", 1.0, 20.0, def_sigma, step=0.5)
        lambd = st.slider("λ (frequência)", 2.0, 32.0, def_lambd, step=1.0)
        gamma = st.slider("γ (elipsicidade)", 0.1, 2.0, def_gamma, step=0.05)
        psi_opcao = st.selectbox(
            "ψ (fase)",
            ["−π/2  (detector de degraus — recomendado)", "0  (detector de linhas)"],
            index=def_psi_opcao_idx,
        )
        psi_val = -math.pi / 2 if "π/2" in psi_opcao else 0.0
        n_ori = st.slider("Nº de orientações", 4, 16, def_n_ori)

    st.caption(
        f"Banco atual: máscara {tam}×{tam}, σ={sigma}, λ={lambd}, "
        f"γ={gamma}, ψ={'−π/2' if psi_val < 0 else '0'}, {n_ori} orientações"
    )

    # ── Redimensionamento ────────────────────────────────────────────────────
    st.divider()
    larg_max = st.slider(
        "Largura máxima (px)", 200, 1200, 600, step=50,
        help="Imagens maiores serão redimensionadas para controlar o tempo",
    )

    # ── Botão de processamento ───────────────────────────────────────────────
    st.divider()
    processar = st.button("🚀 Processar", type="primary", use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Área principal — Carregamento da imagem
# ═══════════════════════════════════════════════════════════════════════════════
if pil_img is None:
    st.info("👈 Selecione ou carregue uma imagem na barra lateral para começar.")
    st.stop()

# Converter e redimensionar
rgb = pil_para_rgb_float(pil_img)
rgb = redimensionar(rgb, larg_max)
h, w = rgb.shape[:2]
original_uint8 = np.clip(np.round(rgb), 0, 255).astype(np.uint8)

# Limpar resultados anteriores se a imagem mudou
if "resultados" in st.session_state:
    if st.session_state["resultados"].get("nome") != nome_imagem:
        del st.session_state["resultados"]

# Exibir imagem original
st.image(original_uint8, caption=f"{nome_imagem}  ({w} × {h} px)")


# ═══════════════════════════════════════════════════════════════════════════════
# Processamento (disparado pelo botão)
# ═══════════════════════════════════════════════════════════════════════════════
if processar:
    # Montar parâmetros do banco de Gabor
    orientacoes = [i * 180.0 / n_ori for i in range(n_ori)]
    banco_params = {
        "tamanho_mascara": int(tam),
        "sigma":           float(sigma),
        "lambda":          float(lambd),
        "gamma":           float(gamma),
        "psi":             float(psi_val),
        "orientacoes_graus": orientacoes,
    }

    res_mod = None
    res_cla = None
    tempo_mod = 0.0
    tempo_cla = 0.0

    barra = st.progress(0, text="Iniciando processamento...")

    try:
        # ── Canny Modificado ─────────────────────────────────────────────────
        if metodo in ("Ambos", "Canny Modificado"):
            barra.progress(5, text="Gerando banco de Gabor...")
            banco = gerar_banco_gabor(banco_params)

            barra.progress(15, text="Executando Canny Modificado Gabor–Di Zenzo...")
            t0 = time.perf_counter()
            res_mod = canny_modificado(rgb, banco)
            tempo_mod = time.perf_counter() - t0

            barra.progress(70, text=f"Canny Modificado concluído ({tempo_mod:.1f}s)")

        # ── Canny Clássico ───────────────────────────────────────────────────
        if metodo in ("Ambos", "Canny Clássico"):
            barra.progress(75, text="Executando Canny Clássico...")
            t0 = time.perf_counter()
            res_cla = canny_classico(rgb, GAUSS_PATH, SOBEL_X_PATH, SOBEL_Y_PATH)
            tempo_cla = time.perf_counter() - t0

            barra.progress(95, text=f"Canny Clássico concluído ({tempo_cla:.1f}s)")

        barra.progress(100, text="✅ Processamento concluído!")
        time.sleep(0.5)
        barra.empty()

    except Exception as e:
        barra.empty()
        st.error(f"Erro durante o processamento: {e}")
        st.stop()

    # Armazenar resultados no session_state (persistem entre reruns)
    st.session_state["resultados"] = {
        "res_mod":   res_mod,
        "res_cla":   res_cla,
        "tempo_mod": tempo_mod,
        "tempo_cla": tempo_cla,
        "original":  original_uint8,
        "nome":      nome_imagem,
        "dims":      (w, h),
        "params":    banco_params,
        "metodo":    metodo,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Exibição dos resultados (lê de session_state)
# ═══════════════════════════════════════════════════════════════════════════════
if "resultados" not in st.session_state:
    st.info("Ajuste os parâmetros na barra lateral e clique em **🚀 Processar**.")
    st.stop()

dados = st.session_state["resultados"]
res_mod = dados["res_mod"]
res_cla = dados["res_cla"]
orig = dados["original"]


# ─── Comparação principal ────────────────────────────────────────────────────
st.divider()
st.header("📊 Resultado — Bordas Detectadas")

if res_mod is not None and res_cla is not None:
    # Ambos os métodos
    c1, c2, c3 = st.columns(3)
    with c1:
        st.image(orig, caption="Original", use_container_width=True)
    with c2:
        n_cla = int(res_cla["bordas"].sum())
        st.image(
            binaria_para_uint8(res_cla["bordas"]),
            caption=f"Canny Clássico — {n_cla:,} px",
            use_container_width=True,
        )
    with c3:
        n_mod = int(res_mod["bordas"].sum())
        st.image(
            binaria_para_uint8(res_mod["bordas"]),
            caption=f"Canny Modificado — {n_mod:,} px",
            use_container_width=True,
        )

elif res_mod is not None:
    c1, c2 = st.columns(2)
    with c1:
        st.image(orig, caption="Original", use_container_width=True)
    with c2:
        n_mod = int(res_mod["bordas"].sum())
        st.image(
            binaria_para_uint8(res_mod["bordas"]),
            caption=f"Canny Modificado — {n_mod:,} px",
            use_container_width=True,
        )

elif res_cla is not None:
    c1, c2 = st.columns(2)
    with c1:
        st.image(orig, caption="Original", use_container_width=True)
    with c2:
        n_cla = int(res_cla["bordas"].sum())
        st.image(
            binaria_para_uint8(res_cla["bordas"]),
            caption=f"Canny Clássico — {n_cla:,} px",
            use_container_width=True,
        )


# ─── Nota especial: caso isoluminante (GrayAndMagenta) ───────────────────────
if (dados["nome"] == "GrayAndMagenta.png"
        and res_mod is not None and res_cla is not None):
    n_cla_gm = int(res_cla["bordas"].sum())
    n_mod_gm = int(res_mod["bordas"].sum())
    if n_cla_gm == 0:
        st.success(
            f"🎯 **Caso isoluminante demonstrado!** "
            f"Cinza RGB(100,100,100) e Magenta RGB(172,34,251) têm "
            f"a mesma luminância (Y = 100.0). "
            f"O Canny Clássico detectou **{n_cla_gm} bordas** "
            f"(impossibilidade matemática — gradiente zero). "
            f"O Canny Modificado detectou **{n_mod_gm:,} bordas** "
            f"preservando a informação cromática via fusão vetorial."
        )


# ─── Pipeline do Canny Modificado ────────────────────────────────────────────
if res_mod is not None:
    st.divider()
    st.subheader("🔍 Pipeline — Canny Modificado Gabor–Di Zenzo")
    cols = st.columns(4)
    with cols[0]:
        st.image(
            expansao_histograma(res_mod["magnitude"]),
            caption="1 · Magnitude Di Zenzo",
            use_container_width=True,
        )
    with cols[1]:
        st.image(
            expansao_histograma(res_mod["nms"]),
            caption="2 · Pós-NMS (afinado 1 px)",
            use_container_width=True,
        )
    with cols[2]:
        st.image(
            trimapa_classificacao(res_mod["classes"]),
            caption=(
                f"3 · Histerese  "
                f"(Tl={fmt(res_mod['t_low'])}  Th={fmt(res_mod['t_high'])})"
            ),
            use_container_width=True,
        )
    with cols[3]:
        st.image(
            binaria_para_uint8(res_mod["bordas"]),
            caption=f"4 · Bordas finais ({int(res_mod['bordas'].sum()):,} px)",
            use_container_width=True,
        )


# ─── Pipeline do Canny Clássico ──────────────────────────────────────────────
if res_cla is not None:
    st.divider()
    st.subheader("🔍 Pipeline — Canny Clássico")
    cols = st.columns(4)
    with cols[0]:
        cinza_vis = np.clip(
            np.round(res_cla["cinza"]), 0, 255
        ).astype(np.uint8)
        st.image(
            cinza_vis,
            caption="1 · Y (cinza manual)",
            use_container_width=True,
        )
    with cols[1]:
        st.image(
            expansao_histograma(res_cla["magnitude"]),
            caption="2 · Magnitude Sobel",
            use_container_width=True,
        )
    with cols[2]:
        st.image(
            expansao_histograma(res_cla["nms"]),
            caption="3 · Pós-NMS (afinado 1 px)",
            use_container_width=True,
        )
    with cols[3]:
        st.image(
            binaria_para_uint8(res_cla["bordas"]),
            caption=f"4 · Bordas finais ({int(res_cla['bordas'].sum()):,} px)",
            use_container_width=True,
        )


# ─── Visualização do Banco de Gabor ──────────────────────────────────────────
if res_mod is not None:
    with st.expander("🔬 Banco de Gabor — Máscaras Geradas"):
        banco_vis = res_mod["banco"]
        kernels = banco_vis["kernels"]
        thetas = banco_vis["orientacoes_graus"]
        n_kernels = len(kernels)
        per_row = min(n_kernels, 8)
        cols_k = st.columns(per_row)
        for i, (kernel, theta) in enumerate(zip(kernels, thetas)):
            with cols_k[i % per_row]:
                # Zoom 4× vizinho-mais-próximo para melhor visualização
                vis = zoom_vizinho_mais_proximo(expansao_histograma(kernel), 4)
                st.image(vis, caption=f"θ = {theta}°", use_container_width=True)


# ─── Métricas quantitativas ──────────────────────────────────────────────────
st.divider()
st.subheader("📈 Métricas Quantitativas")

ambos_presentes = res_mod is not None and res_cla is not None
n_metric_cols = 2 if ambos_presentes else 1
metric_cols = st.columns(n_metric_cols)

if res_cla is not None:
    with metric_cols[0]:
        st.markdown("**Canny Clássico**")
        frac_c, blocos_c = fracao_blocos_2x2_cheios(res_cla["bordas"])
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Bordas (px)", f"{int(res_cla['bordas'].sum()):,}")
        mc2.metric("T_high", fmt(res_cla["t_high"]))
        mc3.metric("T_low", fmt(res_cla["t_low"]))
        mc4, mc5, mc6 = st.columns(3)
        mc4.metric("Blocos 2×2", f"{blocos_c}")
        mc5.metric("Fração 2×2", f"{frac_c:.4%}")
        mc6.metric("Tempo", f"{dados['tempo_cla']:.2f}s")

if res_mod is not None:
    idx_mod = 1 if ambos_presentes else 0
    with metric_cols[idx_mod]:
        st.markdown("**Canny Modificado Gabor–Di Zenzo**")
        frac_m, blocos_m = fracao_blocos_2x2_cheios(res_mod["bordas"])
        mm1, mm2, mm3 = st.columns(3)
        mm1.metric("Bordas (px)", f"{int(res_mod['bordas'].sum()):,}")
        mm2.metric("T_high", fmt(res_mod["t_high"]))
        mm3.metric("T_low", fmt(res_mod["t_low"]))
        mm4, mm5, mm6 = st.columns(3)
        mm4.metric("Blocos 2×2", f"{blocos_m}")
        mm5.metric("Fração 2×2", f"{frac_m:.4%}")
        mm6.metric("Tempo", f"{dados['tempo_mod']:.2f}s")


# ─── Parâmetros utilizados ───────────────────────────────────────────────────
with st.expander("📋 Parâmetros utilizados neste processamento"):
    p = dados["params"]
    st.json({
        "imagem":            dados["nome"],
        "metodo":            dados["metodo"],
        "dimensoes":         f"{dados['dims'][0]} × {dados['dims'][1]}",
        "tamanho_mascara":   p["tamanho_mascara"],
        "sigma":             p["sigma"],
        "lambda":            p["lambda"],
        "gamma":             p["gamma"],
        "psi":               round(p["psi"], 6),
        "orientacoes_graus": [round(o, 1) for o in p["orientacoes_graus"]],
    })


# ─── Rodapé ──────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Trabalho Prático — Introdução ao Processamento Digital de Imagens — "
    "UFPB 2026.1 · "
    "Implementação completa do zero (sem cv2.Canny, cv2.filter2D, cv2.getGaborKernel)"
)
