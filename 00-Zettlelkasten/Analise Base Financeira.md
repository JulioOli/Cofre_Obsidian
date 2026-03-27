---
tags:
  - note
  - controladoria
  - base-financeira
  - analise-dados
  - G3S
---
25/03/2026 - 09:00

# ~={Titulo}Análise da Base Financeira — base.csv=~

> Guia de referência para consultar e analisar a base de movimentações financeiras do grupo G3S.
> Arquivo fonte: `02-Referencias/base.csv` — **61.018 registros lógicos** — atualizado em 25/03/2026.
> Relatório descritivo completo: [[RELATORIO_BASE]]

---

## ~={Titulo}Dicionário de Dados Rápido=~

| Coluna | Tipo | O que é | Armadilhas |
|---|---|---|---|
| `codcen` | texto | Código hierárquico do CC (`1.2.5.2`) | Pode ser sintético — verificar se é analítico antes de agregar |
| `descen` | texto | Descrição do CC (`TIPO / DIVISÃO / CIDADE / DEPT`) | Separar por `/` para extrair as dimensões |
| `codcdc` | texto | Código do Plano de Contas (`6.1.1`) | — |
| `descdc` | texto | Descrição da categoria (`COMPRAS DE SUCATAS`) | Encoding pode corromper caracteres (é, ç, ã) |
| `lancamento` | número | ID do lançamento | 1 registro com NaN — remover |
| `ite_pagrec_vencimento` | texto | Data de vencimento (`YYYY-MM-DD`) | `1800-01-01` = saldo migrado legado |
| `iterea_pagamento` | texto | Data de pagamento ou `NAO PAGO` | 254+ variações únicas — normalizar |
| `iterea_valpago` | texto | Valor pago (vírgula decimal) | String — converter para float |
| `documento` | texto | Nº da NF/boleto/documento | `SALDO ADT CLI/FOR` = migração legado |
| `codigo_pessoa` | número | Código do fornecedor/cliente | — |
| `nome` | texto | Nome do fornecedor/cliente | 12 nulos (~0%) |
| `valor_plano` | texto | Valor planejado (negativo=despesa) | String — converter. Negativo = despesa |
| `valor_centro` | texto | Valor rateado ao CC | Geralmente = `valor_plano` |
| `observacao` | texto | Texto livre | Pode ter quebras de linha — causa erro no CSV |
| `nota` | texto | Nota interna | 13.155 nulos (21,6%) |
| `cab_pagrec_id` | número | ID do documento origem | — |
| `valor_bruto` | texto | Valor bruto (sempre positivo) | String — converter. Total: R$436,7M |
| `filial` | texto | Filial do lançamento | `G3S` e `G&S` = mesma filial em períodos diferentes |

---

## ~={Titulo}Dimensões de Análise=~

O campo `descen` carrega 4 dimensões separadas por ` / `:

```
	GERAL CONSOLIDADO / SELETIVA / PRESIDENTE PRUDENTE / COMERCIAL
	     tipo_cc      /  divisao  /       cidade        /   dept
```

Para extrair as dimensões (pandas):
```python
	df[['tipo_cc', 'divisao_cc', 'cidade_cc', 'dept_cc']] = (
	    df['descen'].str.split(' / ', expand=True).iloc[:, :4]
	)
```

---

## ~={Titulo}Filtros Úteis=~

### Por Filial

| Quero ver... | Filtro |
|---|---|
| Apenas G3S Prudente | `filial == 'G3S PRUDENTE'` |
| G3S + G&S da mesma cidade (ex: PP) | `filial.isin(['G3S PRUDENTE', 'G&S PRUDENTE'])` |
| RSE (Ekipa RSE) | `filial == 'RSE'` |
| NVS (Entulho) | `filial == 'NVS - EKIPA'` |

### Por Centro de Custo

| Quero ver... | Filtro em `codcen` |
|---|---|
| Todos os lançamentos da Seletiva (despesa) | Começa com `1.2` |
| Todos os veículos de P. Prudente | Começa com `1.2.5.6` |
| Lançamentos de receita da Seletiva | Começa com `2.2` |
| RSE / Ekipa Locações | Começa com `1.6` ou `2.6` |
| G8S / Ekipa Serv. G&S | Começa com `1.7` ou `2.7` |
| Familiares (sócios) | Começa com `1.9` ou `2.9` |
| Intercompany | `1.10.1` ou `2.10.1` |

### Por Categoria (descdc)

| Quero ver... | Filtro em `descdc` |
|---|---|
| Compras de sucata | `== 'COMPRAS DE SUCATAS'` |
| Vendas de sucata | `== 'VENDAS DE SUCATAS'` |
| Todos os custos operacionais de frota | Começa com `7.1` no `codcdc` |
| Pessoal | Começa com `7.3` no `codcdc` |
| Transporte | `== 'TRANSPORTE DE SUCATA'` ou `6.6.*` |

### Por Status de Pagamento

| Quero ver... | Filtro em `iterea_pagamento` |
|---|---|
| Contas a pagar em aberto | `== 'NAO PAGO'` |
| Lançamentos já baixados | `!= 'NAO PAGO'` |
| Vencidos não pagos | `== 'NAO PAGO'` + `ite_pagrec_vencimento < hoje` |

---

## ~={Titulo}Combinações CC + PC Mais Comuns=~

