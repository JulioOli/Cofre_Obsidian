---
tags:
  - note
  - controladoria
  - bcbi
  - auditoria
  - G3S
  - seletiva
---
27/05/2026

# ~={Titulo}BCBI — Auditoria Analítico (jan–mai/2026)=~

> Inconsistências identificadas no **Analítico de Custos** do BCBI (Seletiva), extraídas ao vivo de `custos.php` com filtro **Com Projeto**, CC ramo **1.2 / 2.2**, período **01/2026 a 05/2026**.

**Relacionado:** [[BCBI - Classificação Analítico Plano de Contas]] · [[Melhoria BCBI]] · `04-Notebooks/Auditorias/auditoria_bcbi.ipynb`

---

## ~={Titulo}Filtros da auditoria=~

| Filtro | Valor |
|--------|-------|
| URL | `https://bcbi.com.br/seletiva/custos.php` |
| Mês início / fim | **01/2026** a **05/2026** |
| Projeto | **Com Projeto** |
| Unidades | Assis, Campo Grande, Cidade Alta, Dourados, Londrina, Maringá, Prudente |
| Centro de custo | Ramo **1.2 / 2.2 Seletiva** (filiais e departamentos analíticos selecionados) |
| Extração | 27/05/2026 — modais via clique no **nome** da linha (ex.: CUSTO ADMINISTRATIVO, SALÁRIO) |

> ⚠️ Dados de **maio/2026** podem estar parcialmente fechados (Sagi atualizado em 27/05/2026 14:05). Tratar alertas de maio como possível **fechamento incompleto**, não necessariamente erro de cadastro.

---

## ~={Titulo}Resumo executivo=~

| Categoria | Cód. | Total jan–mai | Observação principal |
|-----------|------|---------------|----------------------|
| Custo administrativo | 2.1.1 | −R$ 2.673.151,73 | Maio incompleto (−84% vs abr); migração Internet/Telecom |
| Salário | 2.1.2 | −R$ 2.031.762,05 | Pico em fev (+42% vs jan); abr = mai (valores idênticos) |
| Tributos (fixo) | 2.1.3 | Sem dados | Esperado (categoria vazia no cadastro) |
| Operacional (fixo) | 2.1.4 | Sem dados | Esperado |
| Não operacional (fixo) | 2.1.5 | −R$ 41.739,20 | Só mar e mai (empréstimos) |
| Não operacional (var.) | 2.2.1 | −R$ 1.305.725,03 | Alta variabilidade (normal p/ categoria) |
| Operacional (var.) | 2.2.2 | −R$ 41.889.422,37 | Mai +31% vs abr; compras de sucata |
| Tributos (var.) | 2.2.3 | −R$ 1.644.750,62 | ICMS dispara em abr |
| Manutenção | 2.2.4 | −R$ 629.921,75 | Abr/mai quase zerados (−96%) |
| Receitas | 3.1.1 | +R$ 60.349.387,82 | Crescimento consistente até mai |
| Bônus | BONUS | +R$ 281.916,43 | Só jan, fev e mai |
| Devolução mês anterior | DEVOLUCAO_MES_ANTERIOR | −R$ 215.697,48 | Jan, fev e abr |

### Totais sintéticos (Analítico)

| Linha | Jan | Fev | Mar | Abr | Mai | Total |
|-------|-----|-----|-----|-----|-----|-------|
| Custo fixo | −1.152.586 | −1.201.103 | −967.714 | −932.259 | −492.991 | −4.746.653 |
| Custo variável | −2.527.274 | −2.563.475 | −3.137.188 | −4.675.111 | −3.938.755 | −16.841.803 |
| Receitas totais | +9.654.238 | +9.882.632 | +10.643.912 | +13.131.080 | +17.043.624 | +60.355.487 |

---

## ~={Titulo}Prioridades de investigação=~

1. **Maio incompleto em 2.1.1** — rateios (7.5.35/7.5.36), honorários contábeis (7.5.7) e queda geral de 84% vs abril.
2. **Salários abr = mai** — ambos −R$ 386.494,65; verificar fechamento de maio ou duplicidade.
3. **Manutenção 2.2.4** — quase zero em abr/mai (−96% vs jan–mar).
4. **ICMS abr (2.2.3)** — pico isolado de −R$ 459.802 vs −R$ 77.273 em mai.
5. **Cadastro 2.1.1** — contas extras no modal vs [[BCBI - Classificação Analítico Plano de Contas|classificação]]; migração 7.5.20 + 7.5.3 → 7.5.3 “Internet e telefonia”.

