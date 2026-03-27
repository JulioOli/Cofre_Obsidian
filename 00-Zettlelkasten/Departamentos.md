---
tags:
  - note
  - controladoria
  - centro-de-custo
  - departamentos
  - G3S
atualizado: 27/03/2026
---
24/03/2026 - 09:22

# ~={Titulo}Departamentos — Centro de Custo G3S=~

> **Fonte:** `Centro de Custo.pdf` — 27/03/2026
> Os departamentos são o **4º nível** da hierarquia: `TIPO.DIVISÃO.FILIAL.DEPARTAMENTO`

---

## Departamentos Padrão por Tipo de Unidade

| Departamento | Seletiva | Bracofer | Transmove | Ekipa Cont. | NVS |
|---|:---:|:---:|:---:|:---:|:---:|
| Administrativo | ✅ | ✅ | ✅ | ✅ | ✅ |
| Comercial | ✅ | ✅ | — | ✅ | ✅ |
| Operacional | ✅ | ✅ | — | ✅ | ✅ |
| Logística | ✅ | ✅ | — | ✅ | ✅ |
| Transporte | — | — | ✅ | — | — |
| Corte e Dobra | — | ✅ | — | — | — |
| Veículos | ✅ | ✅ | — | — | — |
| Máquinas e Equipamentos | ✅ | ✅ | — | — | — |
| Projetos | — | ✅ | — | — | — |

---

## Administrativo
Presente em **todas** as divisões operacionais. Concentra despesas administrativas, pessoal de apoio e gestão local.

**Contas do Plano mais usadas:**
- `7.3` Pessoal (Salários, FGTS, INSS, Férias, 13º)
- `7.5` Administrativa (Água, Energia, Telecomunicações, Honorários, Sistemas)
- `7.4` Tributária (IRRF, INSS, PIS, COFINS)

**Onde existe:**

| Divisão | CCs de Administrativo |
|---|---|
| G3S Escritório | 1.1.2 (e múltiplos sub-depts. corporativos) |
| Seletiva | 1.2.2.1 · 1.2.3.1 · 1.2.4.1 · 1.2.5.1 · 1.2.6.1 · 1.2.7.1 · 1.2.8.1 |
| Bracofer | 1.3.1.1 |
| Transmove GSL | 1.4.1.2 · 1.4.2.2 · 1.4.3.2 · 1.4.4.2 |
| Ekipa Contêiner | 1.5.1.1 |
| Ekipa Loc. RSE | 1.6.1 |
| Ekipa Serv. G&S | 1.7.2.1 |
| Render | 1.8.1 |
| NVS Entulho | 1.12.1.1 |

---

## Comercial
Responsável pelas operações de compra e venda. Na Seletiva, pode ser desdobrado em **Comercial Compra** e **Comercial Venda** no corporativo.

**Contas do Plano mais usadas:**
- `7.2` Comercial (Comissão, Viagem, Publicidade, Prêmios)
- `6.1` Compras de Sucatas
- `4.1` Vendas de Sucatas
- `5.4.3` Pesagens Avulsas

**Onde existe:**

| Divisão | CCs de Comercial |
|---|---|
| Seletiva Corporativo | 1.2.1.5 (Compra) · 1.2.1.6 (Venda) |
| Seletiva Filiais | 1.2.2.2 · 1.2.3.2 · 1.2.4.2 · 1.2.5.2 · 1.2.6.2 · 1.2.7.2 · 1.2.8.2 |
| Bracofer | 1.3.1.2 |
| Ekipa Contêiner | 1.5.1.2 |
| Ekipa Loc. RSE | 1.6.2 |
| Ekipa Serv. G&S | 1.7.2.2 |
| NVS Entulho | 1.12.1.2 |

---

## Operacional
Ligado às atividades de pátio: triagem, prensagem, processamento de sucata.

**Contas do Plano mais usadas:**
- `7.1` Operacional — Frota (Manutenção, Combustível, Peças)
- `7.6` Operacional Pátio (Ferramentas, Manutenção Pátio, Aluguel, IPTU)
- `6.2` Processamento Interno

**Onde existe:**

| Divisão | CCs de Operacional |
|---|---|
| Seletiva | 1.2.2.3 · 1.2.3.3 · 1.2.4.3 · 1.2.5.3 · 1.2.6.3 · 1.2.7.3 · 1.2.8.3 |
| Bracofer | 1.3.1.3 |
| Ekipa Contêiner | 1.5.1.3 |
| NVS Entulho | 1.12.1.3 |

---

## Logística
Gestão do transporte interno de sucata, frota própria e terceirizada.

**Contas do Plano mais usadas:**
- `7.1.4` Combustível — Diesel (Posto)
- `7.1.2` Manutenção de Veículos/Máquinas
- `7.1.6` Transporte de Sucata
- `7.1.12` Pedágio
- `7.1.1` Peças de Manutenção
- `6.6` Transporte de Cargas

**Onde existe:**

