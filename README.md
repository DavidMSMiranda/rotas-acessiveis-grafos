# Mapeador de rotas de ônibus acessíveis em SP

Projeto acadêmico da disciplina de **Teoria dos Grafos**. A aplicação representa e analisa parte da rede de ônibus da cidade de São Paulo a partir de dados GTFS da SPTrans, com foco no estudo de caminhos mínimos e restrições **simuladas** de acessibilidade.

> **Atenção:** o programa é um protótipo acadêmico. As restrições de acessibilidade são fictícias e as demais ligações não foram verificadas. Nenhum resultado deve ser interpretado como garantia de rota acessível.

## Integrantes

- **Nome:** [preencher] — **RA:** [preencher] — **E-mail:** [preencher]
- **Professor:** [preencher]
- **Curso / instituição:** [preencher]

## Dados e modelagem

Os dados foram obtidos na [área de desenvolvedores da SPTrans](https://www.sptrans.com.br/desenvolvedores/), no formato [GTFS](https://gtfs.org/documentation/schedule/reference/).

Foram selecionadas as linhas **175P-10** e **875A-10**, considerando uma viagem por sentido de cada linha. O grafo é **direcionado e ponderado (Tipo 6)** e utiliza **lista de adjacências**:

- **238 vértices:** paradas de ônibus distintas;
- **244 arcos:** ligações entre paradas consecutivas, respeitando o sentido das viagens;
- **Pesos:** tempos previstos de deslocamento em minutos, obtidos dos horários GTFS;
- **12 arcos com restrição simulada** e **232 com acessibilidade não verificada**.

As restrições são armazenadas em `acessibilidade_simulada.csv`, separadas dos pesos do `grafo.txt`. A seleção simulada é reproduzível com semente **42**.

## Funcionalidades

O menu da aplicação permite:

- Ler e gravar um grafo em arquivo de texto;
- Inserir e remover vértices e arcos;
- Consultar o arquivo e visualizar o grafo com NetworkX e Matplotlib;
- Identificar componentes fortemente conexas com **Kosaraju**, classificar a conexidade (**C0 a C3**) e construir o grafo reduzido;
- Consultar as restrições simuladas de acessibilidade;
- Calcular o **caminho mínimo com Dijkstra**, com ou sem exclusão dos arcos marcados como restritos;
- Analisar graus de entrada e saída, vértices isolados e ciclos direcionados com busca em profundidade (**DFS**).

A aplicação também valida entradas inválidas, rejeita pesos negativos e preserva o grafo carregado quando a leitura de outro arquivo falha.

## Estrutura dos arquivos

```text
rotas-acessiveis-grafos/
├── app_gui.py
├── gerador_grafo.py
├── grafo.txt
├── acessibilidade_simulada.csv
├── grafo_invalido_teste.txt
├── routes.txt
├── trips.txt
├── stop_times.txt
├── stops.txt
├── requirements.txt
├── README.md
├── relatorio/
│   └── relatorio_final.pdf
└── evidencias_testes/
```

Os quatro arquivos GTFS devem ficar **na mesma pasta de `gerador_grafo.py`** na versão atual do programa. Caso os dados GTFS não sejam redistribuídos no repositório, obtenha-os na fonte original indicada acima e coloque-os nessa pasta antes de executar o gerador. Os nomes de arquivos e a versão da base devem corresponder aos usados no projeto para reproduzir exatamente os resultados.

## Como executar (Windows / VSCode)

É necessário ter **Python 3** instalado. Na pasta do projeto, abra o terminal do VSCode e execute:

```powershell
python -m pip install -r requirements.txt
python app_gui.py
```

Na janela da aplicação, escolha **a) Ler dados do arquivo** e selecione `grafo.txt`. Para carregar automaticamente o CSV correspondente, mantenha `grafo.txt` e `acessibilidade_simulada.csv` na **mesma pasta**, sem modificar seus dados.

A biblioteca **Tkinter** faz parte da instalação padrão do Python em muitos ambientes Windows; não está listada no `requirements.txt` porque não é instalada normalmente pelo `pip`.

### Regerar o grafo (opcional)

Com os quatro arquivos GTFS originais na pasta do gerador, execute:

```powershell
python gerador_grafo.py
```

**Cuidado:** esse comando **sobrescreve** `grafo.txt` e `acessibilidade_simulada.csv`. Faça uma cópia antes. Os resultados dependem do conjunto de dados GTFS utilizado.

## Exemplos de resultados e testes

- Grafo original: **238 vértices**, **244 arcos**, **conexidade C3** e presença de ciclos direcionados;
- Maior grau de entrada e maior grau de saída: **2**;
- Dijkstra do vértice **6** ao **8**, sem restrições: caminho `6 → 7 → 8`, com **6 minutos**;
- No mesmo par, com restrições simuladas: **nenhum caminho permitido encontrado**;
- A leitura de `grafo_invalido_teste.txt` é rejeitada sem descartar o grafo previamente carregado;
- A inserção de um vértice isolado muda a classificação estrutural do grafo original de **C3 para C0**.

As capturas de tela dos testes podem ser consultadas na pasta `evidencias_testes/`.

## Limitações

O programa utiliza apenas duas linhas, horários planejados e restrições fictícias. Não considera trânsito em tempo real, espera pelo ônibus, deslocamentos a pé entre paradas ou acessibilidade real verificada. A classificação de conexidade é **estrutural**, não uma certificação de acessibilidade.

## Relatório e apresentação

- Relatório: pasta [`relatorio/`](relatorio/).
- Vídeo de apresentação: **[adicionar link público do YouTube após a gravação]**.

## Fontes

- [SPTrans — Desenvolvedores](https://www.sptrans.com.br/desenvolvedores/)
- [GTFS — Documentação oficial](https://gtfs.org/documentation/schedule/reference/)
- [ONU Brasil — ODS 11](https://brasil.un.org/pt-br/sdgs/11)
