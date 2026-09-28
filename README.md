# Cofre Obsidian + Agentes de IA

Template de cofre (vault) Obsidian pensado para estudos técnicos no estilo **Zettelkasten**, com formatação consistente e regras prontas para agentes de IA (como o Cursor) criarem, editarem e auditar notas no mesmo padrão.

A ideia é: você estuda no Obsidian; a IA trabalha **dentro** do cofre, respeitando a estrutura, os links e o formato das notas.

---

## O que este template oferece

- Estrutura de pastas clara (notas, anexos, referências, templates)
- Convenção de escrita Zettelkasten com links `[[wikilinks]]`
- Template de nota pronto (`03-Templates/New note.md`)
- Regras para agentes de IA em `.cursorrules` (Cursor lê automaticamente)
- Plugins e tema já configurados em `.obsidian/`

---

## Pré-requisitos

1. [Obsidian](https://obsidian.md/) instalado
2. (Opcional, mas recomendado) [Cursor](https://cursor.com/) ou outro editor/agente que aceite regras de projeto no repositório
3. Git, se for clonar o repositório

---

## Como começar

### 1. Obter o cofre

```bash
git clone https://github.com/JulioOli/Cofre_Obsidian.git
```

Ou baixe o ZIP e extraia em qualquer pasta.

### 2. Abrir no Obsidian

1. Abra o Obsidian
2. **Open folder as vault** → selecione a pasta do projeto
3. Se pedir, confie e ative os **community plugins** (eles já vêm listados em `.obsidian/`)

### 3. Abrir com um agente de IA (Cursor)

1. Abra a **mesma pasta do cofre** como projeto no Cursor
2. O arquivo `.cursorrules` passa a orientar o agente: formato das notas, links, pastas e comportamento esperado
3. Peça coisas como: criar notas a partir de um PDF, revisar inconsistências, expandir um conceito, gerar conexões entre notas

> Dica: use o Obsidian para ler/navegar e o Cursor para produzir ou refatorar notas em lote.

---

## Estrutura do cofre

| Pasta | Função |
| --- | --- |
| `00-Zettlelkasten/` | Notas atômicas de conceitos (base do sistema e dos flashcards) |
| `01-Anexos/` | Imagens e anexos (`![[../01-Anexos/arquivo.png]]`) |
| `02-Referencias/` | PDFs, aulas, artigos e material de apoio |
| `03-Templates/` | Modelos de nota (ex.: `New note.md`) |
| `.cursorrules` | Regras que o agente de IA deve seguir |
| `.obsidian/` | Configuração do Obsidian (plugins, tema, hotkeys) |

Novas notas vão por padrão para `00-Zettlelkasten/`. Anexos vão para `01-Anexos/`.

---

## Formato das notas

Toda nota `.md` deve seguir o modelo de `03-Templates/New note.md`:

```markdown
---
tags:
  - note
  - [tags do domínio, se precisar]
---
DD/MM/YY - HH:MM

### ~={Titulo}Título da Seção=~

Texto da nota com ==destaques== e ~={orange}highlights coloridos=~.

___

[[Nota relacionada]]
[[Outra nota|texto do link]]
```

### Convenções importantes

- **Títulos:** `### ~={Titulo}...=~` e subtítulos com `####`
- **Highlights:** `~={cor}texto=~` (ex.: `orange`, `yellow`, `blue`, `cyan`, `red`, `green`, `cinza`)
- **Destaque simples:** `==texto==`
- **Links internos:** `[[nome do arquivo]]`
- **Fim da nota:** `___` + links relacionados

### Regras de linkagem (Zettelkasten)

- Se **X faz parte de Y** → a nota de X aponta para Y
- Se **X é pré-requisito de Y** → a nota de Y aponta para X
- Conceitos em `00-Zettlelkasten/` devem ser **breves e atômicos** (bons para flashcards)
- Se uma nota crescer demais, peça para dividir em subconceitos com links entre eles

---

## Plugins recomendados

Já configurados neste cofre:

| Plugin | Para quê |
| --- | --- |
| **Fast Text Color** | Cores `~={cor}texto=~` nos títulos e highlights |
| **Dataview** | Consultas e listagens a partir de metadados |
| **TagFolder** | Navegação por tags |
| **Admonition** | Blocos de chamada / callouts |
| **Hover Editor** | Editar notas em popover |
| **Recent Files** | Acesso rápido aos arquivos recentes |
| **Quick Latex** | Atalhos de LaTeX |
| **Icon Folder** | Ícones nas pastas |
| **Text Format** / **Enhanced Symbols Prettifier** | Formatação e símbolos |

Tema em uso: **Things** (com snippets CSS em `.obsidian/snippets/`).

Se algum plugin não carregar após clonar, vá em **Settings → Community plugins** e reinstale/ative o que faltar.

---

## Fluxo sugerido: estudar + IA

### No dia a dia (Obsidian)

1. Coloque PDFs/aulas em `02-Referencias/`
2. Crie notas atômicas em `00-Zettlelkasten/`
3. Conecte conceitos com `[[links]]`
4. Use tags no frontmatter para filtrar por disciplina/assunto

### Com o agente (Cursor ou similar)

Exemplos de pedidos úteis:

- *"Cria uma nota Zettelkasten sobre [conceito], no formato do template, com links para notas relacionadas."*
- *"Analisa as notas em `00-Zettlelkasten` e lista inconsistências ou conceitos citados sem nota própria."*
- *"A partir do PDF em `02-Referencias/...`, extrai os conceitos principais e gera notas atômicas linkadas."*
- *"Expande a nota [[X]] sem quebrar a formatação `~={ }=~` nem os links existentes."*
- *"Divide essa nota longa em subconceitos e ajusta os links bidirecionais."*

O `.cursorrules` já instrui o agente a:

- preservar frontmatter, tags e formatação colorida
- manter links bidirecionais
- considerar o conteúdo de `02-Referencias/`
- criar notas curtas e consistentes para estudo/flashcards
- apontar conflitos técnicos de forma clara

---

## Adaptando para outro domínio

O template nasceu em contexto técnico (ex.: redes), mas funciona para qualquer área:

1. Ajuste as tags no frontmatter ao seu domínio
2. Mantenha a pasta `00-Zettlelkasten/` para conceitos-base
3. Use `02-Referencias/` para o material-fonte
4. Se precisar, edite `.cursorrules` para refletir terminologia e hábitos do seu campo — o agente seguirá essas regras

---

## Boas práticas

- Prefira **uma ideia por nota**
- Nomeie arquivos de forma descritiva (e estável)
- Sempre termine a nota com links relacionados
- Não duplique o mesmo conceito em vários arquivos; linke
- Trate PDFs em `02-Referencias/` como fonte; as notas são a síntese ativa
- Versionar o cofre com Git ajuda a acompanhar o que a IA alterou

---

## Estrutura mínima para um fork limpo

Se for usar isto como template pessoal e quiser começar do zero:

1. Clone o repositório
2. Esvazie `00-Zettlelkasten/` (mantenha a pasta)
3. Limpe `01-Anexos/` e `02-Referencias/` conforme quiser
4. Mantenha `03-Templates/`, `.cursorrules` e `.obsidian/`
5. Abra no Obsidian + no Cursor e comece a escrever

---

## Objetivo

Manter um sistema de notas **interconectado, legível e tecnicamente consistente**, em que humanos e agentes de IA colaboram no mesmo formato — facilitando estudo, revisão e criação de flashcards a partir do próprio cofre.
