# Mapeador de Rotas de Ônibus Acessíveis em SP

Projeto acadêmico desenvolvido para a disciplina de **Teoria dos Grafos**, utilizando Python e dados GTFS do transporte público de São Paulo.

## Objetivo

Representar uma rede de ônibus como um **grafo direcionado e ponderado (Tipo 6)**, permitindo analisar conexidade, caminhos mínimos e restrições simuladas de acessibilidade.

O grafo gerado possui **238 vértices e 244 arcos**, com pesos correspondentes a tempos estimados de deslocamento.

## Funcionalidades

- Leitura e validação de grafos.
- Análise de conexidade pelo algoritmo de Kosaraju.
- Cálculo de caminhos mínimos pelo algoritmo de Dijkstra.
- Análise de graus e ciclos.
- Simulação de restrições de acessibilidade.

## Tecnologias

- Python 3
- Tkinter
- Listas de adjacências
- Dados GTFS

## Como executar

É necessário ter Python 3 instalado.

1. Baixe ou clone o repositório.
2. Abra a pasta do projeto no VSCode.
3. No terminal, instale as dependências:

```bash
python -m pip install -r requirements.txt
```

4. Execute a aplicação:

```bash
python app_gui.py
```

5. Na interface, carregue o arquivo `grafo.txt` para iniciar as análises.

## Observação

As restrições de acessibilidade são **simuladas para fins acadêmicos** e não representam condições reais verificadas nas linhas de ônibus.

## Apresentação

[Vídeo de demonstração no YouTube](https://www.youtube.com/watch?v=Va3ge-2BubU)

## Autor

David Mendes
