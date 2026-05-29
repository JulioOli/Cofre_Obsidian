---
tags:
  - note
  - controladoria
  - python
  - fechamento
  - documentacao
  - tools
---
13/05/2026

# Scripts utilitários — folha R e CC

Guia rápido dos scripts em `04-Notebooks/Utitlities/` usados no fluxo de **fechamento / folha** e **centros de custo**. Todos assumem que o terminal está na **raiz do repositório** `Cofre_Trabalho` (ou use caminhos absolutos nos argumentos).

**Primeiro roda esses dois comandos nessa ordem no terminal pra ir pro cofre e ativar o venv:**

```powershell
cd C:\Users\julio.santana\Documents\Projects\Cofre_Trabalho 
```

```
 .\.venv\Scripts\Activate.ps1
```


---

## 1. `base_r_para_fechamento_folha.py`

**O que faz:** lê um **CSV ou Excel** com **~={blue}centro de custo analítico=~** e ~={orange}**valor**=~ (~={blue}`n4_CC`=~ + ~={orange}`valor_nf`=~, **ou** ~={blue}`n4_cod_centro_custo`=~ + ~={orange}`valor_nf`=~), monta a hierarquia **n1–n4** com nomes do `02-Referencias/sagi_rel_centro_custo.csv`, preenche metadados de fechamento (conta, filial, datas, credor etc.) e grava um **Excel** no layout da folha de fechamento.

**Entrada padrão (folha):** `02-Referencias/base_R.csv` — colunas `n4_CC` e `valor_nf`, separador `;`.

**Saída padrão (folha):** `02-Referencias/base_R_fechamento_folha_pagamento.xlsx` (aba `Fechamento`).

**Saída com arquivo customizado:** se você passar outro arquivo de entrada, a saída vira automaticamente `<nome_do_arquivo>_fechamento.xlsx` na mesma pasta (ex.: `7.1.22 - combustivel - diesel.xlsx` → `7.1.22 - combustivel - diesel_fechamento.xlsx`).

**Layout das colunas:** por padrão usa `02-Referencias/FOPA/base_R_fechamento_folha_pagamento_correto.xlsx` como modelo de colunas, **se o arquivo existir**; caso contrário, usa `FECHAMENTO_ODBC_2026_04.xlsx`. Pode forçar com `--layout`.

**Conta padrão:** `7.3.1 SALÁRIOS` (folha). Para outras contas (ex.: diesel interno), use `--cod-conta` e `--conta`.

### Uso mínimo — folha (sem informar arquivo)

```powershell
.\.venv\Scripts\python.exe 04-Notebooks\Utitlities\base_r_para_fechamento_folha.py
```

Com isso: entradas nos caminhos padrão acima, datas padrão da folha, `valor_nf` no CSV em formato brasileiro (`15.419,54`).

### Uso mínimo — informando o arquivo no terminal

Passe o caminho do arquivo **direto no comando** (não precisa editar o `.py`):

```powershell
.\.venv\Scripts\python.exe 04-Notebooks\Utitlities\base_r_para_fechamento_folha.py "02-Referencias/7.1.22 - combustivel - diesel.xlsx"
```

Equivalente com flag:

```powershell
.\.venv\Scripts\python.exe 04-Notebooks\Utitlities\base_r_para_fechamento_folha.py -i "02-Referencias/7.1.22 - combustivel - diesel.xlsx"
```

### Parâmetros úteis (CLI)

| Argumento | Padrão | Função |
|-----------|--------|--------|
| `ENTRADA` (posicional) | — | Arquivo de origem (`.csv` ou `.xlsx`). Atalho: passar direto no comando |
| `--input`, `-i` | `02-Referencias/base_R.csv` | Mesmo que o posicional; sobrescreve se os dois forem informados |
| `--output`, `-o` | *automático* | Folha: `base_R_fechamento_folha_pagamento.xlsx`; demais: `<entrada>_fechamento.xlsx` |
| `--cc-sagi` | `02-Referencias/sagi_rel_centro_custo.csv` | Relação SAGI de CC (descrições por código) |
| `--layout` | *correto* ou ODBC | Excel só para **ordem/nome das colunas** |
| `--sheet-out` | `Fechamento` | Nome da aba |
| `--titulo` | `FOPA_04_2026` | Coluna `titulo` |
| `--observacao` | *automático* | Se omitido: `Processamento de Folha` + data NF (`dd/mm/aaaa`) |
| `--credor` | `PROCESSAMENTO DE FOLHA` | `credor_forn_cli_func` |
| `--origem` | `Saída (Aplicações)` | Coluna `Origem` |
| `--sistema` | `FOPA` | Coluna `Sistema` |
| `--dados-auxiliares` | `Processamento de folha` | Coluna `Dados auxiliares` |
| `--data-nf` | `2026-04-30` | Coluna `data_nf` (`YYYY-MM-DD` ou `DD/MM/YYYY`) |
| `--data-pagamento` | `2026-05-08` | Coluna `data_pagamento` |
| `--multiplicador-valor` | `-1` | Multiplica `valor_nf` da entrada. Use `-1` quando os valores vierem positivos (folha); use `1` se já estiverem negativos |
| `--cod-conta` | `7.3.1` | Código da conta contábil |
| `--conta` | `SALÁRIOS` | Nome da conta |
| `--cod-conta-descr` | *automático* | `<cod-conta> <conta>` — ex.: `7.1.22 COMBUSTÍVEL - DIESEL (INTERNO)` |

