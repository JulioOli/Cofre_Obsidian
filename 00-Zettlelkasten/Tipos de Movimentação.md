---
tags:
  - note
  - controladoria
  - plano-de-contas
  - tipos-movimentacao
  - G3S
atualizado: 27/03/2026
---
24/03/2026 - 09:22

# ~={Titulo}Tipos de Movimentação — Plano de Contas G3S=~

> **Fonte:** `Plano de Contas.pdf` — 27/03/2026 — 238 contas cadastradas
> **Natureza:** `D` = Débito (saída) · `R` = Crédito (entrada)

---

## Visão Geral dos Grupos

| Código | Grupo | Natureza | Descrição |
|---|---|---|---|
| **1** | Despesas (Legado/Migração) | D | Contas de migração do sistema antigo — evitar uso em novos lançamentos |
| **4** | Receita Sucata | R/D | Vendas, adiantamentos e devoluções de sucata |
| **5** | Outras Receitas | R | Locações, vendas de imobilizados, receitas financeiras e serviços |
| **6** | Custos | D/R | Compras de sucata, processamento, fretes de carga |
| **7** | Despesas Gerais | D | Operacional, comercial, pessoal, tributária, administrativa |
| **8** | Aquisições | D | Imobilizado e imóveis |
| **9** | Imobiliária | D | Despesas específicas do portfólio imobiliário |

> ⚠️ Os grupos **2** e **3** (contas legado de receitas e investimentos antigos) e o grupo **9.1** (Receitas Imobiliárias detalhadas) não constam mais no Plano de Contas atual (25/03/2026). Lançamentos históricos nesses códigos podem existir na `base.csv` como registros migrados.

---

## Grupo 1 — Legado / Migração

> Contas de uso interno do sistema ou migração. ==Evitar uso em novos lançamentos.==

| Código | Descrição | Nat. |
|---|---|---|
| 1.2 | Migração Financeiro 3.0 | D |
| 1.35.43 | Estorno de Pagamento Recebido | D |

---

## Grupo 4 — Receita Sucata ⭐ (Core Business)

| Código | Descrição | Nat. |
|---|---|---|
| 4.1 | Vendas de Sucatas | R |
| 4.1.1 | Vendas de Sucatas | R |
| 4.1.2 | Acerto Fornecedor x Credor | R |
| 4.2 | Adiantamento Cliente Sucata | R |
| 4.2.1 | Adiantamento Cliente Sucata | R |
| **4.2.2** | **Devolução de Adiantamento Cliente** | **D** |
| **4.3** | **Devolução de Venda Sucata** | **D** |
| 4.3.1 | Devolução de Venda Sucata | D |

> ⚠️ **Atenção:** As contas 4.2.2 e 4.3 têm natureza **Débito** (redutoras de receita). Lançar sempre em CC de Receita (`2.x`), nunca em CC de Despesa.

---

## Grupo 5 — Outras Receitas

### 5.1 — Locação de Máquinas e Equipamentos
| Código | Descrição | Nat. |
|---|---|---|
| 5.1.1 | Prensa JCH200 — EWU6041 | R |
| 5.1.2 | Locação de Contêiner e Caçambas | R |

### 5.2 — Vendas de Imobilizados
| Código | Descrição | Nat. |
|---|---|---|
| 5.2.1 | Venda de Veículos | R |
| 5.2.2 | Venda de Máquinas e Equipamentos | R |
| 5.2.3 | Venda de Imóveis | R |

### 5.3 — Receitas Financeiras
| Código | Descrição | Nat. |
|---|---|---|
| 5.3.1 | Perdcomp Ressarcimento | R |
| 5.3.2 | Ressarcimento Seguro | R |
| 5.3.3 | Rendimento Financeiro | R |
| 5.3.4 | Variação Cambial Ativa | R |
| 5.3.5 | Banco Transferência Entrada | R |

