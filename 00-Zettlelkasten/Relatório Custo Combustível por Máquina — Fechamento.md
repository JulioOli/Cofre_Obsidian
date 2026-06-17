---
tags:
  - note
  - controladoria
  - fechamento
  - maquinas
  - combustivel
  - G3S
atualizado: 12/06/2026
---
12/06/2026 - 15:30

### ~={Titulo}Relatório Custo Combustível por Máquina — Fechamento=~

> Arquivo: `02-Referencias/Custos-Maquinas/relatorio_custoComb_mes_fechamento.xlsx`
> Consolidação **jan–mai/2026** do custo de **diesel interno (7.1.22)** por ativo (placa ou código de máquina), no **layout de fechamento SAGI** (`FECHAMENTO_ODBC`), pronta para integração ao fechamento geral.

---

#### ~={Titulo}Origem e geração=~

| Etapa | Arquivo / ferramenta |
|---|---|
| **Entrada bruta** | `02-Referencias/Custos-Maquinas/relatorio_custoComb_mes (arquivo do gui).xlsx` |
| **Estrutura da entrada** | Uma aba por competência (`Janeiro 2026` … `Maio 2026`), colunas `n4_CC` + `VALOR` |
| **Conversão** | `04-Notebooks/Utitlities/base_r_para_fechamento_folha.py` com `--all-sheets` e título `COMB_MM_AAAA` |
| **Cadastro CC** | `02-Referencias/SAGI/sagi_rel_centro_custo.csv` (hierarquia n1–n4) |

A observação padrão gerada é ~={cyan}«Custo combustível MM/AAAA por máquina»=~; credor fixo ==ABASTECIMENTO INTERNO==; origem ==Saída (Aplicações)==.

---

#### ~={Titulo}Estrutura do arquivo=~

- **Aba:** `Fechamento`
- **Linhas:** 186 (39 + 38 + 35 + 36 + 38 por mês)
- **Colunas:** 31 — mesmo gabarito do fechamento (id, Segmento, n1–n4, conta, filial, valores, datas, metadados)
- **Conta única:** `7.1.22` — COMBUSTÍVEL - DIESEL (INTERNO) ([[Tipos de Movimentação]])
- **Ativos distintos (n4):** 70 códigos analíticos no período
- **Valores:** `valor_nf`, `valor_pago` e `valor_conta` **negativos** (despesa); `Valor Oficial` espelha `valor_conta`

#### ~={Titulo}Regras de data=~

| Campo | Regra |
|---|---|
| `data_nf` | Último dia do mês de competência (31/01, 28/02, 31/03, 30/04, 31/05/2026) |
| `data_pagamento` | Dia **08** do mês seguinte (padrão do script de fechamento) |
| `titulo` | `COMB_01_2026` … `COMB_05_2026` |

---

#### ~={Titulo}Totais por competência=~

| Mês | Linhas | Total `valor_conta` |
|---|---|---|
| 2026-01 | 39 | −R$ 211.806,59 |
| 2026-02 | 38 | −R$ 239.510,75 |
| 2026-03 | 35 | −R$ 253.898,74 |
| 2026-04 | 36 | −R$ 263.259,65 |
| 2026-05 | 38 | −R$ 218.940,12 |
| **Acumulado** | **186** | **−R$ 1.187.415,85** |

Tendência: custo mensal subiu de jan a ab (**pico em abril**), com leve queda em maio.

---

#### ~={Titulo}Corte por segmento (acum. jan–mai)=~

| Segmento | n1 CC | Linhas | Total |
|---|---|---|---|
| **SELETIVA** | 1.2 | 108 | −R$ 728.938,53 |
| **EKIPA SERVIÇOS - G&S** | 1.7 | 65 | −R$ 404.212,94 |
| **BRACOFER** | 1.3 | 11 | −R$ 42.057,80 |
| **EKIPA LOCAÇÕES RSE** | 1.6 | 2 | −R$ 12.206,58 |

~={yellow}A Seletiva concentra ~61% do diesel interno do período.=~ A G&S aparece sob contratos (`1.7.x`) — alinhado à frota locada descrita em [[Entre Empresas - Faturamento de Máquinas Intercompany]].

---

#### ~={Titulo}Corte por filial (acum.)=~

| Filial | Linhas | Total |
|---|---|---|
| G&S PRUDENTE | 59 | −R$ 360.178,66 |
| G3S PRUDENTE | 31 | −R$ 194.135,47 |
| G3S MARINGA | 31 | −R$ 192.498,03 |
| G3S DOURADOS | 20 | −R$ 157.821,77 |
| G3S CAMPO GRANDE | 14 | −R$ 115.703,01 |
| G3S LONDRINA | 12 | −R$ 68.780,25 |
| G&S BARUERI | 6 | −R$ 44.034,28 |
| BRACOFER | 11 | −R$ 42.057,80 |
| RSE | 2 | −R$ 12.206,58 |

**Maiores consumidores individuais (jan–mai):** PHH0062 (G&S Prudente, −R$ 64k), BZG6A91 e SUY4F83 (G3S Prudente), BKW9I57 e TKI2E74 (G3S Dourados).

---

#### ~={Titulo}Observações para uso no fechamento=~

1. Cada linha é **uma despesa analítica por ativo** — CC nível 5 (placa ou código de máquina), conforme [[Filiais (nível 2)]] e [[Departamentos (nível 3)]].
2. Não há `cod_credor_forn_cli_func` preenchido; o credor textual é genérico (abastecimento interno).
3. Arquivo **complementar** ao `relatorio_custoComb_placas_jan-mar_fechamento.xlsx` (corte por placas em outro recorte temporal).
4. Cruza naturalmente com análises de frota ([[qtd de máquinas por filial]], comparativo Liebherr/Hyundai) pela conta **7.1.22**.

___

[[Tipos de Movimentação]] · [[Divisões (nível 1)]] · [[Filiais (nível 2)]] · [[Scripts utilitários — folha R e CC]] · [[Premissas - Fechamento]] · [[Entre Empresas - Faturamento de Máquinas Intercompany]] · [[qtd de máquinas por filial]] · [[Analise Base Financeira]]
