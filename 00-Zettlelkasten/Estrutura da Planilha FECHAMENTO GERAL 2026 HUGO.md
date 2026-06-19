---
tags:
  - note
  - controladoria
  - fechamento
  - excel
  - dre
atualizado: 19/06/2026
---
19/06/26 - 09:30

### ~={Titulo}O que é=~

Nota de análise estrutural da planilha **`FECHAMENTO GERAL 2026 (HUGO).xlsx`**, localizada em:

```text
02-Referencias/Fechamento/FECHAMENTO GERAL 2026 (HUGO).xlsx
```

A planilha funciona como um ~={orange}modelo gerencial de fechamento=~: ela recebe lançamentos analíticos na aba `Base`, classifica cada conta por um `De-Para` de DRE/custeio e, a partir disso, monta visões de resultado por mês, unidade, centro de custo, custeio por absorção, custeio variável, qualidade de classificação, custo de máquinas e rateio manual de salários.

> ~={red}Ponto crítico:=~ a planilha mistura **base transacional**, **fórmulas**, **tabelas dinâmicas** e **classificações manuais**. Por isso, ao atualizar dados, não basta colar novas linhas: é necessário conferir fórmulas, atualizar intervalos de pivôs e validar o `De-Para`.

___

### ~={Titulo}Resumo técnico do arquivo=~

| Item | Leitura encontrada |
|---|---|
| Arquivo | `FECHAMENTO GERAL 2026 (HUGO).xlsx` |
| Tamanho aproximado | 8,66 MB |
| Quantidade de abas | 12 |
| Aba principal | `Base` |
| Linhas na `Base` | 18.264 linhas de dados + cabeçalho |
| Colunas na `Base` | 35 colunas (`A:AI`) |
| Fórmulas na `Base` | 64.211 fórmulas |
| Tabelas dinâmicas detectadas | 8 |
| Valor consolidado usado nas visões | `Valor Oficial` |

A lógica central é:

```text
Base transacional
  -> fórmulas de classificação via De-Para
  -> campos gerenciais: DE-PARA1, CUSTEIO ABSORÇÃO, CUSTEIO VARIÁVEL, VG_BCBI+
  -> tabelas dinâmicas por DRE, mês, unidade, centro de custo e conta
  -> indicadores manuais no topo de algumas abas
```

___

### ~={Titulo}Fluxo lógico da planilha=~

#### ~={blue}1) A `Base` concentra os lançamentos=~

A `Base` é a camada transacional. Cada linha representa um lançamento ou uma fatia rateada de um lançamento, contendo:

| Bloco | Colunas principais | Função |
|---|---|---|
| Hierarquia de centro de custo | `n1_cod_centro_custo`, `n1_CC`, `n2_CC`, `n3_CC`, `n4_CC` | Identifica divisão, filial/unidade, departamento e nível analítico |
| Plano de contas | `cod_conta`, `conta`, `cod_conta-descr` | Identifica a conta do SAGI/fechamento |
| Documento | `filial`, `titulo`, `observacao`, `credor_forn_cli_func` | Dá rastreabilidade operacional ao lançamento |
| Valores | `valor_nf`, `valor_pago`, `valor_conta`, `Valor Oficial` | Separa valor de documento, pagamento, rateio por conta/CC e valor consolidado |
| Datas | `data_nf`, `data_pagamento` | Alimenta filtros e agrupamentos mensais |
| Classificações gerenciais | `DE-PARA1`, `CUSTEIO ABSORÇÃO`, `CUSTEIO VARIÁVEL`, `VG_BCBI+` | Converte conta contábil em estrutura gerencial |

O campo mais importante para as visões é ~={cyan}`Valor Oficial`=~. As tabelas dinâmicas somam esse campo para produzir DRE, custeio e análises por unidade.

#### ~={blue}2) O `De-Para` traduz contas em categorias gerenciais=~

A aba `De-Para` é a tabela de classificação das contas. Ela recebe `cod_conta-descr` e devolve as classificações usadas na DRE:

