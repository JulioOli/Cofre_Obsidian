---
tags:
  - note
  - tools
  - fechamento
---
27/05/2026

## ~={Titulo}O que faz=~

Lê um export **ODBC do SAGI** (CSV ou XLSX) e converte para o layout padrão do fechamento geral (`FECHAMENTO_ODBC_{AAAA}_{MM}.xlsx`).

O notebook monta as 34 colunas do fechamento a partir das colunas ODBC — **não precisa** de um arquivo `FECHAMENTO_ODBC_*.xlsx` pré-existente como modelo.

**Notebook:** `04-Notebooks/Fechamento/conversao_odbc_para_fechamento.ipynb`

**Relacionado:** [[Analise Base Financeira]] · [[Premissas - Fechamento]] · [[Script de Auditoria Semanal de Lancamentos ODBC - Como Usar]]

## ~={Titulo}Escopo=~

Use este notebook quando a fonte já estiver no **formato ODBC** (export direto do SAGI / query ODBC), com colunas como `codcen`, `descen`, `valor_bruto`, `valor_centro`, etc.

Para outras origens, existem notebooks irmãos:

| Origem | Notebook |
|---|---|
| Despesas ATUA | `normalizar_atua_despesas.ipynb` |
| Receitas ATUA | `normalizar_atua_receitas.ipynb` |
| Custo frete ATUA | `normalizar_atua_custo_frete.ipynb` |
| Supply / Bracofer | `normalizar_supply.ipynb` |

## ~={Titulo}Arquivos envolvidos=~

| Papel | Caminho típico |
|---|---|
| Entrada ODBC | `02-Referencias/Fechamento/dados_odbc_abril-e-maio.xlsx` ou `.csv` |
| Saída por mês | `02-Referencias/Fechamento/FECHAMENTO_ODBC_{AAAA}_{MM}.xlsx` |
| Saída consolidada | `02-Referencias/Fechamento/FECHAMENTO_ODBC_COMPLETO_{AAAA}.xlsx` |
| Sem filtro de mês | `02-Referencias/Fechamento/{nome_do_arquivo}_fechamento.xlsx` |

## ~={Titulo}Mapeamento de valores=~

| Coluna no fechamento | Coluna ODBC |
|---|---|
| `valor_conta` | `valor_centro` |
| `valor_pago` | `valor_bruto` |
| `Valor Oficial` | `valor_bruto` |
| `valor_nf` | `valor_bruto` |

As somas são conferidas automaticamente ao final de cada exportação. Se tudo estiver certo, os totais da saída batem com os da entrada:

```
ODBC valor_bruto = saida valor_pago = Valor Oficial
ODBC valor_centro = saida valor_conta
```

## ~={Titulo}Passo a passo=~

### ~={blue}1) Preparar o arquivo ODBC=~

- Formato aceito: **`.xlsx`**, **`.xls`** ou **`.csv`** (separador `;`, encoding UTF-8 / CP1252).
- Se for XLSX com várias abas, anote o nome da aba (ex.: `ODBC_Pilares`).
- Feche o Excel antes de rodar (arquivo aberto pode causar `PermissionError`).

Colunas **obrigatórias** na entrada:

`codcen`, `descen`, `codcdc`, `descdc`, `filial`, `documento`, `valor_bruto`, `valor_centro`, `observacao`, `lancamento`, `iterea_pagamento`, `codigo_pessoa`, `nome`, `nota`

Se alguma faltar, o notebook lista quais estão ausentes.

### ~={blue}2) Abrir o notebook=~

```text
04-Notebooks/Fechamento/conversao_odbc_para_fechamento.ipynb
```

Use o kernel **`.venv`** do projeto.

### ~={blue}3) Reiniciar o kernel=~

Sempre que abrir o notebook (ou depois de atualizações no código), faça **Restart Kernel → Run All**.

Na célula 1, a saída esperada inclui:

```text
Notebook v2.0 — sem arquivo MODELO externo
Parametros carregados com sucesso.
Layout de saida: 34 colunas (fixo no notebook)
```

> ~={red}Se aparecer erro com `MODELO_PATH` ou `FECHAMENTO_ODBC_2026_04.xlsx`=~, o kernel ainda está com código antigo em memória. Reinicie o kernel e rode tudo de novo a partir da célula 1.

### ~={blue}4) Ajustar os parâmetros (célula 1)=~

