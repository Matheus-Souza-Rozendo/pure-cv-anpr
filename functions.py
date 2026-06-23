import cv2
import numpy as np
import os
import math

def carregar_imagens_placa(pasta, inicio, fim):
    """
    Carrega imagens do padrão 'placaX.jpg' de uma pasta para uma lista.

    """
    lista_imagens = []
    for x in range(inicio, fim + 1):
        nome_arquivo = f"placa{x}.jpg"
        caminho_completo = os.path.join(pasta, nome_arquivo)
        img = cv2.imread(caminho_completo)
        if img is not None:
            lista_imagens.append(img)
    return lista_imagens


def calcula_bounding_box(contour):
    x, y, w, h = cv2.boundingRect(contour)
    return np.array([x, y]),np.array([x + w - 1, y + h - 1])

def Extrair_bounding_boxes(I_bin):
    infoRegioes = []

    contours, hierarchy = cv2.findContours(I_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    for cnt in contours:
        dados_do_componente = dict()

        p0, p1 = calcula_bounding_box(cnt)

        dados_do_componente['bounding_box_p0'] =p0
        dados_do_componente['bounding_box_p1'] =p1

        infoRegioes.append(dados_do_componente)

    return infoRegioes


def recortar_imagem(I, po,p1,borda=1):
  min_x = po[0]
  max_x = p1[0]
  min_y = po[1]
  max_y = p1[1]
  min_x = max(0, min_x - borda)
  min_y = max(0, min_y - borda)
  max_x = min(I.shape[1], max_x + borda)
  max_y = min(I.shape[0], max_y + borda)

  return I[min_y:max_y, min_x:max_x]

def gerar_dicionario_letras(template_letras,LETRAS):
  _, binarized_template = cv2.threshold(template_letras, 127, 255, cv2.THRESH_BINARY_INV)
  info_letras = Extrair_bounding_boxes(binarized_template)
  dicionario_letras = dict()

  for i, regiao in enumerate(info_letras):
    p0 = regiao['bounding_box_p0']
    p1 = regiao['bounding_box_p1']
    dicionario_letras[LETRAS[i]] = recortar_imagem(template_letras, p0, p1)

  return dicionario_letras

def binarizacao(imagem,cor_referencia,limiar):
  distancia = np.linalg.norm(imagem - cor_referencia, axis=2)
  binaria = np.where(distancia <= limiar, 1, 0).astype(np.uint8)*255
  return binaria

def filtragem(imagem,numero_iteracoes):
  kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)) # cria um kernel retangular
  binaria_aberta = cv2.morphologyEx(imagem, cv2.MORPH_OPEN, kernel) # realiza o processo de abertura da imagem binaria
  for _ in range(numero_iteracoes-1):
      binaria_aberta = cv2.morphologyEx(binaria_aberta, cv2.MORPH_OPEN, kernel)
  return binaria_aberta

def analisarRegiao(I_labels,indice):
    dados_do_componente = dict()
    component_image = np.uint8((I_labels == indice)) * 255
    area = cv2.countNonZero(component_image) # calculo a area da imagem
    if area < 500:
        return None

    dados_do_componente['image'] = component_image.copy()
    return dados_do_componente

def analisaRegioes(I_bin):
    infoRegioes = []

    num_labels, I_labels = cv2.connectedComponents(I_bin) #etiquetar cada ilha de pixels brancos

    for n in np.arange(1, num_labels): #ignora a posicao 0 pois ela é o fundo
        dados_do_componente = analisarRegiao(I_labels,n)
        if dados_do_componente is not None:
          infoRegioes.append(dados_do_componente.copy())

    return infoRegioes