| Coluna | Papel |
|---|---|
| `cod_conta-descr` | Chave textual usada na procura |
| `N1` | Agrupamento alto, como `RECEITAS`, `CUSTOS FIXOS`, `DESPESAS VARIÁVEIS` |
| `N2` | Subgrupo gerencial |
| `DE-PARA1` | Linha detalhada da DRE gerencial |
| `CUSTEIO ABSORÇÃO` | Grupo usado no custeio por absorção |
| `CUSTEIO VARIÁVEL` | Grupo usado no custeio variável |
| `VG_BCBI+` | Macrogrupo da visão BCBI+, como `01. VENDAS`, `02. GASTO FIXO`, `03. GASTO VARIÁVEL` |

Na `Base`, as fórmulas principais são `VLOOKUP`/`PROCV` com `IFERROR`:

```text
DE-PARA1           = IFERROR(VLOOKUP(cod_conta-descr, 'De-Para'!A:G, 4, FALSE), "-")
CUSTEIO ABSORÇÃO  = IFERROR(VLOOKUP(cod_conta-descr, 'De-Para'!A:G, 5, FALSE), "-")
CUSTEIO VARIÁVEL  = VLOOKUP(DE-PARA1, 'De-Para'!D:G, 3, FALSE)
VG_BCBI+           = IFERROR(VLOOKUP(cod_conta-descr, 'De-Para'!A:G, 7, FALSE), "-")
```

> ~={yellow}Interpretação:=~ a planilha não classifica a DRE diretamente pelo código da conta isolado; ela usa a chave `cod_conta-descr`. Se a descrição mudar, o `De-Para` pode falhar mesmo que o código continue parecido.

#### ~={blue}3) As abas de relatório usam pivôs e fórmulas=~

As abas analíticas são majoritariamente tabelas dinâmicas sobre a `Base`. Algumas têm também blocos de fórmulas no topo para calcular indicadores como receita líquida, lucro bruto, EBITDA, EBIT e lucro líquido.

O padrão recorrente das tabelas dinâmicas é:

```text
Filtros: divisão/unidade/centro de custo/mês
Linhas: classificação gerencial ou centro de custo
Colunas: mês, unidade ou data
Valores: Soma de Valor Oficial
```

___

### ~={Titulo}Análise de cada aba=~

#### ~={blue}1. Base=~

| Aspecto | Detalhe |
|---|---|
| Dimensão | 18.265 linhas x 35 colunas |
| Função | Base analítica dos lançamentos do fechamento |
| Filtro ativo | `A1:AI11171` |
| Fórmulas | 64.211 fórmulas, principalmente em `AF:AI` |
| Dependência | `De-Para` |

Cabeçalho encontrado:

```text
id, sdssds, n1_cod_centro_custo, n1_centro_custo, n1_CC,
n2_cod_centro_custo, n2_centro_custo, n2_CC,
n3_cod_centro_custo, n3_centro_custo, n3_CC,
n4_cod_centro_custo, n4_centro_custo, n4_CC,
cod_conta, conta, cod_conta-descr, filial, titulo,
valor_nf, valor_pago, valor_conta, observacao,
data_nf, data_pagamento, cod_credor_forn_cli_func,
credor_forn_cli_func, Origem, Sistema, Dados auxiliares,
Valor Oficial, DE-PARA1, CUSTEIO ABSORÇÃO, CUSTEIO VARIÁVEL, VG_BCBI+
```

A `Base` já contém hierarquia de centro de custo aberta em níveis. Isso evita que as visões precisem quebrar o código do CC em tempo de relatório.

Totais lidos por `data_nf`:

| Mês | Linhas | `valor_nf` | `valor_pago` | `valor_conta` | `Valor Oficial` |
|---|---:|---:|---:|---:|---:|
| 2026-01 | 3.096 | 27.905.784,78 | -3.265.964,41 | -3.265.964,41 | -3.265.964,41 |
| 2026-02 | 2.889 | 29.609.258,13 | 2.584.511,05 | 2.584.511,05 | 2.584.511,05 |
| 2026-03 | 3.859 | 62.113.643,26 | 12.672.684,33 | 1.258.237,35 | 1.019.273,32 |
| 2026-04 | 558 | 12.168.623,04 | 4.789.506,32 | 4.787.499,32 | -6.071.245,42 |
| 2026-05 | 7.862 | 71.322.067,63 | -34.824.704,17 | 11.079.002,62 | 11.079.002,62 |

