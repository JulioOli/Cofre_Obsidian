---
tags:
  - note
  - controladoria
  - bcbi
  - plano-de-contas
  - G3S
  - seletiva
---
25/05/2026 - 12:00

# ~={Titulo}BCBI — Classificação Analítico (Plano de Contas)=~

> Mapeamento das **contas do plano SAGI** por **tipo de custo/receita** conforme categorização do BCBI (seção **Analítico** em `custos.php`).
> Extraído automaticamente do painel em 25/05/2026.

**Relacionado:** [[Melhoria BCBI]] · [[Guia Sistemas]] · `02-Referencias/sagi_rel_plano_conta.csv` · `02-Referencias/Plano de Contas.pdf`

---

## ~={Titulo}Onde consultar no BCBI=~

| Item | Valor |
|------|-------|
| URL | `https://seletiva.bcbi.com.br/` → menu **Custos** (`custos.php`) |
| Seção | **ANALÍTICO** (tabela abaixo dos gráficos sintéticos) |
| Detalhe | Clicar no ícone de link em cada linha → modal com contas (`detalhaItem`) |
| Código interno BCBI | Ex.: `2.1.1`, `2.2.2`, `3.1.1` (aparece no título do modal) |

---

## ~={Titulo}Filtros da extração (25/05/2026)=~

| Filtro | Valor |
|--------|-------|
| Mês início / fim | **05/2026** |
| Projeto | **Com Projeto** |
| Unidades | FILIAL9 Assis, FILIAL1 Campo Grande, FILIAL20 Cidade Alta, FILIAL3 Dourados, FILIAL5 Londrina, FILIAL4 Maringá, MATRIZ Prudente |
| Centro de custo | Ramo **1.2 / 2.2 Seletiva** (filiais e departamentos analíticos selecionados) |

> ⚠️ Se alterar filtro de CC, unidade, mês ou “Com Projeto”, a lista de contas por categoria **pode mudar**. Revalidar no BCBI antes de usar em auditoria.

---

## ~={Titulo}Estrutura de categorias BCBI=~

```
CUSTOS
├── CUSTO FIXO (cód. BCBI 2.1.x)
│   ├── Custo administrativo (2.1.1)
│   ├── Salário (2.1.2)
│   ├── Tributos (2.1.3)
│   ├── Operacional (2.1.4)
│   └── Não operacional (2.1.5)
└── CUSTO VARIÁVEL (cód. BCBI 2.2.x)
    ├── Não operacional (2.2.1)
    ├── Operacional (2.2.2)
    ├── Tributos (2.2.3)
    └── Manutenção (2.2.4)

RECEITAS TOTAIS
├── Receitas (3.1.1)
├── Bônus (BONUS)
└── Devolução mês(es) anterior(es) (DEVOLUCAO_MES_ANTERIOR)
```

---

## ~={Titulo}Resumo quantitativo=~

| Tipo | Categoria BCBI | Cód. BCBI | Qtd. contas |
|------|----------------|-----------|-------------|
| Custo fixo | Custo administrativo | 2.1.1 | 9 |
| Custo fixo | Salário | 2.1.2 | 7 |
| Custo fixo | Tributos | 2.1.3 | 0 |
| Custo fixo | Operacional | 2.1.4 | 0 |
| Custo fixo | Não operacional | 2.1.5 | 1 |
| Custo variável | Não operacional | 2.2.1 | 25 |
| Custo variável | Operacional | 2.2.2 | 9 |
| Custo variável | Tributos | 2.2.3 | 5 |
| Custo variável | Manutenção | 2.2.4 | 2 |
| Receitas totais | Receitas | 3.1.1 | 5 |
| Receitas totais | Bônus | BONUS | 0 |
| Receitas totais | Devolução mês anterior | DEVOLUCAO_MES_ANTERIOR | 0 |

**Total:** 63 contas com detalhe listado no popup (categorias vazias = sem linha de conta no modal para o filtro usado).

> **Atenção:** Custo variável → Operacional (`2.2.2`) concentra valor alto na DRE mas exibe poucas contas no detalhe — pode haver agrupamento sintético no pivot DevExtreme sem expansão das filhas.

---

## ~={Titulo}Custo fixo — Custo administrativo (2.1.1)=~

| Código | Descrição |
|--------|-----------|
| 7.5.10 | SEGURANÇA E VIGILÂNCIA |
| 7.5.1 | ÁGUA E ESGOTO |
| 7.5.16 | ALARME E MONITORAMENTO |
| 7.5.20 | INTERNET |
| 7.5.3 | TELECOMUNICAÇÕES |
| 7.5.2 | ENERGIA ELÉTRICA |
| 7.5.28 | SERVIÇO DE LIMPEZA DO ESCRITÓRIO |
| 7.5.18 | SISTEMAS |
| 7.5.31 | ALUGUEL ADMINISTRATIVO |

---

## ~={Titulo}Custo fixo — Salário (2.1.2)=~

| Código | Descrição |
|--------|-----------|
| 7.3.1 | SALÁRIOS |
| 7.3.2 | FGTS |
| 7.3.3 | INSS |
| 7.3.15 | SEGURO DE VIDA |
| 7.3.21 | RESCISÕES |
| 7.3.22 | BOLSA ESTAGIO |
| 7.3.23 | HONORÁRIOS PJ |

