---
tags:
  - note
  - controladoria
  - centro-de-custo
  - divisoes
  - G3S
atualizado: 27/03/2026
---
24/03/2026 - 09:22

# ~={Titulo}Divisões (Unidades de Negócio) — Centro de Custo G3S=~

> **Fonte:** `Centro de Custo.pdf` — 27/03/2026
> O 1º dígito do código define o **tipo**: `1` = Despesa · `2` = Receita
> O 2º nível define a **divisão/unidade de negócio**

---

## Mapa das Divisões

| Cód. Desp. | Cód. Rec. | Divisão | Setor | Obs. |
|---|---|---|---|---|
| 1.1 | — | **G3S Escritório (Pilares)** | Holding / Corporativo | Sede, diretoria e setores de apoio central |
| 1.2 | 2.2 | **Seletiva** | Reciclagem de Sucata | Core business — maior volume de lançamentos |
| 1.3 | 2.3 | **Bracofer** | Distribuição de Ferro Novo | Sub-representada no Plano de Contas |
| 1.4 | 2.4 | **Transmove GSL** | Transporte / Logística | Operações em PP, Dourados, Maringá e Barueri |
| 1.5 | 2.5 | **Ekipa Contêiner** | Locação de Contêineres | Apenas em Presidente Prudente |
| 1.6 | 2.6 | **Ekipa Locações RSE** | Locação de Veículos/Máquinas | CNPJ RSE — grande frota de ativos |
| 1.7 | 2.7 | **Ekipa Locações e Serv. G&S** | Serviços em clientes siderúrgicos | Arcelor, Gerdau, Tupy — contratos externos |
| 1.8 | 2.8 | **Render Locações** | Patrimônio Imobiliário | Imóveis, salas, lotes, chácaras |
| 1.9 | 2.9 | **Familiar** | Pessoas Físicas dos Sócios | Atenção: não misturar com DRE operacional |
| 1.10 | 2.10 | **Resultado Não Operacional** | Intercompany / Imobilizado | Op. entre empresas e venda de ativos |
| — | 2.11 | **Render** | Receitas de Locação (Render) | Receitas específicas — sem CC de despesa espelhado |
| 1.12 | 2.12 | **NVS Serviços de Entulho** | Coleta de Entulho e Resíduos de Construção | [[Departamentos]] |

---

## Detalhamento por Divisão

### 🏢 G3S Escritório / Pilares (`1.1` / `2.1`)
Centro corporativo da holding. Concentra os setores administrativos centrais que não pertencem a nenhuma filial operacional.

**Departamentos disponíveis:**
- 1.1.1 Diretoria → 1.1.1.1 Acionistas
- 1.1.2 Administrativo
- 1.1.3 Financeiro
- 1.1.4 Contabilidade/Fiscal
- 1.1.5 Qualidade
- 1.1.6 Jurídico
- 1.1.7 Logística
- 1.1.8 Ambiental
- 1.1.9 Recursos Humanos
- 1.1.10 Pessoas
- 1.1.11 Segurança do Trabalho
- 1.1.12 Marketing
- 1.1.13 TIC
- 1.1.14 Suprimentos
- 1.1.15 Manutenção Máquinas e Veículos

**Lado Receita (2.1):**
- 2.1.1.1 Acionistas
- 2.1.1.2 Financeiro

---

### ♻️ Seletiva (`1.2` / `2.2`)
Principal unidade de negócio. Compra, processa e vende sucatas metálicas em múltiplas praças.

