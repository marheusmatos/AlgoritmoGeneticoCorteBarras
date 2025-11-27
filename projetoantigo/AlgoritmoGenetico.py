import random
import math
import copy
import time


class AlgoritmoGenetico:

    def __init__(self, tamPopulacao, tamBarra, demandaTotal):
        
        #Dados
        self.tamPopulacao   = tamPopulacao
        self.tamBarra       = tamBarra
        self.qtdTotalItens  = len(demandaTotal)
        self.demandaTotal   = demandaTotal
        self.maxIterations = 100

        self.populacao          = [] # Guarda a população corrente
        self.populacaoPadroes   = [] # Populacao decodificada

        # A soma das duas porcentagens deve ser igual à 0.5 (50%)
        self.porcentagemElitista = 0.15
        self.porcentagemTorneio  = (0.5 - self.porcentagemElitista)

    def imprimeFitness(self):

        for i, individuo in enumerate(self.populacao):
            print("Fitness", i, ":", individuo['fitness'])

    def execute(self):

        inicio = time.time()

        self.gerarPopulaçãoInicial()

        for it in range(self.maxIterations):

            print('Iteração:', it)

            print("Entrando na Decodificação")
            self.decodificacao()
            print("Saindo da Decodificação")

            print("Entrando na Função de Fitness")
            self.calculaFitnessPopulacao()
            print("Saindo da Função de Fitness")

            # Ordena a população e população de padrões decrescentemente pelo fitness
            self.populacao.sort(key = lambda individuo: individuo['fitness'], reverse=True)
            self.populacaoPadroes.sort(key = lambda individuo: individuo[-1]['fitness'], reverse=True)

            for indice, individuoPadrao in enumerate(self.populacaoPadroes):
                print("Individuo:", indice, "- Barras:", len(individuoPadrao), "- Fitness:", self.populacao[indice]['fitness'])

            print('Tempo decorrido: %.2f segundos' %(time.time() - inicio))

            print("Entrando na Seleção")
            self.selecao()
            print("Saindo da Seleção")

            intervaloAceitacao = 0.5

            if self.verificaHomogeneidade(intervaloAceitacao):
                print("!!!!!! CONVERGIU !!!!!!")
                print(self.populacao)
                print('Tempo decorrido: %.2f segundos' %(time.time() - inicio))
                break

            self.populacaoPadroes = []

    def selecao(self):

        proximaGeracao = []

        tamanhoIndividuo = len(self.populacao[0]['individuo'])

        numCompetidoresPorRodada    = int(self.tamPopulacao * 0.2)  # 30% do tamanho da população
        numPontos                   = int(tamanhoIndividuo * 0.1)   # 30% do tamanho do cromossomo do individuo
        numMutacoes                 = 300

        fatiaElitista   = math.ceil(self.tamPopulacao * self.porcentagemElitista)
        fatiaTorneio    = math.ceil(self.tamPopulacao * self.porcentagemTorneio)

        # Copia os primeiros individuos elitistamente
        for i in range(fatiaElitista):
            proximaGeracao.append(self.populacao[i])
            self.populacao.pop(i)

        # Seleciona alguns individuos por torneio
        individuosSelecionados = self.torneio(numCompetidoresPorRodada, fatiaTorneio, self.populacao)

        # Adiciona os individuos selecionados por torneio à proxima geração
        for i in range(fatiaTorneio):
            proximaGeracao.append(individuosSelecionados[i])

        # Faz o cruzamento dos individuos e adicionam os filhos à proxima geração
        for i in range(0, len(proximaGeracao), 2):
            
            filhos = self.cruzamentoNpontos(numPontos, proximaGeracao[i], proximaGeracao[i + 1])
        
            for filho in filhos:
                proximaGeracao.append(filho)

        while len(proximaGeracao) > self.tamPopulacao:
            proximaGeracao.pop(-1)

        # Atribui a próxima geração à população
        self.populacao = proximaGeracao

        # Calcula os fitness dos individuos resultantes
        self.calculaFitnessPopulacao()

        # Verifica o fitness de cada individuo da nova população e
        # se o individuo for infactivel (fitness < 0.0) então factibiliza-o
        for individuo in self.populacao:

            fitness = individuo['fitness']

            if fitness < 0.0:
                self.factibilizacaoAleatoria(individuo)

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

        # Armazena o fitness no indivíduo
    
    def calculaFitness(self, indiceIndividuo):
        
        individuo = self.populacao[indiceIndividuo]['individuo']
        
        qtdBarras = len(self.populacaoPadroes[indiceIndividuo])
        
        fitness = 1000 / qtdBarras

        if(self.calculaItensNaoAtendidos(individuo)):
            fitness *= -1
        
        self.populacao[indiceIndividuo]['fitness'] = fitness
        self.populacaoPadroes[indiceIndividuo][-1]['fitness'] = fitness
    
    def calculaFitnessPopulacao(self):
        
        for indice in range(self.tamPopulacao):
            self.calculaFitness(indice)

    def printPopulacao(self):

        for i in range(len(self.populacao)):
            print('Individuo ' + str(i+1) + ':', self.populacao[i])

    def printPopulacaoPadroes(self):
        for i in range(len(self.populacaoPadroes)):
            print('Individuo ' + str(i+1) + ':', self.populacaoPadroes[i])

    def gerarIndividuo(self):
        individuo = {'individuo': []}
        demandas = copy.deepcopy(self.demandaTotal)

        while demandas != []:
            i = random.randint(0, len(demandas) - 1)

            demanda = demandas[i]
            item = demandas[i]['item']
            individuo['individuo'].append(item)
            demanda['quantidade'] -= 1
            if(demanda['quantidade'] == 0):
                demandas.pop(i)

        self.populacao.append(individuo)

    def gerarPopulaçãoInicial(self):
        for i in range(self.tamPopulacao):
            self.gerarIndividuo()

    def decodificacao(self):
        
        populacaoCopia = copy.deepcopy(self.populacao)

        for individuo in populacaoCopia:
            individuoPadroes = []
            while individuo['individuo'] != []:
                individuoPadroes.append(self.criaPadrao())
                i = 0
                while i < len(individuo['individuo']): 
                    item = individuo['individuo'][i]

                    if(self.demandaTotal[item]['tamanho']  <= individuoPadroes[-1]['sobra']):
                        individuoPadroes[-1]['padrao'].append(item)
                        individuoPadroes[-1]['sobra'] -= self.demandaTotal[item]['tamanho']
                        individuo['individuo'].pop(i)
                        i -= 1
                    i += 1
                        
            self.populacaoPadroes.append(individuoPadroes)

    def criaPadrao(self):
        return {'padrao': [], 'sobra': self.tamBarra}

    def calculaItensNaoAtendidos(self, individuo):
        
        #alocando lista
        itensIndividuo = [0 for x in range(self.qtdTotalItens)]

        for item in individuo:
            itensIndividuo[item] += 1

        itensNaoAtendidos = 0

        for i in range(self.qtdTotalItens):
            if itensIndividuo[i] < self.demandaTotal[i]['quantidade']:
                itensNaoAtendidos += 1

        return itensNaoAtendidos

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

            # Obtém uma lista com os indices dos competidores restantes
            indicesCompetidores = list(range(len(competidores)))
            
            # Sorteia os competidores que participarão desta rodada do torneio
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
        return competidoresSelecionados

    def mutacaoTrocaAlelos(self, numMutacoes, individuo):
        
        indices = []

        individuo = copy.deepcopy(individuo['individuo'])

        for i in range(len(individuo)):
            for j in range(len(individuo)):

                if i != j and j >= i:
                    indices.append((i, j))

        if numMutacoes <= len(indices):

            indicesSelecionados = random.sample(indices, numMutacoes)

            for src, dst in indicesSelecionados:
                aux = individuo[src]
                individuo[src] = individuo[dst]
                individuo[dst] = aux

        return {'individuo': individuo}

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