---

## ~={Titulo}Custo fixo — Tributos (2.1.3)=~

*Nenhuma conta listada no detalhe BCBI para o filtro da extração.*

---

## ~={Titulo}Custo fixo — Operacional (2.1.4)=~

*Nenhuma conta listada no detalhe BCBI para o filtro da extração.*

---

## ~={Titulo}Custo fixo — Não operacional (2.1.5)=~

| Código | Descrição |
|--------|-----------|
| 7.11.7 | EMPRESTIMOS |

---

## ~={Titulo}Custo variável — Não operacional (2.2.1)=~

| Código | Descrição |
|--------|-----------|
| 7.1.8 | DESPESAS DE VIAGEM |
| 7.1.12 | PEDÁGIO |
| 7.1.16 | SERVIÇOS DE TERCEIROS |
| 7.1.21 | LOCAÇÃO DE VEÍCULOS |
| 7.2.6 | EVENTOS ENDOMARKETING |
| 7.3.4 | EXAMES MÉDICOS |
| 7.3.5 | ALIMENTAÇÃO DO TRABALHADOR |
| 7.3.8 | CESTA BÁSICA |
| 7.3.13 | SINDICATOS |
| 7.5.4 | MATERIAL DE LIMPEZA E HIGIENE |
| 7.5.5 | MATERIAL DE ESCRITÓRIO |
| 7.5.6 | MANUTENÇÕES E REPAROS - ESTRUTURA ADMINISTRATIVA |
| 7.5.8 | HONORÁRIOS ADVOCATÍCIOS |
| 7.5.9 | CONSULTORIA |
| 7.5.11 | CORREIOS |
| 7.5.21 | MATERIAL DE INFORMÁTICA |
| 7.5.22 | DESPESAS BANCARIAS |
| 7.5.23 | JUROS E MULTAS |
| 7.5.27 | MATERIAL DE COPA/COZINHA |
| 7.5.32 | TAXAS E LICENÇAS |
| 7.5.34 | MOVEIS E ELETRODOMESTICOS |
| 7.7.1 | SERVIÇOS CONTRATADOS |
| 7.7.2 | MATERIAL PARA REFORMA |
| 8.1.6 | ELETRÔNICOS |
| 9.2.3 | ENGENHEIROS E ARQUITETOS |

---

## ~={Titulo}Custo variável — Operacional (2.2.2)=~

| Código | Descrição |
|--------|-----------|
| 6.1.1 | COMPRAS DE SUCATAS |
| 6.2.2 | MATERIAIS - CORTE DE SUCATA |
| 6.6.1 | FRETE DE TERCEIROS |
| 6.6.6 | FRETE DE COLETA |
| 7.1.3 | LOCAÇÃO DE EQUIPAMENTOS E FERRAMENTAS |
| 7.1.6 | TRANSPORTE DE SUCATA |
| 7.1.22 | COMBUSTÍVEL - DIESEL (INTERNO) |
| 7.3.9 | SEGURANÇA DO TRABALHO |
| 7.6.3 | MANUTENÇÃO PATIO |

---

## ~={Titulo}Custo variável — Tributos (2.2.3)=~

| Código | Descrição |
|--------|-----------|
| 7.4.5 | ISS |
| 7.4.8 | IOF |
| 7.4.9 | DIFAL |
| 7.4.12 | ICMS |
| 7.5.17 | TAXAS |

---

## ~={Titulo}Custo variável — Manutenção (2.2.4)=~

| Código | Descrição |
|--------|-----------|
| 7.1.1 | PEÇAS DE MANUTENÇÃO |
| 7.1.2 | MANUTENÇÃO DE VEÍCULOS/MAQUINAS |

---

## ~={Titulo}Receitas totais — Receitas (3.1.1)=~

| Código | Descrição |
|--------|-----------|
| 4.1.1 | VENDAS DE SUCATAS |
| 5.3.3 | RENDIMENTO FINANCEIRO |
| 5.4.3 | PESAGENS AVULSAS |
| 5.4.8 | ESTORNO DE PAGAMENTO INDEVIDO |
| 5.4.13 | LOGISTICA REVERSA |

---

## ~={Titulo}Receitas totais — Bônus (BONUS)=~

*Sem contas no detalhe do modal para o filtro da extração.*

---

## ~={Titulo}Receitas totais — Devolução mês(es) anterior(es) (DEVOLUCAO_MES_ANTERIOR)=~

*Sem contas no detalhe do modal para o filtro da extração.*

---

## ~={Titulo}Uso na controladoria=~

- **Auditoria BCBI × SAGI:** conferir se lançamentos ODBC usam contas compatíveis com a classificação esperada no BI (`04-Notebooks/Auditorias/auditoria_bcbi.ipynb`).
- **Fechamento / normalização:** ao mapear despesas (ATUA, Supply), validar se a conta SAGI escolhida cai na categoria BCBI correta (ex.: despesas `7.5.x` → custo fixo administrativo).
- **Dúvida de classificação:** abrir o detalhe da categoria no Analítico e comparar com o `codcdc` do lançamento.

___
[[plano de conta]]