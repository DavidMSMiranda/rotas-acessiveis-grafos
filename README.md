# Mapeador de rotas acessíveis de transporte público em SP

Projeto desenvolvido para a disciplina de Teoria dos Grafos, focado na análise da infraestrutura de acessibilidade das rotas de ônibus da SPTrans utilizando dados abertos (GTFS).

## Objetivo
Modelar a rede de transporte público como um Grafo Direcionado Ponderado (Tipo 6), onde os vértices são as paradas e as arestas são os trajetos. O peso das arestas simula o tempo de viagem e restrições estruturais de acessibilidade (arestas com peso 999 representam rotas inacessíveis para cadeirantes).

## Tecnologias Utilizadas
* **Linguagem:** Python 3
* **Interface Gráfica:** Tkinter
* **Estrutura de Dados:** Lista de Adjacências
* **Bibliotecas Visuais e Matemáticas:** `networkx`, `matplotlib`, `pandas`, `scipy`

## Como executar
1. Clone este repositório.
2. Instale as dependências: `pip install networkx matplotlib pandas scipy`
3. Execute a interface gráfica: `python app_gui.py`
4. Na aplicação, utilize o menu para ler o arquivo `grafo.txt` e visualizar a malha.

## Autor
* David Mendes
