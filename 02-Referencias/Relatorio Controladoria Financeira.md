A estrutura atual demonstra um esforço claro de segregação por unidade de negócio, o que é um excelente ponto de partida.

Segue o diagnóstico executivo do modelo de gestão financeira do Grupo G3S, baseado nos relatórios de Centros de Custo (CC) e Plano de Contas (PC) impressos em **25/03/2026** (637 CCs e 241 contas) e na base de movimentações financeiras com **61.018 registros** e volume bruto de **R$ 436,7 milhões**.

### ~={Titulo}1. Cobertura do Modelo e Sub-representação=~

O modelo cobre bem o *core business* da Seletiva (Conta 4 para Sucatas) e as locações da Ekipa (Contas 5.1 e 5.6). No entanto, existem operações sub-representadas no Plano de Contas que podem dificultar a apuração de margens específicas:

| Unidade de Negócio | Centro de Custo | Conta(s) no Plano de Contas | Diagnóstico de Cobertura |
| :--- | :--- | :--- | :--- |
| **Bracofer** | 1.3 / 2.3 | 5.8 (Ferro Novo) | Sub-representada. Possui apenas "Revenda" (5.8.1) e "Outras Receitas" (5.8.2), o que é muito sintético para uma operação de distribuição. |
| **NVS Entulhos** | 1.12 / 2.12 | Ausente / Indefinida | Crítico. Não há contas de receita exclusivas para serviços de entulho no PC, forçando o uso de contas genéricas. |
| **G3S Energia** | 1.13 / 2.13 | 5.8 (Venda de Energia) | Recém-criada. A cobertura inicial é boa, com contas para venda de energia e créditos de carbono, mas precisará de contas de despesa mais detalhadas (ex: manutenção de inversores, seguros). |
| **Imobiliária / Render** | 1.8 / 2.8 / 9 | 8.2 (Aquisições) / 9.2 (Despesas) | Razoável para despesas (IPTU, Condomínio), mas as receitas locatícias podem estar misturadas na genérica 5.6.3 (Locação de Imóveis). |

> ⚠️ **Nota (25/03/2026):** O grupo 9.1 (Receitas Imobiliárias detalhadas por imóvel) **não consta mais** no Plano de Contas vigente. As receitas de locação provavelmente transitaram para `5.6.3` ou foram desativadas neste nível de detalhe.

### ~={Titulo}2. Pontos Cegos Potenciais (Contas Genéricas)=~

Contas com nomenclaturas amplas são os maiores ofensores da qualidade da informação gerencial. No seu Plano de Contas, as seguintes linhas exigem atenção redobrada:

* **5.4.11 Receitas Diversas e 5.4.6 Particular:** Escondem a origem real das entradas de caixa, prejudicando a análise de rentabilidade operacional.
* **7.11.4 Acertos Particulares e 7.11.6 Despesas Gerais Particular:** A presença dessas contas indica uma possível mistura entre o patrimônio da empresa (G3S) e dos sócios (Familiar).
* **7.1.16 Serviços de Terceiros:** Muito abrangente. Não permite distinguir se o gasto foi com manutenção predial, consultoria técnica ou operação de pátio.
* **7.5.26 Despesas Sociais e Doações:** Pode alocar desde pequenos patrocínios até retiradas não justificadas.

### ~={Titulo}3. Consistência dos Centros de Custo na Seletiva=~

A estrutura de nível 3 (Filiais) exige os 4 departamentos padrão, mas a simetria se quebra nos níveis analíticos (nível 4 e 5).