### 5.4 — Outras Receitas
| Código | Descrição | Nat. |
|---|---|---|
| 5.4.1 | Distribuição de Lucros | R |
| 5.4.2 | Empréstimos | R |
| 5.4.3 | Pesagens Avulsas | R |
| 5.4.4 | Descarte de Óleo Usado | R |
| 5.4.5 | Descontos Recebidos | R |
| 5.4.6 | Particular ⚠️ | R |
| 5.4.7 | Operações Entre Empresas | R |
| 5.4.8 | Estorno de Pagamento Indevido | R |
| 5.4.9 | Doações Recebidas | R |
| 5.4.10 | Ajuste Compensações de Cheques | R |
| 5.4.11 | Receitas Diversas ⚠️ | R |
| 5.4.12 | Juros e Multas | R |
| 5.4.13 | Logística Reversa | R |
| 5.4.14 | Migração | R |
| 5.4.15 | Faturamento Indevido | R |

### 5.5 — Adiantamento Cliente Locação
| Código | Descrição | Nat. |
|---|---|---|
| 5.5 | Adiantamento Cliente Locação | R |

### 5.6 — Locação (Ekipa RSE)
| Código | Descrição | Nat. |
|---|---|---|
| 5.6.1 | Locação de Máquinas e Equipamentos | R |
| 5.6.2 | Locação de Contêiner e Caçambas | R |
| 5.6.3 | Locação de Imóveis | R |
| 5.6.4 | Locação de Veículos | R |

### 5.7 — Fretes e Carretos
| Código | Descrição | Nat. |
|---|---|---|
| 5.7.1 | Fretes | R |
| 5.7.2 | Frete Próprio | R |

### 5.8 — Ferro Novo (Bracofer)
| Código | Descrição | Nat. |
|---|---|---|
| 5.8.1 | Revenda | R |
| 5.8.2 | Outras Receitas | R |

---

## Grupo 6 — Custos ⭐ (Core Business)

| Código | Descrição | Nat. |
|---|---|---|
| 6.1.1 | Compras de Sucatas | D |
| 6.2.1 | Mão de Obra — Corte de Sucata | D |
| 6.2.2 | Materiais — Corte de Sucata | D |
| 6.3.1 | Adiantamentos Concedidos (fornecedor sucata) | D |
| **6.3.2** | **Devolução de Adiantamento Fornecedor** | **R** |
| **6.4.1** | **Devolução de Compra Sucata** | **R** |
| 6.5.1 | Compra p/ Revenda | D |
| 6.5.2 | Industrialização | D |
| 6.5.3 | Compra de Máquinas e Equipamentos | D |
| 6.6.1 | Frete de Terceiros | D |
| 6.6.2 | INSS Patronal s/ Frete | D |
| 6.6.3 | ICMS da Prestação de Transporte | D |
| 6.6.4 | Seguro de Cargas | D |
| 6.6.5 | Tarifa Pamcard | D |
| 6.6.6 | Frete de Coleta | D |

> ⚠️ **Atenção:** Contas 6.3.2 e 6.4.1 têm natureza **Crédito** (redutoras de custo). Devoluções de compra devem ser lançadas contra o CC de Despesa original (`1.x`), nunca em CC de Receita.

---

## Grupo 7 — Despesas Gerais

### 7.1 — Operacional (Frota e Pátio)
| Código | Descrição |
|---|---|
| 7.1.1 | Peças de Manutenção |
| 7.1.2 | Manutenção de Veículos/Máquinas |
| 7.1.3 | Locação de Equipamentos e Ferramentas |
| 7.1.4 | Combustível — Diesel (Posto) |
| 7.1.5 | Combustível — Gasolina e Etanol |
| 7.1.6 | Transporte de Sucata |
| 7.1.7 | Transporte Manutenção |
| 7.1.8 | Despesas de Viagem |
| 7.1.9 | Multas de Trânsito |
| 7.1.10 | IPVA |
| 7.1.11 | Licenciamento / DPVAT |
| 7.1.12 | Pedágio |
| 7.1.13 | Taxa 1º Registro Veículo |
| 7.1.14 | Despachante |
| 7.1.15 | Vistorias |
| 7.1.16 | Serviços de Terceiros ⚠️ |
| 7.1.17 | Gás — Uso Oficina |
| 7.1.18 | Fretes e Carretos |
| 7.1.19 | Multa por Excesso de Peso |
| 7.1.20 | Rastreador / Monitoramento |
| 7.1.21 | Locação de Veículos |
| 7.1.22 | Combustível — Diesel (Interno) |
| 7.1.23 | Combustível — Diesel (Estoque) |