| Divisão | CCs de Logística |
|---|---|
| Seletiva | 1.2.2.4 · 1.2.3.4 · 1.2.4.4 · 1.2.5.4 · 1.2.6.4 · 1.2.7.4 · 1.2.8.4 |
| Bracofer | 1.3.1.4 |
| Ekipa Contêiner | 1.5.1.4 |
| NVS Entulho | 1.12.1.4 |

> ⚠️ **Assis (`1.2.6.4`) e Maringá Cidade Alta (`1.2.8.4`):** Logística é o departamento mais analítico disponível, pois não há veículos ou máquinas cadastrados individualmente. Todos os custos operacionais ficam neste CC genérico, dificultando análise de eficiência.

---

## Transporte
Exclusivo da **Transmove GSL**. Substitui Operacional + Logística nesta divisão.

**Contas do Plano mais usadas:**
- `7.1.4` / `7.1.22` Combustível
- `7.1.2` Manutenção
- `7.1.12` Pedágio
- `6.6` Transporte de Cargas

| Filial | CC Desp. | CC Rec. |
|---|---|---|
| Presidente Prudente | 1.4.1.1 | 2.4.1.1 |
| Dourados | 1.4.2.1 | 2.4.2.1 |
| Maringá | 1.4.3.1 | 2.4.3.1 |
| Barueri | 1.4.4.1 | — |

---

## Corte e Dobra
Exclusivo da **Bracofer** em Presidente Prudente (`1.3.1.5`).

**Contas do Plano mais usadas:**
- `6.2.1` Mão de Obra — Corte de Sucata
- `6.2.2` Materiais — Corte de Sucata
- `7.1.1` Peças de Manutenção

---

## Veículos (Frota Analítica — Nível 5)
Cada veículo com seu próprio CC. Permite rastrear o custo total de propriedade (TCO) por placa.

| Divisão / Filial | Qtd. veículos cadastrados |
|---|---|
| Seletiva — Corporativo | 4 veículos + 3 prensas móveis |
| Seletiva — Dourados | 7 |
| Seletiva — Londrina | 5 |
| Seletiva — Maringá Distrito | 13 (veículos analíticos) |
| Seletiva — Presidente Prudente | 17 |
| Seletiva — Campo Grande | 5 |
| Bracofer — Presidente Prudente | 4 |
| Ekipa Loc. RSE | ~50 ativos (veículos + máquinas) |
| Ekipa Serv. G&S | Ativos por contrato |

> 💡 Para localizar um ativo por placa, use o prefixo do CC da filial. Ex: `1.2.5.6.*` = todos os veículos de Presidente Prudente.

---

## Máquinas e Equipamentos (Frota Analítica — Nível 5)

| Divisão / Filial | Qtd. máquinas cadastradas |
|---|---|
| Seletiva — Dourados | 5 |
| Seletiva — Londrina | 3 |
| Seletiva — Maringá Distrito | 6 |
| Seletiva — Presidente Prudente | 11 |
| Seletiva — Campo Grande | 2 |
| Bracofer — Presidente Prudente | 5 |

---

## Departamentos Especiais — G3S Escritório (`1.1`)

| CC | Departamento | Função |
|---|---|---|
| 1.1.1.1 | Acionistas | Remuneração e distribuições de sócios |
| 1.1.4 | Contabilidade/Fiscal | Escrituração e obrigações acessórias |
| 1.1.5 | Qualidade | ISO, auditorias, licenciamentos |
| 1.1.6 | Jurídico | Contratos e processos |
| 1.1.8 | Ambiental | Licenças ambientais, CETESB |
| 1.1.9 | Recursos Humanos | Gestão de pessoal centralizada |
| 1.1.11 | Segurança do Trabalho | EPI, CIPA, treinamentos |
| 1.1.12 | Marketing | Publicidade e propaganda |
| 1.1.13 | TIC | Infraestrutura de tecnologia |
| 1.1.14 | Suprimentos | Compras corporativas |
| 1.1.15 | Manutenção Máquinas e Veículos | Manutenção centralizada |

---

## Referência Rápida — Departamento × Conta

| Quero lançar… | Conta | Departamento sugerido |
|---|---|---|
| Salário de operador | `7.3.1` | Operacional |
| Combustível de caminhão | `7.1.4` | CC do veículo (nível 5) |
| Manutenção de prensa | `7.1.2` | CC da máquina (nível 5) |
| Compra de sucata | `6.1.1` | Comercial |
| Venda de sucata | `4.1.1` | Comercial (CC Receita `2.x`) |
| Frete de coleta | `6.6.6` | Logística |
| Honorários contábeis | `7.5.7` | Administrativo |
| IPVA de veículo | `7.1.10` | CC do veículo (nível 5) |
| Locação de máquina (receita) | `5.6.1` | Comercial (CC Receita `2.x`) |
| INSS folha | `7.3.3` | Administrativo / Operacional |
| Pedágio | `7.1.12` | Logística / Transporte |
| Aluguel de pátio | `7.6.4` | Operacional |

---

## Departamentos Especiais — NVS Entulho

| CC         | Departamento                | Função    |
| ---------- | --------------------------- | --------- |
| `1.12.1.2` | 🗑️ NVS Entulho - Unidade I | Comercial |

---

[[Divisões]] · [[Filiais]] · [[Tipos de Movimentação]]