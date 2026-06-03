---
tags:
  - note
  - tools
---
30/04/2026 - 10:13



## O que faz

Lê o pivot do Excel `02-Referencias/Auditoria/Detalhamento Custos com 2.1.1 - <periodo>.xlsx`, achata a hierarquia (Plano → Credor → Documento → Histórico) e gera um relatório multi-aba destacando divergências entre os meses (planos com salto de valor, credores avulsos / com mudança de plano de contas, lançamentos com z-score atípico).

## Escopo desta nota

Esta nota é **somente** para `scripts/auditoria_custos_fixos.py` (análise de pivot de custos fixos).

Para a auditoria semanal de lacunas do ODBC (com canvas na IDE), usar:

- `scripts/auditoria_lancamentos.py`
- `02-Referencias/Meus_Dados/regras_auditoria.yaml`
- nota: `00-Zettlelkasten/Script de Auditoria Semanal de Lancamentos ODBC - Como Usar.md`

## Passo a passo

### 1) Abrir o PowerShell na raiz do projeto

```powershell
cd C:\Users\julio.santana\Documents\Projects\Cofre_Trabalho
```

### 2) Ativar o venv

```powershell
.\.venv\Scripts\Activate.ps1
```

O prompt deve mudar para `(.venv) PS C:\...>`.

### 3) Rodar o script

```powershell
python scripts/auditoria_custos_fixos.py
```

### 4) Conferir o resultado

- Console mostra a reconciliação (soma das folhas vs. `Grande Total` deve dar `R$ 0,00` em todos os meses) e o top 5 de planos / credores / lançamentos com flag.
- Excel gerado em `02-Referencias/Auditoria/auditoria_custos_fixos_2026.xlsx` com as abas:
	- `00 - Resumo` — contagem de flags por severidade
	- `01 - Plano por Mes` — totais e variação por plano
	- `02 - Credor x Plano` — credores fora do padrão
	- `03 - Lancamentos Suspeitos` — folhas com z-score ≥ 2
	- `04 - Dados Achatados` — pivot achatado (uma linha por lançamento-folha) para conferência
	- `05 - Parametros` — limiares usados na execução

## Parâmetros opcionais

```powershell
python scripts/auditoria_custos_fixos.py `
	--limiar-pct 0.5 `
	--valor-minimo 200 `
	--zscore 2.5
```

| Flag | Default | O que faz |
|---|---|---|
| `--src` | `02-Referencias/Auditoria/Detalhamento Custos com 2.1.1 - 01_2026 a 04_2026.xlsx` | Caminho do pivot de origem |
| `--dst` | `02-Referencias/Auditoria/auditoria_custos_fixos_2026.xlsx` | Caminho do relatório de saída |
| `--limiar-pct` | `0.30` | Variação % mínima vs. mediana de referência para virar flag |
| `--valor-minimo` | `100.0` | Ignora variações abaixo desse valor absoluto (R$) |
| `--zscore` | `2.0` | |z| mínimo para sinalizar lançamento atípico |

**Referência no script:** `MES_REFERENCIA` = JAN + FEV (baseline auditado); `MESES_AUDITAR` = MAR + ABR (contraste no texto da aba Parâmetros). As colunas mensais no Excel são `JAN/2026`, ` FEV/2026`, `  MAR/2026`, `   ABR/2026` (espaços à esquerda como o Excel exporta).

## Quando atualizar

Quando chegar uma nova versão do pivot (ex.: incluindo MAI/2026), abrir o script e ajustar:

- `COLS_VALOR_ORIG` — mapeamento dos cabeçalhos do Excel para nomes internos
- `MESES`, `MES_REFERENCIA`, `MESES_AUDITAR`, `MES_LABEL`

E rodar de novo. Os totais aparecem na aba `05 - Parametros` para conferência rápida.

## Significado das flags

**Aba `01 - Plano por Mes`:**
- `MES_UNICO:<MES>` — gasto aparece em apenas um mês (provável sazonalidade ou lançamento atípico)
- `MES_ZERADO:<MES>` — outros meses têm valor mas esse está zerado
- `VARIACAO_<SEV>:<MES>(±X%)` — variação vs. mediana dos demais meses

**Aba `02 - Credor x Plano`:**
- `CREDOR_AVULSO:<MES>` — credor aparece em só 1 mês
- `FALTA_NO_MES:<MES>` — credor não zerado em todos os meses; pode repetir a flag (um rótulo por mês sem lançamento)
- `VARIACAO_CREDOR_<SEV>:±X%` — diferença entre o maior e o menor valor do credor
- `MUDANCA_DE_PLANO(N)` — mesmo credor lançado em N planos de contas distintos (forte indício de CC errado)

**Aba `03 - Lancamentos Suspeitos`:**
- `VALOR_FOGE_PADRAO_<SEV>(z=±X)` — valor a |X| desvios padrão da média do par (plano, credor)
- `POSSIVEL_ESTORNO` — valor positivo num grupo predominantemente negativo

___

[[Analise Base Financeira]]