---

## ~={Titulo}2.1.1 — Custo administrativo (fixo)=~

**Totais mensais:** jan −814.202 · fev −719.937 · mar −505.260 · abr −545.764 · **mai −87.988** · total −2.673.152

### Contas com buraco mensal

| Conta | Descrição | Jan | Fev | Mar | Abr | Mai | Problema |
|-------|-----------|:---:|:---:|:---:|:---:|:---:|----------|
| 7.5.10 | Segurança e vigilância | ✓ | ✓ | ✓ | ✓ | ✓ | OK |
| 7.5.1 | Água e esgoto | ✓ | ✓ | ✓ | ✓ | ✓ | OK |
| 7.5.16 | Alarme e monitoramento | ✓ | ✓ | ✓ | ✓ | ✓ | OK |
| 7.5.28 | Limpeza do escritório | ✓ | ✓ | ✓ | ✓ | ✓ | OK |
| 7.5.18 | Sistemas | ✓ | ✓ | ✓ | ✓ | ✓ | OK |
| 7.5.13 | Seguros | — | — | ✓ | — | ✓ | Falta jan/fev/abr |
| 7.5.7 | Honorários contábeis | ✓ | ✓ | ✓ | ✓ | — | **Falta mai** |
| 7.5.36 | Rateio Pilares | ✓ | ✓ | ✓ | ✓ | — | **Falta mai** |
| 7.5.35 | Rateio Seletiva Apoio | ✓ | ✓ | ✓ | ✓ | — | **Falta mai** |
| 7.5.20 | Internet | ✓ | ✓ | — | — | — | Migrado p/ 7.5.3 |
| 7.5.3 | Telecomunicações | ✓ | ✓ | — | — | — | Migrado p/ 7.5.3 |
| 7.5.3 | Internet e telefonia | — | — | ✓ | ✓ | ✓ | Consolidação a partir de mar |

### Valores atípicos

| Conta | Observação |
|-------|------------|
| 7.5.2 Energia elétrica | Mar −R$ 65.237 vs mai −R$ 5.763 (−91%) |
| 7.5.31 Aluguel administrativo | Jan–abr ~R$ 70–105 mil → mai −R$ 44.643 (−42%) |
| 7.6.5 IPTU pátio | Abr −R$ 54.760 (pico isolado) |
| 7.1.20 Rastreador | Irregular; zerado em mai |
| **Total categoria** | Abr −545.764 → mai −87.988 (−84%) |

### Divergências vs classificação cadastrada

Contas **no modal e fora do `.md`** (25/05): 7.5.13, 7.1.20, 7.5.7, 7.6.5, 7.5.36, 7.5.35.

Contas **no `.md` e ausentes como linha própria** no período: 7.5.20 e 7.5.3 (Telecom) substituídas por 7.5.3 (Internet e telefonia) a partir de mar/2026.

---

## ~={Titulo}2.1.2 — Salário (fixo)=~

**Totais mensais:** jan −338.384 · fev −481.165 · mar −439.224 · abr −386.495 · **mai −386.495** · total −2.031.762

| Conta | Descrição | Alerta |
|-------|-----------|--------|
| 7.3.1 | Salários | Fev −R$ 361.726 vs jan −R$ 293.773 (+23%) |
| 7.3.2 | FGTS | Fev −R$ 28.977 vs mar −R$ 5.507 |
| 7.3.21 | Rescisões | Fev −R$ 16.479 vs jan −R$ 145 |
| 7.3.3 | INSS | Presente mar–mai; ausente jan/fev |
| 7.3.12 | Pro labore | **Extra** — só fev (−R$ 502) |
| **Total** | | Fev +42% vs jan; **abr = mai** (valores idênticos) |

Todas as 7 contas do cadastro oficial aparecem no modal.

---

## ~={Titulo}2.1.3 / 2.1.4 — Tributos e Operacional (fixo)=~

**Sem dados** no modal — consistente com [[BCBI - Classificação Analítico Plano de Contas|classificação]] (0 contas cadastradas).

---

## ~={Titulo}2.1.5 — Não operacional (fixo)=~

| Conta | Descrição | Mar | Mai | Total |
|-------|-----------|-----|-----|-------|
| 7.11.7 | Empréstimos | −R$ 23.230 | −R$ 18.509 | −R$ 41.739 |

Sem lançamentos em jan, fev e abr — coerente com natureza de empréstimo (não recorrente mensal).

---

## ~={Titulo}2.2.1 — Não operacional (variável)=~

**Total:** −R$ 1.305.725 · 45 contas com movimento no período.

