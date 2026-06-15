---
tags:
  - note
  - controladoria
  - maquinas
  - G3S
  - RSE
atualizado: 11/06/2026
---
11/06/2026 - 11:30

# ~={Titulo}Quantidade de escavadeiras Hyundai e Liebherr por filial=~

> Contagem de **escavadeiras** (placas `EHH` / `EHL`) por localização operacional.
> Fonte: aba `BASE DADOS` de `02-Referencias/Custos-Maquinas/Entre Empresas Abril 2026.xlsx` (atualizado abr/2026).
> Ver também [[Entre Empresas - Faturamento de Máquinas Intercompany]].

---

## ~={Titulo}Parque total (abr/2026)=~

| Marca | Qtd. |
|---|---|
| ~={yellow}Hyundai=~ | **17** |
| ~={blue}Liebherr=~ | **7** |
| **Total escavadeiras** | **24** |

> ⚠️ A placa `EHH0044` (Joinville/Tupy) está sem `MARCA` preenchida na planilha; contada como Hyundai pelo prefixo `EHH` e pelo cadastro em `relatorio_marcas_maquinas_base.xlsx`.

---

## ~={Titulo}Por localização (planilha)=~

| **Localização** | **Cidade / unidade** | ~={yellow}Hyundai=~ | ~={blue}Liebherr=~ |
|---|---|---:|---:|
| SP - PRUDENTE - SUCATA + RESERVA | Prudente | 3 | 2 |
| PR - MARINGÁ + CIDADE ALTA | Maringá | 3 | 2 |
| PR - LONDRINA | Londrina | 3 | — |
| MS - DOURADOS | Dourados | 2 | 1 |
| MS - CAMPO GRANDE | Campo Grande | 2 | — |
| RJ - BARRA MANSA | Barra Mansa (AM Bar) | 2 | — |
| SC - JOINVILLE | Tupy (contrato externo) | 1 | 1 |
| RSE | Pátio RSE / manutenção | 1 | 1 |

### ~={Titulo}Placas por local=~

| Local | Hyundai (`EHH`) | Liebherr (`EHL`) |
|---|---|---|
| Prudente | EHH0005, EHH0007, EHH0046 | EHL0028, EHL0070 |
| Maringá | EHH0004, EHH0006, EHH0039 | EHL0014, EHL0043 |
| Londrina | EHH0002, EHH0008, EHH0040 | — |
| Dourados | EHH0003, EHH0036 | EHL0042 |
| Campo Grande | EHH0019, EHH0038 | — |
| Barra Mansa | EHH0015, EHH0037 | — |
| Tupy / Joinville | EHH0044 | EHL0041 |
| Pátio RSE | EHH0009 | EHL0013 |

---

## ~={Titulo}Apelidos operacionais=~

Algumas máquinas têm **nome operacional** usado em relatórios de custo, mas na planilha intercompany aparecem em outra `LOCALIZAÇÃO`:

| Apelido | Placa | Marca | Local na planilha |
|---|---|---|---|
| Matheus | EHH0007 | Hyundai | Prudente (Sucata) |
| Multi Aço | EHH0037 | Hyundai | Barra Mansa |

> Esses apelidos **não são filiais separadas** na base intercompany — já estão contabilizados em Prudente e Barra Mansa.

---

## ~={Titulo}Correções em relação à versão anterior=~

| Local | Antes | Agora | Motivo |
|---|---|---|---|
| Prudente | H 2 · L 1 | H 3 · L 2 | Inclui `EHH0007` (Matheus) e `EHH0005` (Reserva); Liebherr `EHL0028` e `EHL0070` em Sucata |
| Londrina | H 2 · L — | H 3 · L — | Terceira escavadeira `EHH0002` na base |
| Pátio de Manutenção | H 0 · L 2 | H 1 · L 1 | Local `RSE` na planilha (`EHH0009`, `EHL0013`); Liebherr de Prudente não são pátio |
| Matheus / Multi Aço | linhas próprias | incorporados | Máquinas existem, mas a localização oficial é Prudente e Barra Mansa |

___

[[Entre Empresas - Faturamento de Máquinas Intercompany]] · [[Filiais (nível 2)]] · [[Estrutura Empresarial G3S]] · [[Divisões (nível 1)]]
