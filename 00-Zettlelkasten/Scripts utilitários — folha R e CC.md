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

**Pré-requisito:** ambiente Python do projeto (`.venv`) com `pandas` e `openpyxl` instalados.

```powershell
cd C:\Users\julio.santana\Documents\Projects\Cofre_Trabalho
.\.venv\Scripts\python.exe 04-Notebooks\Utitlities\<script>.py [opções]
```

No Linux/macOS, troque por `source .venv/bin/activate` e `python 04-Notebooks/Utitlities/<script>.py`.

---

## 1. `base_r_para_fechamento_folha.py`

**O que faz:** lê `02-Referencias/base_R.csv` (colunas `n4_CC` e `valor_nf`, separador `;`), monta a hierarquia **n1–n4** com nomes do `02-Referencias/sagi_rel_centro_custo.csv`, preenche metadados de **folha de pagamento** (conta **7.3.1 SALÁRIOS**, valores negativos, filial, FOPA, datas etc.) e grava um **Excel** no layout da folha de fechamento.

**Saída padrão:** `02-Referencias/base_R_fechamento_folha_pagamento.xlsx` (aba `Fechamento`).

**Layout das colunas:** por padrão usa `02-Referencias/base_R_fechamento_folha_pagamento_correto.xlsx` como modelo de colunas, **se o arquivo existir**; caso contrário, usa `FECHAMENTO_ODBC_2026_04.xlsx`.

### Uso mínimo

```powershell
.\.venv\Scripts\python.exe 04-Notebooks\Utitlities\base_r_para_fechamento_folha.py
```

Com isso: entradas nos caminhos padrão acima, datas padrão da folha (ajuste na próxima seção), `valor_nf` no CSV em formato brasileiro (`15.419,54`).

### Parâmetros úteis (CLI)

| Argumento | Padrão | Função |
|-----------|--------|--------|
| `--input` | `02-Referencias/base_R.csv` | CSV de origem |
| `--cc-sagi` | `02-Referencias/sagi_rel_centro_custo.csv` | Relação SAGI de CC (descrições por código) |
| `--layout` | *correto* ou ODBC | Excel só para **ordem/nome das colunas** |
| `--output` | `02-Referencias/base_R_fechamento_folha_pagamento.xlsx` | Arquivo gerado |
| `--sheet-out` | `Fechamento` | Nome da aba |
| `--titulo` | `FOPA_04_2026` | Coluna `titulo` |
| `--observacao` | *automático* | Se omitido: `Processamento de Folha` + data NF (`dd/mm/aaaa`) |
| `--credor` | `PROCESSAMENTO DE FOLHA` | `credor_forn_cli_func` |
| `--origem` | `Saída (Aplicações)` | Coluna `Origem` |
| `--sistema` | `FOPA` | Coluna `Sistema` |
| `--dados-auxiliares` | `Processamento de folha` | Coluna `Dados auxiliares` |
| `--data-nf` | `2026-04-30` | Coluna `data_nf` (`YYYY-MM-DD` ou `DD/MM/YYYY`) |
| `--data-pagamento` | `2026-05-08` | Coluna `data_pagamento` |
| `--multiplicador-valor` | `-1` | Multiplica `valor_nf` do CSV (negativo = despesa/saída, como no modelo corrigido) |

**Exemplo** — outro mês e arquivo de saída explícito:

```powershell
.\.venv\Scripts\python.exe 04-Notebooks\Utitlities\base_r_para_fechamento_folha.py `
  --data-nf 2026-05-31 `
  --data-pagamento 2026-06-06 `
  --titulo FOPA_05_2026 `
  --output 02-Referencias/base_R_fechamento_folha_pagamento_05.xlsx
```

### Onde ajustar regras “fixas” no código

No próprio `.py` (comentários no topo do arquivo ajudam):

- **`SEGMENTO_POR_N1`** — valor da coluna `Segmento` por código `n1` (ex.: `1.2` → SELETIVA).
- **`N1_CENTRO_CUSTO_OVERRIDE`** — ex.: `1.1` usa **PILARES** em `n1_centro_custo`, enquanto `n1_CC` continua com a descrição SAGI (**G3S ESCRITORIO**).
- **`FILIAL_POR_N2_COD`** — filial por `n2_cod_centro_custo` (ex.: `1.2.5` → G3S PRUDENTE). Se aparecer **CC novo** no `base_R.csv`, o script interrompe com erro pedindo inclusão nesse dicionário.

### Conferência

Depois de gerar, vale comparar com o modelo corrigido (ordenando por `n4_CC`) ou importar no mesmo fluxo do notebook de despesas do fechamento.

---

## 2. `descobre_cc_inativos.py`

**O que faz:** compara os códigos de centro de custo presentes em `02-Referencias/centro-de-custo_ativos-e-inativos.csv` com `02-Referencias/centro-de-custo_apenas-ativos.csv` e **imprime no terminal** a lista de códigos que estão no relatório “completo” mas **não** no de “só ativos” (tratados como inativos para aquele recorte).

**Uso:**

```powershell
.\.venv\Scripts\python.exe 04-Notebooks\Utitlities\descobre_cc_inativos.py
```

Não gera arquivo; só saída de texto para copiar ou arquivar.

---

## Ligações

- [[Analise Base Financeira]] — dicionário de campos e filtros por CC / categoria.
- Arquivos em `02-Referencias/`: `base_R.csv`, `sagi_rel_centro_custo.csv`, `base_R_fechamento_folha_pagamento_correto.xlsx` (layout de referência).
