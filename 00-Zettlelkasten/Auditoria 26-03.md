---
tags:
  - note
---
26/03/2026 - 08:35



Tenho todos os dados. Vou compilar o relatório consolidado da auditoria.

---

## 🔎 Relatório de Auditoria de Lançamentos — 26/03/2026

---

### 🔴 ALTA — Ação imediata necessária

---

#### REGRA 1 — 188 ADTs lançados em `4.1.1` VENDAS DE SUCATAS

ADTs deveriam estar em `4.2.1` ADIANTAMENTO CLIENTE SUCATA. Todos os abaixo inflam artificialmente a linha de **Vendas de Sucatas** na DRE.

**Prioridade máxima — alto valor (>R$100.000):**

| Documento | Filial | Valor | Vencimento | CC |
|---|---|---|---|---|
| ADT-15122025 | G3S PRUDENTE | **R$ 756.140,50** | 2025-12-15 | 2.2.5.2 |
| ADT-03022026 | G3S CAMPO GRANDE | **R$ 551.820,71** | 2026-02-03 | 2.2.7.2 |
| ADT-03022026 | G3S CAMPO GRANDE | **R$ 551.820,71** | 2026-02-04 | 2.2.7.2 |
| ADT-04022026 | G3S CAMPO GRANDE | **R$ 563.133,60** | 2026-02-04 | 2.2.7.2 |
| ADT-19022026 | G3S CAMPO GRANDE | **R$ 548.886,24** | 2026-02-20 | 2.2.7.2 |
| ADT-20012026 | G3S CAMPO GRANDE | **R$ 570.315,90** | 2026-01-20 | 2.2.7.2 |
| ADT-21012026 | G3S CAMPO GRANDE | **R$ 584.280,00** | 2026-01-21 | 2.2.7.2 |
| ADT-07012026 | G3S CAMPO GRANDE | **R$ 584.280,00** | 2026-01-07 | 2.2.7.2 |
| ADT-16012026 | G3S CAMPO GRANDE | **R$ 558.835,20** | 2026-01-16 | 2.2.7.2 |
| ADT-25022026 | G3S CAMPO GRANDE | **R$ 554.148,00** | 2026-02-25 | 2.2.7.2 |
| ADT-23102025 | G3S CAMPO GRANDE | **R$ 484.250,40** | 2025-10-23 | 2.2.7.2 |
| ADT-12012025 | G3S CAMPO GRANDE | **R$ 286.297,20** | 2026-01-12 | 2.2.7.2 |
| ADT-05122025 | G3S CAMPO GRANDE | **R$ 158.371,20** | 2025-12-05 | 2.2.7.2 |
| ADT21082025 | G3S CAMPO GRANDE | **R$ 161.416,80** | 2025-08-21 | 2.2.7.2 |
| ADT-11082025 | G3S CAMPO GRANDE | **R$ 161.416,80** | 2026-09-11 | 2.2.7.2 |

> **Correção:** Trocar conta `4.1.1` → `4.2.1` via **Troca de Plano de Contas em Lote** no SAGI.

---

#### REGRA 4 — Três Lançamentos iguais de ADT Campo Grande R$629.463,55

| Documento | Filial | Valor | Vencimento |
|---|---|---|---|
| ADT-23032026 | G3S CAMPO GRANDE | R$ 629.463,55 | 2026-03-23 |
| ADT-20032026-1 | G3S CAMPO GRANDE | R$ 629.463,55 | 2026-03-23 |
| ADT-23032026-2 | G3S CAMPO GRANDE | R$ 629.463,55 | 2026-03-23 |

O mesmo valor e data aparecem em **3 documentos diferentes** — soma fictícia de **R$ 1.888.390,65** na DRE. Além da conta errada (4.1.1 em vez de 4.2.1), há dois lançamentos extras a estornar.

> ⚠️ **Escalar para o gestor antes de qualquer ação.** Confirmar qual documento é o legítimo e estornar os demais com novo lançamento correto.

---

#### REGRA 3 — Duplicata exata: ADT00008205 G3S LONDRINA

| Documento | Filial | Valor | Vencimento | CC | Conta |
|---|---|---|---|---|---|
| ADT00008205 | G3S LONDRINA | R$ 17.444,00 | 2026-02-12 | 1.2.3.2 | 4.1.1 |
| ADT00008205 | G3S LONDRINA | R$ 17.444,00 | 2026-02-12 | 1.2.3.2 | 4.1.1 |

Lançamento duplicado exato — mesmo documento, CC, conta e data. Soma: **R$ 34.888,00** no lugar de R$ 17.444,00. Além disso, conta errada (deve ser 4.2.1).

---

### 🟡 MÉDIA — Impacto na DRE e nos CCs analíticos

---

#### REGRA 7 — 367 manutenções (`7.1.2`) lançadas em CC de departamento genérico

A conta `7.1.2 MANUTENÇÃO DE VEÍCULOS/MÁQUINAS` deve estar no CC do **ativo específico** (nível 5, ex: `1.2.5.6.7`). Esses lançamentos impedem o cálculo de TCO (custo total de propriedade) por veículo.