**Exemplo** — folha de outro mês:

```powershell
.\.venv\Scripts\python.exe 04-Notebooks\Utitlities\base_r_para_fechamento_folha.py `
  --data-nf 2026-05-31 `
  --data-pagamento 2026-06-06 `
  --titulo FOPA_05_2026 `
  --output 02-Referencias/base_R_fechamento_folha_pagamento_05.xlsx
```

**Exemplo** — diesel interno (conta 7.1.22), informando só o arquivo de entrada:

```powershell
.\.venv\Scripts\python.exe 04-Notebooks\Utitlities\base_r_para_fechamento_folha.py `
  "02-Referencias/7.1.22 - combustivel - diesel.xlsx" `
  --layout "02-Referencias/FOPA/base_R_fechamento_folha_pagamento_correto.xlsx" `
  --cod-conta "7.1.22" `
  --conta "COMBUSTÍVEL - DIESEL (INTERNO)" `
  --titulo "SAGI_05_2026" `
  --sistema "SAGI" `
  --multiplicador-valor 1 `
  --data-nf "2026-05-31"
```

### Onde ajustar regras “fixas” no código

No próprio `.py` (comentários no topo do arquivo ajudam):

- **`SEGMENTO_POR_N1`** — valor da coluna `Segmento` por código `n1` (ex.: `1.2` → SELETIVA).
- **`N1_CENTRO_CUSTO_OVERRIDE`** — ex.: `1.1` usa **PILARES** em `n1_centro_custo`, enquanto `n1_CC` continua com a descrição SAGI (**G3S ESCRITORIO**).
- **`FILIAL_POR_N2_COD`** — filial por `n2_cod_centro_custo` (ex.: `1.2.5` → G3S PRUDENTE). Se aparecer **CC novo** na entrada, o script interrompe com erro pedindo inclusão nesse dicionário.

### Conferência

Depois de gerar, vale comparar com o modelo corrigido (ordenando por `n4_CC`) ou importar no mesmo fluxo do notebook de despesas do fechamento.

---

## 2. `r_fopa_para_fechamento.py`

**O que faz:** lê `02-Referencias/R_FOPA.xlsx` (colunas `n4_CC`, `Data nf`, `Valor plano`), monta a hierarquia **n1–n4** com nomes do `sagi_rel_centro_custo.csv`, preenche metadados de **folha** (conta **7.3.1 SALÁRIOS**, valores negativos, FOPA) e grava Excel no **layout de fechamento** (`FECHAMENTO_ODBC_2026_04.xlsx` ou modelo corrigido da folha).

**Diferença do script 1:** a competência vem da coluna **Data nf** por linha (`titulo` = `FOPA_MM_AAAA`, `data_pagamento` padrão = dia **8** do mês seguinte). Linhas sem valor ou com `Valor plano` = 0 são ignoradas.

**Ajustes automáticos (evitam correção manual):** descrições de CC usam o **SAGI** (ex.: `ARCELOR/BARRA MANSA/RJ-OPERADORES` em vez de `ARCELOR/BARRA MANS`); typo `1.7.8.1.1` → `1.7.1.8.1` (TUPY); filial `1.7.1.8.1` → **G&S PRUDENTE**.

**Saída padrão:** `02-Referencias/R_FOPA_fechamento.xlsx` (aba `Fechamento`).

### Uso mínimo

```powershell
.\.venv\Scripts\python.exe 04-Notebooks\Utitlities\r_fopa_para_fechamento.py
```

### Parâmetros úteis

| Argumento | Padrão | Função |
|-----------|--------|--------|
| `--input` | `02-Referencias/R_FOPA.xlsx` | Planilha de origem |
| `--output` | `02-Referencias/R_FOPA_fechamento.xlsx` | Arquivo gerado |
| `--mes` | — | Filtra uma competência (`2026-04` ou `2026-04-30`) |
| `--data-pagamento` | automático | Fixa pagamento para todas as linhas |
| `--multiplicador-valor` | `-1` | Despesa negativa (padrão fechamento) |
| `--incluir-zerados` | — | Mantém linhas com valor 0 |

**Exemplo** — só abril:

```powershell
.\.venv\Scripts\python.exe 04-Notebooks\Utitlities\r_fopa_para_fechamento.py `
  --mes 2026-04 `
  --output 02-Referencias/R_FOPA_fechamento_04.xlsx
```

---

## 3. `descobre_cc_inativos.py`

**O que faz:** compara os códigos de centro de custo presentes em `02-Referencias/centro-de-custo_ativos-e-inativos.csv` com `02-Referencias/centro-de-custo_apenas-ativos.csv` e **imprime no terminal** a lista de códigos que estão no relatório “completo” mas **não** no de “só ativos” (tratados como inativos para aquele recorte).

**Uso:**

```powershell
.\.venv\Scripts\python.exe 04-Notebooks\Utitlities\descobre_cc_inativos.py
```

Não gera arquivo; só saída de texto para copiar ou arquivar.

---

## Ligações

- [[Analise Base Financeira]] — dicionário de campos e filtros por CC / categoria.
- Arquivos em `02-Referencias/`: `base_R.csv`, `sagi_rel_centro_custo.csv`, `FOPA/base_R_fechamento_folha_pagamento_correto.xlsx` (layout de referência).