| Filial Seletiva (1.2) | Possui Adm/Com/Oper/Log? | Granularidade de Ativos (Veículos / Máquinas) |
| :--- | :--- | :--- |
| **Dourados (1.2.2)** | Sim | Alta. 7 veículos + 5 máquinas analíticos. |
| **Londrina (1.2.3)** | Sim | Alta. 5 veículos + 3 máquinas analíticos. |
| **Pres. Prudente (1.2.5)** | Sim | Altíssima. 17 veículos + 11 máquinas + Prensa Fixa JCG800 + Projeto Sistema de Incêndio. |
| **Maringá Distrito (1.2.4)** | Sim | Alta. 13 veículos + 6 máquinas + Prensa Fixa + Pátio GXS. |
| **Campo Grande (1.2.7)** | Sim | Média. 5 veículos + 2 máquinas + Projetos Corumba e Und. Própria CG. |
| **Assis (1.2.6)** | Sim | Baixíssima. Para no departamento de Logística (1.2.6.4), sem rastreio de frotas ou maquinário local. |
| **Maringá Cid. Alta (1.2.8)** | Sim | Baixíssima. Para em Logística (1.2.8.4), sem detalhamento de ativos operacionais. |

### ~={Titulo}4. Rastreabilidade de Ativos (TCO)=~

A estrutura atual de CCs analíticos permite o custeio primário (combustível, manutenção, IPVA) focado na **Despesa (1.x)**. É possível rastrear gastos alocando contas como 7.1.2 (Manutenção de Veículos/Maquinas) diretamente na placa EWU6003 (1.2.5.6.1).

O que precisa ser melhorado: O lado da **Receita (2.x)** carece da mesma granularidade. O CC de receita da filial de Pres. Prudente (2.2.5), por exemplo, não desce ao nível de equipamento ou caminhão. Isso significa que conseguimos saber *quanto custa* manter o caminhão BKW9157, mas não sabemos *quanta receita de frete ou coleta* ele gerou individualmente, impossibilitando o cálculo exato do Retorno sobre o Ativo (ROA).

### ~={Titulo}5. Risco de Dupla Contagem=~

A macroestrutura previne o erro primário ao forçar o "1" para Despesa e "2" para Receita no primeiro dígito. Contudo, o risco operacional de dupla contagem reside nas contas de **Devolução e Adiantamento**:
* Conta 4.2.2 (Devolução de Adiantamento Cliente) tem natureza "D" (Débito).
* Conta 4.3 (Devolução de Venda Sucata) tem natureza "D" (Débito).
* Conta 6.4 (Devolução de Compra Sucata) tem natureza "R" (Receita/Crédito).

Se a equipe lançar uma devolução de compra (6.4) contra um CC de Receita (2.x) em vez de creditar o CC de Despesa (1.x) original, o EBITDA do grupo será artificialmente inflado em ambas as pontas.

---

### ~={Titulo}6. Top 3 Insights Prioritários para Investigação=~

1. **Governança e Princípio da Entidade:** Extraia uma razão analítica combinando os CCs Familiares (1.9.1 a 1.9.6) com as contas do PC 7.11.2 (Pagamentos para Sócios) e 7.11.4 (Acertos Particulares). Verifique o volume financeiro transitando nessas contas para garantir que despesas de pessoas físicas não estejam poluindo as margens operacionais (DRE) da G3S.

2. **Operações Entre Empresas (Intercompany):** Avalie o saldo do CC 1.10.1 (Operações entre Empresa) contra o 2.10.1. A base atual registra uma transação de **R$ 27,9M** (AJUSTESALDO300925) em OPERAÇÕES ENTRE EMPRESAS na filial RSE — se a Ekipa RSE fatura para a Seletiva, essas receitas e custos internos precisam se anular (zerar) na consolidação do balanço do Grupo, caso contrário, vocês estão pagando impostos sobre receitas irreais ou duplicando custos.

3. **Auditoria na Logística de Assis e Maringá (Cid. Alta):** Investigue como os custos de combustível (7.1.4) e manutenção (7.1.2) estão sendo lançados nessas filiais que não possuem veículos cadastrados. É provável que estejam sendo jogados no CC genérico "1.2.6.4 Logística", o que mascara gargalos de ineficiência operacional nessas praças em comparação com Presidente Prudente.
