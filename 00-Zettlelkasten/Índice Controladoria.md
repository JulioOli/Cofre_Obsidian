---
tags:
  - note
  - controladoria
  - indice
  - G3S
---
24/03/2026 - 09:22

# ~={Titulo}Índice — Controladoria G3S (Seletiva)=~

> Notas de referência geradas a partir dos arquivos oficiais do sistema Sygecom.
> **Última atualização:** 18/06/2026
> Quando os arquivos fonte forem atualizados, solicitar revisão das notas abaixo.

---

## Navegação Rápida

| Nota                          | Descrição                                                                    |
| ----------------------------- | ---------------------------------------------------------------------------- |
| [[Tipos de Movimentação]]     | Natureza dos lançamentos: Despesa, Receita, Custo, Investimento, etc.        |
| [[Divisões (nível 1)]]                  | Unidades de negócio do Grupo (Seletiva, Bracofer, Transmove, Ekipa…)         |
| [[Filiais (nível 2)]]                   | Filiais por divisão com seus códigos de centro de custo                      |
| [[Departamentos (nível 3)]]             | Departamentos disponíveis por tipo de unidade                                |
| [[Estrutura Empresarial G3S]] | Relação entre G3S, G&S, GSE/RSE, Transmóvel e demais CNPJs do grupo          |
| [[Guia Sistemas]]                 | Procedimentos práticos no sistema: CC vs PC, Troca em Lote, Rateios, CIF/FOB |
| [[Analise Base Financeira]]   | Dicionário de dados, filtros e armadilhas do ODBC (base.csv)                 |
| [[Valores ODBC e Fechamento — Mapeamento de Colunas]] | Lógica de `valor_bruto`, `valor_centro`, `valor_plano` e mapeamento para o fechamento |
| [[BCBI - Classificação Analítico Plano de Contas]] | Mapeamento contas SAGI → tipo custo/receita no Analítico do BCBI (Seletiva) |

---

## Estrutura Hierárquica do Centro de Custo

O campo `descen` segue o padrão:

```
	TIPO / DIVISÃO / FILIAL / DEPARTAMENTO
```

| Referência | Dimensão | Exemplos |
|---|---|---|
| 1º bloco do código | **Tipo/Natureza** | `1` = DESPESA · `2` = RECEITA |
| 1º nível lógico (`x.X`) | **Divisão** | Seletiva, Bracofer, Transmove, Ekipa... |
| 2º nível lógico (`x.x.X`) | **Filial/Cidade** | Dourados, Londrina, Maringá, Pres. Prudente... |
| 3º nível lógico (`x.x.x.X`) | **Departamento** | Administrativo, Comercial, Operacional, Logística |
| Blocos após o 3º nível lógico | **Ativo específico** | Placa de veículo, código de máquina |

---

## Resumo do Grupo

- **Empresa:** G3S Comércio e Indústria de Ferro e Aço Ltda
- **CNPJ:** 20.947.332/0004-38
- **Setor:** Reciclagem e comercialização de sucatas
- **Total de Centros de Custo:** 632
- **Total de Contas no Plano:** 240
- **Sistema:** Sygecom
- **Fonte:** `Centro de Custo.pdf` · `Plano de Contas.pdf` (02-Referencias) — impressos em 16/06/2026
- **Novas contas (jun/2026):** `7.2.8` Material Gráfico · `7.2.9` Feiras e Exposições — ver [[Tipos de Movimentação]]

___
