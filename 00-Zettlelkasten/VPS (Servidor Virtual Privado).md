---
tags:
  - note
  - infraestrutura
  - hospedagem
  - devops
---
03/06/26 - 10:45

___

### ~={Titulo}O que é VPS=~
**VPS** (*Virtual Private Server*, em português **Servidor Virtual Privado**) é uma máquina virtual com recursos dedicados (CPU, RAM, disco, rede) que roda em hardware físico compartilhado com outros VPS, mas com **isolamento** e **controle administrativo** parecidos aos de um servidor dedicado.

Em termos práticos: você aluga um “pedaço” de servidor que se comporta como um computador Linux (ou Windows) na internet, acessível por IP e SSH, onde você instala o que quiser.

### ~={Titulo}Como funciona por baixo dos panos=~
#### ~={Titulo}Virtualização=~
Um provedor possui servidores físicos potentes. Sobre eles roda um **hypervisor** (software de virtualização, ex.: KVM, Xen, VMware, Hyper-V) que cria várias **máquinas virtuais (VM)** independentes.

| Camada | Papel |
|--------|--------|
| Hardware físico | CPU, RAM, SSD/NVMe, rede do datacenter |
| Hypervisor | Divide o hardware em VMs isoladas |
| VPS (sua VM) | Sistema operacional + seus serviços |
| Seus projetos | Site, API, banco, filas, etc. |

Cada VPS recebe uma fatia **garantida** ou **compartilhada** de recursos, conforme o plano contratado.

#### ~={Titulo}Isolamento e “privado”=~
O termo *Private* não significa que o hardware é só seu — significa que **outro cliente no mesmo host físico não enxerga seus arquivos nem processos**, desde que o provedor configure a virtualização corretamente. Você tem usuário root (Linux) ou administrador (Windows) e instala pacotes, abre portas e configura firewall.

### ~={Titulo}VPS x outras formas de hospedagem=~
| Modelo | Controle | Complexidade | Custo típico | Bom para |
|--------|----------|--------------|--------------|----------|
| **Hospedagem compartilhada** | Baixo (painel cPanel) | Baixa | Menor | Site simples, WordPress sem customização |
| **VPS** | Alto (SSH, root) | Média | Médio | Sites custom, APIs, stacks próprias |
| **Servidor dedicado** | Total no hardware | Média–alta | Alto | Carga pesada, compliance rígido |
| **PaaS** (Vercel, Railway, Render) | Deploy por Git | Baixa–média | Variável | Apps modernas sem administrar SO |
| **Serverless / FaaS** | Funções sob demanda | Baixa (lógica) | Pay-per-use | Eventos, APIs esporádicas |

~={cyan}VPS é o meio-termo clássico:=~ mais liberdade que hospedagem compartilhada, sem pagar um servidor físico inteiro.

### ~={Titulo}O que você recebe ao contratar=~
- **IP público** (fixo ou elástico, conforme provedor)
- **SO** à escolha (Ubuntu, Debian, AlmaLinux, etc.)
- **Recursos** do plano: vCPU, RAM, disco (SSD), banda
- **Acesso remoto**: SSH (Linux) ou RDP (Windows)
- **Painel opcional** do provedor (reinício, snapshot, firewall básico, DNS)

Você é responsável por **atualizar o sistema**, **segurança**, **backups** e **monitoramento** — diferente de hospedagem gerenciada, onde o provedor faz parte disso.

### ~={Titulo}Para que serve (além de site estático)=~
- Site institucional ou blog (Nginx/Apache + PHP ou estático)
- **API** backend (Node, Python/FastAPI, Go, etc.)
- **Banco de dados** (PostgreSQL, MySQL, Redis) na mesma VPS ou em outra
- **Reverse proxy** + múltiplos projetos no mesmo servidor (Traefik, Caddy, Nginx)
- Bots, cron jobs, filas (Celery, workers)
- VPN self-hosted, Git self-hosted (Gitea), ferramentas internas
- Ambiente de **homologação** espelhando produção

### ~={Titulo}Fluxo prático — hospedar um site no VPS=~
Visão em etapas do que você faria na primeira vez:

```mermaid
flowchart LR
  A[Contratar VPS] --> B[Configurar DNS]
  B --> C[SSH e hardening]
  C --> D[Instalar stack web]
  D --> E[Deploy do projeto]
  E --> F[HTTPS com Let's Encrypt]
  F --> G[Backup e monitoramento]
```

#### ~={Titulo}1. Contratar e acessar=~
1. Escolher provedor (DigitalOcean, Linode/Akamai, Hetzner, Vultr, AWS Lightsail, OVH, etc.) e região próxima aos usuários (ex.: São Paulo se público BR).
2. Criar a VPS com **Ubuntu LTS** (padrão comum para tutoriais).
3. Anotar IP público; configurar chave SSH no painel (evitar senha só em texto).
4. Conectar: `ssh root@SEU_IP` (ou usuário não-root após criar).

