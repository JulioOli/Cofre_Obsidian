# Relatório Liebherr × Hyundai

## Dashboard Excel (reunião ~10 min) — recomendado

```powershell
# Planilha completa (nova ou sobrescreve tudo)
.\.venv\Scripts\python.exe outputs\relatorios\comparativo_liebherr_hyundai\export_dashboard_excel.py

# Só adiciona/atualiza aba Mix por conta (preserva suas edições nas demais abas)
.\.venv\Scripts\python.exe outputs\relatorios\comparativo_liebherr_hyundai\export_dashboard_excel.py --mix-only
```

Saída: `outputs/tabelas/dashboard_liebherr_hyundai.xlsx`

| Aba | Uso |
|-----|-----|
| **Apresentação** | KPIs + 4 gráficos para abrir a reunião |
| **Mix por conta** | Gráficos nativos: % do volume da marca e R$/máquina (rótulos nas barras; legenda clicável) |
| **Gasto por Local** | Expandir/recolher Local → Marca → Máquina; filtros no cabeçalho |
| **Resumo Local×Marca** | Pivot pronto + gráfico de barras |
| **Série mensal** | Gráfico de linhas nativo (Excel) |
| **Fonte_Dados** | Base para Tabela Dinâmica + Slicers + Gráfico Dinâmico |
| **Como usar** | Passo a passo (pivot como na planilha do diretor) |

Também gerado pelo **Passo 10** do notebook `analise_comparativa_liebherr_hyundai.ipynb`.

---

## Relatório LaTeX (PDF completo)

Relatório executivo para impressão/PDF, sem código Python.

## Pré-requisitos

1. Rodar **Run All** em `04-Notebooks/analise_comparativa_liebherr_hyundai.ipynb` (até o **Passo 9 — Exportar LaTeX**).
2. Ter uma distribuição LaTeX instalada ([MiKTeX](https://miktex.org/) ou [TeX Live](https://www.tug.org/texlive/)).

## Gerar o PDF

### WSL / Linux (bash)

Na raiz do repositório (`Cofre_Trabalho`):

```bash
# 1) venv do projeto (Linux — não use .venv\Scripts\activate)
source .venv/bin/activate

# 2) pasta do relatório (barras /, não \)
cd outputs/relatorios/comparativo_liebherr_hyundai

# 2b) Gerar/copiar figuras para ./figuras/ (obrigatório antes do pdflatex)
# Na raiz do repo, com venv ativo:
# python outputs/relatorios/comparativo_liebherr_hyundai/sincronizar_figuras.py
# Ou já nesta pasta:
python3 sincronizar_figuras.py

# 3) LaTeX — instalar uma vez se pdflatex não existir
# sudo apt update && sudo apt install -y texlive-latex-extra texlive-lang-portuguese

pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

### Windows (PowerShell)

```powershell
cd outputs\relatorios\comparativo_liebherr_hyundai
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

O arquivo `main.pdf` será criado nesta pasta.

> **Antes de compilar:** rode **Run All** no notebook (Passos 1–9) para gerar as figuras novas (`01_volume_por_ano.png`, `04_serie_mensal_2025.png`, etc.). Sem isso o `pdflatex` falha ao incluir imagens ausentes.

## Arquivos

| Arquivo | Função |
|---------|--------|
| `main.tex` | Estrutura do relatório e figuras |
| `preamble.tex` | Pacotes e configuração |
| `capa.tex` | Capa e sumário |
| `dados.tex` | Data, período e autoria (gerado pelo notebook) |
| `insights.tex` | Bullets do resumo (gerado) |
| `kpi.tex` | Tabela de KPIs (gerado) |
| `conclusao.tex` | Parágrafo de fechamento (gerado) |
| `localizacao.tex` | Tabelas de localização do parque (gerado) |
| `gasto_mensal_maquinas.tex` | Tabela máquina × mês (gerado) |

Figuras PNG: `outputs/figuras/liebherr_hyundai/` (referenciadas por caminho relativo).

## Personalizar

- Edite `conclusao.tex` manualmente após a exportação para incluir recomendações em linguagem de gestão.
- Para omitir um gráfico, comente o bloco `figure` correspondente em `main.tex`.
