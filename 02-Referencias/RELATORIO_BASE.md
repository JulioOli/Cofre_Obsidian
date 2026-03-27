# ~={Titulo}Relatório Descritivo — Base de Movimentação Financeira=~

**Arquivo:** `base.csv`  
**Gerado em:** 26/03/2026 *(base.csv atualizada em 27/03/2026 — recalcular estatísticas)*  
**Ferramenta de análise:** Python + pandas (`.venv`)

---

## 1. Visão Geral

A base contém o histórico de **movimentações financeiras** (lançamentos de contas a pagar e a receber) de um grupo empresarial do setor de **reciclagem e comercialização de sucatas** (G3S / G&S), com operações em múltiplas cidades do Brasil.

| Dimensão | Valor |
|---|---|
| Total de registros lógicos | 60.922 |
| Total de colunas | 18 |
| Tamanho em disco | ~17 MB |
| Período (datas de vencimento válidas) | 2020 a 2029 |
| Volume financeiro bruto total | R$ 436.263.908,21 |
| Saldo planejado consolidado (valor_plano) | −R$ 28.807.554,76 |
| Filiais distintas | 20 |
| Categorias de lançamento (descdc) | 158 |
| Fornecedores/Clientes distintos (nome) | ~5.549 |

---

## 2. Estrutura das Colunas

| Coluna | Tipo Original | Descrição |
|---|---|---|
| `codcen` | object | Código hierárquico do centro de custo (ex: `1.2.8.1`) |
| `descen` | object | Descrição completa do centro de custo (estrutura: TIPO / DIVISÃO / CIDADE / DEPARTAMENTO) |
| `codcdc` | object | Código da categoria de despesa/receita |
| `descdc` | object | Descrição da categoria (ex: COMPRAS DE SUCATAS) |
| `lancamento` | float64 | Número identificador do lançamento |
| `ite_pagrec_vencimento` | object | Data de vencimento da parcela (formato YYYY-MM-DD) |
| `iterea_pagamento` | object | Status de pagamento: `"NAO PAGO"` ou data real de pagamento |
| `iterea_valpago` | object | Valor efetivamente pago na baixa |
| `documento` | object | Número do documento fiscal (NF, boleto, etc.) |
| `codigo_pessoa` | float64 | Código interno do fornecedor ou cliente |
| `nome` | object | Nome do fornecedor ou cliente |
| `valor_plano` | object | Valor planejado (negativo = despesa, positivo = receita) |
| `valor_centro` | object | Valor rateado ao centro de custo (geralmente igual ao valor_plano) |
| `observacao` | object | Texto livre com observações do lançamento |
| `nota` | object | Campo de nota interna (21,6% nulo) |
| `cab_pagrec_id` | float64 | ID do cabeçalho do documento de pagamento/recebimento |
| `valor_bruto` | object | Valor bruto da movimentação (sempre positivo) |
| `filial` | object | Nome da filial onde o lançamento foi realizado |

### Hierarquia do Centro de Custo (`descen`)

O campo `descen` segue a estrutura `TIPO / DIVISÃO / CIDADE / DEPARTAMENTO`:

```
GERAL CONSOLIDADO / SELETIVA / MARINGA / COMERCIAL
RECEITA           / SELETIVA / LONDRINA / ADMINISTRATIVO
DESPESA           / PILARES  / PRESIDENTE PRUDENTE / VEICULOS
```

| Nível | Campo extraído | Valores mais comuns |
|---|---|---|
| Tipo | `tipo_cc` | GERAL CONSOLIDADO (55%), RECEITA (24%), DESPESA (18%) |
| Divisão | `divisao_cc` | SELETIVA (86%), PILARES (3%), EKIPA (2%) |
| Cidade | `cidade_cc` | Pres. Prudente (28%), Maringá (20%), Londrina (13%) |
| Departamento | `dept_cc` | COMERCIAL (69%), ADMINISTRATIVO (7%), VEÍCULOS (5%) |

---

## 3. Qualidade dos Dados

### 3.1 Valores Nulos

