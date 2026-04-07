---
tags:
  - note
  - controladoria
  - auditoria
  - bcbi
  - checklist
---
06/04/26 - 09:55


___

# ~={Titulo}Checklist de Auditoria BCBI x Base=~

Objetivo: usar o BCBI como termometro de anomalias e confirmar na `base.csv` se a estranheza vem de classificacao contabil, lancamento operacional, rateio/duplicidade ou regra de agrupamento do BI.

---

### ~={Titulo}Checklist rapido mensal (15-30 min)=~

- [x] Validar filtro do BCBI (divisao, mes e unidade correta).
- [ ] Anotar os cards com maior diferenca percebida (ex.: custo fixo, custo variavel, internet, manutencao, viagens).
- [ ] Definir 3 prioridades de investigacao (maior valor, maior variacao percentual e item recorrente).
- [x] Abrir a `base.csv` e filtrar o mesmo periodo do BCBI.
- [ ] Verificar se o desvio esta em `codcdc/descdc`, no `codcen`, na descricao historica ou em duplicidade/rateio.
- [ ] Classificar o achado: ==erro de lancamento==, ==inconsistencia de cadastro==, ==regra BI==, ou ==sem impacto material==.

---

### ~={Titulo}Roteiro de investigacao por anomalia=~

#### ~={Titulo}1) Confirmacao do sintoma=~
- [ ] Qual indicador no BCBI parece estranho?
- [ ] Qual valor esperado x realizado?
- [ ] Qual mes/filial/divisao esta em foco?

#### ~={Titulo}2) Recorte na base=~
- [ ] Filtrar periodo identico ao BCBI.
- [ ] Filtrar por conta principal (ex.: `7.5.20 INTERNET`).
- [ ] Expandir para contas correlatas (ex.: `7.5.3 TELECOMUNICACOES`) para capturar classificacoes alternativas.

#### ~={Titulo}3) Testes de causa raiz=~
- [ ] **Classificacao contabil:** conta esperada x conta lancada (`codcdc/descdc`).
- [ ] **Centro de custo:** verificar se `codcen/descen` condiz com a natureza do gasto.
- [ ] **Texto historico:** procurar palavras-chave que indiquem mudanca de contexto (ex.: internet, telefonia, link, embratel).
- [ ] **Duplicidade/rateio:** mesmo documento + filial + valor + vencimento, validando soma.
- [ ] **Recorrencia:** mesmo fornecedor repetindo a mesma inconsistência em meses seguidos.

#### ~={Titulo}4) Fechamento do achado=~
- [ ] Registrar impacto estimado (R$ e quantidade de lancamentos).
- [ ] Definir acao: corrigir no SAGI, alinhar cadastro, ou abrir apontamento para equipe do BI.
- [ ] Guardar evidencia (filtros usados, documentos, fornecedores e contas envolvidas).

---

### ~={Titulo}Checklist especifico: Internet em custo fixo/variavel=~

- [ ] Levantar todos os lancamentos com `descdc = INTERNET` (`codcdc 7.5.20`).
- [ ] Procurar internet descrita em outras contas (ex.: `7.5.3 TELECOMUNICACOES` com historico contendo "INTERNET").
- [ ] Separar por fornecedor (Claro, Telmex, Digital Net, etc.) para achar padrao de classificacao.
- [ ] Validar se houve troca de conta por filial (ex.: uma filial usa `7.5.20`, outra usa `7.5.3` para servicos parecidos).
- [ ] Confirmar impacto no agrupamento de custo fixo vs variavel visto no BCBI.
- [ ] Se a base estiver coerente, sinalizar como possivel regra de agrupamento da camada BI.

---

### ~={Titulo}Modelo de registro do achado=~

| Campo | Preenchimento |
|---|---|
| Data da analise | dd/mm/aaaa |
| Indicador BCBI | Ex.: Internet Total |
| Sintoma | Ex.: valor em custo fixo acima do padrao |
| Escopo | mes, divisao, filial |
| Evidencia na base | conta, cc, documento, fornecedor |
| Causa provavel | lancamento / cadastro / regra BI |
| Impacto estimado | R$ e qtd lancamentos |
| Proxima acao | corrigir SAGI / reportar BI / monitorar |

---

### ~={Titulo}Criterio de prioridade=~

- 🔴 Alta: impacto > R$ 100.000,00 ou distorcao relevante em indicador executivo.
- 🟡 Media: impacto entre R$ 10.000,00 e R$ 100.000,00, sem risco de decisao imediata.
- 🟢 Baixa: impacto pequeno, mas recorrente (ajuste de higiene de cadastro/processo).

___

[[Guia SAGI]]
[[Analise Base Financeira]]
[[Tipos de Movimentação]]
