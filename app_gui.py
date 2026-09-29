'''
NOME: David Mendes
SÍNTESE DO CONTEÚDO: Aplicação em Python com Interface Gráfica para modelagem, manipulação e análise de conexidade de um grafo direcionado e ponderado (Tipo 6), focado em rotas de transporte público acessíveis via dados GTFS da SPTrans.
HISTÓRICO DE ALTERAÇÕES:
- 30/08/2026 | David | Criação da classe base GrafoLista e manipulação do arquivo grafo.txt.
- 09/09/2026 | David | Implementação da Interface Gráfica (Tkinter) e desenho visual com NetworkX/Matplotlib.
- 17/09/2026 | David | Integração do algoritmo de Kosaraju (FCONEX) para atestar a categoria C3 e ajustes de layout.
'''


import os
import tkinter as tk
from tkinter import filedialog, messagebox
import networkx as nx
import matplotlib.pyplot as plt


# =====================================================================
# 1) e 2) CLASSE LÓGICA DO GRAFO (Lista de Adjacências)
# =====================================================================
class GrafoLista:
    def __init__(self, direcionado=True):
        self.direcionado = direcionado
        self.tipo_grafo = 6 # Orientado com peso na aresta
        self.adjacencias = {} 
        self.rotulos = {}     
        self.arquivo_atual = "" 

    # c) Permite inserir novos vértices juntamente com seus rótulos
    def inserir_vertice(self, id_vertice, rotulo):
        if id_vertice not in self.adjacencias:
            self.adjacencias[id_vertice] = []
            self.rotulos[id_vertice] = rotulo
            return True, f"Vértice {id_vertice} inserido!"
        return False, "Vértice já existe. ID deve ser único."

    # d) Permite inserir novas arestas com os respectivos pesos
    def inserir_aresta(self, u, v, peso):
        if u in self.adjacencias and v in self.adjacencias:
            for aresta in self.adjacencias[u]:
                if aresta[0] == v:
                    aresta[1] = peso
                    return True, f"Aresta {u}->{v} atualizada."
            self.adjacencias[u].append([v, peso])
            return True, f"Aresta {u}->{v} inserida."
        return False, "Vértices de origem ou destino não existem."

    # e) Permite remover vértices (removendo arestas associadas automaticamente)
    def remover_vertice(self, id_vertice):
        if id_vertice in self.adjacencias:
            del self.adjacencias[id_vertice]
            if id_vertice in self.rotulos:
                del self.rotulos[id_vertice]
            for u in self.adjacencias:
                self.adjacencias[u] = [a for a in self.adjacencias[u] if a[0] != id_vertice]
            return True, "Vértice e conexões removidos."
        return False, "Vértice não encontrado."

    # f) Permite remover arestas
    def remover_aresta(self, u, v):
        if u in self.adjacencias:
            tam_orig = len(self.adjacencias[u])
            self.adjacencias[u] = [a for a in self.adjacencias[u] if a[0] != v]
            if len(self.adjacencias[u]) < tam_orig:
                return True, "Aresta removida."
            return False, "Aresta não encontrada."
        return False, "Vértice de origem não existe."

    # a) Deve ser lido o arquivo grafo.txt e montado o grafo
    def ler_arquivo(self, caminho):
        try:
            with open(caminho, 'r', encoding='utf-8') as file:
                linhas = [l.strip() for l in file.readlines() if l.strip()]
                self.tipo_grafo = int(linhas[0])
                n = int(linhas[1])
                self.adjacencias.clear()
                self.rotulos.clear()
                
                idx = 2
                for _ in range(n):
                    partes = linhas[idx].split('"')
                    id_vertice = int(partes[0].strip())
                    rotulo = partes[1].strip()
                    self.inserir_vertice(id_vertice, rotulo)
                    idx += 1
                
                m = int(linhas[idx])
                idx += 1
                for _ in range(m):
                    u, v, peso = map(int, linhas[idx].split())
                    self.inserir_aresta(u, v, peso)
                    idx += 1
            self.arquivo_atual = caminho
            return True, "Arquivo carregado com sucesso!"
        except Exception as e:
            return False, f"Erro ao ler: {str(e)}"

    # b) Deve gravar o grafo da memória RAM para o arquivo grafo.txt
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

    # LÓGICA INTERNA PARA O ITEM (i) - FCONEX (Algoritmo de Kosaraju)
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


