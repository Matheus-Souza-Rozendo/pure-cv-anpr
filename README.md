# Sistema de Reconhecimento de Placas Veiculares (LPR/ANPR) Clássico

## Sobre o Projeto

Este projeto consiste no desenvolvimento de um sistema de visão computacional capaz de realizar o reconhecimento automático de placas veiculares do padrão Mercosul a partir de imagens digitais coloridas (RGB). A solução foi inteiramente construída utilizando técnicas puras de processamento de imagens, operando em dois níveis de complexidade: condições ideais e cenários com distorções geométricas.

---

## Metodologia e Pipeline de Processamento

A arquitetura da solução foi dividida em cinco etapas principais para garantir a extração correta dos caracteres.

### 1. Pré-processamento

* A segmentação inicial é baseada na distância Euclidiana de cor em relação à área branca da placa, utilizando a referência BGR(200, 200, 200).
* A distância entre o pixel da imagem e a referência é calculada pela fórmula matemática:

$$D(P_{img},P_{ref})=\sqrt{(R_{img}-R_{ref})^{2}+(G_{img}-G_{ref})^{2}+(B_{img}-B_{ref})^{2}}$$


* Pixels com distância inferior ao limiar de 100 assumem o valor branco (255), gerando a imagem binarizada.
* Pequenos ruídos são eliminados utilizando o filtro morfológico de Abertura com um kernel de tamanho 3x3.

### 2. Detecção da Região de Interesse (ROI)

* A extração de componentes conexos lista e rotula os grupos de pixels isolados.
* Regiões com área inferior a 500 pixels são descartadas pelo algoritmo.
* Uma heurística busca identificar a placa contando as sub-regiões (buracos) internas, priorizando componentes cujo número de filhos se aproxime de 7.
* A seleção baseia-se na fórmula de distância de confiança:

$$|N_{sub}-7|$$


* A máscara binária resultante é unida à imagem original por uma operação lógica AND para isolar a placa.

### 3. Correção Geométrica (Transformação de Perspectiva)

* O Algoritmo de Ramer-Douglas-Peucker aproxima o contorno detectado para localizar os quatro vértices exatos da placa.
* Uma matriz de Homografia (H) é calculada para retificar a inclinação do objeto na imagem.
* O mapeamento matemático dos pontos da imagem original para a visão frontal é dado pela equação:

$$s\begin{bmatrix}x^{\prime}\\ y^{\prime}\\ 1\end{bmatrix}=\begin{bmatrix}h_{11}&h_{12}&h_{13}\\ h_{21}&h_{22}&h_{23}\\ h_{31}&h_{32}&h_{33}\end{bmatrix}\begin{bmatrix}x\\ y\\ 1\end{bmatrix}$$



### 4. Segmentação e OCR (Reconhecimento Óptico)

* Os sete maiores contornos são isolados e ordenados horizontalmente para garantir a leitura da esquerda para a direita.
* A classificação utiliza *Template Matching*, comparando os recortes com um banco de imagens da fonte padrão Mercosul.
* A similaridade é medida pelo Coeficiente de Correlação Cruzada Normalizada, que é robusto a variações de iluminação.
* O valor de correlação R é obtido através da equação:

$$R(x,y)=\frac{\sum_{x^{\prime},y^{\prime}}(T^{\prime}(x^{\prime},y^{\prime})\cdot I^{\prime}(x+x^{\prime},y+y^{\prime}))}{\sqrt{\sum_{x^{\prime},y^{\prime}}T^{\prime}(x^{\prime},y^{\prime})^{2}\cdot\sum_{x^{\prime},y^{\prime}}P^{\prime}(x+x^{\prime},y+y^{\prime})^{2}}}$$


* Para evitar falsos positivos, aplica-se uma validação posicional estrita baseada na máscara de caracteres Letra/Dígito (L-L-L-D-L-D-D).

---

## Resultados Obtidos

O sistema foi validado em um conjunto de dados dividido por dificuldade, demonstrando alta eficácia no método proposto.

| Nível de Dificuldade | Total Placas | Acertos Placa | Acurácia (Placas) | Chars Corretos | Acurácia (Chars) |
| --- | --- | --- | --- | --- | --- |
| Nível 1 | 5 | 5 | 100% | 35/35 | 100% |
| Nível 2 | 7 | 6 | 85,7% | 48/49 | 97,9% |
| Geral | 12 | 11 | 91,6% | 83/84 | 98,8% |
| *Tabela de desempenho do algoritmo.* |  |  |  |  |  |

* **Acurácia Global:** 91,6% de acerto nas placas inteiras e 98,8% nos caracteres individuais.
* **Robustez:** Nas amostras do Nível 1 (cenário ideal), obteve-se 100% de precisão.
* **Casos Limites:** A única falha registrada ocorreu devido à fusão visual entre o logo do Mercosul e a letra "B" (lida como "T") em uma das amostras com distorção.
