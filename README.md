# Trabalho Prático — PDI 2026.1

Implementação e comparação do **Canny clássico** com o **Canny Modificado
Gabor–Di Zenzo** (abordagem vetorial para imagens coloridas), conforme a
"Especificação do Trabalho Prático.pdf".

Todas as funções críticas (correlação espacial, geração de Gabor, NMS,
histerese, expansão de histograma) foram implementadas **do zero** — sem
`cv2.Canny`, `cv2.filter2D` ou `cv2.getGaborKernel`. NumPy é usado apenas
para álgebra de matrizes; Pillow apenas para abrir/salvar imagens.

## Estrutura

```
src/
  filtragem.py        Módulo A — correlação 2D própria + filtros de .txt/.json
  gabor.py            Módulo B — banco de Gabor paramétrico via JSON
  bordas.py           NMS (1 px), histerese (BFS), limiares por percentil
  canny_classico.py   Pipeline clássico (Y manual -> Gaussiana -> Sobel -> NMS -> histerese)
  canny_modificado.py Módulo C — pipeline Gabor–Di Zenzo (fusão L2 + redução por máximo)
  visualizacao.py     Expansão de histograma [0,255], painéis, zoom 8x
  imagem_io.py        Abrir/salvar imagens (Pillow), conversão Y manual
config/
  sobel_x.txt, sobel_y.txt      filtros estáticos (formato .txt)
  gaussiana_5x5.json            filtro estático (formato .json, com normalização)
  gabor_banco_padrao.json       banco de Gabor padrão (Módulo B)
  experimentos/                 configurações JSON geradas pelas varreduras
experimentos/
  experimento1.py     Sensibilidade paramétrica (lambda, sigma, psi, gamma)
  experimento2.py     Validação de NMS/histerese, zooms 1 px, comparação
testes/
  testes_sanidade.py  38 testes unitários (correlação vs cálculo manual etc.)
  teste_e2e.py        Teste end-to-end do projeto completo
resultados/           mapas, painéis e logs gerados pelos experimentos
demo.py               roda os dois detectores em QUALQUER imagem (apresentação)
gerar_relatorio_pdf.py  gera o relatório formal em PDF (entregável)
RELATORIO.md          relatório com a discussão dos experimentos (markdown)
Relatorio_Trabalho_Pratico_PDI.pdf  relatório formal (introdução, materiais e
                      métodos, resultados, discussão, conclusão)
```

## Como rodar

```powershell
pip install -r requirements.txt
python testes\testes_sanidade.py     # valida os módulos
python experimentos\experimento1.py  # ~18 min (máscara 73x73 na Bear domina)
python experimentos\experimento2.py  # ~2 min
python testes\teste_e2e.py           # valida o projeto de ponta a ponta
python demo.py GrayAndMagenta.png    # demo em uma imagem avulsa (~1 s)
python gerar_relatorio_pdf.py        # regenera o relatório PDF
```

## Convenções

- Coordenadas: `x` = colunas (direita), `y` = linhas (para **baixo**).
- `theta` é a direção da **variação** (portadora do Gabor / gradiente);
  a borda detectada é perpendicular a `theta` (theta = 0 -> borda vertical).
- `psi` em radianos; o banco padrão usa `psi = -pi/2` (portadora ímpar,
  detector de degraus com pico único — ver discussão no RELATORIO.md).
- Tratamento de borda da correlação: replicação do pixel da margem.
- Limiarização: T_high = percentil 90 dos máximos pós-NMS (acima de um piso
  de ruído de 0.5), T_low = 0.4*T_high — justificativa no RELATORIO.md.