~={red}Atenção:=~ em março e abril, `valor_conta` e `Valor Oficial` não coincidem. Isso indica que `Valor Oficial` pode ter recebido ajuste/manualização ou vir de uma regra diferente em parte da base. Essa diferença deve ser validada antes de usar a planilha como fonte final.

Outro ponto importante: há variação textual em `Origem`:

| Origem | Linhas | Soma de `Valor Oficial` |
|---|---:|---:|
| `Entradas (Origem)` | 2.010 | 47.308.289,25 |
| `Entrada (Origem)` | 1.586 | 30.172.909,61 |
| `Saídas (Aplicações)` | 9.347 | -53.335.133,50 |
| `Saida (Aplicacoes)` | 5.321 | -18.800.488,21 |

Essa duplicidade com e sem acento/parêntese padronizado pode atrapalhar filtros, pivôs e comparações automatizadas.

#### ~={blue}2. De-Para=~

| Aspecto | Detalhe |
|---|---|
| Dimensão | 184 linhas x 7 colunas |
| Função | Mapa de classificação das contas |
| Fórmulas | Não há fórmulas |
| Filtro ativo | `A1:G184` |

É a principal tabela de parametrização. Exemplos de mapeamento:

| `cod_conta-descr` | `DE-PARA1` | `CUSTEIO ABSORÇÃO` | `CUSTEIO VARIÁVEL` | `VG_BCBI+` |
|---|---|---|---|---|
| `4.1.1 VENDAS DE SUCATAS` | `3.01.01 RECEITA COM VENDA DE SUCATAS` | `3.01 RECEITA OPERACIONAL BRUTA` | `3.01 RECEITA OPERACIONAL` | `01. VENDAS` |
| `5.4.3 PESAGENS AVULSAS` | `3.01.02 RECEITA COM PESAGENS AVULSAS` | `3.01 RECEITA OPERACIONAL BRUTA` | `3.01 RECEITA OPERACIONAL` | `01. VENDAS` |
| `7.3.1 SALÁRIOS` | classificação de mão de obra/custo ou despesa conforme regra do mapa | alimenta custeio e visão BCBI+ | alimenta variável/fixo | alimenta macrogrupo |

> ~={yellow}Regra de manutenção:=~ todo novo `cod_conta-descr` que aparecer na `Base` precisa existir aqui. Caso contrário, a `Base` retorna `-` e o lançamento pode sumir ou cair em agrupamento genérico nas visões.

#### ~={blue}3. Modelo DRE=~

| Aspecto | Detalhe |
|---|---|
| Dimensão | 186 linhas x 3 colunas |
| Função | Estrutura textual de DRE/modelo contábil |
| Fórmulas | 12 fórmulas simples, muitas apenas `=` |
| Papel prático | Referência de plano de DRE, não parece ser a aba que calcula o resultado final |

Essa aba é um esqueleto de DRE com códigos e descrições como:

```text
3.1 Receita Operacional Bruta
3.2 Receita Não-Operacional Bruta
4.1 Custo das Vendas e Serviços Prestados
```

Ela serve mais como referência estrutural do que como relatório operacional. As visões efetivamente usadas estão nas abas `V1`, `V2`, `V3` e nos pivôs.

#### ~={blue}4. V1 - (H) Custeio Absorção=~

| Aspecto | Detalhe |
|---|---|
| Dimensão | 121 linhas x 8 colunas |
| Função | DRE mensal por custeio por absorção |
| Pivô | `B14:H30` |
| Valor | Soma de `Valor Oficial` |
| Linhas do pivô | `CUSTEIO ABSORÇÃO` > `DE-PARA1` |
| Colunas do pivô | `Meses (data_nf)` |
| Filtros | `sdssds`, `n1_CC`, `n2_CC` |
| Fórmulas | 35 fórmulas de indicadores |

A parte superior calcula indicadores:

