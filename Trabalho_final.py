import cv2
import numpy as np
import functions

LIMIAR_BINARIZACAO = 100
COR_REFERENCIA = np.array([200, 200, 200])
ABERTURA_ITERACOES = 11
LETRAS = "9876543102ZYXWVUTSRQPONMLKJIHGFEDCBA"
LARGURA_MAXIMA = 834
ALTURA_MAXIMA = 382

template_letras = cv2.imread('banco_de_imagens\\fonte_mercosul.png', cv2.IMREAD_GRAYSCALE)

dicionario_letras = functions.gerar_dicionario_letras(template_letras,LETRAS)

resultados = dict()


def mostrar_imagem(imagem):
    cv2.imshow("Imagem",imagem)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def processar(imagens, n):
    for img in imagens:
      regiao_placa = functions.processar_imagem(img,COR_REFERENCIA,LIMIAR_BINARIZACAO,ABERTURA_ITERACOES,ALTURA_MAXIMA,LARGURA_MAXIMA,n)
      cv2.imshow(f'imagem segmentada {n}',regiao_placa)
      imagem, texto_reconhecido = functions.analisar_placa(regiao_placa, dicionario_letras,LETRAS)
      mostrar_imagem(imagem)
      resultados[f'placa {n}']=texto_reconhecido
      n=n+1

def analisar_resultado(inicio,fim,total_placas):
   total_caracteres = total_placas*7
   total_caracteres_certos = 0
   total_placas_certas = 0
   for i in range(inicio,fim+1):
        caracteres = 0
        for n in range(0,7):
            if resultados[f'placa {i}'][n]==resultados_esperados[f'placa {i}'][n]:
                caracteres=caracteres+1
        total_caracteres_certos = total_caracteres_certos+caracteres
        if caracteres == 7:
            total_placas_certas = total_placas_certas+1

   print("Total placas certas:",total_placas_certas)
   print("Total caracteres certos:",total_caracteres_certos)
   print("Taxa placas certas:",total_placas_certas/total_placas)
   print("Taxa caracteres certos:",total_caracteres_certos/total_caracteres)

   

#Carregando o vetor de imagens
imagensnivel1 = functions.carregar_imagens_placa("banco_de_imagens\\nivel1",1,5)
imagensnivel2 = functions.carregar_imagens_placa("banco_de_imagens\\nivel2",6,12)

processar(imagensnivel1,1)
processar(imagensnivel2,6)

#print(resultados)

resultados_esperados = {
   'placa 1': 'RIO2A18', 
   'placa 2': 'RIO2A18', 
   'placa 3': 'LSN4I49', 
   'placa 4': 'LSU3J43', 
   'placa 5': 'LSN4I49', 
   'placa 6': 'PXL9D49', 
   'placa 7': 'PLQ8F28', 
   'placa 8': 'PLK3J59', 
   'placa 9': 'OZL7H33', 
   'placa 10': 'BDB1B52', 
   'placa 11': 'BCV3G50', 
   'placa 12': 'LQQ4J66'
   }

#analisando resultados nivel 1

print("\n\nresultados nivel 1")
analisar_resultado(1,5,5)

print("\n\nresultados nivel 2")
analisar_resultado(6,12,7)

print("\n\nresultados total")
analisar_resultado(1,12,12)

print("\n\n\n",resultados)





