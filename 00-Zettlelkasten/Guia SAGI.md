---
tags:
  - note
  - controladoria
  - sagi
  - procedimentos
  - G3S
---
25/03/2026 - 09:00

# ~={Titulo}Guia Prático — Sistema SAGI=~

> Material de apoio para uso do SAGI no dia a dia da Controladoria G3S.
> Baseado em explicações do gestor, anotações de reunião e screenshots do sistema.

---

## ~={Titulo}Sistemas Utilizados=~

| Sistema | Empresa | Função |
|---|---|---|
| **SAGI** (Sygecom) | G3S, RSE, G8S, Render, Ekipa | Sistema principal: compras/vendas de sucata, locações, NF da G8S, financeiro |
| **ATUA** (GSL) | Transmóvel / GSL | Sistema da transportadora — emite CTe e gerencia fretes |

> ⚠️ O ATUA integra com o SAGI: as notas de serviço de transporte emitidas no ATUA aparecem como lançamentos no SAGI.

A tela de login do SAGI mostra no rodapé: **usuário logado, setor, CNPJ e filial conectada**. No canto superior direito aparece a filial ativa (ex: `G3S PRUDENTE`). Lançamentos são feitos sempre no contexto da filial selecionada.

---

## ~={Titulo}Conceitos Fundamentais=~

### Centro de Custo (CC)

> **"Onde" e "quem"** do lançamento — é o endereço.

**Responde à pergunta:** "Em qual parte da empresa esse dinheiro entrou ou saiu?"

- É **hierárquico**: `TIPO.DIVISÃO.FILIAL.DEPARTAMENTO.ATIVO`
- O 1º dígito sempre define o tipo: `1` = Despesa · `2` = Receita
- **Sintético:** nó da árvore, agrupa, ==não recebe lançamento direto==
- **Analítico:** folha da árvore, ==recebe o lançamento==

**Exemplo:**
```
1.2.5.2 → DESPESA / SELETIVA / PRESIDENTE PRUDENTE / COMERCIAL
```
→ Este CC analítico recebe as compras de sucata da filial de P. Prudente.

---

### Plano de Contas (PC)

> **"O quê"** do lançamento — é a etiqueta.

**Responde à pergunta:** "Qual é a natureza desse dinheiro?"

- É como uma etiqueta que descreve o tipo de movimentação
- Tem natureza `D` (Débito/saída) ou `R` (Crédito/entrada)
- **Sintético** vs **Analítico** — mesma lógica do CC

**Exemplos:**
| Código | Descrição | Natureza |
|---|---|---|
| 6.1.1 | Compras de Sucatas | D (saída) |
| 4.1.1 | Vendas de Sucatas | R (entrada) |
| 7.3.1 | Salários | D (saída) |
| 7.1.4 | Combustível — Diesel (Posto) | D (saída) |

---

### Como CC e PC formam a "frase completa"

> ==Juntos, CC + PC descrevem completamente um lançamento.==

| Campo | Código | Responde |
|---|---|---|
| Centro de Custo (codcen) | `1.2.5.2` | Onde? Quem? → Seletiva Pres. Prudente, dpto Comercial |
| Plano de Contas (codcdc) | `6.1.1` | O quê? → Compras de Sucatas |

**Resultado:** *"A filial de Presidente Prudente, no departamento Comercial, comprou sucata."*

---

## ~={Titulo}Navegação no SAGI — Menus Principais=~

```
	Menu Principal
	├── Financeiro 3.0
	│   ├── Movimentação
	│   │   ├── Realizações Financeiras
	│   │   ├── Realizar Pagamento
	│   │   ├── Excluir Realizações Financeiras
	│   │   └── Troca de Plano de Conta / Centro de Custo Financeiro em Lote  ← procedimento importante
	│   ├── Cadastro
	│   │   ├── Cadastrar Conta
	│   │   └── Alterar Conta
	│   └── Relatórios
	├── Compra / Entrada
	├── Venda / Saída
	├── Estoque
	├── Passagem Avulsa
	├── Fiscal
	├── Controle de Funcionário
	├── Transportes
	├── Produção
	└── Serviço 3.0
```

---

## ~={Titulo}Procedimento: Troca de Plano de Conta / CC em Lote=~

> Usado quando lançamentos foram feitos com **Plano de Contas errado** — situação frequente. Permite corrigir em lote sem precisar editar registro por registro.

**Caminho no SAGI:**
1. `Financeiro 3.0`
2. `Movimentação`
3. `Troca de Plano de Conta / Centro de Custo Financeiro em Lote`

**Filtros disponíveis:**
- **Período de:** data inicial do intervalo de lançamentos a corrigir
- **Até:** data final
- **Tipo:** escolha entre `PLANO DE CONTA` ou `CENTRO DE CUSTO`
- **Filtro:** campo de busca para localizar o código/descrição incorreto
- **Filiais:** botão para selecionar a filial a filtrar
- **Filtrar:** executa a pesquisa