| Coluna | Nulos | % |
|---|---|---|
| `nota` | 13.141 | 21,6% |
| `nome` | 12 | ~0% |
| Demais colunas | ≤1 | ~0% |

A linha com `lancamento = NaN` (1 registro) é provavelmente uma linha de cabeçalho duplicada ou registro corrompido — deve ser removida na limpeza.

### 3.2 Datas Inválidas

A coluna `ite_pagrec_vencimento` contém datas fora do intervalo esperado:

- **Mínimo encontrado:** `1800-01-01` (data inválida, padrão de sistema legado para saldos migrados)
- **Máximo encontrado:** `2029-08-05` (lançamentos futuros, esperado para a pagar)
- **Recomendação:** Filtrar registros com data anterior a `2015-01-01` como anomalias antes de análises temporais.

### 3.3 Status de Pagamento (`iterea_pagamento`)

O campo mistura dois tipos de valores no mesmo campo:
- `"NAO PAGO"` — string literal indicando inadimplência
- Data de pagamento (formato `YYYY-MM-DD`) — indica que o lançamento foi baixado

> **Atenção de QA:** Auditar variações de grafia (ex: `"NAO PAGO "` com espaço) e datas mal formatadas.

### 3.4 Colunas Financeiras como String

As colunas `valor_plano`, `valor_centro`, `valor_bruto` e `iterea_valpago` são carregadas como `object` (string). Alguns registros contêm formatação com vírgula decimal (padrão brasileiro, ex: `"11879,5"`). A limpeza deve aplicar `.replace(',', '.')` seguido de conversão para `float`.

---

## 4. Filiais

O grupo opera com **20 filiais** identificadas. Há duplicidade de nomes históricos (ex: `G3S PRUDENTE` e `G&S PRUDENTE` referem-se à mesma unidade em diferentes períodos).

| Filial | Lançamentos | % do total |
|---|---|---|
| G3S PRUDENTE | 15.030 | 24,7% |
| G3S MARINGA | 11.560 | 19,0% |
| G3S CAMPO GRANDE | 9.217 | 15,1% |
| G3S LONDRINA | 7.706 | 12,6% |
| G3S DOURADOS | 5.119 | 8,4% |
| G&S PRUDENTE | 4.773 | 7,8% |
| RSE | 2.556 | 4,2% |
| G3S CIDADE ALTA | 2.201 | 3,6% |
| G&S MARINGA | 872 | 1,4% |
| G&S DOURADOS | 665 | 1,1% |
| NVS - EKIPA | 347 | 0,6% |
| G&S BARUERI | 246 | 0,4% |
| G3S ADM | 181 | 0,3% |
| G&S LONDRINA | 151 | 0,2% |
| GXS MARINGA | 142 | 0,2% |
| Outras (4 filiais) | 48 | 0,1% |

> **Nota:** `G3S` e `G&S` no nome da mesma cidade indicam renomeações societárias ao longo do tempo. Recomenda-se criar um campo `grupo_filial` para consolidação.

---

## 5. Categorias de Lançamento (`descdc`)

As **158 categorias** cobrem tanto receitas quanto despesas. As 15 mais frequentes respondem por ~83% dos registros:

| Categoria | Lançamentos | % |
|---|---|---|
| COMPRAS DE SUCATAS | 26.475 | 43,5% |
| VENDAS DE SUCATAS | 9.032 | 14,8% |
| MANUTENÇÃO DE VEÍCULOS/MAQUINAS | 3.595 | 5,9% |
| PESAGENS AVULSAS | 2.852 | 4,7% |
| TRANSPORTE DE SUCATA | 1.407 | 2,3% |
| DESPESAS DE VIAGEM | 1.310 | 2,1% |
| DESPESAS BANCARIAS | 1.035 | 1,7% |
| RENDIMENTO FINANCEIRO | 883 | 1,4% |
| LOCACAO DE CONTEINER E CACAMBAS | 733 | 1,2% |
| SALÁRIOS | 651 | 1,1% |
| ALIMENTAÇÃO DO TRABALHADOR | 645 | 1,1% |
| SISTEMAS | 586 | 1,0% |
| SEGUROS | 472 | 0,8% |
| RASTREADOR/ MONITORAMENTO | 435 | 0,7% |
| PEDÁGIO | 422 | 0,7% |