```text
1 - RECEITA LÍQUIDA (3.01 + 3.02 - 3.03)
2 - LUCRO BRUTO (1 - 4.01 - 4.02 - 4.03)
3 - EBITDA (2 - 4.04 - 4.05 - 4.06 - 4.07 - 4.08)
4 - EBIT
5 - LUCRO ANTES IR/CSLL
LUCRO LÍQUIDO DO EXERCÍCIO
```

As fórmulas referenciam linhas fixas da própria aba, por exemplo:

```text
Receita líquida = linhas 16 + 17 + 18
Lucro bruto = receita líquida + grupos 4.01 + 4.02 + 4.03
EBITDA = lucro bruto + despesas 4.04 a 4.08
```

~={red}Risco:=~ se a estrutura do pivô mudar de linha, as fórmulas do topo podem apontar para a linha errada.

#### ~={blue}5. V2 - (H) Custeio Variável=~

| Aspecto | Detalhe |
|---|---|
| Dimensão | 73 linhas x 42 colunas |
| Função | Indicadores por tonelada e DRE no critério variável |
| Pivô | `B27:F42` |
| Valor | Soma de `Valor Oficial` |
| Linhas do pivô | `CUSTEIO VARIÁVEL` > `CUSTEIO ABSORÇÃO` > `DE-PARA1` |
| Colunas do pivô | `Meses (data_nf)` > `Dias (data_nf)` > `data_nf` |
| Filtros | `sdssds`, `n1_CC`, `n2_CC` |
| Fórmulas | 210 fórmulas |

A aba começa com indicadores operacionais em tonelada:

```text
TONELADA PROCESSADA
CUSTO TOTAL / TONELADA
CUSTO FIXO / TONELADA
CUSTO VARIÁVEL / TONELADA
DESPESA TOTAL / TONELADA
DESPESA FIXA / TONELADA
```

As toneladas de janeiro e fevereiro aparecem digitadas/construídas por fórmula simples:

```text
jan = 6794,4693 * 1000
fev = 7529,083601 * 1000
```

Os custos por tonelada dividem grupos do pivô pela tonelada processada:

```text
CUSTO TOTAL / TONELADA = -(CUSTO FIXO + CUSTO VARIÁVEL) / TONELADA
CUSTO FIXO / TONELADA = -CUSTO FIXO / TONELADA
CUSTO VARIÁVEL / TONELADA = -CUSTO VARIÁVEL / TONELADA
```

~={red}Risco:=~ meses sem tonelada alimentada geram `#DIV/0!`. Para usar essa aba em meses futuros, é necessário inserir a tonelada processada antes de interpretar os indicadores unitários.

#### ~={blue}6. V3 - Visão Gerencial=~

| Aspecto | Detalhe |
|---|---|
| Dimensão | 6.193 linhas x 165 colunas |
| Função | Visão gerencial ampla por divisão/unidade |
| Pivô | `B13:O29` |
| Valor | Soma de `Valor Oficial` |
| Linhas do pivô | `CUSTEIO ABSORÇÃO` > `DE-PARA1` > `credor_forn_cli_func` > `titulo` > `observacao` |
| Colunas do pivô | `sdssds` |
| Filtros | `Meses (data_nf)`, `n1_CC` |
| Fórmulas | 24 fórmulas de indicadores |

Essa aba é a visão mais gerencial/consolidada. Ela abre o resultado por macrodivisão, como:

```text
BRACOFER
EKIPA CONTEINER
EKIPA LOCACOES E SERV G&S
EKIPA LOCACOES RSE
FAMILIAR
PILARES
SELETIVA
TRANSMOVE GSL
TOTAL
```

A parte de cima calcula indicadores semelhantes ao `V1`, mas por colunas de unidade:

```text
Receita líquida = 3.01 + 3.02 - 3.03
Lucro bruto = receita líquida + 4.01 + 4.02 + 4.03
EBITDA = lucro bruto + 4.04 + 4.05 + 4.06 + 4.07 + 4.08
Lucro antes IR/CSLL = EBIT + 4.09 + 4.10
```

Como o pivô desce até fornecedor, título e observação, essa aba também serve para rastrear quais documentos compõem um grupo gerencial.

#### ~={blue}7. (H) Custeio BCBI+=~

