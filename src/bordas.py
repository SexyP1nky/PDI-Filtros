# -*- coding: utf-8 -*-
"""
Afinamento (Supressão de Não-Máximos) e Limiarização por Histerese,
implementados do zero.

Convenção de orientação: o ângulo (em graus) é a direção da VARIAÇÃO
(direção do gradiente / da portadora do Gabor), no sistema x = colunas
(-> direita), y = linhas (-> baixo). A borda é PERPENDICULAR a esse ângulo;
o NMS compara o pixel com os dois vizinhos AO LONGO do ângulo (ortogonais
à borda), como pede a especificação.
"""

from collections import deque

import numpy as np

# bin de direção -> deslocamento (di, dj) do vizinho no sentido +theta
# (di = linhas para baixo, dj = colunas para a direita)
_DESLOCAMENTOS = {
    0: (0, 1),     # variação horizontal  -> compara esquerda/direita
    45: (1, 1),    # variação diagonal    -> compara baixo-direita/cima-esquerda
    90: (1, 0),    # variação vertical    -> compara baixo/cima
    135: (1, -1),  # variação anti-diagonal -> compara baixo-esquerda/cima-direita
}


def quantizar_orientacao(orientacao_graus):
    """Quantiza ângulos (graus) nos 4 eixos de vizinhança: 0, 45, 90, 135.

    Faixas (após módulo 180): [0,22.5)U[157.5,180) -> 0; [22.5,67.5) -> 45;
    [67.5,112.5) -> 90; [112.5,157.5) -> 135.
    """
    ang = np.mod(np.asarray(orientacao_graus, dtype=np.float64), 180.0)
    bins = np.zeros(ang.shape, dtype=np.uint8)
    bins[(ang >= 22.5) & (ang < 67.5)] = 45
    bins[(ang >= 67.5) & (ang < 112.5)] = 90
    bins[(ang >= 112.5) & (ang < 157.5)] = 135
    return bins


def supressao_nao_maximos(magnitude, orientacao_graus):
    """Supressão de Não-Máximos (NMS) guiada pela orientação.

    Mantém um pixel somente se sua magnitude for máxima em relação aos dois
    vizinhos ao longo da direção de variação (ortogonais à borda). Em platôs
    de magnitude igual, um critério de desempate assimétrico (> de um lado,
    >= do outro) garante espessura final de exatamente 1 pixel.

    Retorna um mapa float32 com a magnitude preservada nos máximos e 0 nos
    pixels suprimidos.
    """
    mag = np.asarray(magnitude, dtype=np.float32)
    if mag.ndim != 2:
        raise ValueError("a magnitude deve ser um mapa 2D")
    alt, larg = mag.shape
    pad = np.pad(mag, 1, mode="constant")
    bins = quantizar_orientacao(orientacao_graus)
    if bins.shape != mag.shape:
        raise ValueError("magnitude e orientação devem ter o mesmo formato")

    saida = np.zeros_like(mag)
    for valor_bin, (di, dj) in _DESLOCAMENTOS.items():
        viz_pos = pad[1 + di:1 + di + alt, 1 + dj:1 + dj + larg]  # sentido +theta
        viz_neg = pad[1 - di:1 - di + alt, 1 - dj:1 - dj + larg]  # sentido -theta
        # desempate: estritamente maior no sentido -theta, maior ou igual no +theta
        manter = (mag > viz_neg) & (mag >= viz_pos) & (mag > 0)
        selecao = manter & (bins == valor_bin)
        saida[selecao] = mag[selecao]
    return saida


def classificar_bordas(mag_nms, t_low, t_high):
    """Classifica cada pixel pós-NMS em: 2 = forte, 1 = fraco, 0 = suprimido."""
    classes = np.zeros(mag_nms.shape, dtype=np.uint8)
    classes[(mag_nms >= t_low) & (mag_nms < t_high)] = 1
    classes[mag_nms >= t_high] = 2
    return classes


def histerese(mag_nms, t_low, t_high):
    """Limiarização por histerese com análise de conectividade (BFS 8-conexa).

    Pixels fortes (>= t_high) são bordas; pixels fracos (>= t_low e < t_high)
    só viram borda se estiverem conectados (direta ou transitivamente, em
    8-vizinhança) a algum pixel forte. Retorna máscara booleana de bordas.
    """
    if t_low > t_high:
        raise ValueError("t_low deve ser <= t_high")
    mag = np.asarray(mag_nms)
    alt, larg = mag.shape
    fortes = mag >= t_high
    candidatos = mag >= t_low  # fortes + fracos

    resultado = fortes.copy()
    fila = deque(zip(*np.nonzero(fortes)))
    while fila:
        i, j = fila.popleft()
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                a, b = i + di, j + dj
                if 0 <= a < alt and 0 <= b < larg \
                        and candidatos[a, b] and not resultado[a, b]:
                    resultado[a, b] = True
                    fila.append((a, b))
    return resultado


def limiares_por_percentil(mag_nms, percentil_forte=90.0, razao_fraco=0.4,
                           piso_absoluto=0.5):
    """Escolhe (t_low, t_high) a partir da distribuição dos máximos do NMS.

    t_high = percentil 'percentil_forte' dos valores pós-NMS acima do piso
    (cristas candidatas); t_low = razao_fraco * t_high (razão Tlow:Thigh de
    1:2.5, dentro da faixa 1:2 a 1:3 recomendada por Canny).

    'piso_absoluto' é um piso de magnitude que separa estrutura real de
    ruído numérico: em imagens 0..255, a menor borda real possível (degrau
    de 1 nível de cinza) produz magnitude Sobel >= 4 e respostas de Gabor da
    mesma ordem, enquanto resíduos de arredondamento float ficam em ~1e-4.
    Sem o piso, uma imagem sem estrutura (ex.: luminância constante) teria
    limiares adaptados ao ruído de máquina e geraria bordas espúrias.

    Retorna (t_low, t_high). Se não houver nenhum candidato acima do piso,
    retorna (inf, inf) — nenhum pixel vira borda.
    """
    valores = mag_nms[mag_nms > piso_absoluto]
    if valores.size == 0:
        return float("inf"), float("inf")
    t_high = float(np.percentile(valores, percentil_forte))
    t_low = max(razao_fraco * t_high, piso_absoluto)
    return t_low, t_high


def fracao_blocos_2x2_cheios(bordas):
    """Métrica de afinamento: fração de blocos 2x2 totalmente preenchidos.

    Em um mapa perfeitamente afinado (1 pixel de espessura) nenhum bloco 2x2
    deveria estar completamente cheio (exceções raras em junções). Retorna
    (fração, total_de_blocos_cheios).
    """
    b = np.asarray(bordas, dtype=bool)
    cheios = b[:-1, :-1] & b[1:, :-1] & b[:-1, 1:] & b[1:, 1:]
    n_cheios = int(cheios.sum())
    n_pixels_borda = int(b.sum())
    if n_pixels_borda == 0:
        return 0.0, 0
    return n_cheios / n_pixels_borda, n_cheios
