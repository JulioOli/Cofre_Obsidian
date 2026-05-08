---
tags:
  - note
  - tools
---
07/05/2026 - 12:18

## ~={Titulo}O que faz=~

Lê o relatório de despesas do sistema **ATUA** (`Relatorio_Despesas_Sistema-ATUA_{MM}.xls`, GSL Logistica) e converte para o layout do fechamento SAGI (`FECHAMENTO_ODBC_{AAAA}_{MM}.xlsx`).

A GSL Logistica é tratada no SAGI como a divisão **1.4 TRANSMOVE GSL**, com 4 filiais (`1.4.1` Presidente Prudente, `1.4.2` Dourados, `1.4.3` Maringá, `1.4.4` Barueri) e 2 setores analíticos (`.1` TRANSPORTE / `.2` ADMINISTRATIVO). O notebook resolve o de-para entre os códigos do ATUA e do SAGI e gera o Excel pronto pra colar no fechamento.

## ~={Titulo}Escopo desta nota=~

Esta nota é **somente** para `04-Notebooks/Fechamento/normalizar_atua_despesas.ipynb` (despesas do ATUA).

Existem notebooks irmãos pra outros recortes do mesmo sistema (`receitas`, `custo_frete`); o fluxo é parecido, mas as regras de mapeamento e os filtros de histórico são específicos de cada um.

## ~={Titulo}Arquivos envolvidos=~

- Notebook: `04-Notebooks/Fechamento/normalizar_atua_despesas.ipynb`
- Entrada: `02-Referencias/ATUA/Relatorio_Despesas_Sistema-ATUA_{MM}.xls`
- Modelo de colunas: `02-Referencias/FECHAMENTO_ODBC_{AAAA}_{MM}.xlsx`
- Saída: `02-Referencias/ATUA/ATUA_despesas_fechamento_{MM}-{AAAA}.xlsx`

## ~={red}IMPORTANTE - Limpar o XLS antes de rodar=~

O export do ATUA vem com **uma linha de totais antes do cabeçalho**. Se você rodar o notebook direto no arquivo recém-baixado, ele lê o cabeçalho errado e quebra (ou pega colunas vazias).

### ~={blue}Passos da limpeza=~

1. Abrir o `Relatorio_Despesas_Sistema-ATUA_{MM}.xls` no Excel ou LibreOffice Calc.
2. **Excluir a primeira linha** da planilha (a linha de totais, acima da linha que começa com `dt_lancamento`, `cd_caixa`, `cd_pessoa_favorecido`, ...).
3. Salvar o arquivo no mesmo formato (`.xls`).
4. Fechar o Excel (importante: se o arquivo ficar aberto, a leitura do notebook pode falhar com `PermissionError`).

> Bônus: o ato de re-salvar pelo Excel também conserta o `CompDocError: Workbook corruption` que às vezes aparece nos `.xls` gerados pelo ATUA (o stream OLE2 vem inconsistente direto do sistema).

Depois dessa limpeza, a primeira linha do `.xls` deve ser exatamente o cabeçalho (`dt_lancamento`, `cd_caixa`, ...).

## ~={Titulo}Passo a passo=~

### ~={blue}1) Garantir que os arquivos de referência existem=~

Em `02-Referencias/`:

- `FECHAMENTO_ODBC_{AAAA}_{MM}.xlsx` - usado como modelo de colunas. Se o do mês corrente ainda não existir, o notebook usa automaticamente o mais recente disponível (com aviso).
- `ATUA/Relatorio_Despesas_Sistema-ATUA_{MM}.xls` - já com a primeira linha removida (ver bloco anterior).

### ~={blue}2) Abrir o notebook=~

```text
04-Notebooks/Fechamento/normalizar_atua_despesas.ipynb
```

Garanta que o kernel é o `.venv` do projeto.

### ~={blue}3) Ajustar os parâmetros da primeira célula de código=~

```python
MES_REFERENCIA = "04/2026"   # mês/ano do fechamento (formato MM/AAAA)
PERIODO_ARQUIVO = None       # use "Jan-Fev" se o relatório for consolidado de vários meses
MODELO_MES = "04/2026"       # mês do FECHAMENTO_ODBC a usar como modelo de colunas
```

