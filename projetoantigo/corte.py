from AlgoritmoGenetico import AlgoritmoGenetico
import pandas as pd
import os

tam_barra, pedidos = map(int, input().split())

demanda = []

print(f'Tamanho da barra: {tam_barra}, Pedidos: {pedidos}')

i = 0
while i < pedidos:

    tam_pedido, qtd = map(int, input().split())

    demanda.append({'item': i, 'tamanho': tam_pedido, 'quantidade': qtd})
    print(f'Demanda:{demanda}')
    i+=1


algoritmoGenetico = AlgoritmoGenetico(20, tam_barra, demanda)
algoritmoGenetico.execute()
