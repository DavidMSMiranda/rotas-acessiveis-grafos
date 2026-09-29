'''
NOME: David Mendes
SÍNTESE DO CONTEÚDO: Aplicação em Python com Interface Gráfica para modelagem, manipulação e análise de conexidade de um grafo direcionado e ponderado (Tipo 6), focado em rotas de transporte público acessíveis via dados GTFS da SPTrans.
HISTÓRICO DE ALTERAÇÕES:
- 30/08/2026 | David | Criação da classe base GrafoLista e manipulação do arquivo grafo.txt.
- 09/09/2026 | David | Implementação da Interface Gráfica (Tkinter) e desenho visual com NetworkX/Matplotlib.
- 17/09/2026 | David | Integração do algoritmo de Kosaraju (FCONEX) para atestar a categoria C3 e ajustes de layout.
'''

import pandas as pd
import random

def gerar_grafo_gtfs():
    print("1. Carregando arquivos GTFS (isso pode levar alguns segundos)...")
    try:
        routes = pd.read_csv("routes.txt", dtype=str)
        trips = pd.read_csv("trips.txt", dtype=str)
        stop_times = pd.read_csv("stop_times.txt", dtype=str)
        stops = pd.read_csv("stops.txt", dtype=str)
    except FileNotFoundError as e:
        print(f"Erro: O arquivo {e.filename} nao foi encontrado na pasta.")
        return

    print("2. Cruzando dados e filtrando rotas...")
    # Escolhendo rotas estrategicas que se cruzam e geram volume de vertices/arestas
    #linhas_alvo = ["106A-10", "175P-10", "1178-10", "1783-10", "208M-10", "875A-10"]
    #linhas_alvo = ["175P-10", "208M-10", "875A-10"]
    linhas_alvo = ["175P-10", "875A-10"]
    trips_filtradas = trips[trips['route_id'].isin(linhas_alvo)]

    # Pegando 1 viagem (trip) de ida (0) e 1 de volta (1) por linha para compor a malha
    trips_selecionadas = trips_filtradas.drop_duplicates(subset=['route_id', 'direction_id'])['trip_id'].tolist()

    # Filtrando e ordenando as paradas sequenciais dessas viagens
    st_filtrado = stop_times[stop_times['trip_id'].isin(trips_selecionadas)].copy()
    st_filtrado['stop_sequence'] = st_filtrado['stop_sequence'].astype(int)
    st_filtrado = st_filtrado.sort_values(by=['trip_id', 'stop_sequence'])

    print("3. Construindo Vertices e Arestas...")
    vertices_brutos = list(st_filtrado['stop_id'].unique())
    arestas = set() # 'set' evita que rotas diferentes que passam na mesma rua dupliquem a aresta

    for trip_id, group in st_filtrado.groupby('trip_id'):
        paradas = group['stop_id'].tolist()
        for i in range(len(paradas) - 1):
            origem = paradas[i]
            destino = paradas[i+1]
            if origem != destino: # Evita self-loops acidentais
                arestas.add((origem, destino))

    print("4. Remapeando IDs e aplicando acessibilidade...")
    # Converte IDs da SPTrans (ex: 18848) para 0, 1, 2, 3...
    mapa_ids = {stop_id: idx for idx, stop_id in enumerate(vertices_brutos)}
    dict_nomes = stops.set_index('stop_id')['stop_name'].to_dict()

    print(f"-> Total de Vertices criados: {len(vertices_brutos)}")
    print(f"-> Total de Arestas criadas: {len(arestas)}")

    # 5. Escrevendo o arquivo final
    with open("grafo.txt", "w", encoding="utf-8") as f:
        f.write("6\n") # Tipo do Grafo (Direcionado com peso na aresta)
        f.write(f"{len(vertices_brutos)}\n")
        
        for stop_id_gtfs, id_simples in mapa_ids.items():
            nome = dict_nomes.get(stop_id_gtfs, "Ponto Desconhecido").replace('"', '')
            f.write(f'{id_simples} "{nome}" 0\n')
            
        f.write(f"{len(arestas)}\n")
        
        for origem_gtfs, destino_gtfs in arestas:
            u = mapa_ids[origem_gtfs]
            v = mapa_ids[destino_gtfs]
            
            # Peso base: 2 a 12 minutos
            peso = random.randint(2, 12)
            # Simulacao de Ponto/Rota Inacessivel para cadeirantes: 5% de chance de penalidade maxima
            if random.random() < 0.05:
                peso = 999
                
            f.write(f"{u} {v} {peso}\n")

    print("\nSUCESSO! Arquivo 'grafo.txt' gerado e pronto para a aplicacao da atividade.")

if __name__ == "__main__":
    gerar_grafo_gtfs()