---

## 6. Status de Pagamento

| Status | Qtd | % |
|---|---|---|
| Pago (com data de baixa) | 57.596 | 94,5% |
| NAO PAGO | 3.326 | 5,5% |

Os 3.326 registros "NAO PAGO" representam o **contas a pagar em aberto**. Uma análise adicional de vencimento vs. data atual permitiria classificá-los em **a vencer** e **vencidos** (inadimplência real).

---

## 7. Análise Financeira Sumária

### Colunas de valor

| Coluna | Soma | Média aprox. |
|---|---|---|
| `valor_bruto` | R$ 436.263.908,21 | R$ 7.161,83 |
| `valor_plano` | −R$ 28.807.554,76 | −R$ 472,85 |

> O `valor_plano` negativo dominante confirma que a base contém predominantemente **despesas** (compras de sucata, custos operacionais). As receitas de venda existem, mas em menor volume de lançamentos.

### Maiores Transações

| Descrição | Filial | Valor Bruto |
|---|---|---|
| OPERAÇÕES ENTRE EMPRESAS | RSE | R$ 27.965.323,40 |
| MAQUINAS E EQUIPAMENTOS | G3S CAMPO GRANDE | R$ 1.258.158,92 |
| VENDAS DE SUCATAS (3x) | G3S CAMPO GRANDE | R$ 629.463,55 cada |
| ADIANTAMENTO CLIENTE SUCATA | G3S PRUDENTE | R$ 371.897,99 |

> A transação de R$ 27,9M (documento `AJUSTESALDO300925`) é uma **operação interempresa** com a RSE. Deve ser tratada como item especial em análises de rentabilidade para evitar distorção.

---

## 8. Recomendações de QA

1. **Remover ou isolar** o registro com `lancamento = NaN` (linha corrompida).
2. **Filtrar datas inválidas** (anteriores a 2015) em análises temporais — usar coluna auxiliar `data_valida`.
3. **Normalizar nomes de filiais** — unificar `G3S X` e `G&S X` em um campo `grupo_filial`.
4. **Converter colunas financeiras** para `float` com `replace(',', '.')` e logar valores inválidos.
5. **Criar flag `pago`** booleano a partir de `iterea_pagamento != "NAO PAGO"` para facilitar filtros.
6. **Extrair hierarquia de `descen`** em colunas separadas (`tipo_cc`, `divisao_cc`, `cidade_cc`, `dept_cc`) para análises dimensionais.
7. **Auditar `iterea_pagamento`** — podem existir variações de grafia ou formatos de data inválidos misturados.

---

## 9. Diagrama Estrutural da Base

```
base.csv (61.018 registros lógicos)
│
├── Identificação do Lançamento
│   ├── lancamento        (ID único)
│   ├── cab_pagrec_id     (ID do documento de origem)
│   └── documento         (número do doc. fiscal)
│
├── Classificação Financeira
│   ├── codcen / descen   (Centro de Custo hierárquico)
│   └── codcdc / descdc   (Categoria da movimentação)
│
├── Valores
│   ├── valor_bruto       (sempre positivo)
│   ├── valor_plano       (negativo=despesa, positivo=receita)
│   ├── valor_centro      (rateio ao centro de custo)
│   └── iterea_valpago    (valor efetivamente pago)
│
├── Datas
│   ├── ite_pagrec_vencimento  (data de vencimento)
│   └── iterea_pagamento       (data de pagamento ou "NAO PAGO")
│
├── Contraparte
│   ├── codigo_pessoa     (código do fornecedor/cliente)
│   └── nome              (nome do fornecedor/cliente)
│
└── Localização
    ├── filial            (unidade operacional)
    └── observacao / nota (texto livre)
```

---

*Relatório gerado em 26/03/2026. `base.csv` foi atualizada em 27/03/2026 — execute `analise_base.ipynb` para recalcular as estatísticas. Novos arquivos disponíveis: `SYG_MOV COMPRAS.csv` e `SYG_MOV VENDAS.csv`.*
