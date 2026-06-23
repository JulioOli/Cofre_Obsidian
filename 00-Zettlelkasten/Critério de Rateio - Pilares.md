---
tags:
  - note
  - controladoria
  - rateio
  - pilares
  - fechamento
atualizado: 22/06/2026
---
27/04/2026 - 10:20

![[../01-Anexos/Pasted image 20260427102141.png]]

### ~={Titulo}O que é o rateio Pilares=~

Despesas do escritório central (~={cyan}Pilares / `1.1` G3S ESCRITÓRIO=~) são redistribuídas para as unidades operacionais que se beneficiam da estrutura administrativa. No SAGI, a contrapartida do rateio usa a conta ==`7.5.36` RATEIO PILARES== (ver [[Tipos de Movimentação]]).

Fonte oficial dos percentuais e tabelas por fornecedor: `02-Referencias/analises rateios da pilares.xlsx` (aba `RATEIO PILARES` e abas auxiliares). Automação mensal: notebook `04-Notebooks/Fechamento/rateio_pilares_faturamento_head.ipynb`.

---

### ~={Titulo}Fórmula do critério (Faturamento × Head)=~

O critério combina **dois pesos com peso igual (50% + 50%)**:

```
%TOTAL = (0,5 × %Faturamento) + (0,5 × %Headcount)
```

| Componente | Origem no Excel | O que mede |
|---|---|---|
| **%Faturamento** | Aba `análsie Faturamento` — `Soma de Valor Oficial` por segmento (`Origem = Entrada`) | Participação de cada empresa no faturamento bruto do grupo |
| **%Head** | Aba `análise H` — contagem de funcionários na aba `dados HEAD` (exclui lotação `PILARES`) | Participação de cada empresa no quadro de colaboradores |

~={yellow}Importante:=~ funcionários com `EMPRESA = PILARES` em `dados HEAD` são a **origem** do custo rateado — não entram como destino do rateio.

**Base de faturamento** (período da planilha): R$ 97.488.545,25.

**Base de headcount**: 101 colaboradores (70 Seletiva · 18 Bracofer · 8 G&S · 4 Transmove · 1 Ekipa Contêiner).

---

### ~={Titulo}Percentuais por segmento (%TOTAL)=~

| Empresa | % Faturamento (bruto) | 0,5 × FAT | % Head (bruto) | 0,5 × HEAD | **% TOTAL** |
|---|---:|---:|---:|---:|---:|
| **SELETIVA** | 74,59% | 37,30% | 69,31% | 34,65% | **71,95%** |
| **BRACOFER** | 12,49% | 6,24% | 17,82% | 8,91% | **15,15%** |
| **TRANSMOVE GSL** | 9,27% | 4,63% | 3,96% | 1,98% | **6,61%** |
| **EKIPA LOCAÇÕES E SERV G&S** | 3,09% | 1,55% | 7,92% | 3,96% | **5,51%** |
| **EKIPA CONTEINER** | 0,56% | 0,28% | 0,99% | 0,50% | **0,78%** |
| **Total** | 100% | 50% | 100% | 50% | **100%** |

> A nota anterior trazia apenas quatro segmentos e percentuais arredondados (16% / 1% / 72% / 7%), sem **G&S** e sem detalhar a fórmula.

---

#### ~={Titulo}Desdobramento da Seletiva=~

O total Seletiva (**71,95%**) **não** vai para um único CC. Na aba `RATEIO PILARES`, a planilha desconsidera o agregado e rateia em **partes iguais** entre cinco filiais:

| Filial Seletiva | % do total rateado |
|---|---:|
| Dourados | 14,39% |
| Londrina | 14,39% |
| Maringá | 14,39% |
| Presidente Prudente | 14,39% |
| Campo Grande | 14,39% |

~={orange}⚠️=~ **Assis** e **Maringá Cidade Alta** não aparecem nesse desdobramento de cinco vias — mas entram nas tabelas de CC por fornecedor (abaixo) via `1.2.8.1` quando o rateio é por centro de custo administrativo.

---

### ~={Titulo}Aplicação no SAGI — CC e conta por fornecedor=~

Após calcular o % por segmento, cada nota é quebrada em linhas de **Centro de Custo analítico** + **conta do Plano de Contas**. O Excel traz tabelas prontas por credor (aba `IMPRIMIR` consolida as principais).

#### ~={Titulo}Padrão ADMINISTRATIVO (maioria dos fornecedores)=~

