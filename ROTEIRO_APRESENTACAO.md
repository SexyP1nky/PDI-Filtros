      # Roteiro de Apresentação — Trabalho Prático de PDI
## Canny Clássico × Canny Modificado Gabor–Di Zenzo

**Duração-alvo: ~20 min de fala + perguntas.** Cada seção tem: **FALA**
(o que dizer, em primeira pessoa do plural), **MOSTRAR** (o arquivo/figura
a exibir — nunca código) e **FAÇA** (ação ao vivo). Os tempos somam 20 min;
ensaie com cronômetro.

> Para grupos: divida as seções entre os integrantes, mas TODOS devem
> dominar a seção 11 (perguntas) — a especificação exige que cada
> integrante conheça o trabalho inteiro.

---

## 0. Preparação ANTES do dia (checklist)

- [ ] Notebook com o projeto em `C:\TrabalhoPratico`, testado NO PRÓPRIO
      notebook (rodar `python testes\teste_e2e.py` uma vez na véspera).
- [ ] Abrir ANTES de começar, em abas do visualizador de imagens, na ordem
      das seções: todas as figuras listadas nos "MOSTRAR" abaixo.
- [ ] Terminal já aberto na pasta do projeto, fonte grande (Ctrl+= no
      Windows Terminal), com os comandos da seção 12 colados no histórico.
- [ ] Relatório impresso (exigência da especificação) + PDF e código já
      enviados antes da primeira aula de apresentações.
