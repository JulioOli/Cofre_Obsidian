---
tags:
  - note
  - tools
---
05/05/2026 - 13:50

## ~={Titulo}O que faz=~

Lê a exportação do ODBC em `02-Referencias/Meus_Dados/base.csv`, aplica regras configuráveis em `02-Referencias/Meus_Dados/regras_auditoria.yaml` e gera um relatório Excel com possíveis inconsistências em lançamentos recorrentes.

O objetivo é rodar isso semanalmente para apontar situações como:

- ausência de lançamento esperado no período
- valor fora do padrão
- duplicidade
- fornecedor/cliente fora do esperado
- frequência fora da cadência normal
- valor zerado em conta que normalmente recebe valor

## ~={Titulo}Arquivos envolvidos=~

- Script principal: `scripts/auditoria_lancamentos.py`
- Base de entrada: `02-Referencias/Meus_Dados/base.csv`
- Regras: `02-Referencias/Meus_Dados/regras_auditoria.yaml`
- Baseline de fechamento: `02-Referencias/Meus_Dados/Lancamentos_CustosFixos_e_DespesasFixas_Fechamento2026.xlsx`
- **Saída padrão (canvas):** `~/.cursor/projects/.../canvases/auditoria-lacunas.canvas.tsx` (abre na IDE lado a lado com o chat)
- Saída opcional (Excel): `02-Referencias/relatorio_auditoria_AAAA-MM-DD.xlsx` (use `--excel`)
- Notebook de apoio: `04-Notebooks/Auditorias/auditoria_lancamentos.ipynb`

### Contas foco definidas na reunião

- `7.5.1` Água e Esgoto
- `7.5.2` Energia Elétrica
- `7.5.20` Internet
- `7.5.3` Telecomunicações
- `7.5.31` Aluguéis Administrativo
- `5.1` Locação de Máquinas e Equipamentos
- `7.3.23` Honorários PJ

## ~={Titulo}Regra importante da base=~

Registros com `ite_pagrec_vencimento = 1800-01-01` são tratados como **migrados** e ficam fora da análise temporal por padrão.

Isso evita que saldos antigos ou migrações do sistema distorçam os padrões semanais/mensais.

## ~={Titulo}Passo a passo=~

### ~={blue}1) Abrir o PowerShell na raiz do projeto=~

```powershell
cd C:\Users\julio.santana\Documents\Projects\Cofre_Trabalho
```

### ~={blue}2) Ativar o ambiente virtual=~

Se estiver usando o `.venv` do projeto:

```powershell
.\.venv\Scripts\Activate.ps1
```

### ~={blue}3) Atualizar o=~ `base.csv`

Antes de rodar, substituir/atualizar:

```text
02-Referencias/Meus_Dados/base.csv
```

Esse arquivo deve vir da consulta mais recente do ODBC.

### ~={blue}4) Conferir ou ajustar as regras=~

Abrir:

```text
02-Referencias/Meus_Dados/regras_auditoria.yaml
```

Cada item dentro de `regras:` representa uma verificação.

### ~={blue}5) Rodar o script=~

```powershell
python scripts/auditoria_lancamentos.py
```

### ~={blue}6) Conferir o resultado=~

Por padrão, o script atualiza o canvas:

```text
~/.cursor/projects/.../canvases/auditoria-lacunas.canvas.tsx
```

Para gerar também o Excel detalhado:

```powershell
python scripts/auditoria_lancamentos.py --ref-date "2026-05-05" --excel
```

No Excel, as abas principais são:

- `00_painel` com visão executiva (total, lacunas e ranking por conta)
- `01_lacunas` com foco em faltas de lançamento (`ausencia_mensal` e `frequencia`)
- `resumo` com contagem por tipo de alerta e severidade
- uma aba por tipo de anomalia, por exemplo `ausencia_mensal`, `desvio_valor`, `duplicata`, etc.

## ~={green}Exemplo de execução com data de referência=~

Útil para simular uma execução semanal em uma data específica:

```powershell
python scripts/auditoria_lancamentos.py --ref-date "2026-05-05"
```

## ~={orange}Flags opcionais=~

```powershell
python scripts/auditoria_lancamentos.py `
  --csv "02-Referencias/Meus_Dados/base.csv" `
  --regras "02-Referencias/Meus_Dados/regras_auditoria.yaml" `
  --ref-date "2026-05-05" `
  --out "02-Referencias/relatorio_auditoria_2026-05-05.xlsx"
```

