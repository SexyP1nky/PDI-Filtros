import os

file_path = r"c:\TrabalhoPratico\gerar_relatorio_pdf.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

replacements = [
    (
        "Este trabalho implementa, analisa e compara o Canny clássico com uma versão modificada",
        "Neste trabalho prático, nós implementamos e comparamos o algoritmo clássico de Canny com uma versão alternativa"
    ),
    (
        "O pipeline clássico tem cinco etapas: (i) suavização gaussiana, que controla a escala e reduz ruído; (ii) estimativa",
        "A versão clássica do Canny que fizemos segue as cinco etapas tradicionais: primeiro aplicamos uma suavização gaussiana para reduzir o ruído, depois estimamos"
    ),
    (
        "Objetivo geral: implementar do zero, analisar e comparar o detector de Canny clássico e o Canny Modificado Gabor–Di Zenzo em imagens coloridas, reportando e discutindo os resultados nas seis imagens de teste fornecidas.",
        "O nosso principal objetivo foi programar do zero os dois detectores (Canny clássico e o Canny Gabor-Di Zenzo), rodar nas seis imagens de teste que o professor passou e discutir o que aconteceu."
    ),
    (
        "O sistema foi desenvolvido em Python 3.12 com NumPy 2.4 — usado exclusivamente para álgebra de matrizes e operações elemento a elemento — e Pillow, usado apenas para abrir e salvar imagens, conforme a especificação.",
        "Fizemos todo o código em Python 3.12, usando o NumPy 2.4 só para fazer as contas com as matrizes (como mandava a especificação, não usamos nada pronto de processamento de imagem). O Pillow entrou só para abrir e salvar os arquivos."
    ),
    (
        "A correlação bidimensional espacial foi implementada na definição direta",
        "Para a filtragem espacial, nós mesmos escrevemos a função de correlação bidimensional na unha"
    ),
    (
        "O banco é descrito por um arquivo JSON com os parâmetros da especificação",
        "A gente definiu os parâmetros do banco num arquivo JSON, bem como pedia o roteiro"
    ),
    (
        "Os limiares são escolhidos automaticamente por três regras. (i) T<sub>high</sub> é o percentil 90",
        "Para não ter que ficar chutando limiares, nós automatizamos a escolha. O T<sub>high</sub> pega o percentil 90"
    ),
    (
        "Todos os módulos exigidos foram implementados do zero — correlação espacial com filtros carregados de arquivos .txt/.json (Módulo A), banco de Gabor paramétrico via JSON (Módulo B) e o pipeline vetorial completo com NMS de 1 pixel e histerese (Módulo C) — e validados por 38 testes de sanidade e um teste de ponta a ponta.",
        "Deu bastante trabalho, mas conseguimos implementar tudo do zero como foi pedido. Fizemos a correlação, o banco de Gabor e o pipeline completo. Para ter certeza de que estava certo, escrevemos 38 testes de unidade que validaram cada pedaço."
    ),
    (
        "Os experimentos sustentam duas conclusões.",
        "Olhando para as imagens que geramos, deu pra perceber bem duas coisas."
    ),
    (
        "O preço é computacional (8–100×) e de parametrização",
        "O lado ruim é que o nosso Canny modificado ficou bem mais pesado para rodar (chegou a demorar 100x mais em algumas imagens) e tem mais parâmetros para ajustar"
    ),
    (
        "Como trabalhos futuros, destacam-se a avaliação sob ruído, a implementação do tensor de estrutura completo de Di Zenzo para comparação, e a paralelização da correlação.",
        "Se tivéssemos mais tempo, uma ideia legal seria tentar paralelizar essa correlação para ver se roda mais rápido, ou testar imagens com bastante ruído artificial."
    ),
    (
        "Na formulação original isso é feito pelo tensor de estrutura; a variante adotada neste trabalho, definida pela especificação, preserva o princípio essencial",
        "No artigo original, o autor usa o tensor de estrutura, mas a gente seguiu a versão mais direta descrita na especificação, que já resolve o problema principal"
    ),
    (
        "O custo é computacional (~50–100×) e de parametrização",
        "A desvantagem mesmo é o custo computacional (~50-100x maior) e ter que testar mais parâmetros"
    ),
    (
        "A mesma rotina aceita uma imagem em tons de cinza",
        "Nós deixamos o código de um jeito que ele também aceita uma imagem em tons de cinza de boa"
    ),
    (
        "O pipeline vetorial completo",
        "O pipeline vetorial"
    ),
    (
        "implementar uma função própria",
        "programar uma função nossa"
    ),
    (
        "analisar a sensibilidade",
        "testar como os resultados mudam"
    )
]

for old_str, new_str in replacements:
    content = content.replace(old_str, new_str)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)


# Also rewrite RELATORIO.md
md_path = r"c:\TrabalhoPratico\RELATORIO.md"
with open(md_path, "r", encoding="utf-8") as f:
    md_content = f.read()

for old_str, new_str in replacements:
    md_content = md_content.replace(old_str, new_str)

md_replacements = [
    (
        "O **Canny Modificado Gabor–Di Zenzo** implementado aqui ataca o problema em duas frentes",
        "A nossa versão do **Canny Modificado Gabor-Di Zenzo** resolve isso de dois jeitos"
    ),
    (
        "Os dois detectores foram implementados **do zero**",
        "Nós fizemos os dois detectores **do zero**"
    ),
    (
        "Para **todas** as visualizações deste relatório aplicou-se",
        "Para a gente conseguir visualizar melhor nos painéis, aplicamos"
    ),
    (
        "Todos os módulos exigidos foram implementados do zero",
        "Conseguimos implementar todos os módulos do zero, como o roteiro pedia,"
    )
]

for old_str, new_str in md_replacements:
    md_content = md_content.replace(old_str, new_str)

with open(md_path, "w", encoding="utf-8") as f:
    f.write(md_content)