# =====================================================================
# 3) INTERFACE GRÁFICA (GUI) E MENU DE OPÇÕES
# =====================================================================
class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mapeador de rotas de ônibus acessíveis em SP")
        self.root.geometry("450x550")
        self.root.configure(bg="#50678c")
        self.grafo = GrafoLista()

        tk.Label(root, text="Menu de Opções", font=("Arial", 16, "bold"), pady=30, bg="#50678c",fg="white" ).pack(anchor="center")

        botoes = [
            ("a) Ler dados do arquivo", self.btn_ler_arquivo),
            ("b) Gravar dados no arquivo", self.btn_gravar_arquivo),
            ("c) Inserir Vértice", self.form_inserir_vertice),
            ("d) Inserir Aresta", self.form_inserir_aresta),
            ("e) Remover Vértice", self.form_remover_vertice),
            ("f) Remover Aresta", self.form_remover_aresta),
            ("g) Mostrar conteúdo do arquivo", self.btn_mostrar_conteudo),
            ("h) Mostrar Grafo (Visual)", self.btn_mostrar_grafo),
            ("i) Conexidade e Grafo Reduzido", self.btn_conexidade),
            ("j) Encerrar Aplicação", self.encerrar_aplicacao)
        ]

        for texto, comando in botoes:
            tk.Button(root, text=texto, command=comando, width=35, pady=5).pack(pady=3, anchor="center")

    # Método que atualiza o gráfico em tempo real se a janela estiver aberta
    def atualizar_tela_se_aberta(self):
        if plt.fignum_exists("Visualização do Grafo"):
            self.btn_mostrar_grafo()

    def btn_ler_arquivo(self):
        caminho = filedialog.askopenfilename(title="Selecione o arquivo grafo.txt", filetypes=[("Arquivos de Texto", "*.txt"), ("Todos", "*.*")])
        if caminho:
            sucesso, msg = self.grafo.ler_arquivo(caminho)
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                self.atualizar_tela_se_aberta()
            else:
                messagebox.showerror("Erro", msg)

    def btn_gravar_arquivo(self):
        if not self.grafo.adjacencias:
            messagebox.showwarning("Aviso", "O grafo está vazio.")
            return
        if messagebox.askyesno("Atenção", "Suas alterações serão sobreescritas no arquivo. Tem certeza?"):
            caminho = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="grafo.txt", title="Salvar como...")
            if caminho:
                sucesso, msg = self.grafo.gravar_arquivo(caminho)
                messagebox.showinfo("Resultado", msg)

    # Formulário melhorado para Inserir Vértice (Todos os campos numa tela só)
    def form_inserir_vertice(self):
        janela = tk.Toplevel(self.root)
        janela.title("Inserir Vértice")
        janela.geometry("250x150")
        
        tk.Label(janela, text="ID Numérico:").pack(pady=2)
        entry_id = tk.Entry(janela)
        entry_id.pack(pady=2)
        
        tk.Label(janela, text="Rótulo (Nome do Ponto):").pack(pady=2)
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
                messagebox.showerror("Erro", "O ID deve ser um número inteiro válido.")
                
        tk.Button(janela, text="Confirmar", command=salvar).pack(pady=10)

    # Formulário melhorado para Inserir Aresta
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
        
        tk.Label(janela, text="Peso (Tempo/Esforço):").pack()
        entry_peso = tk.Entry(janela)
        entry_peso.pack(pady=2)
        
        def salvar():
            try:
                u = int(entry_u.get())
                v = int(entry_v.get())
                p = int(entry_peso.get())
                sucesso, msg = self.grafo.inserir_aresta(u, v, p)
                messagebox.showinfo("Aviso", msg)
                self.atualizar_tela_se_aberta()
                janela.destroy()
            except ValueError:
                messagebox.showerror("Erro", "Todos os campos devem ser números inteiros.")
                
        tk.Button(janela, text="Confirmar", command=salvar).pack(pady=10)

    def form_remover_vertice(self):
        if messagebox.askyesno("Atenção", "Isso removerá as arestas ligadas a ele. Tem certeza?"):
            janela = tk.Toplevel(self.root)
            janela.title("Remover Vértice")
            janela.geometry("200x100")
            tk.Label(janela, text="ID do Vértice:").pack(pady=5)
            entry_id = tk.Entry(janela)
            entry_id.pack()
            
            def remover():
                try:
                    sucesso, msg = self.grafo.remover_vertice(int(entry_id.get()))
                    messagebox.showinfo("Resultado", msg)
                    self.atualizar_tela_se_aberta()
                    janela.destroy()
                except ValueError:
                    messagebox.showerror("Erro", "Digite um número válido.")
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
                messagebox.showerror("Erro", "Digite números válidos.")
        tk.Button(janela, text="Remover", command=remover).pack(pady=5)

    # g) Mostra o conteúdo atual do arquivo
    def btn_mostrar_conteudo(self):
        if not self.grafo.arquivo_atual or not os.path.exists(self.grafo.arquivo_atual):
            messagebox.showwarning("Aviso", "Nenhum arquivo lido ou gravado ainda.")
            return
        janela = tk.Toplevel(self.root)
        janela.title("Conteúdo do Arquivo")
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

        # Cria uma janelinha perguntando qual o tipo de visualização
        janela_escolha = tk.Toplevel(self.root)
        janela_escolha.title("Escolha a Visualização")
        janela_escolha.geometry("300x150")
        janela_escolha.configure(bg="#50678c")
        
        tk.Label(janela_escolha, text="Como deseja visualizar o grafo?", font=("Arial", 11, "bold"), bg="#50678c", fg="white").pack(pady=15)
        
        tk.Button(janela_escolha, text="1. Grafo Visual (Desenho 2D)", width=25,
                  command=lambda: [janela_escolha.destroy(), self._mostrar_grafo_visual()]).pack(pady=5)
                  
        tk.Button(janela_escolha, text="2. Lista de Adjacências (Texto)", width=25,
                  command=lambda: [janela_escolha.destroy(), self._mostrar_lista_adjacencia()]).pack(pady=5)

    # Função auxiliar 1: O desenho gráfico 
    def _mostrar_grafo_visual(self):
        fig = plt.figure("Visualização do Grafo", figsize=(12, 8))
        fig.clf() 
        
        G = nx.DiGraph()
        for u in self.grafo.adjacencias:
            G.add_node(u)
            for v, peso in self.grafo.adjacencias[u]:
                G.add_edge(u, v, weight=peso)

        # k=3.0 afasta muito mais os vértices uns dos outros. 
        # iterations=100 dá mais tempo para o algoritmo desembaraçar os nós.
        pos = nx.spring_layout(G, seed=42, k=3.0, iterations=100)
        # node_size=150 (bolinhas menores) e font_size=7 despoluem a tela
        nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=150, font_weight='bold', font_size=7, arrows=True, arrowsize=8, edge_color='gray')
        pesos = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=pesos, font_color='red', font_size=6)
        
        plt.title("Grafo do Projeto (Rotas Acessíveis) - Utilize o Zoom para navegar")
        plt.axis('off')
        plt.tight_layout() # Aproveita melhor os cantos da janela
        plt.draw() # Desenha a atualização
        plt.show(block=False) 
        plt.pause(0.001)

    # Função auxiliar 2: Tela de Lista de Adjacências
    def _mostrar_lista_adjacencia(self):
        janela_lista = tk.Toplevel(self.root)
        janela_lista.title("Grafo - Lista de Adjacências")
        janela_lista.geometry("600x500")
        
        
        txt = tk.Text(janela_lista, wrap=tk.WORD, font=("Consolas", 10), padx=10, pady=10)
        txt.pack(expand=True, fill=tk.BOTH, padx=15, pady=15)
        
        txt.insert(tk.END, "=== LISTA DE ADJACÊNCIAS ===\n\n")
        
        # Monta a estrutura visual da lista de adjacências
        for u in sorted(self.grafo.adjacencias.keys()):
            nome_u = self.grafo.rotulos.get(u, "Desconhecido")
            conexoes = self.grafo.adjacencias[u]
            
            linha = f"[{u}] {nome_u}  --->  "
            if not conexoes:
                linha += "Nenhuma conexão (Fim de linha)\n"
            else:
                lista_str = []
                for v, peso in conexoes:
                    nome_v = self.grafo.rotulos.get(v, "Desconhecido")
                    # Se o peso for 999, indica que é a rota inacessível
                    alerta_peso = f"PESO: {peso}" if peso != 999 else "INACESSÍVEL (999)"
                    lista_str.append(f"[{v}] {nome_v} ({alerta_peso})")
                
                linha += "  |  ".join(lista_str) + "\n"
                
            txt.insert(tk.END, linha + "\n")
            
        txt.config(state=tk.DISABLED) # Impede edição



    # i) Apresentar a conexidade e Grafo Reduzido
    def btn_conexidade(self):
        if not self.grafo.adjacencias:
            messagebox.showwarning("Aviso", "O grafo está vazio.")
            return
        
        componentes = self.grafo.analisar_conexidade()
        
        resultado = "=== ANÁLISE DE CONEXIDADE ===\n\n"
        resultado += "Componentes Fortemente Conexas (CFC):\n"
        for idx, comp in enumerate(componentes):
            nomes = [self.grafo.rotulos.get(n, str(n)) for n in comp]
            resultado += f"CFC {idx + 1}: {nomes}\n"

        if len(componentes) == 1 and len(self.grafo.adjacencias) > 0:
            resultado += "\nCategoria: C3 (Grafo Fortemente Conexo)\n"
        else:
            resultado += "\nCategoria: Menor que C3 (Existem múltiplas componentes)\n"

        resultado += "\n=== GRAFO REDUZIDO ===\n"
        mapa_comp = {no: idx + 1 for idx, comp in enumerate(componentes) for no in comp}
        arestas_red = {(mapa_comp[u], mapa_comp[v]) for u in self.grafo.adjacencias for v, _ in self.grafo.adjacencias[u] if mapa_comp[u] != mapa_comp[v]}
        
        if not arestas_red:
            resultado += "O grafo reduzido é um vértice único ou vértices totalmente isolados."
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

    # j) O programa deve ser encerrado
    def encerrar_aplicacao(self):
        plt.close('all') 
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppGUI(root)
    root.mainloop()