| CC (`codcen`) | PC (`codcdc`) | O que significa |
|---|---|---|
| `1.2.x.2` (Comercial Seletiva) | `6.1.1` | Compra de sucata na filial X |
| `2.2.x.2` (Comercial Seletiva — receita) | `4.1.1` | Venda de sucata na filial X |
| `1.2.x.6.y` (Veículo específico) | `7.1.2` | Manutenção do veículo Y |
| `1.2.x.6.y` (Veículo específico) | `7.1.4` | Abastecimento diesel do veículo Y |
| `1.2.x.4` (Logística da filial) | `7.1.6` | Transporte de sucata |
| `1.2.x.1` (Administrativo) | `7.3.1` | Salários da filial X |
| `1.1` (G3S Escritório) | `7.5.7` | Honorários contábeis centrais |
| `1.9.x` (Familiar) | `7.11.2` | Pagamento a sócios |
| `1.10.1` (Intercompany) | `5.4.7` | Operação entre empresas do grupo |

---

## ~={Titulo}Armadilhas Conhecidas=~

### 1. Datas Inválidas (`1800-01-01`)
Registros com `ite_pagrec_vencimento = '1800-01-01'` e `iterea_pagamento = '1800-01-01'` são **saldos migrados** do sistema antigo. Eles representam saldos de abertura, não transações reais. Filtrar antes de qualquer análise temporal:
```python
df_valido = df[df['ite_pagrec_vencimento'] > '2015-01-01']
```

### 2. Colunas Financeiras como String
`valor_bruto`, `valor_plano`, `valor_centro`, `iterea_valpago` são strings com vírgula decimal:
```python
for col in ['valor_bruto', 'valor_plano', 'valor_centro', 'iterea_valpago']:
    df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')
```

### 3. `NAO PAGO` misturado com datas
A coluna `iterea_pagamento` tem 2 tipos de valor. Criar flag separado:
```python
df['pago'] = df['iterea_pagamento'] != 'NAO PAGO'
df['data_pagamento'] = pd.to_datetime(df['iterea_pagamento'], errors='coerce')
```

### 4. Duplicidade de filiais (`G3S` vs `G&S`)
A mesma unidade aparece com dois nomes ao longo do tempo. Criar campo normalizado:
```python
df['filial_grupo'] = df['filial'].str.replace('G&S', 'G3S')
```

### 5. Operação intercompany distorce totais
O registro `AJUSTESALDO300925` (R$27,9M) em `RSE` com `OPERAÇÕES ENTRE EMPRESAS` infla o volume bruto total. Isolar antes de análises de rentabilidade:
```python
df_operacional = df[df['descdc'] != 'OPERAÇÕES ENTRE EMPRESAS']
```

### 6. Encoding com caracteres corrompidos
O arquivo usa ISO-8859-1 ou UTF-8 com BOM. Ao abrir no Excel ou Python, especificar encoding:
```python
df = pd.read_csv('base.csv', sep=';', encoding='utf-8-sig', on_bad_lines='skip')
# ou
df = pd.read_csv('base.csv', sep=';', encoding='latin-1')
```

### 7. Registros migrados com `SALDO ADT CLI/FOR`
Documentos `SALDO ADT CLI`, `SALDO ADT FOR`, `MIGRADO` etc. são saldos de abertura, não transações reais. Filtrar para análises de movimentação real.

---

## ~={Titulo}Flags de Atenção=~

| O que verificar | Coluna | Critério |
|---|---|---|
| Contas genéricas (poluem DRE) | `codcdc` | `5.4.6`, `5.4.11`, `7.11.4`, `7.11.6`, `7.1.16` |
| Lançamentos de sócios | `codcen` | Começa com `1.9` ou `2.9` |
| Operações intercompany | `codcen` | `1.10.1` ou `2.10.1` |
| Devoluções invertidas | `codcdc` + `codcen` | `6.4.1` em CC `2.x` (errado!) |
| Adiantamentos a conciliar | `codcdc` | `6.3.1` ou `4.2.1` sem baixa correspondente |
| Saldos legados | `ite_pagrec_vencimento` | `< 2015-01-01` |

---

## ~={Titulo}Resumo por Divisão (na base)=~

Com base nas categorias e CCs predominantes:

| Divisão | Categoria dominante | % aprox. |
|---|---|---|
| Seletiva — Comercial | COMPRAS DE SUCATAS | 43,5% |
| Seletiva — Comercial (rec.) | VENDAS DE SUCATAS | 14,8% |
| Seletiva — Frota | MANUTENÇÃO DE VEÍCULOS/MAQUINAS | 5,9% |
| Seletiva — Comercial | PESAGENS AVULSAS | 4,7% |
| Seletiva — Logística | TRANSPORTE DE SUCATA | 2,3% |
| Geral — Adm. | DESPESAS DE VIAGEM | 2,1% |
| G3S — Financeiro | DESPESAS BANCARIAS | 1,7% |
| Render / RSE | RENDIMENTO FINANCEIRO | 1,4% |
| Ekipa Contêiner | LOCACAO DE CONTEINER E CACAMBAS | 1,2% |
| Geral — RH | SALÁRIOS | 1,1% |

___

[[Guia SAGI]] · [[Divisões]] · [[Tipos de Movimentação]] · [[Filiais]] · [[00 - Índice Controladoria]]