| Aspecto | Detalhe |
|---|---|
| Dimensão | 174 linhas x 42 colunas |
| Função | Resultado no agrupamento `VG_BCBI+` |
| Pivô | `B5:F40` |
| Valor | Soma de `Valor Oficial` |
| Linhas do pivô | `VG_BCBI+` > `CUSTEIO ABSORÇÃO` > `DE-PARA1` > `n2_CC` |
| Colunas do pivô | `Meses (data_nf)` > `Dias (data_nf)` > `data_nf` |
| Filtros | `sdssds`, `n1_CC` |
| Fórmulas | Não há fórmulas fora do pivô |

Essa aba organiza a DRE no padrão mais sintético do BCBI+:

```text
01. VENDAS
02. GASTO FIXO
03. GASTO VARIÁVEL
04. GANHOS/PERDAS FINANCEIRAS
```

Contagem dos principais grupos encontrados na `Base`:

| `VG_BCBI+` | Linhas |
|---|---:|
| vazio / `None` | 7.180 |
| `03. GASTO VARIÁVEL` | 5.798 |
| `02. GASTO FIXO` | 2.787 |
| `01. VENDAS` | 2.122 |
| `04. GANHOS/PERDAS FINANCEIRAS` | 286 |
| `-` | 91 |

~={red}Atenção:=~ a quantidade alta de linhas sem `VG_BCBI+` indica que parte da `Base` pode estar sem classificação para essa visão ou que há linhas além do intervalo de fórmula/cache atualizado.

#### ~={blue}8. (H) K Unidade 1=~

| Aspecto | Detalhe |
|---|---|
| Dimensão | 350 linhas x 179 colunas |
| Função | Visão por unidade/filial em nível mais sintético |
| Pivô | `B7:K21` |
| Valor | Soma de `Valor Oficial` |
| Linhas do pivô | `DE-PARA2` > `DE-PARA1` > `n3_centro_custo` |
| Colunas do pivô | `n2_CC` > `Meses (data_nf)` > `Dias (data_nf)` > `data_nf` |
| Filtros | `sdssds`, `n1_CC`, `filial`, `CUSTEIO VARIÁVEL` |

Essa aba compara unidades da Seletiva por centro de custo de nível 2, por exemplo:

```text
1.2.1 CORPORATIVO SUCATA
1.2.2 DOURADOS
1.2.3 LONDRINA
1.2.4 MARINGA DISTRITO
1.2.5 PRESIDENTE PRUDENTE
1.2.6 ASSIS
1.2.7 CAMPO GRANDE
1.2.8 MARINGA CIDADE ALTA
```

O nome `DE-PARA2` aparece no cache do pivô, mas a `Base` atual tem as colunas `DE-PARA1`, `CUSTEIO ABSORÇÃO`, `CUSTEIO VARIÁVEL` e `VG_BCBI+`. Isso sugere cache antigo ou renomeação histórica de campo.

#### ~={blue}9. (H) K Unidade 2=~

| Aspecto | Detalhe |
|---|---|
| Dimensão | 351 linhas x 179 colunas |
| Função | Visão por unidade em nível mais detalhado |
| Pivô | `B8:K82` |
| Valor | Soma de `Valor Oficial` |
| Linhas do pivô | `DE-PARA1` > `n3_centro_custo` |
| Colunas do pivô | `n2_CC` > `Meses (data_nf)` > `Dias (data_nf)` > `data_nf` |
| Filtros | `sdssds`, `n1_CC`, `filial`, `CUSTEIO VARIÁVEL`, `DE-PARA2` |

Enquanto a `K Unidade 1` resume por grandes agrupamentos, a `K Unidade 2` abre por linhas gerenciais mais detalhadas, como:

```text
4.06.02 DESPESA COM DESPESAS DE VIAGEM
4.04.02 DESPESA COM CONSULTORIA
4.01.07 CUSTO COM FRETES E CARRETOS
4.04.21 DESPESA COM SISTEMAS
4.08.10 DESPESA COM IPTU PÁTIO
```

É útil para comparar quais tipos de gasto aparecem por filial/unidade.

#### ~={blue}10. Analise Qualidade=~