Casos especiais:

- **Relatório consolidado** (ex.: `Relatorio_Despesas_Sistema-ATUA_Jan-Fev.xls`):
  preencher `PERIODO_ARQUIVO = "Jan-Fev"`. A saída fica como `ATUA_despesas_fechamento_Jan-Fev.xlsx`.
- **Modelo do mês ainda não foi gerado**: deixar `MODELO_MES` apontando pra um mês que já existe em disco, ou apenas `None` (o notebook acha o mais recente).

### ~={blue}4) Rodar célula por célula=~

A ordem das células já segue o fluxo do trabalho:

1. **Leitura do XLS** - lê a aba `base` (ou a primeira aba se `base` não existir) e mantém só as colunas usadas.
2. **Filtro de históricos** - exclui automaticamente os `cd_historico` `{225, 230, 231, 237, 238}` (Remessa, Devolução de peça, Pamcard, Center Peças & afins, Transferências entre filiais), conforme dinâmica de tratamento de despesas.
3. **Filtro `CUSTO JA ALOCADO`** - exclui linhas cuja `nm_unidade_centro_custo` contém `CUSTO JA ALOCADO` (evita duplicidade com a nota-mãe).
4. **Mapa de Centros de Custo (ATUA → SAGI)** - converte `cd_unidade` + `cd_centro_custo` para o código hierárquico do SAGI (`1.4.X.Y`).
5. **Mapa de Plano de Contas (ATUA → SAGI)** - converte `cd_historico` para `cod_conta` do SAGI.
6. **Conversão para o layout FECHAMENTO_ODBC** - monta o DataFrame final com todas as colunas do modelo.
7. **Salvamento** - grava o `.xlsx` em `02-Referencias/ATUA/`.

### ~={blue}5) Conferir o resultado=~

Procure no console por:

- `Linhas lidas: X` - tem que bater com o que aparece no ATUA depois dos filtros.
- `Linhas com CC nao mapeado: 0` e `Linhas com PC nao mapeado: 0` - **ambos têm que ser zero**. Se aparecer alguma linha não mapeada, ver bloco `Quando algo não foi mapeado` abaixo.
- `Arquivo gerado: ...ATUA_despesas_fechamento_{MM}-{AAAA}.xlsx` - é o arquivo que vai pro fechamento.

## ~={Titulo}Mapa de Centros de Custo (ATUA -> SAGI)=~

| `cd_unidade` ATUA | Filial ATUA | Filial SAGI | Código SAGI nível 2 |
|---|---|---|---|
| 8 | FROTA TERCEIRO PRUDENTE | PRESIDENTE PRUDENTE | `1.4.1` |
| 9 | PRUDENTE ADMINISTRATIVO/COMERCIAL | PRESIDENTE PRUDENTE | `1.4.1` |
| 12 | MARINGA ADMINISTRATIVO/COMERCIAL | MARINGA | `1.4.3` |
| 16 | DOURADOS ADMINISTRATIVO/COMERCIAL | DOURADOS | `1.4.2` |
| 26 | BARUERI ADMINISTRATIVO/COMERCIAL | BARUERI | `1.4.4` |

| `cd_centro_custo` ATUA | Setor SAGI | Sufixo |
|---|---|---|
| 81 (Transporte) | TRANSPORTE | `.1` |
| 95 (Sucata) | TRANSPORTE | `.1` |
| 100 (ADMINISTRATIVO/COMERCIAL) | ADMINISTRATIVO | `.2` |
| 102 (FROTA TERCEIRO PRUDENTE) | TRANSPORTE | `.1` |

> Exceção: lançamentos com `cd_historico = 31` (MULTAS DE TRANSITO) são forçados pro setor TRANSPORTE (sufixo `.1`), mesmo que o ATUA tenha lançado em ADMINISTRATIVO.

## ~={Titulo}Mapa de Plano de Contas (ATUA -> SAGI)=~

