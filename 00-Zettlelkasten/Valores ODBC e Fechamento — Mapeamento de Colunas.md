---
tags:
  - note
  - controladoria
  - fechamento
  - base-financeira
  - G3S
atualizado: 17/06/2026
---
17/06/26 - 10:00

### ~={Titulo}O que é=~

Nota de referência sobre a ~={orange}lógica dos valores financeiros=~ no fluxo **ODBC (SAGI) → layout de fechamento** (`FECHAMENTO_ODBC_*.xlsx`).

O export ODBC traz **quatro colunas de valor** com papéis distintos. No fechamento, três delas viram colunas do Excel (`valor_nf`, `valor_pago`, `valor_conta`) e uma quarta alimenta o ~={cyan}**Valor Oficial**=~ — campo usado em rateios, gráficos e consolidados da controladoria.

> ~={red}Erro comum:=~ tratar `valor_bruto`, `valor_plano` e `valor_centro` como se fossem iguais. Em lançamentos **rateados**, os totais **não batem** entre si — e isso é esperado.

---

### ~={Titulo}Colunas no ODBC (origem)=~

| Coluna ODBC | O que representa | Observação |
|---|---|---|
| `valor_bruto` | Valor **cheio** do documento (nota fiscal / título) | Sempre positivo na base; é o “valor da NF” antes do rateio |
| `iterea_valpago` | Valor **efetivamente pago** na parcela/item | Pode ser zero (título em aberto) ou menor que o bruto (pagamento parcial) |
| `valor_plano` | Parcela do valor **rateada pelo plano de contas** | Negativo = despesa; positivo = receita. Soma das linhas rateadas por conta |
| `valor_centro` | Parcela do valor **rateada pelo centro de custo** | Mesma lógica de sinal que `valor_plano`, mas no eixo CC |

#### ~={Titulo}Quando `valor_plano` e `valor_centro` coincidem=~

Em lançamentos **sem rateio** (uma linha = um documento inteiro), `valor_plano` e `valor_centro` costumam ser **iguais**. Quando o mesmo documento é **quebrado** em várias linhas (vários CCs ou várias contas), cada linha traz apenas a **fatia** daquele rateio — e a soma das fatias fecha com o `valor_bruto` do documento.

---

### ~={Titulo}Colunas no fechamento (destino)=~

| Coluna fechamento | Significado operacional |
|---|---|
| `valor_nf` | Valor da nota fiscal / documento (valor cheio) |
| `valor_pago` | Valor pago (fluxo de caixa da parcela) |
| `valor_conta` | Valor **analítico por centro de custo** — base para DRE por CC |
| `Valor Oficial` | Valor **oficial** para consolidados, rateios e gráficos da controladoria |

---

### ~={Titulo}Mapeamento correto (ODBC → fechamento)=~

Regra vigente a partir da **v2.4** do notebook `conversao_odbc_para_fechamento.ipynb` (validada com o gestor em jun/2026):

| Coluna fechamento | ← | Coluna ODBC |
|---|---|---|
| `valor_nf` | ← | `valor_bruto` |
| `valor_pago` | ← | `iterea_valpago` |
| `valor_conta` | ← | `valor_centro` |
| `Valor Oficial` | ← | `valor_centro` |

~={yellow}Destaque:=~ o **Valor Oficial** deve vir de `valor_centro`, **não** de `valor_plano`. O `valor_plano` reflete o rateio pelo **plano de contas**; o fechamento oficial trabalha com o rateio pelo **centro de custo**.

#### ~={Titulo}Conferência de totais (exemplo maio/2026)=~

Em um mês com rateio intenso, os totais **devem ser diferentes**:

```
ODBC valor_bruto     ≈ 61.019.831,74  →  saida valor_nf
ODBC iterea_valpago  ≈ 35.150.395,83  →  saida valor_pago
ODBC valor_centro    ≈ 10.733.310,96  →  saida valor_conta = Valor Oficial
```

Se `valor_nf`, `valor_pago` e `valor_conta` saírem **idênticos** linha a linha, o mapeamento provavelmente está errado (código antigo usava `valor_bruto` ou `valor_plano` em colunas que deveriam refletir rateio).

---

### ~={Titulo}Sinais e gravação no Excel=~

- Na base ODBC, ~={blue}receitas=~ tendem a vir **positivas** e ~={blue}despesas=~ **negativas** em `valor_centro` / `valor_plano`.
- No Excel de fechamento, `valor_conta` e `Valor Oficial` têm o **sinal preservado** (não forçar `-abs` na gravação).
- `valor_pago` pode ser normalizado pelo utilitário `fechamento_excel.py` conforme o layout legado do fechamento.
- `valor_nf` mantém o valor cheio do documento (positivo na exportação ODBC típica).

---

### ~={Titulo}Onde isso se aplica=~

| Contexto | Observação |
|---|---|
| Notebook `conversao_odbc_para_fechamento.ipynb` | Mapeamento principal ODBC → `FECHAMENTO_ODBC_*.xlsx` |
| `base.csv` / exports ODBC | Mesmas colunas; ver [[Analise Base Financeira]] |
| Rateios (Pilares, APOIO) | Somam `valor_centro` ou `Valor Oficial` conforme o critério — ver [[Critério de Rateio - Pilares]] |
| ATUA / Supply / Folha | Outras origens montam o layout de fechamento com regras próprias; não usar este mapeamento ODBC nelas |

---

### ~={Titulo}Armadilhas na auditoria=~

1. **Comparar soma de `valor_bruto` com `valor_conta`** — em mês rateado, não devem ser iguais.
2. **Usar `valor_plano` como Valor Oficial** — distorce DRE por CC quando há rateio cruzado conta × centro.
3. **Ignorar `iterea_valpago` = 0** — título pode estar lançado (`valor_bruto` > 0) mas ainda não pago.
4. **Duplicatas com mesmo `valor_bruto`** — podem ser **rateio legítimo**; validar se a soma de `valor_centro` ou `valor_plano` fecha o bruto antes de marcar erro (ver regra 3 em auditoria de lançamentos).

___

[[Analise Base Financeira]] · [[Notebook Conversao ODBC para Fechamento - Como Usar]] · [[Premissas - Fechamento]] · [[Critério de Rateio - Pilares]] · [[Tipos de Movimentação]]