| Aspecto | Detalhe |
|---|---|
| Dimensão | 41 linhas x 6 colunas |
| Função | Auditoria de qualidade por conta, CC e fornecedor |
| Pivô | `A6:F41` |
| Valor | Soma de `Valor Oficial` |
| Linhas do pivô | `conta` > `n3_CC` > `credor_forn_cli_func` |
| Colunas do pivô | `Meses (data_nf)` |
| Filtros | `sdssds`, `n1_CC`, `n2_CC` |

Essa aba parece desenhada para investigar padrões estranhos, especialmente despesas recorrentes por fornecedor e centro de custo. O exemplo visível na extração mostra abertura de `SEGURO DE VIDA` por CC e fornecedor, como `ICATU SEGUROS`.

Uso prático:

```text
Conta suspeita
  -> Centro de custo onde caiu
  -> Fornecedor responsável
  -> Meses em que apareceu
```

#### ~={blue}11. CUSTO MAQ=~

| Aspecto | Detalhe |
|---|---|
| Dimensão | 132 linhas x 5 colunas |
| Função | Resultado/custo por centro de custo de máquina/ativo |
| Pivô | `A3:E128` |
| Valor | Soma de `Valor Oficial` |
| Linhas do pivô | `n3_CC` > `n4_CC` > `DE-PARA1` > `observacao` |
| Colunas do pivô | `Meses (data_nf)` |
| Filtro | `n1_CC` |

Essa aba abre custo por centro de custo de máquina/ativo, permitindo enxergar:

```text
Centro de custo nível 3
  -> Centro de custo nível 4 / ativo
  -> Conta gerencial
  -> Observação/documento
```

Exemplo visível:

```text
1.2.1.8 PRENSA MOVEL
  1.2.1.8.1 GDU0275
    4.03.03 CUSTO COM MANUTENÇÃO DE VEÍCULOS/MÁQUINAS
    4.01.06 CUSTO COM PEÇAS DE MANUTENÇÃO
```

É uma aba importante para cruzar com [[Relatório Custo Combustível por Máquina — Fechamento]] e com as notas de [[Filiais (nível 2)]] e [[Departamentos (nível 3)]].

#### ~={blue}12. Rateio Salário=~

| Aspecto | Detalhe |
|---|---|
| Dimensão | 39 linhas x 29 colunas |
| Função | Tabela auxiliar/manual de rateio de salários |
| Fórmulas | Não há fórmulas detectadas |
| Pivôs | Não há pivôs detectados |
| Estrutura | Linhas com centros de custo comerciais e operacionais da Seletiva |

Essa aba não é relatório dinâmico; ela parece ser uma planilha auxiliar manual para montar ou documentar rateio de salários entre CCs. Aparecem nomes como:

```text
GISELE, BEATRIZ, GIOVANNA, MARCONDES, JONATAN E FERNANDO
MARIO
MAURICIO
THOMAZ
```

As linhas carregam campos equivalentes ao layout da `Base`:

```text
sdssds, n1_cod_centro_custo, n1_centro_custo, n1_CC,
n2_cod_centro_custo, n2_centro_custo, n2_CC,
n3_cod_centro_custo, n3_centro_custo, n3_CC,
n4_cod_centro_custo, n4_centro_custo, n4_CC,
cod_conta, conta, cod_conta-descr, filial
```

Interpretação provável: é uma área de apoio para redistribuir `7.3.1 SALÁRIOS` entre unidades/departamentos comerciais e operacionais.

___

### ~={Titulo}Dependências entre abas=~

| Aba | Depende de | Como depende |
|---|---|---|
| `Base` | `De-Para` | Fórmulas `VLOOKUP`/`IFERROR` em `AF:AI` |
| `De-Para` | Parametrização manual | Não depende de outras abas |
| `Modelo DRE` | Estrutura manual | Serve como referência textual |
| `V1 - (H) Custeio Absorção` | `Base` | Tabela dinâmica + fórmulas no topo |
| `V2 - (H) Custeio Variável` | `Base` + toneladas manuais | Tabela dinâmica + indicadores por tonelada |
| `V3 - Visão Gerencial` | `Base` | Tabela dinâmica + fórmulas no topo |
| `(H) Custeio BCBI+` | `Base` | Tabela dinâmica com `VG_BCBI+` |
| `(H) K Unidade 1` | `Base` | Tabela dinâmica por unidade/CC |
| `(H) K Unidade 2` | `Base` | Tabela dinâmica detalhada por unidade/CC |
| `Analise Qualidade` | `Base` | Tabela dinâmica de auditoria |
| `CUSTO MAQ` | `Base` | Tabela dinâmica por máquina/ativo |
| `Rateio Salário` | Manual | Tabela auxiliar sem fórmula/pivô |

