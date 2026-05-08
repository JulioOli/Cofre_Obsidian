---
tags:
  - note
---
27/04/2026 - 11:45



Melhoria no BCBI: Criação de Tela de Projeções Anuais e Indicadores de Ritmo de Estoque

**Descrição / Contexto:** A diretoria (Marcondes) solicitou uma evolução no painel atual do BCBI para melhorar a visibilidade sobre as projeções financeiras e operacionais até o final do ano. O objetivo principal é facilitar a tomada de decisão com base no "ritmo" (forecast) atual em relação às metas anuais, além de aprimorar o monitoramento do estoque.

**Requisitos e Especificações:**

**1. Novo Indicador no Card de Estoque (Painel Principal)**

- **Ação:** Adicionar a métrica de **"Ritmo da Baixa de Estoque Mensal"**.

- **Local:** Diretamente no card de "ESTOQUE" já existente na visão geral do BCBI (onde atualmente constam os valores em R$ e KG).

- **Objetivo:** Permitir a visualização rápida da projeção de consumo/saída de estoque para o mês vigente, baseando-se na velocidade atual de baixas.


**2. Nova Métrica de "Ritmo Anual"**

- **Ação:** Implementar o cálculo e a exibição do **Ritmo Anual**.

- **Objetivo:** Projetar os resultados acumulados para o fechamento do ano (dezembro), extrapolando o ritmo atual de receitas, custos e movimentações.


**3. Nova Aba/Tela Dedicada a Projeções (Sugestão de Adição)**

- **Ação:** Criar uma nova tela (aba) no menu do BI chamada **"Projeções Anuais"**.

- **Objetivo:** Consolidar as métricas de Ritmo Anual em uma visão única e detalhada.

- **Comportamento Esperado:** Esta tela deve compilar os dados de realização atualizados e aplicar a projeção até o final do ano, idealmente permitindo o comparativo de "Realizado x Ritmo Anual (Projeção) x Meta Anual".


**Critérios de Aceite (DoD):**

- [ ] O card de "ESTOQUE" exibe claramente a informação de ritmo de baixa mensal.

- [ ] O menu principal do BCBI possui a nova aba "Projeções Anuais".

- [ ] Os cálculos de ritmo anual (forecast) estão validados e refletem a projeção correta para o resto do ano.

___
