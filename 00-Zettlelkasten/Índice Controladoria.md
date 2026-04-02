---
tags:
  - note
  - controladoria
  - indice
  - G3S
---
24/03/2026 - 09:22

# ~={Titulo}Índice — Controladoria G3S=~

> Notas de referência geradas a partir dos arquivos oficiais do sistema Sygecom.
> **Última atualização:** 25/03/2026
> Quando os arquivos fonte forem atualizados, solicitar revisão das notas abaixo.

---

## Navegação Rápida

| Nota                          | Descrição                                                                    |
| ----------------------------- | ---------------------------------------------------------------------------- |
| [[Tipos de Movimentação]]     | Natureza dos lançamentos: Despesa, Receita, Custo, Investimento, etc.        |
| [[Divisões]]                  | Unidades de negócio do Grupo (Seletiva, Bracofer, Transmove, Ekipa…)         |
| [[Filiais]]                   | Filiais por divisão com seus códigos de centro de custo                      |
| [[Departamentos]]             | Departamentos disponíveis por tipo de unidade                                |
| [[Estrutura Empresarial G3S]] | Relação entre G3S, G&S, GSE/RSE, Transmóvel e demais CNPJs do grupo          |
| [[Guia SAGI]]                 | Procedimentos práticos no sistema: CC vs PC, Troca em Lote, Rateios, CIF/FOB |
| [[Analise Base Financeira]]   | Dicionário de dados, filtros e armadilhas do ODBC (base.csv)                 |

---

## Estrutura Hierárquica do Centro de Custo

O campo `descen` segue o padrão:

```
	TIPO / DIVISÃO / FILIAL / DEPARTAMENTO
```

| Nível | Dimensão | Exemplos |
|---|---|---|
| 1º dígito do código | **Tipo** | `1` = DESPESA · `2` = RECEITA |
| 2º nível (`x.X`) | **Divisão** | Seletiva, Bracofer, Transmove, Ekipa... |
| 3º nível (`x.x.X`) | **Filial/Cidade** | Dourados, Londrina, Maringá, Pres. Prudente... |
| 4º nível (`x.x.x.X`) | **Departamento** | Administrativo, Comercial, Operacional, Logística |
| 5º nível+ | **Ativo específico** | Placa de veículo, código de máquina |

---

## Resumo do Grupo

- **Empresa:** G3S Comércio e Indústria de Ferro e Aço Ltda
- **CNPJ:** 20.947.332/0004-38
- **Setor:** Reciclagem e comercialização de sucatas
- **Total de Centros de Custo:** 632
- **Total de Contas no Plano:** 238
- **Sistema:** Sygecom
- **Fonte:** `Centro de Custo.pdf` · `Plano de Contas.pdf` (02-Referencias) — impressos em 25/03/2026

___