### 7.2 — Comercial
| Código | Descrição |
|---|---|
| 7.2.2 | Comissão |
| 7.2.3 | Prêmios |
| 7.2.4 | Brindes |
| 7.2.5 | Publicidade e Propaganda |
| 7.2.6 | Eventos Endomarketing |
| 7.2.7 | Patrocínios |

### 7.3 — Pessoal
| Código | Descrição |
|---|---|
| 7.3.1 | Salários |
| 7.3.2 | FGTS |
| 7.3.3 | INSS |
| 7.3.4 | Exames Médicos |
| 7.3.5 | Alimentação do Trabalhador |
| 7.3.6 | Plano de Saúde |
| 7.3.7 | Aluguel de Funcionário |
| 7.3.8 | Cesta Básica |
| 7.3.9 | Segurança do Trabalho |
| 7.3.10 | Transporte de Colaboradores |
| 7.3.11 | Uniformes |
| 7.3.12 | Pró-Labore |
| 7.3.13 | Sindicatos |
| 7.3.14 | Treinamentos e Desenvolvimento |
| 7.3.15 | Seguro de Vida |
| 7.3.16 | Empréstimo Consignado |
| 7.3.17 | Convênios |
| 7.3.18 | Custa Processual e Trabalhista |
| 7.3.19 | Férias |
| 7.3.20 | Gratificação 13º Salário |
| 7.3.21 | Rescisões |
| 7.3.22 | Bolsa Estágio |
| 7.3.23 | Honorários PJ |
| 7.3.24 | Folha — Remessa |
| 7.3.25 | Benefícios Diversos |
| 7.3.26 | Provisão 13º e Férias |
| 7.3.27 | Provisão de Encargos |

### 7.4 — Tributária
| Código | Descrição |
|---|---|
| 7.4.1 | PIS |
| 7.4.2 | COFINS |
| 7.4.3 | IRPJ |
| 7.4.4 | CSLL |
| 7.4.5 | ISS |
| 7.4.6 | IRRF |
| 7.4.7 | CSRF |
| 7.4.8 | IOF |
| 7.4.9 | DIFAL |
| 7.4.10 | ITCMD |
| 7.4.11 | IRPF |
| 7.4.12 | ICMS |
| 7.4.13 | DASN |

### 7.5 — Administrativa
| Código | Descrição |
|---|---|
| 7.5.1 | Água e Esgoto |
| 7.5.2 | Energia Elétrica |
| 7.5.3 | Telecomunicações |
| 7.5.4 | Material de Limpeza e Higiene |
| 7.5.5 | Material de Escritório |
| 7.5.6 | Manutenções e Reparos — Estrutura Administrativa |
| 7.5.7 | Honorários Contábeis |
| 7.5.8 | Honorários Advocatícios |
| 7.5.9 | Consultoria |
| 7.5.10 | Segurança e Vigilância |
| 7.5.11 | Correios |
| 7.5.13 | Seguros |
| 7.5.15 | Ração |
| 7.5.16 | Alarme e Monitoramento |
| 7.5.17 | Taxas |
| 7.5.18 | Sistemas |
| 7.5.19 | Entidades e Associações |
| 7.5.20 | Internet |
| 7.5.21 | Material de Informática |
| 7.5.22 | Despesas Bancárias |
| 7.5.23 | Juros e Multas |
| 7.5.24 | Descontos Concedidos |
| 7.5.25 | Despesa de Cartório |
| 7.5.26 | Despesas Sociais e Doações ⚠️ |
| 7.5.27 | Material de Copa/Cozinha |
| 7.5.28 | Serviço de Limpeza do Escritório |
| 7.5.29 | Lanches |
| 7.5.30 | Homologação Pgtos Eletrônicos |
| 7.5.31 | Aluguel Administrativo |
| 7.5.32 | Taxas e Licenças |
| 7.5.33 | Aluguel Vaga Garagem |
| 7.5.34 | Móveis e Eletrodomésticos |
| 7.5.35 | Rateio Seletiva Apoio |
| 7.5.36 | Rateio Pilares |