| Conta | Destaque |
|-------|----------|
| 7.1.8 Despesas de viagem | Mai −R$ 90.411 (pico) |
| 7.5.23 Juros e multas | Abr −R$ 176.268 (atípico) |
| 7.5.8 Honorários advocatícios | Mai −R$ 47.539 |

Variabilidade esperada para categoria variável.

---

## ~={Titulo}2.2.2 — Operacional (variável)=~

**Totais mensais:** jan −6,8M · fev −7,7M · mar −7,2M · abr −9,1M · **mai −11,1M** · total −41,9M

| Conta | Jan | Fev | Mar | Abr | Mai | Alerta |
|-------|-----|-----|-----|-----|-----|--------|
| 6.1.1 Compras de sucata | −5,0M | −5,8M | −5,0M | −5,3M | **−7,4M** | Mai +39% vs abr |
| 7.1.6 Transporte de sucata | −841k | −739k | −1,2M | −2,2M | **−3,3M** | Crescimento contínuo |
| 6.6.6 Frete de coleta | — | — | −235k | −297k | −285k | Só a partir de mar |

---

## ~={Titulo}2.2.3 — Tributos (variável)=~

**Total:** −R$ 1.644.751

| Conta | Alerta |
|-------|--------|
| 7.4.12 ICMS | Abr −R$ 459.802 vs mai −R$ 77.273 (−83%) |
| 7.4.2 COFINS | Abr −R$ 178.965; demais meses zerados |
| 7.4.1 PIS | Abr −R$ 38.416 (isolado) |

---

## ~={Titulo}2.2.4 — Manutenção=~

**Totais mensais:** jan −199.282 · fev −219.346 · mar −201.355 · **abr −7.890** · **mai −2.049** · total −629.922

| Conta | Jan–Mar | Abr | Mai |
|-------|---------|-----|-----|
| 7.1.1 Peças de manutenção | ~R$ 24–197k/mês | R$ 441 | R$ 237 |
| 7.1.2 Manut. veículos/máquinas | ~R$ 177–219k/mês | R$ 7.449 | R$ 1.812 |

**Queda de ~96% em abr/mai** — investigar atraso de lançamento ou reclassificação para 2.2.2.

---

## ~={Titulo}Receitas=~

### 3.1.1 — Receitas

**Total:** +R$ 60.349.388 · Vendas sucata jan R$ 9,4M → mai R$ 16,7M (+77%).

Contas adicionais no modal vs cadastro: 5.3.4 Variação cambial, 5.3.2 Ressarcimento seguro, 5.4.2 Empréstimos, 5.4.11 Receitas diversas, 6.3.2 Devolução adiantamento.

### BONUS

| Mês | Valor |
|-----|-------|
| Jan | +R$ 273.846 |
| Fev | +R$ 5.068 |
| Mai | +R$ 3.003 |
| Mar/Abr | — |

### DEVOLUCAO_MES_ANTERIOR

| Mês | Valor |
|-----|-------|
| Jan | −R$ 38.825 |
| Fev | −R$ 112.419 |
| Abr | −R$ 64.453 |

Detalhe: linha “DEVOLUÇÃO” + estorno em 4.1.1 Vendas de sucatas.

---

## ~={Titulo}Como reproduzir no BCBI=~

1. Abrir `https://bcbi.com.br/seletiva/custos.php` (logado).
2. Filtros: **01/2026** a **05/2026**, unidades Seletiva, CC **1.2 / 2.2**, **Com Projeto**.
3. Clicar em **Atualizar dados** (ou `carregaDados()` no console).
4. Rolar até a seção **ANALÍTICO**.
5. Clicar no **nome azul** da linha (CUSTO ADMINISTRATIVO, SALÁRIO, etc.) — o modal `detalhaItem` abre com contas × meses.

---

## ~={Titulo}Próximos passos sugeridos=~

- [ ] Validar com financeiro se maio/2026 está fechado para pagamentos administrativos e salários.
- [ ] Conferir migração de contas 7.5.20 / 7.5.3 → 7.5.3 unificada no SAGI.
- [ ] Investigar queda de manutenção (2.2.4) em abr/mai vs histórico jan–mar.
- [ ] Revisar lançamento ICMS abr/2026 (7.4.12) e PIS/COFINS no mesmo mês.
- [ ] Atualizar [[BCBI - Classificação Analítico Plano de Contas]] com contas extras encontradas em 2.1.1.

___
[[BCBI - Classificação Analítico Plano de Contas]] · [[Melhoria BCBI]] · [[plano de conta]]