- [ ] Decorar os 8 números da "cola" (seção 13).
- [ ] Plano B: se o notebook falhar, TODAS as figuras já existem em
      `resultados\` — a apresentação inteira funciona sem rodar nada.

---

## 1. Abertura — o problema (1 min)

**FALA:** "O detector de Canny clássico tem uma limitação estrutural: ele
converte a imagem colorida para tons de cinza ANTES de calcular qualquer
gradiente. Essa conversão, Y = 0,299R + 0,587G + 0,114B, projeta um espaço
de cor tridimensional em um único eixo. Toda vez que duas cores diferentes
caem no mesmo valor de Y, a borda entre elas deixa de existir antes mesmo
de o detector começar a trabalhar. Nosso trabalho implementa, do zero, o
Canny clássico e uma versão modificada — que filtra com um banco de Gabor
e funde a informação de cor no domínio das derivadas, à maneira vetorial
de Di Zenzo — e compara os dois nas seis imagens fornecidas."

**MOSTRAR:** nada ainda (ou um slide de título).

---

## 2. A tese em 60 segundos — o caso extremo (2 min)

**MOSTRAR:** `resultados\experimento2\GrayAndMagenta\painel_comparacao.png`

**FALA:** "Esta imagem tem duas cores: cinza RGB (100,100,100) e magenta
RGB (172,34,251). Façam a conta comigo para o magenta:
0,299×172 = 51,4; 0,587×34 = 20,0; 0,114×251 = 28,6. Soma: 100,0.
O cinza, obviamente, também dá 100. Ou seja: depois da conversão para
tons de cinza, esta imagem é uma CONSTANTE — não existe gradiente. O
painel do meio mostra o Canny clássico: zero pixels de borda. Não é um
bug nem má calibração: é impossibilidade matemática. O painel da direita
é o nosso Canny modificado: a borda vertical completa, com exatamente um
pixel de largura. Esse é o fenômeno que motiva todo o trabalho; nas
próximas seções mostramos COMO chegamos nele."

**FAÇA:** aponte os três painéis na ordem original → clássico → modificado.
Escreva a aritmética do Y no quadro/slide — fazer a conta ao vivo
desarma a pergunta "vocês têm certeza de que é isoluminante?".

---

## 3. Arquitetura e entrada das imagens (1,5 min)

**MOSTRAR:** a árvore de pastas no Explorer (`src`, `config`,
`experimentos`, `testes`, `resultados`).

**FALA:** "O sistema é modular, como pede a especificação. **Entrada de
imagens:** o Pillow é usado SÓ para decodificar o arquivo — JPG, PNG ou
WEBP — para uma matriz NumPy float H×W×3 na faixa 0 a 255; a partir daí,
só os nossos módulos tocam os dados. Dois cuidados na entrada: imagens
RGBA com transparência real, como o escudo do Barcelona, são compostas
sobre fundo branco manualmente — alfa vezes a cor mais um-menos-alfa vezes
branco —, e a conversão para cinza do Canny clássico é feita pela fórmula
manual exigida na especificação, nunca pela do Pillow. Os scripts de
experimento processam automaticamente as seis imagens fornecidas, e temos
um utilitário de demonstração que aceita qualquer imagem por argumento —
vamos usá-lo ao vivo daqui a pouco."

**Módulos (aponte as pastas):** "Módulo A — filtragem espacial genérica;
Módulo B — gerador do banco de Gabor; Módulo C — o pipeline modificado;
mais o Canny clássico, NMS, histerese e visualização, compartilhados."

---

## 4. Módulo A — filtragem espacial por arquivos de configuração (2 min)

**MOSTRAR (1):** `config\sobel_x.txt` aberto no Bloco de Notas.
**MOSTRAR (2):** `config\gaussiana_5x5.json` aberto no Bloco de Notas.

**FALA:** "O Módulo A implementa a correlação bidimensional espacial do
zero — a soma de K(u,v) vezes a vizinhança do pixel, na definição direta,
no domínio espacial. Não usamos cv2.filter2D, scipy, nem FFT. E, como a
especificação exige, o programa LÊ as máscaras estáticas de arquivos
externos: aqui está o Sobel X num arquivo texto — notem que dá para editar
no Bloco de Notas — e aqui a Gaussiana 5×5 num JSON, com um campo
'normalizar' que faz o carregador dividir pela soma dos coeficientes.
Como provamos que a correlação está correta sem mostrar código? Temos uma
suíte com 38 testes que compara a nossa correlação com um cálculo de
referência feito com laços explícitos, elemento por elemento, nos dois
modos de borda — replicação e zeros — em imagens cinza e RGB. Rodamos ela
ao vivo no final."

**Pergunta que isso já responde:** "como sei que não usaram função
pronta?" → seção 11, P1.

---

## 5. Módulo B — banco de Gabor paramétrico (2,5 min)

**MOSTRAR (1):** `config\gabor_banco_padrao.json` no Bloco de Notas.
**MOSTRAR (2):** `resultados\experimento1\kernels_banco_padrao.png`.

**FALA:** "O Módulo B carrega TODOS os parâmetros do banco de um arquivo
JSON — tamanho da máscara, sigma, lambda, gamma, psi e a lista de
orientações, exatamente os nomes da especificação — e gera as máscaras
dinamicamente pela fórmula do Gabor: uma envoltória gaussiana elíptica
vezes uma portadora cossenoidal rotacionada. Aqui está o banco padrão:
máscara 31×31, sigma 4, lambda 8, gamma 0,5, psi −π/2 e oito orientações,
de 0 a 157,5 graus de 22,5 em 22,5." [troque para a figura dos kernels]
"E aqui estão as oito máscaras geradas — claro é positivo, escuro é
negativo, já com a expansão de histograma que a especificação manda usar
para exibição, porque os valores reais são negativos e positivos. Notem a
rotação progressiva: theta é a direção da VARIAÇÃO, então o filtro de
theta 0 detecta bordas VERTICAIS."

**FAÇA (plante a semente do demo):** "Guardem o psi = −π/2: daqui a pouco
mostramos POR QUE essa escolha — e o que acontece de errado com psi = 0."

---

## 6. Módulo C — o pipeline modificado, passo a passo (3 min)

**MOSTRAR (1):** `resultados\apresentacao\gm_resposta_por_canal_theta0.png`

**FALA (passos 1–3):** "O coração do trabalho. Passo um: para cada uma das
oito orientações, a MESMA máscara é aplicada aos canais R, G e B
separadamente, pelo Módulo A — os canais nunca se misturam na filtragem.
Esta figura mostra isso na GrayAndMagenta com o filtro de theta 0, tudo na
MESMA escala de cinza: o canal R responde com máximo 1929, o G com 1768, o
B com 4046 — cada canal enxerga a borda individualmente. Passo dois, a
fusão de Di Zenzo: a norma Euclidiana das três respostas, pixel a pixel.
Raiz de 1929² mais 1768² mais 4046² dá 4818 — exatamente o máximo do
painel 'fusão L2'. E o último painel é a resposta do mesmo filtro sobre o
Y em tons de cinza: máximo 0,00002. Preto. A informação morre na projeção,
não no filtro. Passo três: das oito orientações, cada pixel guarda a
magnitude MÁXIMA e o ângulo vencedor — a Orientação Final."

**MOSTRAR (2):** `resultados\experimento2\PlacaMercosul\painel_modificado.png`

**FALA (passos 4–5):** "Passos quatro e cinco, nesta placa real: da
esquerda para a direita — o mapa de magnitudes de Di Zenzo; o afinamento
por supressão de não-máximos, guiado pela Orientação Final, comparando
cada pixel com os dois vizinhos ortogonais à borda; a classificação da
histerese — branco é forte, cinza é fraco, preto suprimido; e as bordas
finais, onde os fracos só sobrevivem se conectados a um forte."

---

## 7. Experimento 1 — sensibilidade paramétrica (4 min)

### 7.1 Lambda: frequência espacial

**MOSTRAR:** `resultados\experimento1\Zebra\painel_lambda_modificado.png`
(e `kernels_varredura_lambda.png` se houver tempo)

**FALA:** "Lambda é o comprimento de onda da portadora. Com lambda 4, o
filtro sintoniza alta frequência: capim e textura fina respondem;
estruturas largas somem. Com lambda 8, as listras da zebra — período
compatível — atingem resposta máxima. Com lambda 16, invertem-se os
papéis: os MACROCONTORNOS dominam — silhueta, horizonte, nuvens — e as
listras finas começam a se fundir. Documentamos isso nas seis imagens; a
magnitude máxima cresce com lambda porque, com menos oscilações sob a
envoltória, há menos cancelamento ao integrar um degrau."

### 7.2 Sigma: a pergunta do sigma excessivo

**MOSTRAR:** `resultados\experimento1\Zebra\painel_sigma_modificado.png`

**FALA:** "Sigma é a escala da envoltória. A especificação pergunta o que
acontece com sigma excessivo num cenário texturizado — testamos sigma 12,
máscara 73×73, e a resposta está aqui: o suporte do filtro, de mais ou
menos 36 pixels, engloba VÁRIOS períodos das listras. As respostas de
bordas vizinhas, com sinais opostos, se sobrepõem dentro da envoltória e
se cancelam parcialmente: o mapa degenera nessas manchas borradas, os
máximos se DESLOCAM das bordas reais e o NMS em cima disso produz cristas
largas e espúrias. É o compromisso de incerteza espaço-frequência:
seletividade em frequência ao custo de localização espacial."

### 7.3 Psi: por que −π/2 (a pergunta-armadilha respondida antes)

**MOSTRAR:** `resultados\experimento1\GrayAndMagenta\painel_psi.png`

**FALA:** "Prometemos explicar o psi. Com psi 0 a portadora é cossenoidal —
filtro PAR, simétrico. Sobre um degrau, um filtro par tem resposta NULA
exatamente no centro da borda, com dois picos simétricos a um quarto de
lambda de cada lado — vejam o vale escuro no meio da faixa, e o NMS
devolvendo DUAS linhas paralelas. Linha dupla. Com psi −π/2 a portadora é
senoidal — filtro ÍMPAR, anti-simétrico, soma exatamente zero — e o pico é
ÚNICO, no centro do degrau. Por isso o banco padrão usa psi −π/2: é o
detector de degraus correto para um pipeline que afina para um pixel."

### 7.4 Gamma (rápido)

**MOSTRAR:** `resultados\experimento1\FCBarcelona\painel_gamma.png`

**FALA:** "Gamma controla a elipsicidade. Gamma 0,25 alonga a envoltória
AO LONGO da borda: contornos retos ficam mais contínuos; cantos borram.
Gamma 1, isotrópico, localiza curvas melhor com resposta mais fraca.
Adotamos 0,5 como meio-termo."

### 7.5 Escalar × vetorial em todas as configurações

**MOSTRAR:** `resultados\experimento1\GrayAndMagenta\painel_tradicional_vs_modificado.png`

**FALA:** "E o ponto central do Experimento 1: aplicamos o MESMO banco de
duas formas — sobre o Y, escalar, e sobre R,G,B com fusão, vetorial. Na
GrayAndMagenta o escalar deu máximo ZERO nas CINCO configurações testadas
— lambda 4, 8, 16, sigma 2 e 12. Nenhum parâmetro salva o método escalar,
porque a informação já foi destruída antes do filtro."

---

## 8. Experimento 2 — afinamento e histerese (4 min)

### 8.1 Limiares justificados

**MOSTRAR:** tabela da seção 5.1 do `RELATORIO.md` (impressa ou na tela).

**FALA:** "Como escolhemos Thigh e Tlow? Três regras. Primeira: Thigh é o
percentil 90 dos valores que SOBREVIVEM ao NMS — depois do afinamento só
restam picos de crista candidatos, então o percentil se adapta ao conteúdo:
deu 184 no urso clássico e 7951 no escudo modificado, sem ajuste manual
por imagem. Segunda: Tlow é 0,4 vezes Thigh — razão de 2,5 para 1, dentro
da faixa de 2:1 a 3:1 recomendada pelo próprio Canny: a histerese rastreia
continuações fracas sem semear ruído. Terceira: um piso absoluto de 0,5 —
o menor degrau real possível em dados 0–255 gera magnitude Sobel maior ou
igual a 4, enquanto ruído de arredondamento float fica em 10⁻⁴; sem esse
piso, uma imagem SEM estrutura teria o percentil adaptado ao ruído de
máquina e produziria bordas falsas. Foi exatamente o que detectamos e
corrigimos na GrayAndMagenta em cinza: máximo 7,6 vezes 10 elevado a menos
6 — com o piso, o sistema responde 'não há bordas', que é o correto."

### 8.2 Prova do 1 pixel

**MOSTRAR (1):** `resultados\experimento2\GrayAndMagenta\painel_zoom_mod.png`
**MOSTRAR (2):** `resultados\experimento2\PlacaMercosul\painel_zoom_mod.png`

**FALA:** "A especificação pede demonstração por zoom digital de que as
linhas finais têm exatamente um pixel. Zoom de 8 vezes por replicação de
pixels, na janela de maior densidade de bordas: magnitude como faixa
larga; pós-NMS reduzido a cristas de um pixel; bordas finais limpas. E
quantificamos: contamos blocos 2×2 totalmente preenchidos — numa linha de
1 pixel não deveria haver nenhum, exceto em junções onde duas bordas se
cruzam. Resultado: zero por cento na GrayAndMagenta — 224 linhas, um pixel
em cada — e abaixo de 0,3% em TODAS as imagens, com os raros casos em
cruzamentos de cristas. No NMS, garantimos o pixel único mesmo em platôs
de magnitude igual com um critério de desempate assimétrico — estritamente
maior de um lado, maior-ou-igual do outro."

### 8.3 Comparação final + caso real

**MOSTRAR (1):** `resultados\experimento2\FCBarcelona\painel_comparacao.png`

**FALA:** "O caso real mais revelador. O clássico, 2603 pixels: pega a
silhueta — contraste enorme com o fundo branco — mas perde quase toda a
estrutura interna. Por quê? Medimos as cores das listras inferiores: grená
RGB (162,33,75) tem Y igual a 76; azul RGB (0,82,159) tem Y igual a 66.
Diferença de DEZ níveis em 255 — quatro por cento — abaixo de qualquer
limiar útil. É a GrayAndMagenta acontecendo numa imagem do mundo real. No
espaço RGB, a distância entre essas cores é 189. O modificado, 7036
pixels: listras, divisão dos quartéis, faixa FCB, bola com costuras."

**MOSTRAR (2):** `resultados\experimento2\Zebra\painel_comparacao.png` (contraponto honesto)

**FALA:** "Honestidade científica: onde a luminância JÁ carrega as bordas —
listras preto-e-branco — o clássico é competitivo e 50 a 100 vezes mais
rápido: 1,7 segundo contra 64 no urso. O modificado custa 8 orientações
vezes máscara 31×31 vezes 3 canais; o clássico, uma Gaussiana 5×5 e dois
Sobéis 3×3 num canal só. O ganho do vetorial aparece quando a cor importa."

---

## 9. Demonstração ao vivo (2 min) — o momento mais forte

**FAÇA (terminal, fonte grande):**

```
python demo.py GrayAndMagenta.png
```

**FALA (enquanto roda — termina em ~1 s):** "Ao vivo: o pipeline completo
na GrayAndMagenta. Vejam a saída: modificado — Tlow 1927, Thigh 4818,
224 pixels de borda, zero blocos 2×2; clássico — limiares infinitos, ZERO
bordas. Sem truque: é a imagem do enunciado, processada agora."

**FAÇA (abra `resultados\demo\GrayAndMagenta\painel_comparacao.png`).**

**FAÇA (segunda demo — Módulo B dirigido por arquivo):**

```
python demo.py GrayAndMagenta.png --banco config\experimentos\gabor_t31_s4_l16_g0.5_psim1.5708.json --metodo modificado
```

**FALA:** "E para provar que o banco é 100% dirigido por configuração:
mesmo comando, outro JSON — lambda 16 em vez de 8. Os limiares mudam
— Thigh vai a 10024 — e a borda continua sendo encontrada. Se o professor
quiser, rodamos com QUALQUER imagem: `python demo.py <arquivo>`."

**Plano B:** se o terminal falhar, os mesmos painéis já existem em
`resultados\demo\` (rodados na véspera) — mostre-os e siga.

### 9.1 Validação automática (30 s, opcional se houver tempo)

```
python testes\testes_sanidade.py
```

**FALA:** "38 verificações: correlação contra cálculo manual com laços,
carga de filtros, simetrias do Gabor, NMS de um pixel em platôs, histerese,
expansão de histograma, fórmula do Y e o pipeline isoluminante completo.
Todas passando."

---

## 10. Fechamento (1 min)

**FALA:** "Concluindo: implementamos do zero os três módulos e os dois
detectores; mostramos que os parâmetros do Gabor governam O QUE é borda —
lambda escolhe a banda, sigma troca localização por seletividade e em
excesso destrói a localização, gamma troca continuidade por curvatura, psi
decide entre detector de linhas e de degraus; e demonstramos a tese
central nas duas pontas: na imagem-limite construída — zero contra 224
pixels com largura de exatamente um — e numa imagem real, as listras do
escudo com delta-Y de dez níveis. O custo é computacional: 50 a 100 vezes.
Quando a cor importa, ele se paga. Perguntas?"

---

## 11. Banco de perguntas prováveis — com respostas prontas

**P1. "Como sei que vocês não usaram cv2/scipy escondido?"**
R: "Pode verificar ao vivo:" → FAÇA: `findstr /s /i "cv2 scipy skimage" src\*.py experimentos\*.py demo.py`
→ só aparecem duas docstrings dizendo que NÃO usamos. E o
`requirements.txt` só tem numpy, pillow e matplotlib (este último só gera
o gráfico de perfil do relatório).

**P2. "A abordagem de vocês é o Di Zenzo 'de verdade'?"** (armadilha)
R: "O Di Zenzo original de 1986 monta o tensor de estrutura — a soma dos
produtos externos dos gradientes por canal — e extrai o maior autovalor.
A especificação define uma variante mais direta do mesmo princípio: fundir
a cor NO DOMÍNIO DAS DERIVADAS, pela norma L2 das respostas por canal, com
redução por máximo sobre as orientações do banco. Implementamos exatamente
o fluxo da especificação. O espírito é o mesmo — derivar antes, fundir
depois — e o caso isoluminante prova que a propriedade essencial foi
preservada."

**P3. "Correlação ou convolução? Faz diferença?"**
R: "Implementamos correlação, como a especificação pede — sem o flip do
kernel. Para máscaras simétricas (Gaussiana, Gabor par) é idêntico; para
as ímpares (Sobel, Gabor senoidal) muda só o sinal/orientação da resposta,
e nossas máscaras de arquivo já estão na convenção de correlação. A
magnitude — que é o que limiarizamos — não muda."

**P4. "O banco tem 8 orientações, mas o NMS só compara em 4 direções. Por quê?"**
R: "A vizinhança discreta 8-conexa só oferece 4 eixos: 0°, 45°, 90° e
135°. Quantizamos a Orientação Final para o eixo mais próximo — erro
máximo de 22,5°, o mesmo esquema do Canny clássico. As 8 orientações do
banco continuam valendo para a MAGNITUDE (seletividade do filtro); a
quantização afeta só a escolha do par de vizinhos no afinamento. A prova
de que basta: blocos 2×2 abaixo de 0,3% em todas as imagens."

**P5. "Por que percentil 90 e não Otsu / um valor fixo?"**
R: "Valor fixo não transfere entre imagens — as magnitudes vão de centenas
a dezenas de milhares conforme conteúdo e kernel. Otsu pressupõe histograma
bimodal de intensidades, que não é o caso de magnitudes pós-NMS. O
percentil sobre os SOBREVIVENTES do NMS limiariza exatamente a população
de interesse — picos de crista — e se adapta sozinho; os 12 valores usados
estão na tabela 5.1 do relatório."

**P6. "E os dois lóbulos fracos paralelos na GrayAndMagenta? Não são bordas falsas?"**
R: "São os lóbulos laterais do filtro ímpar, a meio lambda da borda, com
metade da magnitude. Ficam entre Tlow e Thigh — fracos — e NÃO tocam a
linha forte, então a histerese os elimina: dos 448 fracos, zero entraram
no resultado. É a histerese fazendo exatamente o papel dela."

**P7. "Por que máscara 31 para sigma 4? E 73 para sigma 12?"**
R: "Regra de ~6 sigma + 1: cobre 3 desvios de cada lado, 99,7% da
envoltória. 6×4+1 = 25; usamos 31, o valor de exemplo da especificação,
que cobre com folga. Para sigma 12: 6×12+1 = 73."

**P8. "Por que replicar a borda em vez de preencher com zeros?"**
R: "Zeros criam um degrau artificial na moldura da imagem — o filtro
responderia forte no contorno inteiro, gerando bordas falsas. Replicar o
pixel da margem estende a imagem de forma neutra. Implementamos os dois
modos; replicação é o padrão e foi usada em todos os experimentos."

**P9. "Float32 não perde precisão?"**
R: "As magnitudes chegam a ~4×10⁴; com precisão relativa de 10⁻⁷ do
float32, o erro absoluto é da ordem de 10⁻³ — irrelevante contra limiares
de milhares. E os testes comparam contra referência em float64 com
tolerância apertada, passando."

**P10. "Funciona com ruído?"** (honestidade)
R: "Não há experimento com ruído na especificação nem no nosso roteiro —
seria a extensão natural. A expectativa teórica: a envoltória gaussiana do
Gabor já é um filtro passa-baixa embutido — sigma controla essa robustez —
e o limiar por percentil sobe junto com o assoalho de ruído. Podemos rodar
ao vivo com qualquer imagem ruidosa que o senhor fornecer: o demo aceita
qualquer arquivo."

**P11. "Onde o modificado é PIOR que o clássico?"** (honestidade — tenha isso pronto)
R: "Três pontos. Custo: 50 a 100 vezes mais caro. Na placa: o modificado
resolve as DUAS bordas de cada traço de caractere — contorno duplo — onde
o clássico dá um traço único mais limpo, porque lambda 8 está na escala da
largura do traço. E em cenas onde a luminância já carrega tudo, como as
listras da zebra, o ganho não justifica o custo."

**P12. "Como vocês exibem mapas com valores negativos?"**
R: "Expansão de histograma para [0,255], como a Seção 3 da especificação
manda — só para exibição; o pipeline opera nos valores reais. Detalhe
honesto: a expansão é individual por mapa, então brilho não é comparável
entre painéis — por isso os rótulos trazem o máximo real de cada um. Na
figura por canal, usamos escala COMUM justamente para poder comparar."

**P13. "Se eu der uma imagem em tons de cinza ao modificado, o que acontece?"**
R: "Ela é decodificada como RGB com R=G=B; as três respostas ficam iguais
e a fusão L2 vira raiz de 3 vezes a resposta escalar — o modificado
degenera elegantemente para o comportamento escalar, como esperado."

**P14. "Por que compor o RGBA sobre branco e não preto?"**
R: "Branco é o fundo de documento padrão e o fundo natural do escudo. A
escolha muda as bordas da silhueta — qualquer composição cria uma borda
com o fundo escolhido — e está documentada; o miolo da imagem não é
afetado."

**P15. "Qual a complexidade?"**
R: "O(H·W·k²) por canal por orientação. Modificado: ×3 canais ×8
orientações com k=31; clássico: k=5 mais dois k=3 num canal. Medido: 63,9 s
contra 1,7 s na imagem de 2,4 megapixels."

**P16. "Esse psi = −π/2 não é 'cola' para o NMS funcionar?"**
R: "É uma escolha de projeto justificada experimentalmente — está no
painel do psi: o filtro par tem resposta nula no centro do degrau, então
NENHUM pós-processamento recupera a linha única; o ímpar é o detector de
degraus correto. A especificação deixa psi como parâmetro livre do banco,
e nós documentamos o efeito dos dois valores."

**P17. "Os limiares foram escolhidos por imagem na mão?"**
R: "Não — a regra (P90 + razão 0,4 + piso) é UMA só para todas as imagens
e métodos; a tabela 5.1 mostra os valores RESULTANTES. O sistema também
aceita limiares manuais, que usamos para estudo, não nos resultados."

---

## 12. Cola de comandos (deixar no histórico do terminal)

```
python demo.py GrayAndMagenta.png
python demo.py GrayAndMagenta.png --banco config\experimentos\gabor_t31_s4_l16_g0.5_psim1.5708.json --metodo modificado
python demo.py FCBarcelona.png
python testes\testes_sanidade.py
python testes\teste_e2e.py
findstr /s /i "cv2 scipy skimage" src\*.py experimentos\*.py demo.py
```

Tempos esperados: GrayAndMagenta ~1 s; FCBarcelona ~8 s; Zebra ~10 s;
Bear ~65 s (NÃO rode a Bear ao vivo — use os painéis prontos).

---

## 13. Números para decorar (a "cola" de bolso)

| Fato | Número |
|---|---|
| Y do cinza E do magenta na GrayAndMagenta | 100,0 (isoluminante exato) |
| Clássico × modificado na GrayAndMagenta | 0 px × 224 px (224/224 linhas com 1 px) |
| Magnitude clássico na GrayAndMagenta | 7,6×10⁻⁶ (ruído float) × 4818 no modificado |
| Fusão na figura por canal (θ=0) | √(1929²+1768²+4046²) = 4818 |
| Listras do escudo: grená × azul | Y 76 × 66 (ΔY≈10); distância RGB ≈ 189 |
| FCBarcelona: bordas | clássico 2603 × modificado 7036 |
| Blocos 2×2 cheios (pior caso) | 0,27% (Zebra mod.); G&M = 0% |
| Custo na Bear (2,4 MP) | 63,9 s × 1,7 s (~37×; até ~100× conforme imagem) |
| Limiares | Thigh = P90 pós-NMS; Tlow = 0,4·Thigh; piso 0,5 |
| Testes | 38 de sanidade + E2E em 5 etapas, todos passando |

---

## 14. Mapa requisito → evidência visual (se o professor pedir prova item a item)

| Exigência da especificação | Evidência (abrir) |
|---|---|
| Correlação própria lendo filtros .txt/.json | `config\sobel_x.txt`, `config\gaussiana_5x5.json` + testes verdes |
| Banco de Gabor via JSON, máscaras dinâmicas | `config\gabor_banco_padrao.json` + `kernels_banco_padrao.png` + demo com `--banco` |
| Filtragem por canal + fusão L2 | `resultados\apresentacao\gm_resposta_por_canal_theta0.png` |
| Redução por máximo + Orientação Final | `painel_modificado.png` (magnitude + NMS guiado) |
| NMS com exatamente 1 px | `painel_zoom_mod.png` (qualquer imagem) + métrica 2×2 |
| Histerese fortes/fracos/suprimidos | painel "classes" (branco/cinza/preto) em `painel_modificado.png` |
| Expansão de histograma p/ exibição | qualquer mapa + rótulos com máximos reais |
| Y manual | conta ao vivo na seção 2 + teste verde |
| Exp. 1: λ, σ (excessivo), métodos | painéis `painel_lambda_*`, `painel_sigma_*`, `painel_tradicional_vs_modificado` |
| Exp. 2: lado a lado, zoom, limiares, G&M | `painel_modificado`, `painel_zoom_*`, tabela 5.1, `perfil_linha_central.png` |

---

## 15. Lembretes de logística (especificação, itens fora deste roteiro)

- E-mail "Equipe de PDI" para leonardo@ci.ufpb.br até **15/06/2026**.
- Relatório IMPRESSO entregue na apresentação; PDF + código enviados até a
  primeira aula de apresentações (entrega: 01/07/2026).
- Todos os integrantes presentes; qualquer um pode receber qualquer
  pergunta — todos devem ensaiar a seção 11.