___

### ~={Titulo}Campos mais importantes=~

#### ~={blue}`Valor Oficial`=~

É o valor que alimenta as tabelas dinâmicas. Todas as visões principais usam `Soma de Valor Oficial`.

Se esse campo estiver errado, todas as abas gerenciais ficam erradas, mesmo que `valor_nf` ou `valor_conta` estejam corretos.

#### ~={blue}`cod_conta-descr`=~

É a chave de classificação do `De-Para`. A qualidade desse campo determina se o lançamento recebe DRE correta.

#### ~={blue}`DE-PARA1`=~

É a linha gerencial detalhada, usada em DRE, unidade, custeio e custo de máquina.

#### ~={blue}`CUSTEIO ABSORÇÃO`=~

Agrupa contas no modelo de absorção, separando receita, custo da mercadoria, mão de obra, despesas administrativas, comerciais, financeiras e operacionais.

#### ~={blue}`CUSTEIO VARIÁVEL`=~

Agrupa contas pelo critério fixo/variável e é a base da aba `V2`.

#### ~={blue}`VG_BCBI+`=~

Cria o agrupamento sintético da visão BCBI+:

```text
01. VENDAS
02. GASTO FIXO
03. GASTO VARIÁVEL
04. GANHOS/PERDAS FINANCEIRAS
```

___

### ~={Titulo}Fragilidades encontradas=~

#### ~={red}1. Intervalos de pivô menores que a `Base` atual=~

A `Base` tem 18.264 linhas de dados, mas os caches de algumas tabelas dinâmicas apontam para intervalos menores:

| Cache / uso | Intervalo fonte |
|---|---|
| Alguns pivôs de `V2`, `V3`, `(H) Custeio BCBI+` | `Base!A1:AI10047` |
| Pivô de `V1` | `Base!A1:AI11172` |
| Pivôs de `(H) K Unidade 1` e `(H) K Unidade 2` | `Base!A1:AH3016` |
| Alguns pivôs | `Base!A1:AH1048576` ou `Base!A1:AI1048576` |

Impacto: se o pivô não estiver usando todas as linhas, o relatório pode ignorar lançamentos recentes.

Correção recomendada:

```text
1. Transformar a Base em Tabela do Excel.
2. Apontar todos os pivôs para a tabela, não para intervalos fixos.
3. Atualizar todos os pivôs após colar dados novos.
4. Conferir se as colunas chegam até AI, incluindo VG_BCBI+.
```

#### ~={red}2. Filtro da `Base` cobre só até a linha 11171=~

O autofiltro da `Base` está em:

```text
A1:AI11171
```

Mas a aba tem 18.265 linhas. Isso significa que há linhas fora do filtro visual.

Impacto: ao filtrar manualmente, o usuário pode achar que está vendo a base inteira, mas parte dos lançamentos pode ficar fora do filtro.

#### ~={red}3. Campos antigos nos caches dos pivôs=~

Alguns caches usam o nome `DE-PARA2`, mas a `Base` atual usa `CUSTEIO ABSORÇÃO` e `CUSTEIO VARIÁVEL` nas colunas finais. Isso indica histórico de renomeação ou cache não totalmente reconstruído.

Impacto: pivôs podem continuar funcionando pelo cache antigo, mas ficam frágeis quando a fonte é atualizada.

#### ~={yellow}4. `Origem` não está padronizada=~

Foram encontradas quatro grafias:

```text
Entrada (Origem)
Entradas (Origem)
Saida (Aplicacoes)
Saídas (Aplicações)
```

Impacto: filtros por entrada/saída podem duplicar categorias e quebrar comparações.