```python
BASE_PATH = Path('..') / '..' / '02-Referencias' / 'fechamento_pilares_01-05.xlsx'
BASE_SHEET = 'ODBC_Pilares'          # None = primeira aba
MESES_REFERENCIA = ['01/2026', '02/2026', '03/2026']  # None = sem filtro
CAMPO_DATA_FILTRO = 'lancamento'       # ou 'ite_pagrec_vencimento'
OUT_DIR = Path('..') / '..' / '02-Referencias'
PREFIXO_SAIDA = 'FECHAMENTO_ODBC'
```

| Parâmetro | Descrição |
|---|---|
| `BASE_PATH` | Arquivo ODBC de entrada |
| `BASE_SHEET` | Aba do Excel (`None` = primeira) |
| `MESES_REFERENCIA` | Lista `MM/AAAA` para filtrar e gerar um arquivo por mês. `None` = converte tudo de uma vez |
| `CAMPO_DATA_FILTRO` | Coluna usada no filtro mensal: `lancamento` (data do lançamento) ou `ite_pagrec_vencimento` |
| `OUT_DIR` | Pasta de saída |
| `PREFIXO_SAIDA` | Prefixo dos arquivos gerados por mês |

### ~={blue}5) Executar todas as células=~

Ordem do fluxo:

1. **Parâmetros** — valida caminhos e define layout de saída.
2. **Funções auxiliares** — parsing de valores, datas, hierarquia de CC, etc.
3. **Leitura + conversão + exportação** — lê o ODBC, filtra por mês (se configurado), converte e salva os Excel.
4. **Checagem de colunas** — confirma que a saída tem as 34 colunas esperadas.

## ~={Titulo}Exemplos de uso=~

### Vários meses de um XLSX

```python
BASE_PATH = Path('..') / '..' / '02-Referencias' / 'fechamento_pilares_01-05.xlsx'
BASE_SHEET = 'ODBC_Pilares'
MESES_REFERENCIA = ['01/2026', '02/2026', '03/2026', '04/2026', '05/2026']
```

Gera: `FECHAMENTO_ODBC_2026_01.xlsx` … `05.xlsx` + `FECHAMENTO_ODBC_COMPLETO_2026.xlsx`.

### Um único mês de um CSV

```python
BASE_PATH = Path('..') / '..' / '02-Referencias' / 'Meus_Dados' / 'base.csv'
BASE_SHEET = None
MESES_REFERENCIA = ['04/2026']
CAMPO_DATA_FILTRO = 'lancamento'
```

### Arquivo inteiro, sem filtrar por mês

```python
MESES_REFERENCIA = None
```

Gera um único arquivo: `{stem_do_arquivo}_fechamento.xlsx`.

## ~={Titulo}Conferência dos resultados=~

Após cada mês (e no consolidado), o notebook imprime os totais. Exemplo:

```text
04/2026: ODBC valor_bruto=1,234,567.89 | saida valor_pago=1,234,567.89 | Valor Oficial=1,234,567.89
04/2026: ODBC valor_centro=-987,654.32 | saida valor_conta=-987,654.32
```

Se os pares não baterem, verifique:

- Se o arquivo ODBC foi salvo com valores numéricos (Excel) ou texto com vírgula (CSV).
- Se há linhas duplicadas ou filtros de mês incorretos (`CAMPO_DATA_FILTRO` / `MESES_REFERENCIA`).

## ~={Titulo}Problemas comuns=~

| Sintoma | Causa provável | Solução |
|---|---|---|
| `MODELO_PATH` / `FECHAMENTO_ODBC_2026_04.xlsx` | Kernel com código antigo | Restart Kernel → Run All |
| `Colunas ODBC obrigatorias ausentes` | Export incompleto ou aba errada | Conferir `BASE_SHEET` e colunas do arquivo |
| `Nenhum registro encontrado para MM/AAAA` | Filtro de mês não encontrou datas | Trocar `CAMPO_DATA_FILTRO` ou conferir formato da data na coluna |
| Valores multiplicados por ~100 | Bug corrigido na v2.0 | Reiniciar kernel e rodar versão atual |
| `PermissionError` ao salvar | Excel aberto | Fechar o arquivo de saída/entrada |

## ~={Titulo}O que o notebook monta automaticamente=~

Além dos valores, o notebook deriva do ODBC:

- Hierarquia de centro de custo (`codcen` → `n1`…`n4` código e descrição)
- Descrições de CC a partir de `descen` (split por `/`)
- `Origem` — `Entrada (Origem)` se `cod_conta` começa com `4.` ou `5.`; senão `Saida (Aplicacoes)`
- `Sistema` = `SAGI` (fixo)
- `id` sequencial com 6 dígitos

Campos deixados em branco por padrão: `DE-PARA1`, `DE-PARA2`, `CUSTEIO VARIÁVEL`.