**Filiais:** → ver [[Filiais#Seletiva]]

**Corporativo Sucata (`1.2.1`):** Estrutura central da operação de sucata.
- Apoio · Coordenação MS · Coordenação PR · Coordenação SP
- Comercial Compra Sucata · Comercial Venda Sucata
- Prensas Móveis (frota) · Veículos corporativos

---

### 🔩 Bracofer (`1.3` / `2.3`)
Distribuição de ferro novo (barras, perfis). Presente apenas em Presidente Prudente.

**Departamentos:** Administrativo · Comercial · Operacional · Logística · Corte e Dobra · Veículos · Máquinas e Equipamentos · Projetos

> ⚠️ Sub-representada no Plano de Contas: apenas contas `5.8` (Ferro Novo) com granularidade insuficiente para análise de margens.

---

### 🚛 Transmove GSL (`1.4` / `2.4`)
Transportadora do grupo. Opera nas praças de Presidente Prudente, Dourados, Maringá e Barueri.

**Departamentos por filial:** Transporte · Administrativo

| Filial | CC Desp. | CC Rec. |
|---|---|---|
| Presidente Prudente | 1.4.1 | 2.4.1 |
| Dourados | 1.4.2 | 2.4.2 |
| Maringá | 1.4.3 | 2.4.3 |
| Barueri | 1.4.4 | — |

---

### 📦 Ekipa Contêiner (`1.5` / `2.5`)
Locação de contêineres e caçambas. Presente apenas em Presidente Prudente.

**Departamentos:** Administrativo · Comercial · Operacional · Logística

---

### 🏗️ Ekipa Locações RSE (`1.6` / `2.6`)
Locação de veículos pesados, máquinas e equipamentos sob o CNPJ da RSE. Grande frota de ativos rastreados individualmente.

**Estrutura:**
- Administrativo · Comercial
- Veículos, Máquinas e Equipamentos (frota individual — ~50 ativos)
- Contêiner
- Contratos: Gerdau — Jaraguá do Sul/SC

---

### 🏭 Ekipa Locações e Serv. G&S (`1.7` / `2.7`)
Serviços de operação de pátio e locação em clientes siderúrgicos externos.

**Contratos ativos:**

| Contrato | Local | CC Desp. | CC Rec. |
|---|---|---|---|
| Arcelor Resende | RJ | 1.7.1.2 | 2.7.1.2 |
| Arcelor Barra Mansa | RJ | 1.7.1.3 | 2.7.1.3 |
| Arcelor Piracicaba | SP | 1.7.1.4 | 2.7.1.4 |
| Arcelor Iracemápolis | SP | 1.7.1.14 | 2.7.1.13 |
| Gerdau São Caetano do Sul | SP | 1.7.1.7 | 2.7.1.7 |
| Tupy Joinville | SC | 1.7.1.8 | 2.7.1.8 |
| Arcelor Juiz de Fora | MG | — | 2.7.1.5 |
| Arcelor Curitiba | PR | — | 2.7.1.6 |
| Tupy Betim | MG | — | 2.7.1.9 |
| Transmove — Prancha Salione | — | 1.7.1.10 | 2.7.1.10 |
| Seletiva — Prensa Móvel | — | 1.7.1.11 | 2.7.1.11 |
| G&G | — | — | 2.7.1.12 |

---

### 🏠 Render Locações (`1.8` / `2.8`)
Portfólio imobiliário do grupo. Inclui imóveis operacionais (barracões, pátios) e patrimoniais (apartamentos, lotes, chácaras).

**Sub-portfólios:**

| Sub-portfólio | CC Desp. | CC Rec. | Descrição |
|---|---|---|---|
| RSS | 1.8.3 | 2.8.3 | Imóveis em Assis e Presidente Prudente (barracões, salas, apartamentos) |
| Salteiro Empreendimentos | 1.8.4 | 2.8.4 | Chácara Takigawa |
| Renato Salteiro | 1.8.5 | 2.8.5 | Apartamentos e vagas — Torres Oxford, Liverpool, Londres, Inglaterra (P. Prudente) |
| Gabriel Salteiro | 1.8.6 | 2.8.6 | Apto 23 — Heitor Graça |
| Giuliana Salmazzo | 1.8.7 | 2.8.7 | Patrimônio pessoal (também presente em Familiar `1.9.2`) |
| GXS | 1.8.8 | 2.8.8 | Maringá — Lote 09 Quadra 05 |
| RSR | 1.8.9 | 2.8.9 | Imóveis em P. Prudente — Helena F. Borghi, 100 (17 unidades) |
| S1 a S4, S6, S9 | 1.8.10–15 | 2.8.10–15 | Sítios, fazendas e lotes em Rosana, Três Lagoas e P. Prudente |

> ⚠️ **CC Temporário:** `1.8.16 CHN0029 (TEMPORARIO)` — ativo temporário cadastrado no Render. Monitorar para reclassificação ou encerramento.

---

### 👨‍👩‍👧 Familiar (`1.9` / `2.9`)
Centros de custo de pessoas físicas dos sócios. Devem ser acompanhados separadamente para não poluir o DRE operacional.

| CC Desp. | CC Rec. | Nome |
|---|---|---|
| 1.9.1 | 2.9.1 | Renato Salteiro |
| 1.9.2 | 2.9.2 | Giuliana Salmazzo |
| 1.9.3 | 2.9.3 | Gabriel Salteiro |
| 1.9.4 | 2.9.4 | Espólio Zacharias |
| 1.9.5 | 2.9.5 | Ilda Salteiro |
| 1.9.6 | 2.9.6 | Gleice Salteiro |

---

### 🔄 Resultado Não Operacional (`1.10` / `2.10`)
| CC | Descrição |
|---|---|
| 1.10.1 / 2.10.1 | Operações entre Empresas (Intercompany) |
| 1.10.2 | Imobilizado |

> ⚠️ O saldo de `1.10.1` deve ser zerado contra `2.10.1` na consolidação do grupo. Caso contrário há risco de dupla contagem / inflação de receitas.

---

### 🗑️ NVS Serviços de Entulho (`1.12` / `2.12`)
Coleta e destinação de entulhos. Apenas em Presidente Prudente.

**Departamentos:** Administrativo · Comercial · Operacional · Logística

> ⚠️ Não possui contas exclusivas no Plano de Contas. Lançamentos provavelmente alocados em contas genéricas.

___

[[Filiais]] · [[Departamentos]] · [[Tipos de Movimentação]] · [[Estrutura Empresarial G3S]]