| `cd_historico` ATUA | Descrição ATUA | Código SAGI | Descrição SAGI |
|---|---|---|---|
| 15 | ENERGIA ELETRICA | `7.5.2` | ENERGIA ELETRICA |
| 16 | ALUGUEL E CONDOMINIOS | `7.5.31` | ALUGUEL ADMINISTRATIVO |
| 17 | SEGURO DE CARGAS | `6.6.4` | SEGURO DE CARGAS |
| 23 | TARIFAS BANCARIAS | `7.5.22` | DESPESAS BANCARIAS |
| 26 | ASSESSORIAS E TELECONSULTAS | `7.5.9` | CONSULTORIA |
| 31 | MULTAS DE TRANSITO | `7.1.9` | MULTAS DE TRANSITO |
| 46 | IMPOSTOS E TAXAS DIVERSAS | `7.5.17` | TAXAS |
| 62 | FRETES PAGOS | `6.6.1` | FRETE DE TERCEIROS |
| 69 | HONORARIOS CONTABEIS | `7.5.7` | HONORARIOS CONTABEIS |
| 95 | ICMS | `7.4.12` | ICMS |
| 209 | PESSOAL - INSS PATRONAL | `7.3.3` | INSS |
| 229 | PESSOAL - PRO LABORE | `7.3.12` | PRO LABORE |
| 231 | DIESEL - PAMCARD | `7.1.4` | COMBUSTIVEL - DIESEL (POSTO) |

## ~={orange}Quando algo não foi mapeado=~

Se aparecer no console:

```text
[ALERTA] Centros de Custo nao mapeados:
  cd_unidade=XX (...) | cd_centro_custo=YY (...)
```

ou

```text
[ALERTA] Planos de Contas nao mapeados:
  cd_historico=ZZ (...)
```

significa que o ATUA trouxe um código novo. Nesse caso:

1. Identificar no `02-Referencias/Plano de Contas.pdf` qual é o equivalente SAGI.
2. Adicionar a entrada no dicionário `MAPA_FILIAL` / `MAPA_DEPARTAMENTO` (centro de custo) ou `MAPA_PLANO_CONTAS` (plano de contas) na célula correspondente do notebook.
3. Re-rodar a partir da célula que define o mapa.
4. Atualizar também a tabela aqui nesta nota, pra histórico.

## ~={Titulo}Histórico de filtros aplicados=~

### Históricos desconsiderados (não vão pro fechamento)

| `cd_historico` | Descrição | Motivo |
|---|---|---|
| 225 | Remessa | Movimento entre filiais |
| 230 | Devolução de peça | Analisar caso a caso |
| 231 | DIESEL - PAMCARD | Já lançado via SAGI |
| 237 | Center Peças / Distribuidora Automotiva / Odapel / Pellegrino | Já lançado via SAGI |
| 238 | Transferências entre filiais | Não é despesa |

### Linhas com `CUSTO JA ALOCADO`

Linhas em que `nm_unidade_centro_custo` contém `CUSTO JA ALOCADO` representam custos que já foram rateados a outra filial via nota-mãe. São excluídas pra não duplicar.

## ~={Titulo}Saída esperada=~

O arquivo gerado em `02-Referencias/ATUA/ATUA_despesas_fechamento_{MM}-{AAAA}.xlsx` segue **exatamente o layout do FECHAMENTO_ODBC**, com:

- `Origem` = `Saidas (Aplicacoes)` (fixo, todo o relatório ATUA é saída)
- `Sistema` = `ATUA`
- Hierarquia completa de centros de custo (`n1` a `n4`)
- Plano de contas (`cod_conta`, `conta`, `cod_conta-descr`)
- Valor formatado em pt-BR (`R$ 1.234,56` -> `1.234,56`)
- Datas no formato `dd/mm/aaaa`

Esse arquivo deve ser anexado ao consolidado mensal de fechamento.

___
[[plano de conta]]
[[centro de custo]]
[[Estrutura Empresarial G3S]]
[[Filiais]]
[[Departamentos]]
[[Divisões]]
[[fechamento março e abril]]
