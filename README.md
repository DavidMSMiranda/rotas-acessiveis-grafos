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

1. Baixe ou clone o repositório.
2. Instale as dependências necessárias ao projeto.
3. Execute a interface gráfica:

```bash
python app_gui.py
```

4. Carregue o arquivo `grafo.txt` pelo menu da aplicação.

## Observação

As restrições de acessibilidade são **simuladas para fins acadêmicos** e não representam condições reais verificadas nas linhas de ônibus.

## Apresentação

[Vídeo de demonstração no YouTube](https://www.youtube.com/watch?v=Va3ge-2BubU)

## Autor

David Mendes