Usado por: RH (Expertise, RHGestor), Sem Parar, Smart Tax (consultoria), Publicidade, Kinghost, Consulti mensalidade, entre outros.

| Centro de Custo | Segmento destino | % para o CC |
|---|---|---:|
| `1.2.2.1` ADMINISTRATIVO | Seletiva — Dourados | 11,55% |
| `1.2.3.1` ADMINISTRATIVO | Seletiva — Londrina | 11,55% |
| `1.2.4.1` ADMINISTRATIVO | Seletiva — Maringá Distrito | 11,55% |
| `1.2.5.1` ADMINISTRATIVO | Seletiva — Presidente Prudente | 11,55% |
| `1.2.7.1` ADMINISTRATIVO | Seletiva — Campo Grande | 11,55% |
| `1.2.8.1` ADMINISTRATIVO | Seletiva — Maringá Cidade Alta | 11,55% |
| `1.3.1.1` ADMINISTRATIVO | Bracofer | 17,82% |
| `1.4.1.2` ADMINISTRATIVO | Transmove GSL | 3,96% |
| `1.5.1.1` ADMINISTRATIVO | Ekipa Contêiner | 0,99% |
| `1.7.2.1` ADMINISTRATIVO | Ekipa Locações e Serv. G&S | 7,92% |

Contas usadas conforme o fornecedor (exemplos):

| Fornecedor | Conta |
|---|---|
| RHGestor, AMTI, Consulti (mensalidade), BMC Active* | `7.5.18` SISTEMAS |
| Expertise GP, Smart Tax (mensalidade) | `7.5.9` CONSULTORIA |
| Sem Parar | `7.3.25` BENEFÍCIOS DIVERSOS |
| Divulgação Assessoria, Kinghost | `7.2.5` PUBLICIDADE E PROPAGANDA |

\* BMC Active usa departamento **LOGÍSTICA** em vez de Administrativo — ver aba `BMC-ACTIVE`.

#### ~={Titulo}Padrão LOGÍSTICA (BMC Active)=~

| Centro de Custo | % para o CC |
|---|---:|
| `1.2.2.4` · `1.2.3.4` · `1.2.4.4` · `1.2.5.4` · `1.2.7.4` · `1.2.8.4` LOGISTICA (Seletiva) | 13,70% cada |
| `1.3.1.4` LOGISTICA (Bracofer) | 13,76% |
| `1.5.1.4` LOGISTICA (Ekipa Contêiner) | 0,62% |
| `1.7.2.1` ADMINISTRATIVO (G&S) | 3,41% |

Conta: `7.5.18` SISTEMAS.

#### ~={Titulo}Padrão restrito Seletiva + Bracofer (AMTI, Smart Tax)=~

Sete CCs administrativos (`1.2.2.1` a `1.2.8.1` + `1.3.1.1`), ~14,28% cada — sem Transmove, Contêiner nem G&S.

#### ~={Titulo}Casos especiais=~

| Fornecedor | Tratamento |
|---|---|
| **MM Soares / Consulti — projetos** | Pedir extrato ao Marcelo (Consulti) e ratear conforme apontamentos por empresa |
| **Konfido** | Pedir relação usuários × máquina (PC) ao Consulti para ratear por unidade |
| **Smart Tax — mensalidade** | Na aba `IMPRIMIR`, a nota de mensalidade usa `7.5.9` CONSULTORIA; na aba `smart TAX`, o rateio padrão cai em `7.5.18` SISTEMAS — confirmar com a nota fiscal qual conta aplicar |

---

### ~={Titulo}Fluxo operacional no fechamento=~

1. Exportar lançamentos Pilares do período (`Pilares_{Mês}.CSV` em `02-Referencias/Meus_Dados/`).
2. Somar `Valor Oficial` das despesas a ratear.
3. Aplicar os **%TOTAL** por segmento (tabela acima).
4. Para Seletiva, subdividir em cinco filiais (14,39% cada) **ou** usar diretamente a tabela de CC do fornecedor.
5. Lançar no SAGI via **Troca em Lote** (CC + conta `7.5.36` na origem Pilares) — ver [[Guia Sistemas]].

~={cyan}Valor a ratear:=~ usar `valor_centro` / **Valor Oficial**, não `valor_plano` — ver [[Valores ODBC e Fechamento — Mapeamento de Colunas]].

---

___

[[fechamento]] · [[Tipos de Movimentação]] · [[Valores ODBC e Fechamento — Mapeamento de Colunas]] · [[Guia Sistemas]] · [[Estrutura Empresarial G3S]] · [[Divisões (nível 1)]]
