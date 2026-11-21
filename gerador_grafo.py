'''
PROJETO: Mapeador de rotas de onibus acessiveis em SP.
SINTESE: Gera grafo direcionado e ponderado a partir de quatro arquivos GTFS.
'''

import csv
import math
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Mantemos as mesmas duas linhas e a estrutura do grafo Tipo 6.
LINHAS = ("175P-10", "875A-10")
SEMENTE = 42
FRACAO_SIMULADA = 0.05
PASTA = Path(__file__).resolve().parent
# Os arquivos originais GTFS ficam na subpasta "Dados GTFS".
# Os arquivos gerados (grafo.txt e CSV) continuam na pasta principal.
PASTA_GTFS = PASTA / "Dados GTFS"


def ler_csv(nome, colunas):
    """Le um GTFS e verifica a presenca das colunas exigidas."""
    # Busca cada arquivo de entrada na subpasta, sem mudar as saidas do gerador.
    caminho = PASTA_GTFS / nome
    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        faltantes = set(colunas) - set(leitor.fieldnames or [])
        if faltantes:
            raise ValueError(f"{nome}: faltam as colunas {sorted(faltantes)}")
        return list(leitor)


def horario_em_segundos(horario):
    """Converte HH:MM:SS do GTFS; aceita horas acima de 23."""
    partes = horario.split(":")
    if len(partes) != 3:
        raise ValueError(f"Horario GTFS invalido: {horario}")
    h, m, s = map(int, partes)
    if h < 0 or not 0 <= m < 60 or not 0 <= s < 60:
        raise ValueError(f"Horario GTFS invalido: {horario}")
    return h * 3600 + m * 60 + s


def gerar_grafo_gtfs():
    """Produz um grafo compativel com a GUI e um CSV de acessibilidade simulada."""
    print("1. Lendo e validando arquivos GTFS...")
    routes = ler_csv("routes.txt", ["route_id", "route_short_name"])
    trips = ler_csv("trips.txt", ["route_id", "trip_id", "direction_id"])
    tempos = ler_csv("stop_times.txt", ["trip_id", "stop_id", "stop_sequence", "arrival_time", "departure_time"])
    stops = ler_csv("stops.txt", ["stop_id", "stop_name"])

    ids_rotas = {r["route_id"] for r in routes if r["route_short_name"] in LINHAS}
    if not ids_rotas:
        raise ValueError("As linhas selecionadas nao constam de routes.txt")

    # Seleciona uma viagem por linha e sentido, como no gerador original.
    viagens_por_sentido = {}
    for viagem in trips:
        if viagem["route_id"] in ids_rotas:
            chave = (viagem["route_id"], viagem["direction_id"])
            viagens_por_sentido.setdefault(chave, viagem["trip_id"])
    if len(viagens_por_sentido) != 4:
        raise ValueError("Nao foram encontradas viagens de ida e volta das duas linhas")

    selecionadas = set(viagens_por_sentido.values())
    horarios_por_viagem = defaultdict(list)
    for registro in tempos:
        if registro["trip_id"] in selecionadas:
            horarios_por_viagem[registro["trip_id"]].append(registro)

    # Dicionario mantem a primeira ocorrencia da parada e preserva IDs estaveis.
    ids_paradas = {}
    nomes_paradas = {s["stop_id"]: s["stop_name"] for s in stops}
    custos = {}
    linhas_por_aresta = defaultdict(set)
    for chave, trip_id in sorted(viagens_por_sentido.items()):
        sequencia = sorted(horarios_por_viagem[trip_id], key=lambda r: int(r["stop_sequence"]))
        if len(sequencia) < 2:
            raise ValueError(f"Viagem sem paradas suficientes: {trip_id}")
        for registro in sequencia:
            stop_id = registro["stop_id"]
            if stop_id not in nomes_paradas:
                raise ValueError(f"Parada {stop_id} nao existe em stops.txt")
            ids_paradas.setdefault(stop_id, len(ids_paradas))
        for anterior, proximo in zip(sequencia, sequencia[1:]):
            u, v = anterior["stop_id"], proximo["stop_id"]
            if u == v:
                continue  # Nao criamos lacos de um ponto para ele mesmo.
            inicio = horario_em_segundos(anterior["departure_time"])
            fim = horario_em_segundos(proximo["arrival_time"])
            duracao = fim - inicio
            if duracao <= 0:
                raise ValueError(f"Duracao invalida entre {u} e {v} na viagem {trip_id}")
            # O grafo.txt usa pesos inteiros; arredondamos minutos para cima.
            peso = math.ceil(duracao / 60)
            # Se duas viagens usarem a mesma ligacao, conservamos o menor tempo.
            aresta = (u, v)
            custos[aresta] = min(custos.get(aresta, peso), peso)
            linhas_por_aresta[aresta].add(chave[0])

    # A amostra simulada e reproduzivel; nao representa condicao real da SPTrans.
    arestas_ordenadas = sorted(custos, key=lambda a: (ids_paradas[a[0]], ids_paradas[a[1]]))
    quantidade = round(len(arestas_ordenadas) * FRACAO_SIMULADA)
    bloqueadas = set(random.Random(SEMENTE).sample(arestas_ordenadas, quantidade))

    # Nome de saida exigido pelo professor. Cuidado: gerar novamente sobrescreve
    # o grafo.txt e o CSV; mantenha uma copia antes de executar o gerador.
    saida_grafo = PASTA / "grafo.txt"
    saida_acessibilidade = PASTA / "acessibilidade_simulada.csv"
    with saida_grafo.open("w", encoding="utf-8", newline="") as arquivo:
        arquivo.write(f"6\n{len(ids_paradas)}\n")
        for parada, identificador in ids_paradas.items():
            nome = nomes_paradas[parada].replace('"', "").replace("\n", " ")
            arquivo.write(f'{identificador} "{nome}" 0\n')
        arquivo.write(f"{len(arestas_ordenadas)}\n")
        for u, v in arestas_ordenadas:
            arquivo.write(f"{ids_paradas[u]} {ids_paradas[v]} {custos[(u, v)]}\n")

    # A acessibilidade nao altera o custo nem e confundida com conexidade.
    # O CSV guarda os IDs originais GTFS para permitir futuras verificacoes.
    with saida_acessibilidade.open("w", encoding="utf-8", newline="") as arquivo:
        campos = ["origem_id", "destino_id", "origem_gtfs", "destino_gtfs",
                  "linhas", "tempo_min", "acessibilidade", "origem_informacao"]
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        for u, v in arestas_ordenadas:
            escritor.writerow({
                "origem_id": ids_paradas[u], "destino_id": ids_paradas[v],
                "origem_gtfs": u, "destino_gtfs": v,
                "linhas": "/".join(sorted(linhas_por_aresta[(u, v)])),
                "tempo_min": custos[(u, v)],
                "acessibilidade": "inacessivel_simulado" if (u, v) in bloqueadas else "nao_verificada",
                "origem_informacao": "simulacao_semente_42" if (u, v) in bloqueadas else "sem_dado_GTFS",
            })

    print(f"2. Grafo: {len(ids_paradas)} vertices; {len(arestas_ordenadas)} arestas")
    print(f"3. Restricoes SIMULADAS: {len(bloqueadas)} arestas (semente {SEMENTE})")
    print(f"4. Arquivos criados: {saida_grafo.name}, {saida_acessibilidade.name}")
    print("O app_gui.py pode carregar o CSV ao abrir o grafo.txt correspondente.")


if __name__ == "__main__":
    try:
        gerar_grafo_gtfs()
    except (OSError, ValueError) as erro:
        print(f"Erro ao gerar o grafo: {erro}")