#### ~={yellow}5. Muitos registros sem `VG_BCBI+`=~

Foram encontradas 7.180 linhas com `VG_BCBI+` vazio/`None` e 91 linhas com `-`.

Impacto: a aba `(H) Custeio BCBI+` pode subrepresentar parte dos lançamentos ou agrupá-los fora das categorias esperadas.

#### ~={yellow}6. Fórmulas de indicadores dependem de linhas fixas=~

As abas `V1`, `V2` e `V3` calculam indicadores por fórmulas que apontam para linhas fixas do relatório.

Impacto: ao expandir, recolher ou alterar a estrutura do pivô, os indicadores podem continuar apontando para linhas antigas.

___

### ~={Titulo}Checklist para atualizar a planilha com segurança=~

1. Colar ou importar a nova base mantendo exatamente as colunas `A:AI`.
2. Garantir que as fórmulas de `AF:AI` foram copiadas até a última linha da `Base`.
3. Conferir se todo `cod_conta-descr` da `Base` existe no `De-Para`.
4. Padronizar `Origem` para apenas duas categorias: `Entrada (Origem)` e `Saida (Aplicacoes)` ou o padrão escolhido.
5. Atualizar o autofiltro da `Base` para cobrir todas as linhas.
6. Atualizar a origem de todos os pivôs para cobrir `A:AI` até a última linha ou, melhor, usar uma Tabela do Excel.
7. Dar `Atualizar Tudo` nas tabelas dinâmicas.
8. Validar se `V1`, `V2`, `V3`, `(H) Custeio BCBI+`, `K Unidade`, `Analise Qualidade` e `CUSTO MAQ` batem com a soma de `Valor Oficial` da `Base`.
9. Conferir manualmente indicadores por tonelada na `V2`, porque dependem de tonelagem alimentada.
10. Validar diferenças entre `valor_conta` e `Valor Oficial`, especialmente nos meses em que os totais divergem.

___

### ~={Titulo}Relação com o fluxo ODBC=~

Essa planilha parece ser o modelo legado/gerencial que inspirou o layout de fechamento usado nos notebooks atuais. Ela se conecta conceitualmente com:

- [[Notebook Conversao ODBC para Fechamento - Como Usar]]
- [[Valores ODBC e Fechamento — Mapeamento de Colunas]]
- [[Analise Base Financeira]]
- [[Premissas - Fechamento]]

No fluxo novo, a tendência é gerar uma `Base` mais padronizada via notebook e reduzir dependência de ajustes manuais de Excel. Mesmo assim, a lógica de classificação do `De-Para` continua sendo essencial: ela é o coração da conversão entre conta operacional e DRE gerencial.

___

### ~={Titulo}Resumo executivo=~

A planilha tem quatro camadas:

```text
1. Dados: Base
2. Parametrização: De-Para
3. Modelo conceitual: Modelo DRE
4. Relatórios: V1, V2, V3, BCBI+, K Unidade, Analise Qualidade, CUSTO MAQ
```

O ponto mais sensível é garantir que ~={cyan}`Valor Oficial`=~ e as classificações `DE-PARA1`, `CUSTEIO ABSORÇÃO`, `CUSTEIO VARIÁVEL` e `VG_BCBI+` estejam preenchidas em todas as linhas. Depois disso, os pivôs precisam apontar para a base inteira.

> ~={red}Conclusão:=~ a planilha é útil como modelo gerencial, mas exige manutenção cuidadosa de intervalos, fórmulas e `De-Para`. Para uso recorrente, o ideal é transformar a `Base` em Tabela do Excel ou migrar a geração das visões para scripts/notebooks, deixando o Excel apenas como saída de conferência.

___

[[Notebook Conversao ODBC para Fechamento - Como Usar]] · [[Valores ODBC e Fechamento — Mapeamento de Colunas]] · [[Analise Base Financeira]] · [[Premissas - Fechamento]] · [[Tipos de Movimentação]] · [[Divisões (nível 1)]] ·[[Filiais (nível 2)]] · [[Departamentos (nível 3)]] · [[Relatório Custo Combustível por Máquina — Fechamento]]
