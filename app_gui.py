'''
NOME: David Mendes
SINTESE DO CONTEUDO: Aplicacao em Python com Interface Grafica para modelagem, 
manipulacao e analise de conexidade de um grafo direcionado e ponderado, focado em 
rotas de transporte publico acessiveis via dados GTFS da SPTrans.
'''


import os
import re
import csv
import heapq  # Fila de prioridade para o algoritmo de Dijkstra.
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import networkx as nx
import matplotlib.pyplot as plt


# =====================================================================
# 1) e 2) CLASSE LOGICA DO GRAFO (Lista de Adjacencias)
# =====================================================================
class GrafoLista:
    def __init__(self, direcionado=True):
        self.direcionado = direcionado
        self.tipo_grafo = 6 # Orientado com peso na aresta
        self.adjacencias = {} 
        self.rotulos = {}     
        self.arquivo_atual = "" 
        # Estado separado do peso: so contem restricoes simuladas validadas.
        self.acessibilidade = {}
        # Indica se o grafo foi modificado apos o carregamento.
        # Evita utilizar o CSV original em um grafo editado.
        self.csv_desatualizado = False

    # c) Permite inserir novos vertices juntamente com seus rotulos
    def inserir_vertice(self, id_vertice, rotulo):
        if id_vertice not in self.adjacencias:
            self.adjacencias[id_vertice] = []
            self.rotulos[id_vertice] = rotulo
            self.acessibilidade.clear()  # Uma edicao exige nova conferencia do CSV.
            # Marca o CSV como desatualizado apos uma alteracao no grafo.
            self.csv_desatualizado = True
            return True, f"Vertice {id_vertice} inserido!"
        return False, "Vertice ja existe. ID deve ser unico."

    # d) Permite inserir novas arestas com os respectivos pesos
    def inserir_aresta(self, u, v, peso):
        # Dijkstra exige pesos nao negativos. Rejeita a operacao antes
        # de inserir ou atualizar qualquer aresta na memoria.
        if peso < 0:
            return False, "O peso da aresta nao pode ser negativo."

        if u in self.adjacencias and v in self.adjacencias:
            for aresta in self.adjacencias[u]:
                if aresta[0] == v:
                    aresta[1] = peso
                    self.acessibilidade.clear()
                    # Marca o CSV como desatualizado apos uma alteracao no grafo.
                    self.csv_desatualizado = True
                    return True, f"Aresta {u}->{v} atualizada."
            self.adjacencias[u].append([v, peso])
            self.acessibilidade.clear()
            # Marca o CSV como desatualizado apos uma alteracao no grafo.
            self.csv_desatualizado = True
            return True, f"Aresta {u}->{v} inserida."
        return False, "Vertices de origem ou destino nao existem."

    # e) Permite remover vertices (removendo arestas associadas automaticamente)
    def remover_vertice(self, id_vertice):
        if id_vertice in self.adjacencias:
            del self.adjacencias[id_vertice]
            if id_vertice in self.rotulos:
                del self.rotulos[id_vertice]
            for u in self.adjacencias:
                self.adjacencias[u] = [a for a in self.adjacencias[u] if a[0] != id_vertice]
            self.acessibilidade.clear()
            # Marca o CSV como desatualizado apos uma alteracao no grafo.
            self.csv_desatualizado = True
            return True, "Vertice e conexoes removidos."
        return False, "Vertice nao encontrado."

    # f) Permite remover arestas
    def remover_aresta(self, u, v):
        if u in self.adjacencias:
            tam_orig = len(self.adjacencias[u])
            self.adjacencias[u] = [a for a in self.adjacencias[u] if a[0] != v]
            if len(self.adjacencias[u]) < tam_orig:
                self.acessibilidade.clear()
                # Marca o CSV como desatualizado apos uma alteracao no grafo.
                self.csv_desatualizado = True
                return True, "Aresta removida."
            return False, "Aresta nao encontrada."
        return False, "Vertice de origem nao existe."

    # a) Carrega o grafo apenas depois de validar todo o arquivo.
    # Evita apagar o grafo anterior quando o arquivo selecionado e invalido.
    def ler_arquivo(self, caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as arquivo:
                linhas = [linha.strip() for linha in arquivo if linha.strip()]

            if len(linhas) < 3:
                raise ValueError("Arquivo incompleto: faltam os dados iniciais.")

            tipo = int(linhas[0])
            if tipo != 6:
                raise ValueError("O projeto aceita apenas grafos do tipo 6.")

            n = int(linhas[1])
            if n < 0:
                raise ValueError("Quantidade de vertices nao pode ser negativa.")
            if len(linhas) < n + 3:
                raise ValueError("Arquivo incompleto: faltam vertices ou arestas.")

            # Estruturas temporarias preservam o grafo atual ate o fim da validacao.
            novas_adjacencias = {}
            novos_rotulos = {}
            padrao_vertice = re.compile(r'^(\d+)\s+"([^"]*)"\s+(-?\d+)$')

            for idx in range(2, 2 + n):
                partes = padrao_vertice.fullmatch(linhas[idx])
                if partes is None:
                    raise ValueError(f"Vertice mal formatado na linha {idx + 1}.")

                vertice = int(partes.group(1))
                rotulo = partes.group(2)
                if vertice in novas_adjacencias:
                    raise ValueError(f"Vertice duplicado: {vertice}.")
                novas_adjacencias[vertice] = []
                novos_rotulos[vertice] = rotulo

            pos_arestas = 2 + n
            m = int(linhas[pos_arestas])
            if m < 0:
                raise ValueError("Quantidade de arestas nao pode ser negativa.")
            if len(linhas) != pos_arestas + 1 + m:
                raise ValueError("Quantidade de linhas diferente do total de arestas informado.")

            arestas_encontradas = set()
            for idx in range(pos_arestas + 1, len(linhas)):
                campos = linhas[idx].split()
                if len(campos) != 3:
                    raise ValueError(f"Aresta mal formatada na linha {idx + 1}.")
                origem, destino, peso = map(int, campos)

                if origem not in novas_adjacencias or destino not in novas_adjacencias:
                    raise ValueError(f"Aresta com vertice inexistente na linha {idx + 1}.")
                if peso < 0:
                    raise ValueError(f"Peso negativo na linha {idx + 1}.")
                if (origem, destino) in arestas_encontradas:
                    raise ValueError(f"Aresta duplicada na linha {idx + 1}.")

                arestas_encontradas.add((origem, destino))
                novas_adjacencias[origem].append([destino, peso])

            # So altera os atributos do objeto se todas as verificacoes passarem.
            self.adjacencias = novas_adjacencias
            self.rotulos = novos_rotulos
            self.tipo_grafo = tipo
            self.arquivo_atual = caminho
            self.acessibilidade.clear()  # Dados de outro grafo nao sao reaproveitados.
            # Uma leitura valida inicia uma nova versao do grafo, ainda sem edicoes.
            # Assim, o CSV correspondente pode ser carregado e validado novamente.
            self.csv_desatualizado = False
            return True, "Arquivo carregado com sucesso!"
        except (OSError, ValueError, IndexError) as erro:
            return False, f"Erro ao ler: {erro}"

    # Le a classificacao simulada separadamente dos custos do grafo.
    # Antes de aplicar o CSV, confere TODAS as arestas e seus tempos.
    # Isso evita associar restricoes a outro arquivo grafo.txt por engano.
    def ler_acessibilidade_csv(self, caminho):
        # Nao reutiliza o CSV de origem apos edicoes feitas pela interface.
        # Recarregar um grafo valido pela opcao a) libera nova validacao.
        if self.csv_desatualizado:
            return False, ("O grafo foi modificado. Recarregue o arquivo original "
                           "antes de consultar os dados de acessibilidade.")

        if not self.adjacencias:
            return False, "Carregue o grafo antes do CSV de acessibilidade."

        try:
            with open(caminho, "r", encoding="utf-8-sig", newline="") as arquivo:
                leitor = csv.DictReader(arquivo)
                obrigatorias = {"origem_id", "destino_id", "tempo_min",
                                "acessibilidade", "origem_informacao"}
                if not obrigatorias.issubset(leitor.fieldnames or []):
                    raise ValueError("O CSV nao possui todas as colunas obrigatorias.")

                # Consulta rapida do peso de cada aresta do grafo carregado.
                pesos = {(u, v): peso for u, ligacoes in self.adjacencias.items()
                         for v, peso in ligacoes}
                temporario = {}
                estados_validos = {"inacessivel_simulado", "nao_verificada"}
                for numero, linha in enumerate(leitor, start=2):
                    u = int(linha["origem_id"])
                    v = int(linha["destino_id"])
                    tempo = int(linha["tempo_min"])
                    estado = linha["acessibilidade"].strip()
                    par = (u, v)
                    if par not in pesos:
                        raise ValueError(f"Linha {numero}: aresta {u}->{v} nao existe no grafo.")
                    if par in temporario:
                        raise ValueError(f"Linha {numero}: aresta duplicada {u}->{v}.")
                    if pesos[par] != tempo:
                        raise ValueError(f"Linha {numero}: tempo diferente do grafo em {u}->{v}.")
                    if estado not in estados_validos:
                        raise ValueError(f"Linha {numero}: classificacao desconhecida: {estado}.")
                    temporario[par] = estado

                if set(temporario) != set(pesos):
                    raise ValueError("O CSV precisa conter todas as arestas do grafo atual.")

            # So altera o estado quando o CSV inteiro foi validado.
            self.acessibilidade = temporario
            restritas = sum(estado == "inacessivel_simulado"
                            for estado in temporario.values())
            return True, (f"CSV carregado: {len(temporario)} arestas;\n "
                          f"{restritas} com restricao SIMULADA;\n "
                          f"{len(temporario)-restritas} vertices sem acessibilidade verificada.")
        except (OSError, ValueError, TypeError) as erro:
            return False, f"Falha ao ler acessibilidade: {erro}"

    # l) Encontra o caminho minimo com Dijkstra em um grafo orientado.
    # Se evitar_restricoes=True, descarta apenas as arestas marcadas no CSV.
    # As demais arestas NAO sao comprovadamente acessiveis.
    # Retorno: (caminho, tempo_total); quando nao ha caminho, (None, None).
    def dijkstra(self, origem, destino, evitar_restricoes=False):
        if origem not in self.adjacencias or destino not in self.adjacencias:
            raise ValueError("Origem ou destino nao existe no grafo.")
        if evitar_restricoes and not self.acessibilidade:
            raise ValueError("Carregue o CSV de acessibilidade para aplicar o filtro.")

        # Dijkstra pressupoe pesos nao negativos.
        for conexoes in self.adjacencias.values():
            for _, peso in conexoes:
                if peso < 0:
                    raise ValueError("Dijkstra nao aceita arestas com pesos negativos.")

        distancias = {origem: 0}
        anteriores = {}
        fila = [(0, origem)]  # (tempo acumulado, vertice)

        while fila:
            tempo_atual, atual = heapq.heappop(fila)
            # Ignora entradas antigas da fila, que ja foram melhoradas.
            if tempo_atual != distancias.get(atual):
                continue
            if atual == destino:
                break

            for vizinho, peso in self.adjacencias[atual]:
                if (evitar_restricoes and
                        self.acessibilidade.get((atual, vizinho)) == "inacessivel_simulado"):
                    continue
                novo_tempo = tempo_atual + peso
                if novo_tempo < distancias.get(vizinho, float("inf")):
                    distancias[vizinho] = novo_tempo
                    anteriores[vizinho] = atual
                    heapq.heappush(fila, (novo_tempo, vizinho))

        if destino not in distancias:
            return None, None

        # Reconstroi o percurso, do destino ate a origem, usando antecessores.
        caminho = [destino]
        while caminho[-1] != origem:
            caminho.append(anteriores[caminho[-1]])
        caminho.reverse()
        return caminho, distancias[destino]

    # b) Deve gravar o grafo da memoria RAM para o arquivo grafo.txt
    def gravar_arquivo(self, caminho):
        try:
            with open(caminho, 'w', encoding='utf-8') as file:
                file.write(f"{self.tipo_grafo}\n")
                file.write(f"{len(self.adjacencias)}\n")
                for u in self.adjacencias:
                    file.write(f'{u} "{self.rotulos[u]}" 0\n')
                
                total_arestas = sum(len(conexoes) for conexoes in self.adjacencias.values())
                file.write(f"{total_arestas}\n")
                
                for u in self.adjacencias:
                    for v, peso in self.adjacencias[u]:
                        file.write(f"{u} {v} {peso}\n")
            self.arquivo_atual = caminho
            return True, "Arquivo salvo com sucesso!"
        except Exception as e:
            return False, f"Erro ao salvar: {str(e)}"

    # LOGICA INTERNA PARA O ITEM (i) - FCONEX (Algoritmo de Kosaraju)
    def _dfs(self, v, visitados, pilha):
        visitados.add(v)
        if v in self.adjacencias:
            for vizinho, _ in self.adjacencias[v]:
                if vizinho not in visitados:
                    self._dfs(vizinho, visitados, pilha)
        pilha.append(v)

    def _transpor_grafo(self):
        g_transposto = {u: [] for u in self.adjacencias}
        for u in self.adjacencias:
            for v, peso in self.adjacencias[u]:
                if v not in g_transposto:
                    g_transposto[v] = []
                g_transposto[v].append([u, peso])
        return g_transposto

    def _dfs_transposto(self, v, visitados, g_transposto, componente):
        visitados.add(v)
        componente.append(v)
        if v in g_transposto:
            for vizinho, _ in g_transposto[v]:
                if vizinho not in visitados:
                    self._dfs_transposto(vizinho, visitados, g_transposto, componente)

    def analisar_conexidade(self):
        visitados = set()
        pilha = []
        for i in self.adjacencias:
            if i not in visitados:
                self._dfs(i, visitados, pilha)

        g_transposto = self._transpor_grafo()
        visitados.clear()
        componentes = []

        while pilha:
            v = pilha.pop()
            if v not in visitados:
                componente = []
                self._dfs_transposto(v, visitados, g_transposto, componente)
                componentes.append(componente)
                
        return componentes

    # Classifica a conexidade do grafo conforme as categorias C0 a C3.
    # A analise considera a direcao das arestas, mas nao seus pesos.
    def classificar_conexidade(self, componentes=None):
        if not self.adjacencias:
            return "C0 (Grafo vazio)"

        if componentes is None:
            componentes = self.analisar_conexidade()
        if len(componentes) == 1:
            return "C3 (Fortemente conexo)"

        # Primeiro verifica a conexidade fraca, ignorando os sentidos das arestas.
        vizinhos = {u: set() for u in self.adjacencias}
        for origem, conexoes in self.adjacencias.items():
            for destino, _ in conexoes:
                vizinhos[origem].add(destino)
                vizinhos[destino].add(origem)

        inicio = next(iter(vizinhos))
        visitados = {inicio}
        pendentes = [inicio]
        while pendentes:
            atual = pendentes.pop()
            for vizinho in vizinhos[atual]:
                if vizinho not in visitados:
                    visitados.add(vizinho)
                    pendentes.append(vizinho)

        if len(visitados) != len(vizinhos):
            return "C0 (Desconexo)"

        # Condensa as componentes fortemente conexas em um grafo reduzido.
        # Nele, C2 exige que todo par de componentes tenha um caminho
        # direcionado em pelo menos um dos dois sentidos.
        indice = {vertice: i for i, comp in enumerate(componentes)
                  for vertice in comp}
        reduzido = {i: set() for i in range(len(componentes))}
        for origem, conexoes in self.adjacencias.items():
            for destino, _ in conexoes:
                if indice[origem] != indice[destino]:
                    reduzido[indice[origem]].add(indice[destino])

        alcances = {}
        for inicio_comp in reduzido:
            alcancados = {inicio_comp}
            pendentes = [inicio_comp]
            while pendentes:
                atual = pendentes.pop()
                for vizinho in reduzido[atual]:
                    if vizinho not in alcancados:
                        alcancados.add(vizinho)
                        pendentes.append(vizinho)
            alcances[inicio_comp] = alcancados

        for i in reduzido:
            for j in range(i + 1, len(reduzido)):
                if j not in alcances[i] and i not in alcances[j]:
                    return "C1 (Simplesmente conexo)"
        return "C2 (Semifortemente conexo)"


    # m) Investiga os semigraus dos vertices do grafo direcionado.
    # d+(v) conta arestas de saida e d-(v) conta arestas de entrada.
    def calcular_graus(self):
        graus = {v: {"entrada": 0, "saida": len(conexoes)}
                 for v, conexoes in self.adjacencias.items()}
        for conexoes in self.adjacencias.values():
            for destino, _ in conexoes:
                graus[destino]["entrada"] += 1
        return graus

    # m) Busca um ciclo direcionado por DFS com tres estados:
    # 0 = nao visitado, 1 = em exploracao, 2 = concluido.
    # A pilha explicita evita ultrapassar o limite de recursao do Python.
    # Retorna um ciclo de exemplo, ou None quando o grafo e aciclico.
    def encontrar_ciclo_direcionado(self):
        estado = {v: 0 for v in self.adjacencias}
        for inicio in self.adjacencias:
            if estado[inicio] != 0:
                continue
            caminho = [inicio]
            posicoes = {inicio: 0}
            estado[inicio] = 1
            pilha = [(inicio, iter(self.adjacencias[inicio]))]
            while pilha:
                atual, vizinhos = pilha[-1]
                try:
                    proximo, _ = next(vizinhos)
                except StopIteration:
                    estado[atual] = 2
                    pilha.pop()
                    posicoes.pop(atual)
                    caminho.pop()
                    continue
                if estado[proximo] == 1:
                    return caminho[posicoes[proximo]:] + [proximo]
                if estado[proximo] == 0:
                    estado[proximo] = 1
                    posicoes[proximo] = len(caminho)
                    caminho.append(proximo)
                    pilha.append((proximo, iter(self.adjacencias[proximo])))
        return None


# =====================================================================
# 3) INTERFACE GRAFICA (GUI) E MENU DE OPCOES
# =====================================================================
class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mapeador de rotas de onibus acessiveis em SP")
        self.root.geometry("470x750")
        self.root.configure(bg="#50678c")
        self.grafo = GrafoLista()

        # Titulo da aplicacao acima do menu, como exige o enunciado.
        tk.Label(root, text="Mapeador de Rotas de Onibus Acessiveis em SP",
                 font=("Arial", 12, "bold"), bg="#50678c", fg="white",
                 wraplength=420).pack(pady=(14, 0))
        tk.Label(root, text="Menu de Opcoes", font=("Arial", 16, "bold"),
                 pady=12, bg="#50678c", fg="white").pack(anchor="center")

        botoes = [
            ("a) Ler dados do arquivo", self.btn_ler_arquivo),
            ("b) Gravar dados no arquivo", self.btn_gravar_arquivo),
            ("c) Inserir Vertice", self.form_inserir_vertice),
            ("d) Inserir Aresta", self.form_inserir_aresta),
            ("e) Remover Vertice", self.form_remover_vertice),
            ("f) Remover Aresta", self.form_remover_aresta),
            ("g) Mostrar conteudo do arquivo", self.btn_mostrar_conteudo),
            ("h) Mostrar Grafo (Visual)", self.btn_mostrar_grafo),
            ("i) Conexidade e Grafo Reduzido", self.btn_conexidade),
            ("k) Consultar Acessibilidade (CSV)", self.btn_acessibilidade),
            ("l) Calcular Caminho Minimo (Dijkstra)", self.btn_dijkstra),
            ("m) Analisar Caracteristicas do Grafo", self.btn_caracteristicas),
            ("j) Encerrar Aplicacao", self.encerrar_aplicacao)
            
        ]

        for texto, comando in botoes:
            tk.Button(root, text=texto, command=comando, width=35, pady=5).pack(pady=3, anchor="center")

    # Metodo que atualiza o grafico em tempo real se a janela estiver aberta
    def atualizar_tela_se_aberta(self):
        if plt.fignum_exists("Visualizacao do Grafo"):
            self.btn_mostrar_grafo()

    def btn_ler_arquivo(self):
        caminho = filedialog.askopenfilename(title="Selecione o arquivo grafo.txt", filetypes=[("Arquivos de Texto", "*.txt"), ("Todos", "*.*")])
        if caminho:
            sucesso, msg = self.grafo.ler_arquivo(caminho)
            if sucesso:
                # Carrega o CSV somente quando o grafo.txt corresponde aos dados gerados.
                # Qualquer incompatibilidade e informada, sem comprometer o grafo.
                detalhe = ""
                if Path(caminho).name == "grafo.txt":
                    arquivo_csv = Path(caminho).with_name("acessibilidade_simulada.csv")
                    if arquivo_csv.exists():
                        ok_csv, detalhe = self.grafo.ler_acessibilidade_csv(arquivo_csv)
                        if not ok_csv:
                            detalhe = "CSV nao aplicado: " + detalhe
                messagebox.showinfo("Sucesso", msg + ("\n" + detalhe if detalhe else ""))
                self.atualizar_tela_se_aberta()
            else:
                messagebox.showerror("Erro", msg)

    def btn_gravar_arquivo(self):
        if not self.grafo.adjacencias:
            messagebox.showwarning("Aviso", "O grafo esta vazio.")
            return
        if messagebox.askyesno("Atencao", "Suas alteracoes serao sobreescritas no arquivo. Tem certeza?"):
            caminho = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="grafo.txt", title="Salvar como...")
            if caminho:
                sucesso, msg = self.grafo.gravar_arquivo(caminho)
                messagebox.showinfo("Resultado", msg)

    # Formulario melhorado para Inserir Vertice (Todos os campos numa tela so)
    def form_inserir_vertice(self):
        janela = tk.Toplevel(self.root)
        janela.title("Inserir Vertice")
        janela.geometry("250x150")
        
        tk.Label(janela, text="ID Numerico:").pack(pady=2)
        entry_id = tk.Entry(janela)
        entry_id.pack(pady=2)
        
        tk.Label(janela, text="Rotulo (Nome do Ponto):").pack(pady=2)
        entry_rotulo = tk.Entry(janela)
        entry_rotulo.pack(pady=2)
        
        def salvar():
            try:
                id_v = int(entry_id.get())
                rot = entry_rotulo.get()
                sucesso, msg = self.grafo.inserir_vertice(id_v, rot)
                messagebox.showinfo("Aviso", msg)
                self.atualizar_tela_se_aberta()
                janela.destroy()
            except ValueError:
                messagebox.showerror("Erro", "O ID deve ser um numero inteiro valido.")
                
        tk.Button(janela, text="Confirmar", command=salvar).pack(pady=10)

    # Formulario melhorado para Inserir Aresta
    def form_inserir_aresta(self):
        janela = tk.Toplevel(self.root)
        janela.title("Inserir Aresta")
        janela.geometry("250x200")
        
        tk.Label(janela, text="ID de Origem:").pack()
        entry_u = tk.Entry(janela)
        entry_u.pack(pady=2)
        
        tk.Label(janela, text="ID de Destino:").pack()
        entry_v = tk.Entry(janela)
        entry_v.pack(pady=2)
        
        tk.Label(janela, text="Peso (Tempo/Esforco):").pack()
        entry_peso = tk.Entry(janela)
        entry_peso.pack(pady=2)
        
        def salvar():
            try:
                u = int(entry_u.get())
                v = int(entry_v.get())
                p = int(entry_peso.get())
                # Tenta inserir ou atualizar a aresta.
                sucesso, msg = self.grafo.inserir_aresta(u, v, p)

                if sucesso:
                    # Informa que a operacao foi realizada.
                    messagebox.showinfo("Sucesso", msg)
                    self.atualizar_tela_se_aberta()
                    janela.destroy()
                else:
                    # Mostra o motivo do erro e mantem o formulario aberto.
                    messagebox.showerror("Erro", msg)
            except ValueError:
                messagebox.showerror("Erro", "Todos os campos devem ser numeros inteiros.")
                
        tk.Button(janela, text="Confirmar", command=salvar).pack(pady=10)

    def form_remover_vertice(self):
        if messagebox.askyesno("Atencao", "Isso removera as arestas ligadas a ele. Tem certeza?"):
            janela = tk.Toplevel(self.root)
            janela.title("Remover Vertice")
            janela.geometry("200x100")
            tk.Label(janela, text="ID do Vertice:").pack(pady=5)
            entry_id = tk.Entry(janela)
            entry_id.pack()
            
            def remover():
                try:
                    sucesso, msg = self.grafo.remover_vertice(int(entry_id.get()))
                    messagebox.showinfo("Resultado", msg)
                    self.atualizar_tela_se_aberta()
                    janela.destroy()
                except ValueError:
                    messagebox.showerror("Erro", "Digite um numero valido.")
            tk.Button(janela, text="Remover", command=remover).pack(pady=5)

    def form_remover_aresta(self):
        janela = tk.Toplevel(self.root)
        janela.title("Remover Aresta")
        janela.geometry("200x150")
        tk.Label(janela, text="ID Origem:").pack()
        entry_u = tk.Entry(janela)
        entry_u.pack(pady=2)
        tk.Label(janela, text="ID Destino:").pack()
        entry_v = tk.Entry(janela)
        entry_v.pack(pady=2)
        
        def remover():
            try:
                sucesso, msg = self.grafo.remover_aresta(int(entry_u.get()), int(entry_v.get()))
                messagebox.showinfo("Resultado", msg)
                self.atualizar_tela_se_aberta()
                janela.destroy()
            except ValueError:
                messagebox.showerror("Erro", "Digite numeros validos.")
        tk.Button(janela, text="Remover", command=remover).pack(pady=5)

    # g) Mostra o conteudo salvo em disco (nao edicoes ainda nao gravadas).
    def btn_mostrar_conteudo(self):
        if not self.grafo.arquivo_atual or not os.path.exists(self.grafo.arquivo_atual):
            messagebox.showwarning("Aviso", "Nenhum arquivo lido ou gravado ainda.")
            return
        janela = tk.Toplevel(self.root)
        janela.title("Conteudo do Arquivo")
        janela.geometry("300x400")
        txt = tk.Text(janela, wrap=tk.WORD)
        txt.pack(expand=True, fill=tk.BOTH)
        with open(self.grafo.arquivo_atual, 'r', encoding='utf-8') as f:
            txt.insert(tk.END, f.read())
        txt.config(state=tk.DISABLED)

    

    # h) Mostrar grafo (Menu de escolha entre Visual e Lista)
    
    def btn_mostrar_grafo(self):
        if not self.grafo.adjacencias:
            messagebox.showwarning("Aviso", "Leia um arquivo .txt ou insira dados antes.")
            return

        # Cria uma janelinha perguntando qual o tipo de visualizacao
        janela_escolha = tk.Toplevel(self.root)
        janela_escolha.title("Escolha a Visualizacao")
        janela_escolha.geometry("300x150")
        janela_escolha.configure(bg="#50678c")
        
        tk.Label(janela_escolha, text="Como deseja visualizar o grafo?", font=("Arial", 11, "bold"), bg="#50678c", fg="white").pack(pady=15)
        
        tk.Button(janela_escolha, text="1. Grafo Visual (Desenho 2D)", width=25,
                  command=lambda: [janela_escolha.destroy(), self._mostrar_grafo_visual()]).pack(pady=5)
                  
        tk.Button(janela_escolha, text="2. Lista de Adjacencias (Texto)", width=25,
                  command=lambda: [janela_escolha.destroy(), self._mostrar_lista_adjacencia()]).pack(pady=5)

    # Funcao auxiliar 1: O desenho grafico 
    def _mostrar_grafo_visual(self):
        fig = plt.figure("Visualizacao do Grafo", figsize=(12, 8))
        fig.clf() 
        
        G = nx.DiGraph()
        for u in self.grafo.adjacencias:
            G.add_node(u)
            for v, peso in self.grafo.adjacencias[u]:
                G.add_edge(u, v, weight=peso)

        # k=3.0 afasta muito mais os vertices uns dos outros. 
        # iterations=100 da mais tempo para o algoritmo desembaracar os nos.
        pos = nx.spring_layout(G, seed=42, k=3.0, iterations=100)
        # node_size=150 (bolinhas menores) e font_size=7 despoluem a tela
        nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=150, font_weight='bold', font_size=7, arrows=True, arrowsize=8, edge_color='gray')
        pesos = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=pesos, font_color='red', font_size=6)
        
        plt.title("Grafo do Projeto (Rotas Acessiveis) - Utilize o Zoom para navegar")
        plt.axis('off')
        plt.tight_layout() # Aproveita melhor os cantos da janela
        plt.draw() # Desenha a atualizacao
        plt.show(block=False) 
        plt.pause(0.001)

    # Funcao auxiliar 2: Tela de Lista de Adjacencias
    def _mostrar_lista_adjacencia(self):
        janela_lista = tk.Toplevel(self.root)
        janela_lista.title("Grafo - Lista de Adjacencias")
        janela_lista.geometry("600x500")
        
        
        # Caixa de texto e barra vertical. A rodinha do mouse funciona no Text.
        frame_lista = tk.Frame(janela_lista)
        frame_lista.pack(expand=True, fill=tk.BOTH, padx=15, pady=15)
        scrollbar = tk.Scrollbar(frame_lista, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        txt = tk.Text(frame_lista, wrap=tk.WORD, font=("Consolas", 10),
                      padx=10, pady=10, yscrollcommand=scrollbar.set)
        txt.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        scrollbar.config(command=txt.yview)

        txt.insert(tk.END, "=== LISTA DE ADJACENCIAS ===\n\n")
        
        # Monta a estrutura visual da lista de adjacencias
        for u in sorted(self.grafo.adjacencias.keys()):
            nome_u = self.grafo.rotulos.get(u, "Desconhecido")
            conexoes = self.grafo.adjacencias[u]
            
            linha = f"[{u}] {nome_u}  --->  "
            if not conexoes:
                linha += "Nenhuma conexao (Fim de linha)\n"
            else:
                lista_str = []
                for v, peso in conexoes:
                    nome_v = self.grafo.rotulos.get(v, "Desconhecido")
                    # Peso representa tempo; acessibilidade e uma informacao distinta.
                    situacao = self.grafo.acessibilidade.get((u, v))
                    if situacao == "inacessivel_simulado":
                        descricao = "RESTRICAO SIMULADA"
                    else:
                        descricao = "ACESSIBILIDADE NAO VERIFICADA"
                    lista_str.append(f"[{v}] {nome_v} (tempo: {peso} min; {descricao})")
                
                linha += "  |  ".join(lista_str) + "\n"
                
            txt.insert(tk.END, linha + "\n")
            
        txt.config(state=tk.DISABLED) # Impede edicao



    # k) Consulta direta, sem criar submenus.
    def btn_acessibilidade(self):
        if not self.grafo.adjacencias:
            messagebox.showwarning("Aviso", "Carregue um grafo primeiro (opcao a).")
            return

        # Permite atualizar manualmente o CSV se necessario.
        caminho = filedialog.askopenfilename(
            title="Escolha acessibilidade_simulada.csv",
            initialdir=str(Path(self.grafo.arquivo_atual).parent),
            filetypes=[("Arquivos CSV", "*.csv")])
        if not caminho:
            return
        sucesso, msg = self.grafo.ler_acessibilidade_csv(caminho)
        if not sucesso:
            messagebox.showerror("Erro", msg)
            return

        janela = tk.Toplevel(self.root)
        janela.title("Restricoes simuladas de acessibilidade")
        janela.geometry("720x460")
        frame = tk.Frame(janela)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        barra = tk.Scrollbar(frame)
        barra.pack(side=tk.RIGHT, fill=tk.Y)
        texto = tk.Text(frame, wrap=tk.WORD, font=("Consolas", 10),
                        yscrollcommand=barra.set)
        texto.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra.config(command=texto.yview)
        texto.insert(tk.END, msg + "\n\n")
        texto.insert(tk.END, "AVISO: restricoes simuladas NAO comprovam "
                    "as condicoes reais das paradas.\n\n")
        texto.insert(tk.END, "=== TRECHOS COM RESTRICAO SIMULADA ===\n\n")
        restritas = sorted((u, v) for (u, v), estado
                           in self.grafo.acessibilidade.items()
                           if estado == "inacessivel_simulado")
        for u, v in restritas:
            nome_u = self.grafo.rotulos.get(u, str(u))
            nome_v = self.grafo.rotulos.get(v, str(v))
            texto.insert(tk.END, f"[{u}] {nome_u}  ->  [{v}] {nome_v}\n")
        texto.config(state=tk.DISABLED)

    # l) Janela de consulta de caminho minimo, sem submenus adicionais.
    def btn_dijkstra(self):
        if not self.grafo.adjacencias:
            messagebox.showwarning("Aviso", "Carregue um grafo primeiro (opcao a).")
            return

        janela = tk.Toplevel(self.root)
        janela.title("Caminho Minimo - Dijkstra")
        janela.geometry("740x540")
        janela.minsize(560, 420)

        # IDs nos campos evitam confusao entre paradas de nomes iguais.
        ids = sorted(self.grafo.adjacencias)
        opcoes = [f"[{v}] {self.grafo.rotulos.get(v, str(v))}" for v in ids]
        indice_por_opcao = dict(zip(opcoes, ids))

        formulario = tk.Frame(janela)
        formulario.pack(fill=tk.X, padx=15, pady=(12, 6))
        tk.Label(formulario, text="Origem:").pack(anchor="w")
        campo_origem = ttk.Combobox(formulario, values=opcoes, state="readonly")
        campo_origem.pack(fill=tk.X, pady=(0, 8))
        tk.Label(formulario, text="Destino:").pack(anchor="w")
        campo_destino = ttk.Combobox(formulario, values=opcoes, state="readonly")
        campo_destino.pack(fill=tk.X, pady=(0, 8))
        campo_origem.current(0)
        campo_destino.current(min(1, len(ids) - 1))

        evitar = tk.BooleanVar(value=bool(self.grafo.acessibilidade))
        filtro = tk.Checkbutton(
            formulario,
            text="Evitar trechos com restricao simulada (CSV)",
            variable=evitar,
        )
        filtro.pack(anchor="w")
        if not self.grafo.acessibilidade:
            # Sem CSV valido, nao existe informacao para aplicar o filtro.
            filtro.config(state=tk.DISABLED)
            tk.Label(formulario, text="CSV nao carregado: consulta apenas por tempo.",
                     fg="darkred").pack(anchor="w")

        frame_resultado = tk.Frame(janela)
        frame_resultado.pack(fill=tk.BOTH, expand=True, padx=15, pady=(4, 12))
        barra = tk.Scrollbar(frame_resultado, orient=tk.VERTICAL)
        barra.pack(side=tk.RIGHT, fill=tk.Y)
        resultado = tk.Text(frame_resultado, wrap=tk.WORD, font=("Consolas", 10),
                            yscrollcommand=barra.set)
        resultado.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra.config(command=resultado.yview)
        resultado.insert(tk.END, "Escolha a origem e o destino e clique em Calcular.\n")
        resultado.config(state=tk.DISABLED)

        def calcular():
            origem = indice_por_opcao.get(campo_origem.get())
            destino = indice_por_opcao.get(campo_destino.get())
            try:
                caminho, tempo = self.grafo.dijkstra(origem, destino, evitar.get())
            except ValueError as erro:
                messagebox.showerror("Erro no calculo", str(erro), parent=janela)
                return

            resultado.config(state=tk.NORMAL)
            resultado.delete("1.0", tk.END)
            resultado.insert(tk.END, "=== CONSULTA DE CAMINHO MINIMO ===\n\n")
            resultado.insert(tk.END, f"Origem: [{origem}] {self.grafo.rotulos[origem]}\n")
            resultado.insert(tk.END, f"Destino: [{destino}] {self.grafo.rotulos[destino]}\n")
            resultado.insert(tk.END, "Filtro: " +
                ("evita restricoes simuladas\n" if evitar.get() else "desativado\n"))

            if caminho is None:
                resultado.insert(tk.END, "\nNao existe caminho para este par de paradas "
                                      "nas condicoes selecionadas.\n")
            else:
                resultado.insert(tk.END, f"\nTempo total: {tempo} min\n")
                resultado.insert(tk.END, f"Trechos percorridos: {len(caminho) - 1}\n\n")
                resultado.insert(tk.END, "Sequencia de paradas:\n")
                for pos, vertice in enumerate(caminho, start=1):
                    resultado.insert(tk.END,
                        f"{pos}. [{vertice}] {self.grafo.rotulos[vertice]}\n")

            resultado.insert(tk.END,
                "\nAVISO: a acessibilidade nao foi verificada na realidade. "
                "Evitar restricoes simuladas NAO garante uma rota acessivel.\n")
            resultado.config(state=tk.DISABLED)

        tk.Button(formulario, text="Calcular caminho minimo",
                  command=calcular, width=27).pack(pady=(7, 0))

    # i) Apresentar a conexidade e Grafo Reduzido
    def btn_conexidade(self):
        if not self.grafo.adjacencias:
            messagebox.showwarning("Aviso", "O grafo esta vazio.")
            return
        
        componentes = self.grafo.analisar_conexidade()
        
        resultado = "=== ANALISE DE CONEXIDADE ===\n\n"
        resultado += "Componentes Fortemente Conexas (CFC):\n"
        for idx, comp in enumerate(componentes):
            nomes = [self.grafo.rotulos.get(n, str(n)) for n in comp]
            resultado += f"CFC {idx + 1}: {nomes}\n"

        # Mostra a categoria completa, mantendo a analise de Kosaraju.
        categoria = self.grafo.classificar_conexidade(componentes)
        resultado += f"\nCategoria: {categoria}\n"
        resultado += "Observacao: classificacao estrutural; nao verifica acessibilidade.\n"

        resultado += "\n=== GRAFO REDUZIDO ===\n"
        mapa_comp = {no: idx + 1 for idx, comp in enumerate(componentes) for no in comp}
        arestas_red = {(mapa_comp[u], mapa_comp[v]) for u in self.grafo.adjacencias for v, _ in self.grafo.adjacencias[u] if mapa_comp[u] != mapa_comp[v]}
        
        if not arestas_red:
            resultado += "O grafo reduzido e um vertice unico ou vertices totalmente isolados."
        else:
            for origem, destino in arestas_red:
                resultado += f"CFC {origem} -> CFC {destino}\n"

        janela = tk.Toplevel(self.root)
        janela.title("Conexidade e Grafo Reduzido")
        janela.geometry("450x350")
        txt = tk.Text(janela, wrap=tk.WORD, padx=10, pady=10)
        txt.pack(expand=True, fill=tk.BOTH)
        txt.insert(tk.END, resultado)
        txt.config(state=tk.DISABLED)

    # m) Apresenta tres investigacoes: semigraus, ciclos e conexidade.
    # Reaproveita Kosaraju da opcao i), sem repetir sua implementacao.
    def btn_caracteristicas(self):
        if not self.grafo.adjacencias:
            messagebox.showwarning("Aviso", "Carregue um grafo primeiro (opcao a).")
            return

        # Calcula os graus dos vertices e verifica a existencia de ciclos.
        # A analise de conexidade permanece exclusivamente na opcao i).
        graus = self.grafo.calcular_graus()
        ciclo = self.grafo.encontrar_ciclo_direcionado()

        # Conta o total de arestas direcionadas do grafo.
        total_arestas = sum(len(ligacoes) for ligacoes in self.grafo.adjacencias.values())
        maior_entrada = max(info["entrada"] for info in graus.values())
        maior_saida = max(info["saida"] for info in graus.values())
        vertices_entrada = [v for v, info in sorted(graus.items())
                            if info["entrada"] == maior_entrada]
        vertices_saida = [v for v, info in sorted(graus.items())
                          if info["saida"] == maior_saida]
        isolados = [v for v, info in sorted(graus.items())
                    if info["entrada"] == 0 and info["saida"] == 0]

        linhas = ["=== CARACTERISTICAS DO GRAFO ===", "",
                  f"Vertices: {len(graus)}",
                  f"Arestas direcionadas: {total_arestas}",
                  "", "=== 1. GRAUS DE ENTRADA E SAIDA ===",
                  f"Maior grau de entrada: {maior_entrada} (vertices: {vertices_entrada})",
                  f"Maior grau de saida: {maior_saida} (vertices: {vertices_saida})",
                  f"Vertices isolados: {len(isolados)}",
                  f"IDs isolados: {isolados if isolados else 'nenhum'}",
                  "", "\n\n=== 2. CICLOS DIRECIONADOS ==="]
        if ciclo is None:
            linhas.append("Nao foi encontrado ciclo direcionado (grafo aciclico).")
        else:
            linhas.append("Foi encontrado pelo menos um ciclo direcionado.")
            linhas.append("Exemplo (IDs): " + " -> ".join(map(str, ciclo)))
        # A conexidade e o grafo reduzido ja sao apresentados na opcao i).
        # Aqui mostramos apenas as caracteristicas relacionadas aos graus e ciclos.
        linhas.extend([
            "",
            "OBSERVACAO: estas sao caracteristicas estruturais do grafo.",
            "Elas nao comprovam acessibilidade real das paradas.",
            "",
            "=== GRAUS DE TODOS OS VERTICES ==="
        ])
        for v, info in sorted(graus.items()):
            linhas.append(f"[{v}] {self.grafo.rotulos.get(v, str(v))}: "
                          f"entrada={info['entrada']}, saida={info['saida']}")

        # Uma janela com rolagem evita acrescentar submenus ou muitos botoes.
        janela = tk.Toplevel(self.root)
        janela.title("Analise das Caracteristicas do Grafo")
        janela.geometry("750x540")
        frame = tk.Frame(janela)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        barra = tk.Scrollbar(frame, orient=tk.VERTICAL)
        barra.pack(side=tk.RIGHT, fill=tk.Y)
        texto = tk.Text(frame, wrap=tk.WORD, font=("Consolas", 10),
                        yscrollcommand=barra.set)
        texto.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra.config(command=texto.yview)
        texto.insert(tk.END, "\n".join(linhas))
        texto.config(state=tk.DISABLED)

    # j) O programa deve ser encerrado
    def encerrar_aplicacao(self):
        plt.close('all') 
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppGUI(root)
    root.mainloop()