import random
import math
import copy
import time
import os
import pandas as pd


class AlgoritmoGenetico:

    def __init__(self, tamPopulacao, larguraBarra, alturaBarra, demandaTotal):
        # Dados do GA
        self.tamPopulacao   = tamPopulacao
        self.larguraBarra   = larguraBarra
        self.alturaBarra    = alturaBarra
        self.qtdTotalItens  = len(demandaTotal)
        self.demandaTotal   = demandaTotal  # lista de dicts {'item', 'largura','altura','quantidade'}
        self.maxIterations = 200

        self.populacao          = [] # Guarda a população corrente
        self.populacaoPadroes   = [] # Populacao decodificada

        # A soma das duas porcentagens deve ser igual à 0.5 (50%)
        self.porcentagemElitista = 0.15
        self.porcentagemTorneio  = (0.5 - self.porcentagemElitista)
        
        self.best_fitness = -math.inf
        self.best_population = []
        self.best_population_patterns = []

        # Pré-computação da lista expandida de itens (cada cópia por quantidade)
        # evita reconstruir a lista toda vez ao gerar indivíduos
        self._expanded_items_template = []
        for d in self.demandaTotal:
            for _ in range(d['quantidade']):
                self._expanded_items_template.append(d['item'])

    def imprimeFitness(self):

        for i, individuo in enumerate(self.populacao):
            print("Fitness", i, ":", individuo['fitness'])

    def execute(self):

        inicio = time.time()

        self.gerarPopulaçãoInicial()

        for it in range(self.maxIterations):

            # prints reduzidos para não poluir I/O
            if it % 10 == 0:
                print('Iteração:', it)

            print("Entrando na Decodificação")
            # decodifica cada indivíduo para layouts 2D (BLF-like)
            self.populacaoPadroes = []
            self.decodificacao()
            print("Saindo da Decodificação")

            print("Entrando na Função de Fitness")
            self.calculaFitnessPopulacao()
            print("Saindo da Função de Fitness")

            # ordena por fitness desc
            self.populacao.sort(key = lambda individuo: individuo['fitness'], reverse=True)
            # populaçaoPadroes corresponde à mesma ordem da população antes da ordenação,
            # então reordenamos para manter correspondência
            # (assumimos que a ordem é a mesma aqui porque geramos pop e popPadroes em mesma ordem)
            # para segurança, reconstruímos com correspondência por cromossomo string
            # Armazenamento da melhor
            current_best_fitness_in_iteration = self.populacao[0]['fitness']
            if current_best_fitness_in_iteration > self.best_fitness:
                self.best_fitness = current_best_fitness_in_iteration
                self.best_population = copy.deepcopy(self.populacao)
                self.best_population_patterns = copy.deepcopy(self.populacaoPadroes)
            
            for indice, individuoPadrao in enumerate(self.populacaoPadroes):
                print("Individuo:", indice, "- Barras:", len(individuoPadrao), "- Fitness:", self.populacao[indice]['fitness'])

            print('Melhor fitness nesta iteração:', current_best_fitness_in_iteration)
            print('Tempo decorrido: %.2f segundos' %(time.time() - inicio))

            print("Entrando na Seleção")
            self.selecao()
            print("Saindo da Seleção")
            
            # critério de convergência
            if it % 20 == 0:  # checagem ocasional de homogeneidade
                intervaloAceitacao = 0.5
                if self.verificaHomogeneidade(intervaloAceitacao):
                    print("Convergiu na iteração", it)
                    break
            
            print('Execução finalizada. Melhor fitness:', self.best_fitness)

            if self.verificaHomogeneidade(intervaloAceitacao):
                print("!!!!!! CONVERGIU !!!!!!")
                print(self.populacao)
                print('Tempo decorrido: %.2f segundos' %(time.time() - inicio))
                break

            self.populacaoPadroes = []

    def selecao(self):

        proximaGeracao = []

        tamanhoIndividuo = len(self.populacao[0]['individuo'])

        numCompetidoresPorRodada    = max(2, int(self.tamPopulacao * 0.2))
        numRodadas                  = max(1, int(self.tamPopulacao * self.porcentagemTorneio))

        fatiaElitista   = math.ceil(self.tamPopulacao * self.porcentagemElitista)
        fatiaTorneio    = math.ceil(self.tamPopulacao * self.porcentagemTorneio)

        # Copia os primeiros individuos elitistamente
        for i in range(fatiaElitista):
            proximaGeracao.append(copy.deepcopy(self.populacao[i]))

        # torneio para preencher fatiaTorneio
        restantes = self.populacao[fatiaElitista:]
        selecionados = self.torneio(numCompetidoresPorRodada, fatiaTorneio, restantes)

        # preencher o resto por cruzamento (circular)
        while len(proximaGeracao) < self.tamPopulacao:
            pai = random.choice(proximaGeracao)
            mae = random.choice(proximaGeracao)
            filhos = self.cruzamentoOx(pai, mae)
            for f in filhos:
                proximaGeracao.append(f)
                if len(proximaGeracao) >= self.tamPopulacao:
                    break
        
        # mutação simples: troca alelos (swap) em alguns indivíduos
        numMutacoesPorIndividuo = max(1, int(0.05 * tamanhoIndividuo))
        for i in range(fatiaElitista, len(proximaGeracao)):
            if random.random() < 0.3:
                proximaGeracao[i] = self.mutacaoTrocaAlelos(numMutacoesPorIndividuo, proximaGeracao[i])

        self.populacao = proximaGeracao
        
    def cruzamentoOx(self, pai, mae):
        
        # Order Crossover (OX) para permutações
        pai_seq = pai['individuo']
        mae_seq = mae['individuo']
        n = len(pai_seq)
        a, b = sorted(random.sample(range(n), 2))
        filho1 = [-1]*n
        filho2 = [-1]*n
        
        # copia segmento
        filho1[a:b+1] = pai_seq[a:b+1]
        filho2[a:b+1] = mae_seq[a:b+1]
            
        # implementação direta sem helpers:
        def fill_from(filho, other):
            
            n = len(filho)
            idx = (b+1)%n
            
            for gene in other[(b+1)%n:] + other[:(b+1)%n]:
                if gene not in filho:
                    while filho[idx] != -1:
                        idx = (idx+1)%n
                    filho[idx] = gene
        
        fill_from(filho1, mae_seq)
        fill_from(filho2, pai_seq)
        
        return [{'individuo': filho1}, {'individuo': filho2}]

    def verificaHomogeneidade(self, intervaloAceitacao):

        def distanciaEuclidiana(primeiro, segundo):

            valor = 0.0

            for i in range(len(primeiro)):
                valor += (primeiro[i] - segundo[i])**2

            return math.sqrt(valor)

        def erroAbsoluto(primeiro, segundo):

            valor = 0.0
            for i in range(len(primeiro)):

                valor += abs(primeiro[i] - segundo[i])

            return valor / len(primeiro)


        individuoBase = self.populacao[0]

        for individuo in self.populacao:

            #similaridade = distanciaEuclidiana(individuoBase['individuo'], individuo['individuo'])
            similaridade = erroAbsoluto(individuoBase['individuo'], individuo['individuo'])

            print("Erro Absoluto:", similaridade)

            if similaridade > intervaloAceitacao:
                return False

        return True
    
    def calculaFitness(self, indiceIndividuo):
        
        individuo = self.populacao[indiceIndividuo]
        padroes = self.populacaoPadroes[indiceIndividuo]
        
        # contar placas usadas e área desperdiçada
        placas = [p for p in padroes if 'placed_rects' in p]
        placas_usadas = len(placas)
        area_total = placas_usadas * (self.larguraBarra * self.alturaBarra)
        area_usada = sum(( (p['width']*p['height']) - p['sobra']) for p in placas) if placas else 0
        area_desperdicio = area_total - area_usada if placas_usadas>0 else 0
        
        # itens não colocados
        not_placed = 0
        for p in padroes:
            if 'not_placed' in p:
                not_placed += len(p['not_placed'])

        # penalidades e combinação
        # melhor fitness: menos placas, menos desperdício, zero not_placed
        if placas_usadas == 0:
            fitness = -1000.0 - 1000.0 * not_placed
        else:
            fitness = 1000.0 / placas_usadas
            # subtrai penalidade proporcional ao desperdício relativo
            fitness -= 0.5 * (area_desperdicio / (self.larguraBarra * self.alturaBarra))
            # penalidade forte para itens não colocados
            fitness -= 50.0 * not_placed
        
        individuo['fitness'] = fitness

        if(self.calculaItensNaoAtendidos(individuo)):
            fitness *= -1
        
        self.populacao[indiceIndividuo]['fitness'] = fitness
        self.populacaoPadroes[indiceIndividuo][-1]['fitness'] = fitness
    
    def calculaFitnessPopulacao(self):
        
        for indice in range(len(self.populacao)):
            self.calculaFitness(indice)

    def save_results(self, output_dir='output'):
        os.makedirs(output_dir, exist_ok=True)

        if not self.best_population:
            print("Nenhuma melhor população encontrada para salvar.")
            return

        # salva melhor população
        population_data = []
        for individual_dict in self.best_population:
            population_data.append({
                'individual_chromosome': str(individual_dict['individuo']),
                'fitness': individual_dict.get('fitness')
            })
        df_population = pd.DataFrame(population_data)
        df_population.to_csv(os.path.join(output_dir, 'best_population.csv'), index=False)
        print(f"Melhor população salva em {os.path.join(output_dir, 'best_population.csv')}")

        # salva padrões do melhor indivíduo (se existir)
        if self.best_population_patterns:
            best_ind = self.best_population_patterns[0]
            patterns_data = []
            for p in best_ind:
                if 'placed_rects' in p:
                    patterns_data.append({
                        'pattern_items': str([r['item'] for r in p['placed_rects']]),
                        'remaining_area': p['sobra'],
                        'width': p.get('width'),
                        'height': p.get('height')
                    })
                elif 'not_placed' in p:
                    patterns_data.append({
                        'pattern_items': str([]),
                        'remaining_area': None,
                        'width': None,
                        'height': None,
                        'not_placed': str(p['not_placed'])
                    })
            df_patterns = pd.DataFrame(patterns_data)
            df_patterns.to_csv(os.path.join(output_dir, 'best_individual_patterns.csv'), index=False)
            print(f"Padrões do melhor indivíduo salvos em {os.path.join(output_dir, 'best_individual_patterns.csv')}")
        else:
            print("Nenhum padrão do melhor indivíduo encontrado para salvar.")

    def gerarIndividuo(self):
        individuo = {'individuo': []}
        demandas = self._expanded_items_template[:]  # cópia rasa da lista de ids

        # expandir por quantidade (cada cópia é um item)
        for d in self.demandaTotal:
            for _ in range(d['quantidade']):
                demandas.append(d['item'])
                
        random.shuffle(demandas)
        individuo['individuo'] = demandas

        return individuo

    def gerarPopulaçãoInicial(self):
        self.populacao = []
        for i in range(self.tamPopulacao):
            self.populacao.append(self.gerarIndividuo())

    def decodificacao(self):
        # Para cada indivíduo, gera lista de placas; cada placa = {'width','height','placed': [rects], 'remaining_area'}
        largura_barra = self.larguraBarra
        altura_barra = self.alturaBarra
        demanda = self.demandaTotal

        for individuo in self.populacao:
            seq = individuo['individuo']  # já é uma lista de ids
            placas = []

            # Evita reatribuições a self em loops
            for item_id in seq:
                item_def = demanda[item_id]
                w = item_def['width']
                h = item_def['height']
                placed_flag = False

                # tenta colocar em placas existentes (itera placas na ordem atual)
                for placa in placas:
                    pos = self._find_position_for_item_in_plate_fast(placa, w, h)
                    if pos is not None:
                        x, y = pos
                        placa['placed'].append({'item': item_id, 'x': x, 'y': y, 'w': w, 'h': h})
                        placa['remaining_area'] -= (w * h)
                        placed_flag = True
                        break

                if not placed_flag:
                    # abre nova placa
                    nova = {'width': largura_barra, 'height': altura_barra, 'placed': [], 'remaining_area': largura_barra * altura_barra}
                    pos = self._find_position_for_item_in_plate_fast(nova, w, h)
                    if pos is not None:
                        x, y = pos
                        nova['placed'].append({'item': item_id, 'x': x, 'y': y, 'w': w, 'h': h})
                        nova['remaining_area'] -= (w * h)
                        placas.append(nova)
                    else:
                        # item maior que placa: não alocado
                        if 'not_placed' not in individuo:
                            individuo['not_placed'] = []
                        individuo['not_placed'].append(item_id)

            # construir padroes
            padroes = []
            for p in placas:
                padroes.append({'padrao': [r['item'] for r in p['placed']],
                                'sobra': p['remaining_area'],
                                'placed_rects': p['placed'],
                                'width': p['width'],
                                'height': p['height']})
            if 'not_placed' in individuo:
                padroes.append({'not_placed': individuo['not_placed']})
            self.populacaoPadroes.append(padroes)
    
    def _find_position_for_item_in_plate_fast(self, plate, w, h):
        # Versão otimizada: gera candidatos a partir das bordas existentes,
        # usa listas ordenadas e terminate early para reduzir verificações.
        if w > plate['width'] or h > plate['height']:
            return None

        placed = plate['placed']
        if not placed:
            return (0, 0)

        # construir listas ordenadas de candidatos (somente bordas)
        xs = sorted({0} | {r['x'] + r['w'] for r in placed})
        ys = sorted({0} | {r['y'] + r['h'] for r in placed})

        area_w = plate['width']
        area_h = plate['height']

        # tentar candidatos em ordem (menor y primeiro, depois x)
        for y in ys:
            if y + h > area_h:
                break  # este y e todos maiores não cabem verticalmente
            for x in xs:
                if x + w > area_w:
                    continue
                rect = {'x': x, 'y': y, 'w': w, 'h': h}
                if not self._collides_any(rect, placed):
                    return (x, y)
        return None
    
    def _collides_any(self, rect, placed):
        rx1, ry1 = rect['x'], rect['y']
        rx2, ry2 = rect['x'] + rect['w'], rect['y'] + rect['h']
        for p in placed:
            px1, py1 = p['x'], p['y']
            px2, py2 = p['x'] + p['w'], p['y'] + p['h']
            # overlap test (axis-aligned)
            if not (rx2 <= px1 or rx1 >= px2 or ry2 <= py1 or ry1 >= py2):
                return True
        return False
    
    def criaPadrao(self):
        return {'padrao': [], 'sobra': self.tamBarra}

    def calculaItensNaoAtendidos(self, individuo):
        
        # conta quantas cópias de cada item foram colocadas
        contagem = [0 for _ in range(self.qtdTotalItens)]
        
        # individuo['individuo'] contains expanded list; but in padroes usamos padrao lists
        # melhor calcular a partir do populacaoPadroes correspondente
        
        return None  # não usado diretamente nesta versão

    def cruzamentoNpontos(self, numPontos, pai, mae):
        """
            numPontos:  O numero de pontos do cruzamento
            pai:        Cromossomo de um individuo
            mae:        Cromossomo de outro individuo
        """

        filhos          = []
        primeiroFilho   = []
        segundoFilho    = []

        pai = copy.deepcopy(pai['individuo'])
        mae = copy.deepcopy(mae['individuo'])

        numPontosValidos = numPontos >= 1 and numPontos <= len(pai)

        if len(pai) == len(mae) and numPontosValidos:

            # Gera uma lista contendo os pontos candidatos
            pontosCandidatos = list(range(1, len(pai) + 1))

            # Seleciona 'numPontos' pontos dos pontos candidatos
            pontosSelecionados = random.sample(pontosCandidatos, numPontos)

            # Ordena os pontos selecionados em ordem crescente
            pontosSelecionados.sort()
            
            #print("pontos selecionados =", pontosSelecionados)

            turno = 0

            for i in range(len(pai)):
            
                if turno < len(pontosSelecionados) and pontosSelecionados[turno] == i:
                    turno += 1
                
                # Turnos pares
                if turno % 2 == 0:
                    primeiroFilho.append(pai[i])
                    segundoFilho.append(mae[i])

                # Turnos împares
                else:
                    segundoFilho.append(pai[i])
                    primeiroFilho.append(mae[i])

        filhos.append({'individuo': primeiroFilho})
        filhos.append({'individuo':segundoFilho})

        return filhos

    def torneio(self, numCompetidoresPorRodada, numRodadas, competidores):
        """
            numCompetidoresPorRodada:   Numero de individuos que competem em cada rodada
            numRodadas:                 Numero de individuos que se deseja selecionar
            competidores:               Todos os competidores que participarao do torneio
            fitness:                    Os respectivos fitness de cada um dos participantes
        """


        # Faz uma cópia das listas para evitar alterações nas listas originais
        competidores  = copy.deepcopy(competidores)

        # Armazenará os competidores selecionados
        competidoresSelecionados = []

        for rodada in range(numRodadas):

            if len(competidores) == 0:
                break
            
            # Obtém uma lista com os indices dos competidores restantes
            indices = list(range(len(competidores)))
            
            if len(indices) < numCompetidoresPorRodada:
                indicesSorteados = indices
            else:
                indicesSorteados = random.sample(indices, numCompetidoresPorRodada)
            
            melhor = None
            melhor_fit = -math.inf
            
            for idx in indicesSorteados:
                fit = competidores[idx].get('fitness', -math.inf)
                if fit > melhor_fit:
                    melhor = competidores[idx]
                    melhor_fit = fit
            
            competidoresSelecionados.append(melhor)
            competidores.remove(melhor)
        
        return competidoresSelecionados
            
        """# Sorteia os competidores que participarão desta rodada do torneio
            indicesSorteados = random.sample(indicesCompetidores, numCompetidoresPorRodada)

            # Armazenará o indice e o fitness do competidor ganhador desta rodada
            competidorSelecionado = {'indice': -1, 'fitness': -math.inf}
            
            #print("Competidores Sorteados:")
            #for i in indicesSorteados:
            #    print(competidores[i])

            # Para cada competidor sorteado verifica quem possui o maior fitness
            for indice in indicesSorteados:

                if competidores[indice]['fitness'] > competidorSelecionado['fitness']:
                    competidorSelecionado['indice'] = indice
                    competidorSelecionado['fitness'] = competidores[indice]['fitness']

            # Obtém o indice do competidor vencedor desta rodada
            indiceMelhorCompetidor = competidorSelecionado['indice']

            #print("Competidor Selecionado:")
            #print(competidores[indiceMelhorCompetidor])
            #print()

            # Adiciona o competidor vencedor desta rodada na lista de competidores selecionados
            competidoresSelecionados.append(competidores[indiceMelhorCompetidor])

            # Remove o competidor selecionado dos competidores restantes
            competidores.pop(indiceMelhorCompetidor)

        # Retorna a lista dos competidores que foram selecionados
        return competidoresSelecionados"""

    def mutacaoTrocaAlelos(self, numMutacoes, individuo):
        
        ind = copy.deepcopy(individuo['individuo'])
        n = len(ind)
        
        for _ in range(numMutacoes):
            i, j = random.sample(range(n), 2)
            ind[i], ind[j] = ind[j], ind[i]
            
        return {'individuo': ind}

    def mutacaoInsereAlelos(self, numMutacoes, individuo):
        
        indices = []

        individuo = copy.deepcopy(individuo['individuo'])

        indices = list(range(len(individuo)))

        indicesParaMutacao = random.sample(indices, numMutacoes)

        for indice in indicesParaMutacao:

            individuo[indice] = random.randint(0, self.qtdTotalItens - 1)

        return {'individuo': individuo}

    def factibilizacaoAleatoria(self, individuo):

        individuo = individuo['individuo']

        tamanhoAntes = len(individuo)

        #alocando lista
        itensIndividuo = [0 for x in range(self.qtdTotalItens)]

        # Contabiliza a quantidade produzida de cada item
        for item in individuo:
            itensIndividuo[item] += 1

        for i in range(self.qtdTotalItens):
            
            itensNaoAtendidos = itensIndividuo[i] - self.demandaTotal[i]['quantidade']

            # Para itens produzidos alem da demanda
            if itensNaoAtendidos > 0:

                itensNaoAtendidos = itensNaoAtendidos
                itemSuperAtendido = i

                for item in range(itensNaoAtendidos):
                    individuo.remove(itemSuperAtendido)

            # Para itens que não atenderam a demanda
            elif itensNaoAtendidos < 0:

                itensNaoAtendidos = abs(itensNaoAtendidos)

                # Para cada item nao atendido insere o item no individuo
                for passo in range(itensNaoAtendidos):

                    indiceParaInsercao = random.randint(0, len(individuo) - 1)
                    itemNaoAtendido = i

                    individuo.insert(indiceParaInsercao, itemNaoAtendido)
        
        tamanhoDepois = len(individuo)

        if tamanhoAntes != tamanhoDepois:
            print("BUG - TAMANHOS DIFERENTES!")