**Passo a passo:**
1. Defina o período (ex: `01/03/2026` a `31/03/2026`)
2. Selecione o tipo `PLANO DE CONTA`
3. No campo Filtro, pesquise o código/descrição que está errado
4. A grade exibe os lançamentos com: **Sel** (checkbox) · **Código** · **Descrição** · **Caminho**
5. Marque os registros a transferir (ou use `Selecionar Todos`)
6. No campo inferior, informe o **novo código** destino
7. Clique em `TRANSFERIR`
8. Confirme a operação

> ⚠️ A operação é irreversível no lote. Verifique o período e o código destino antes de confirmar.

---

## ~={Titulo}Gerencial — Sintético vs. Analítico=~

A visão **Gerencial** no SAGI separa os lançamentos em centros de custos e funciona como um **coletor de valor**: cada CC analítico acumula o saldo de todas as movimentações que foram lançadas nele.

- **Sintéticos:** aparecem nas consultas como agrupadores (subtotais)
- **Analíticos:** possuem saldo próprio — são os únicos que recebem lançamentos

Ao lançar qualquer movimentação financeira, o SAGI exige que você informe:
1. Um **CC analítico** (não pode ser sintético)
2. Um **Plano de Contas analítico** (não pode ser sintético)

---

## ~={Titulo}Rateios — CFOP e CTR=~

> O rateio é o mecanismo que distribui despesas/receitas entre centros de custo quando uma nota fiscal contempla múltiplos departamentos ou filiais.

**Conceitos:**

| Sigla | O que é |
|---|---|
| **CFOP** | Código Fiscal de Operações e Prestações — identifica a natureza da operação na NF |
| **CTR** | Centro de resultado / agrupamento para rateio |
| **CTO** | Parâmetro de configuração que define qual CFOP aciona qual rateio |

**CFOPs relevantes:**
| CFOP | Uso |
|---|---|
| `5xxx` / `3xxx` | **Saídas** (vendas, remessas internas/externas) |
| `1xxx` / `2xxx` | **Entradas** (compras, retornos internos/externos) |
| `1933` | Entrada de serviço de transporte **dentro do estado** |
| `2933` | Entrada de serviço de transporte **fora do estado** |

**Configuração:**
- Parâmetro **CTO** busca o CFOP correspondente
- Busca: `CFOP` → define o tipo de operação → aciona o rateio configurado

---

## ~={Titulo}Transporte — CIF vs. FOB=~

> Define **quem é responsável pelo frete** em uma operação de compra ou venda de sucata.

| Modalidade | Quem transporta | Impacto no SAGI |
|---|---|---|
| **CIF** (Cost, Insurance and Freight) | **Transmóvel** (nos transporta) | A Transmóvel emite CTe no ATUA → NF de serviço entra no SAGI como despesa de frete (`6.6.1`) no CC de Logística |
| **FOB** (Free on Board) | **O cliente/fornecedor** busca com transporte próprio | Não gera lançamento de frete — o custo fica com o parceiro |

> Quando a operação é CIF, a Transmóvel **presta serviço para a G3S**, e a G3S reconhece o custo de frete. Isso aparece na `base.csv` como `descdc = TRANSPORTE DE SUCATA` ou `FRETE DE TERCEIROS` no CC de Logística da filial.

**Apuração do Serviço de Transporte:**
- O SAGI permite apurar o serviço de transporte **por estabelecimento comercial** (filial)
- Isso permite comparar o custo de frete por praça e por período

---

## ~={Titulo}Dicas de Uso Rápido=~

| Situação | O que fazer |
|---|---|
| Lançamento no plano de contas errado | Usar **Troca em Lote** (Financeiro 3.0 > Movimentação) |
| Quero saber todos os gastos de um veículo | Filtrar pelo CC do veículo (ex: `1.2.5.6.1` para EWU6003) |
| Quero ver receitas de uma filial | Filtrar CCs `2.x.filial` (ex: `2.2.5` para Seletiva PP) |
| Preciso conferir um lançamento específico | Usar o campo `documento` para buscar pelo número da NF/boleto |
| Quero comparar filiais por categoria | Agrupar por `descen` (divisão/cidade) + `descdc` (categoria) |
| Saldos históricos ou migrados | Datas `1800-01-01` e documentos `SALDO ADT*` são registros legado |

---

## ~={Titulo}Referências Visuais=~

Imagens do SAGI salvas em `01-Anexos/`:

![[sagi-anotacoes-01.png]]
*Anotações: estrutura N.N.N.N e tipos de movimentação*

![[sagi-anotacoes-02.png]]
*Anotações: G3S, G8S, GSE e Transmóvel*

![[sagi-anotacoes-03.png]]
*Anotações: sistemas SAGI/ATUA e rateios CFOP*

![[sagi-anotacoes-04.png]]
*Anotações: CC + PC (Centro de Custo e Plano de Contas)*

![[sagi-anotacoes-05.png]]
*Procedimento de troca em lote (cliques 1, 2, 3)*

![[sagi-menu-financeiro.png]]
*Screenshot: Menu Financeiro 3.0 > Movimentação*

![[sagi-troca-plano-contas.png]]
*Screenshot: Tela de Troca de Plano de Contas em Lote*

___

[[Estrutura Empresarial G3S]] · [[Divisões]] · [[Tipos de Movimentação]] · [[Analise Base Financeira]] · [[00 - Índice Controladoria]]