#### ~={Titulo}2. Domínio e DNS=~
No registrador do domínio (Registro.br, Cloudflare, etc.):
- Registro **A** apontando `seudominio.com` → IP da VPS
- Opcional: **AAAA** se usar IPv6; **CNAME** para `www` se preferir

Propagação DNS pode levar minutos a algumas horas.

#### ~={Titulo}3. Preparar o servidor (mínimo sensato)=~
- `apt update && apt upgrade` (manter pacotes atuais)
- Criar usuário sudo sem login root direto
- Firewall (**ufw**): liberar 22 (SSH), 80 (HTTP), 443 (HTTPS)
- Fail2ban ou equivalente contra brute-force em SSH

#### ~={Titulo}4. Stack web — dois caminhos comuns=~
**Caminho A — site estático ou SPA buildada**
- Instalar **Nginx** (ou Caddy)
- Pasta `/var/www/seu-site` com arquivos `index.html`, assets
- Nginx como servidor de arquivos + `try_files` para SPA

**Caminho B — app com backend (ex.: Node, Python)**
- Instalar runtime (Node, Python + venv, etc.)
- App escutando em `127.0.0.1:3000` (não expor porta da app direto na internet)
- **Nginx como reverse proxy** na 443 → encaminha para a app
- **systemd** para manter o processo no ar após reboot

#### ~={Titulo}5. HTTPS=~
- **Certbot** + plugin Nginx, ou **Caddy** (HTTPS automático)
- Certificados **Let's Encrypt** gratuitos; renovação automática via cron/systemd

#### ~={Titulo}6. Deploy contínuo (opcional)=~
- Git no servidor + `git pull` + reiniciar serviço
- Ou CI (GitHub Actions) que envia artefato por **rsync/scp** ou faz SSH e roda script de deploy
- Ou **Docker** na VPS: `docker compose up -d` para empacotar app + banco

#### ~={Titulo}7. Operação=~
- Snapshots do provedor antes de mudanças grandes
- Backup off-site (banco + arquivos) — VPS pode falhar ou ser apagada por erro humano
- Logs: `journalctl`, Nginx access/error log; alertas simples (Uptime Kuma, etc.)

### ~={Titulo}Exemplo mínimo — Nginx servindo site estático=~
Após copiar arquivos para `/var/www/meu-site`:

```nginx
server {
    listen 80;
    server_name meudominio.com www.meudominio.com;
    root /var/www/meu-site;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Depois: `certbot --nginx -d meudominio.com -d www.meudominio.com` para ativar HTTPS.

### ~={Titulo}Docker no VPS=~
Muitos projetos hoje usam **Docker Compose** na VPS:
- Um arquivo `docker-compose.yml` define app, banco, volumes
- Portas publicadas só as necessárias (ex.: 80/443 no proxy)
- Facilita reproduzir o mesmo ambiente em outra VPS

~={yellow}Atenção:=~ Docker consome RAM; planos VPS muito pequenos (512 MB–1 GB) podem ficar apertados para app + banco + proxy.

### ~={Titulo}Segurança — checklist rápido=~
- Chave SSH, desabilitar login root por senha
- Firewall ativo; fechar portas não usadas
- Atualizações de segurança regulares
- Não commitar `.env` com senhas; usar variáveis de ambiente no servidor
- HTTPS em tudo que for público
- Backups testados (restaurar de verdade uma vez)

### ~={Titulo}Quando escolher VPS (e quando não)=~
**Escolha VPS se:**
- Precisa de stack custom (versões específicas, serviços extras)
- Quer custo previsível mensal e controle total do SO
- Vários projetos pequenos no mesmo servidor

**Considere PaaS/serverless se:**
- Quer zero administração de SO
- Tráfego muito irregular (serverless pode sair mais barato)
- Frontend estático + API serverless já atende

**Considere hospedagem compartilhada se:**
- Apenas WordPress/blog simples e você não quer SSH

### ~={Titulo}Custos e dimensionamento=~
- Planos entry (~US$ 4–6/mês) servem para site leve, API pequena, homologação
- Monitore **RAM** (primeiro gargalo) e **disco** (logs, banco, uploads)
- Escale verticalmente (plano maior) ou horizontalmente (segunda VPS + load balancer) conforme crescimento

### ~={Titulo}Resumo=~
> [!tip] Em uma frase
> VPS é um **servidor Linux (ou Windows) na nuvem** que você administra: ideal para **hospedar sites, APIs e qualquer projeto** que precise de processo contínuo, porta aberta e controle total, trocando simplicidade de hospedagem compartilhada por **flexibilidade e responsabilidade** de configurar rede, web server, HTTPS e backups.

___
[[Guia Sistemas]]