| CC Genérico | Departamento | Qtd. lançamentos |
|---|---|---|
| `1.2.5.3` | Seletiva PP — Operacional | **110** |
| `1.6.3.4` | RSE — Ativo (num. interno) | 48 |
| `1.6.3.3` | RSE — Ativo (num. interno) | 36 |
| `1.6.3.5` | RSE — Ativo (num. interno) | 28 |
| `1.2.4.3` | Seletiva Maringá — Operacional | 18 |
| `1.3.1.3` | Bracofer PP — Operacional | 15 |
| `1.5.1.2` | Ekipa Contêiner — Comercial | 12 |
| `1.2.2.3` | Seletiva Dourados — Operacional | 8 |
| Demais CCs | (vários) | ~92 |

> **Correção:** Usar **Troca de CC em Lote** para mover cada lançamento ao CC da placa/máquina correspondente. Começar pelos 110 lançamentos de `1.2.5.3`.

---

#### REGRA 6 — 401 documentos "B-xxxxx" lançados em `4.1.1` (possíveis pesagens avulsas)

Documentos com prefixo `B-` e valores muito pequenos (R$1,80 a R$5.000) em `4.1.1 VENDAS DE SUCATAS`. O padrão sugere **pesagens avulsas** que deveriam estar em `5.4.3 PESAGENS AVULSAS`, inflando a linha de receita de sucata.

| Documento | Filial | Valor | Venc. |
|---|---|---|---|
| B-80902 | G3S PRUDENTE | R$ 1,80 | 2025-05-06 |
| B-80900 | G3S PRUDENTE | R$ 2,40 | 2025-04-23 |
| B-80803 | G3S PRUDENTE | R$ 3,30 | 2025-05-17 |
| *(mais 398 documentos…)* | | | |

> **Confirmar com o gestor** se o prefixo "B-" representa pesagem avulsa. Se confirmado, trocar conta `4.1.1` → `5.4.3` em lote.

---

#### REGRA 2 — 119 despesas lançadas em CC de Receita (`2.x`)

119 lançamentos de contas de despesa (7.x, 6.x) em CCs de Receita. Exemplos mais relevantes:

| Documento | Filial | Conta | Descrição | CC Receita | Valor |
|---|---|---|---|---|---|
| NFSE-1077 | G3S CAMPO GRANDE | 7.5.17 | TAXAS | 2.2.7.1 | R$ 18.864,81 |
| CTE-4 a CTE-7 | G3S MARINGA | 7.1.6 | TRANSPORTE DE SUCATA | 2.2.4.2 | ~R$ 28.267 total |
| CF742930062025 | G3S CG | 7.1.1/7.1.2/7.1.4/7.1.5/7.1.8 | Múltiplas | 2.7.1.2 | R$ 7.078,43 cada |

> **Correção:** Trocar o CC de Receita (`2.x`) pelo CC de Despesa correspondente (`1.x`, mesmo nível).

---

### 🟢 BAIXA — Verificação / Monitoramento

---

#### REGRA 3 — GXS MARINGÁ: 3 documentos em CCs duplicados diferentes

| Documento | Valor | CC 1 | CC 2 |
|---|---|---|---|
| 00002463 | R$ 11,89 | 1.2.5.1 (Seletiva PP Adm) | 1.3.1.2 (Bracofer Comercial) |
| 00003123 | R$ 452,61 | 1.1.13 (G3S TIC) | 1.3.1.2 (Bracofer Comercial) |
| 00003927 | R$ 12,01 | 1.2.5.2 (Seletiva PP Comerc.) | 1.3.1.2 (Bracofer Comercial) |

Podem ser rateios legítimos ou lançamentos duplicados por erro. Valores pequenos — verificar com o usuário da filial GXS.

---

#### REGRA 5 — Conta legado `1.35.43` usada recentemente

A conta `1.35.43 ESTORNO DE PAGAMENTO RECEBIDO` pertence ao grupo 1 (migração/legado) e foi usada em lançamentos dos últimos 90 dias. O uso de contas legado em novos lançamentos é indesejado — deve-se utilizar `5.4.8 ESTORNO DE PAGAMENTO INDEVIDO`.

---

#### REGRA 8 — 82 locações (`7.1.3` / `5.6.1`) em CCs da Seletiva

A maioria são faturas da **RSE cobrando locação de ativos para filiais Seletiva** (intercompany legítimo) ou locações de rastreadores (série `200xxxxx` da G&S Prudente). Verificar se há contrato formal registrado para os FAT 5679–5823 de Dourados.

---

### Resumo Executivo

| Severidade | Qtd. achados | Impacto estimado |
|---|---|---|
| 🔴 Alta | 3 grupos | ~R$ 7,5M inflados na DRE (ADTs + triple + duplicata) |
| 🟡 Média | 3 grupos | 888 lançamentos com CC/conta incorretos |
| 🟢 Baixa | 3 grupos | Monitoramento / confirmação com gestor |

**Próximos passos sugeridos:**
1. Escalar o triple-lançamento `ADT Campo Grande R$629.463,55` ao gestor imediatamente
2. Usar **Troca de Plano de Contas em Lote** para corrigir os ADTs em `4.1.1` → `4.2.1`
3. Confirmar prefixo `B-xxxxx` = pesagem para migração em lote para `5.4.3`
4. Iniciar troca de CC para manutenções genéricas no Operacional de PP (`1.2.5.3` — 110 lançamentos)

___