| Flag | O que faz |
|---|---|
| `--csv` | Define o caminho do arquivo de entrada |
| `--regras` | Define o caminho do arquivo YAML de regras |
| `--ref-date` | Data de referência para verificações temporais (`YYYY-MM-DD`) |
| `--out` | Define manualmente o arquivo Excel de saída |
| `--usar-migrados` | Inclui registros migrados na análise |
| `--fechamento` | Caminho do arquivo de fechamento usado como baseline por credor/valor |
| `--ignorar-fechamento` | Desativa o uso do fechamento como referência |
| `--canvas-out` | Caminho onde o canvas (.canvas.tsx) será gerado |
| `--excel` | Gera também o relatório Excel detalhado (saída padrão é canvas) |
| `--sem-canvas` | Pula a geração do canvas |
| `--template-excel` | Arquivo Excel usado como template de formatação visual (fontes, cores, larguras, etc.) |
| `--sem-template-excel` | Desativa a aplicação de formatação via template |

### ~={blue}Template de formatação do Excel=~

Se você já ajustou visualmente um relatório (`negrito`, `cores`, `largura de colunas`, `tamanho de fonte`), ele pode ser reutilizado como template.

Exemplo:

```powershell
python scripts/auditoria_lancamentos.py `
  --ref-date "2026-05-05" `
  --excel `
  --template-excel "02-Referencias/relatorio_auditoria_2026-05-06.xlsx"
```

Com isso, o script gera o Excel novo com os dados atualizados e reaplica a formatação das abas em comum do arquivo template.

## Estrutura das regras

O arquivo `regras_auditoria.yaml` usa o bloco:

```yaml
regras:
  - nome: "Conta de Agua - exemplo"
    tipo: ausencia_mensal
    codcdc: "7.X.XX"
    filial: "G3S PRUDENTE"
    dia_esperado: 10
    tolerancia_dias: 5
    severidade: ALTA
```

### ~={pink}Tipos de regra suportados=~

#### `ausencia_mensal`

Aponta quando um lançamento esperado no mês não apareceu na janela definida.

Campos usuais:

- `codcdc`
- `filial`
- `dia_esperado`
- `tolerancia_dias`
- `severidade`

#### `desvio_valor`

Aponta valores fora do intervalo esperado.

Campos usuais:

- `codcdc`
- `filial` (opcional)
- `codigo_pessoa` (opcional)
- `valor_min`
- `valor_max`
- `severidade`

#### `duplicata`

Procura lançamentos repetidos em uma janela curta.

Campos usuais:

- `codcdc`
- `janela_dias`
- `severidade`

#### `fornecedor_inesperado`

Sinaliza quando a conta aparece com pessoa diferente da esperada.

Campos usuais:

- `codcdc`
- `codigo_pessoa` ou `nome_regex`
- `severidade`

#### `frequencia`

Compara a cadência entre lançamentos.

Campos usuais:

- `codcdc`
- `periodicidade` (`semanal`, `quinzenal`, `mensal`)
- `tolerancia_dias`
- `severidade`

#### `valor_zero`

Aponta registros zerados em contas que normalmente têm valor.

Campos usuais:

- `codcdc`
- `tolerancia_valor_zero`
- `severidade`

## ~={Titulo}Como preencher=~ `codcdc`

O campo `codcdc` aceita padrões simples:

- `7.5.22` -> conta exata
- `7.X.XX` -> aceita dígitos variáveis
- `7.5.*` -> aceita qualquer sequência após `7.5.`

## ~={Titulo}Como usar na rotina semanal=~

### Fluxo sugerido

1. Atualizar o `base.csv` com a exportação recente do ODBC.
2. Revisar se as regras continuam válidas.
3. Rodar o script.
4. Abrir o Excel gerado.
5. Validar os alertas com a equipe/gestor.
6. Ajustar regras quando surgirem novas premissas da operação.

## ~={Titulo}Quando mexer no YAML=~

Editar `regras_auditoria.yaml` quando for necessário:

- incluir uma nova conta para monitoramento
- mudar tolerância de valor
- alterar o dia esperado
- restringir por filial
- trocar a severidade
- incluir novas exceções de fornecedor

## ~={Titulo}Quando usar o notebook=~

Abrir `04-Notebooks/Auditorias/auditoria_lancamentos.ipynb` quando precisar:

- explorar uma conta antes de criar regra
- conferir distribuição por mês
- validar se uma anomalia faz sentido
- testar regras sem depender só do Excel final

## ~={Titulo}Observações práticas=~

- O script foi preparado para ser **flexível**, porque as premissas ainda podem mudar após a reunião.
- O valor real das regras deve ser refinado com base no que for definido pelo gestor.
- O melhor uso é manter o script estável e ajustar o comportamento principalmente pelo YAML.

___
[[plano de conta]]
[[centro de custo]]
[[Analise Base Financeira]]