### 7.6 — Operacional Pátio
| Código | Descrição |
|---|---|
| 7.6.1 | Gás — GLP Copa |
| 7.6.2 | Ferramentas |
| 7.6.3 | Manutenção Pátio |
| 7.6.5 | IPTU Pátio |

### 7.7 — Reformas
| Código | Descrição |
|---|---|
| 7.7.1 | Serviços Contratados |
| 7.7.2 | Material para Reforma |

### 7.8 / 7.9 — Adiantamentos e Devoluções a Credor
| Código | Descrição | Nat. |
|---|---|---|
| 7.8.1 | Adiantamento a Credor | D |
| 7.8.2 | Devolução de Adiantamento a Credor | R |
| 7.9.1 | Devolução a Credor | R |

### 7.11 — Outras Despesas
| Código | Descrição |
|---|---|
| 7.11.1 | Operações Entre Empresas |
| 7.11.2 | Pagamentos para Sócios (Distrib.) |
| 7.11.3 | Ajuste Compensações de Cheques |
| 7.11.4 | Acertos Particulares ⚠️ |
| 7.11.5 | Recargas |
| 7.11.6 | Despesas Gerais Particular ⚠️ |
| 7.11.7 | Empréstimos |

### 7.12 — Financeira
| Código | Descrição |
|---|---|
| 7.12.1 | Variação Cambial Passiva |
| 7.12.2 | Prejuízo com Aplicações |
| 7.12.3 | Banco Transferência Saída |

---

## Grupo 8 — Aquisições

| Código | Descrição | Nat. |
|---|---|---|
| 8.1.1 | Veículos | D |
| 8.1.2 | Máquinas e Equipamentos | D |
| 8.1.3 | Móveis | D |
| 8.1.4 | Computadores e Periféricos | D |
| 8.1.5 | Instalações | D |
| 8.1.6 | Eletrônicos | D |
| 8.2.1 | Imóvel Residencial | D |
| 8.2.2 | Imóvel Comercial | D |
| 8.2.3 | Terreno sem Construção | D |
| 8.3.1 | ITBI | D |
| 8.3.2 | Escritura | D |
| 8.3.3 | Registro | D |
| 8.3.4 | Comissão de Corretores | D |
| 8.4 | Consórcio | D |

---

## Grupo 9 — Imobiliária

### 9.2 — Despesas Imobiliárias
| Código | Descrição | Nat. |
|---|---|---|
| 9.2.1 | IPTU | D |
| 9.2.2 | ITR | D |
| 9.2.3 | Engenheiros e Arquitetos | D |
| 9.2.4 | Topografia | D |
| 9.2.5 | Taxa de Administração de Imóveis | D |
| 9.2.6 | Condomínio | D |
| 9.2.7 | Outros Prestadores de Serviços | D |
| 9.2.8 | Despesas com Imóveis Desocupados | D |

---

> ⚠️ **Contas que exigem atenção especial** (risco de poluição de margens ou dupla contagem):
> - `5.4.6` Particular · `5.4.11` Receitas Diversas
> - `7.11.4` Acertos Particulares · `7.11.6` Despesas Gerais Particular
> - `7.1.16` Serviços de Terceiros (muito abrangente)
> - `7.5.26` Despesas Sociais e Doações

---

___

[[Divisões]] · [[Departamentos]] · [[Filiais]]