def segmentarObjetoPorRegiao(img_original, img_regiao_bin):
    contours, _ = cv2.findContours(img_regiao_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None
    maior_contorno = max(contours, key=cv2.contourArea)
    mask = np.zeros_like(img_regiao_bin)
    cv2.drawContours(mask, [maior_contorno], -1, 255, thickness=cv2.FILLED)
    objeto_segmentado = cv2.bitwise_and(img_original, img_original, mask=mask)
    return objeto_segmentado

def segmentar_placa(imagem_binaria):
  info_regioes = analisaRegioes(imagem_binaria) #listar todos os "objetos" brancos isolados

  regiao_da_placa = None
  regioes_candidatas = []

  for regiao in info_regioes:
    regiao_invertida = cv2.bitwise_not(regiao['image']) #inverto para que as letras fiquem brancas e o fundo preto
    subregioes = analisaRegioes(regiao_invertida) # #listar todos os "objetos" brancos isolados dentro das subregiões
    num_subregioes = len(subregioes) # verifica quantas subregiões tem
    if num_subregioes>1: # se for apenas uma, assume se que não é a região da placa
      info = {
          'image':regiao['image'],
          'nivel_de_confianca':abs(num_subregioes-7), # calcula assumindo que a placa do mercosul tem 7 caracteres
          'num_subregioes':num_subregioes # desempate caso o nivel de confiança de empate
      }
      regioes_candidatas.append(info)

  regioes_candidatas = sorted(regioes_candidatas, key=lambda x: x['nivel_de_confianca']) #ordena pelo nivel de confiança

  if regioes_candidatas:

    menor = regioes_candidatas[0]['nivel_de_confianca'] #acha o menor nivel de confiança (quanto menor, melhor)
    regioes_candidatas = [r for r in regioes_candidatas if r['nivel_de_confianca'] == menor] # filtra apenas o que tem o menor valor
    if len(regioes_candidatas) > 1:
      regioes_candidatas = sorted(regioes_candidatas, key=lambda x: x['num_subregioes']) #se deu empate ordena pelo numero de subregiões
    regiao_da_placa = regioes_candidatas[-1]['image'] # pega a subregião com mais regiões
    return segmentarObjetoPorRegiao(imagem_binaria,regiao_da_placa) #segmenta a região da placa

def localizar_coordenada_placa(imagem):
  contours, h = cv2.findContours(imagem, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  cnt = contours[0]

  for k in np.linspace(0.01, 0.1, 50):
    epsilon = k * cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, epsilon, True)

    if len(approx) == 4:
        return approx
  return None

def ordenar_pontos(coordenadas_forma):
    pontos = []
    coordenadas = coordenadas_forma.reshape(-1, 2)
    for coordenada in coordenadas:
        x = coordenada[0]
        y = coordenada[1]
        ponto = {'x': x, 'y': y,'distancia_origem':math.dist((x,y),(0,0))}
        pontos.append(ponto)

    pontos = sorted(pontos, key=lambda x: x['distancia_origem'])
    return pontos

def transformar_placa(imagem,origem,destino,largura_maxima,altura_maxima):
    M = cv2.getPerspectiveTransform(origem.astype("float32"), destino)
    return cv2.warpPerspective(imagem, M, (largura_maxima, altura_maxima))

def processar_imagem(imagem,cor_referencia,limiar_binarizacao,numero_iteracoes,altura_maxima,largura_maxima,nome):
    imagem_binaria = binarizacao(imagem,cor_referencia,limiar_binarizacao) #binarizo a imagem
    imagem_filtrada = filtragem(imagem_binaria,numero_iteracoes) # filtro a imagem
    imagem_segmentada = segmentar_placa(imagem_filtrada) #segmento a região da placa
    

    if (nome==1 or nome==11 or nome == 10):
       cv2.imshow(f'imagem binaria {nome}',imagem_binaria)
       cv2.imshow(f'imagem Abertura morfologica {nome}',imagem_filtrada)
       cv2.imshow(f'imagem segmentada {nome}',imagem_segmentada)
       

    coordenadas_placa = localizar_coordenada_placa(imagem_segmentada) #localizo as coordenadas da placa
    
    pontos_ordenados = ordenar_pontos(coordenadas_placa)
    
    #cria os pontos de destino e origem
    destino = np.array([[0, 0], [largura_maxima, 0], [largura_maxima, altura_maxima], [0, altura_maxima]], dtype="float32")
    inicio = np.array([[pontos_ordenados[0]['x'],pontos_ordenados[0]['y']],[pontos_ordenados[2]['x'],pontos_ordenados[2]['y']],[pontos_ordenados[3]['x'],pontos_ordenados[3]['y']],[pontos_ordenados[1]['x'],pontos_ordenados[1]['y']]])
    return transformar_placa(imagem_segmentada,inicio,destino,largura_maxima,altura_maxima)

def analisar_placa(placa, templates,letras):
    # Binariza a imagem da placa
    _, placa_binaria = cv2.threshold(placa, 127, 255, cv2.THRESH_BINARY_INV)

    # Encontra contornos
    contornos_placa, _ = cv2.findContours(placa_binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Ordena contornos por área (maior → menor) e pega somente os 7 maiores
    contornos_maiores = sorted(contornos_placa, key=cv2.contourArea, reverse=True)[:7]

    # Reordena os 7 maiores da esquerda para a direita
    contornos_maiores = sorted(contornos_maiores, key=lambda c: cv2.boundingRect(c)[0])

    # Padrão da placa Mercosul: AAA1A11
    # L = letra, D = dígito
    padrao_tipos = ['L', 'L', 'L', 'D', 'L', 'D', 'D']

    img_contornos = cv2.cvtColor(placa, cv2.COLOR_GRAY2BGR)
    texto_reconhecido = ""

    # Processar somente os contornos selecionados
    for idx, contorno in enumerate(contornos_maiores):
        # Se por algum motivo tiver mais de 7 contornos, ignora o resto
        if idx >= len(padrao_tipos):
            break

        tipo_esperado = padrao_tipos[idx]

        (x, y, w, h) = cv2.boundingRect(contorno)
        area = cv2.contourArea(contorno)

        # Recorta o contorno (sem área mínima)
        letra_detectada = placa_binaria[y:y + h, x:x + w]

        # Desenha caixa
        cv2.rectangle(img_contornos, (x, y), (x + w, y + h), (255, 0, 0), 1)

        # Variáveis para guardar o melhor resultado
        melhor_letra = None
        melhor_score = -1.0

        # Vamos percorrer o dicionário na ordem DEFINIDA por LETRAS
        for ch in letras:
            # Se o template dessa letra/número não existir, pula
            if ch not in templates:
                continue

            # Filtra por tipo esperado (letra ou número)
            if tipo_esperado == 'L' and not ch.isalpha():
                continue
            if tipo_esperado == 'D' and not ch.isdigit():
                continue

            template = templates[ch]

            # Redimensiona para o tamanho do template
            letra_detectada_resized = cv2.resize(
                letra_detectada,
                (template.shape[1], template.shape[0])
            )

            # Inverte template sem alterar o original
            template_invertido = cv2.bitwise_not(template)

            # Aplica o matchTemplate
            resultado = cv2.matchTemplate(
                letra_detectada_resized,
                template_invertido,
                cv2.TM_CCOEFF_NORMED
            )

            score = float(np.max(resultado))


            # Guarda o melhor score/letra
            if score > melhor_score:
                melhor_score = score
                melhor_letra = ch

        # Depois de testar as letras/números permitidos pra essa posição, decide a melhor

        if melhor_letra is not None and melhor_score >= 0.05:
            texto_reconhecido += melhor_letra
            cv2.putText(
                img_contornos,
                melhor_letra,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                1,
                cv2.LINE_AA
            )

    return img_contornos, texto_reconhecido