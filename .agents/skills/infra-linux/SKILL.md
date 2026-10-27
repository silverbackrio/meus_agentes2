---
name: infra-linux
description: "Configure e diagnostique servidor Ubuntu em produção: nginx como reverse proxy, cloudflared (quick tunnel e named tunnel), gunicorn/uwsgi como app server, unidades systemd, firewall ufw, SSH, TLS e hardening de sistema e rede. Use quando a tarefa envolver subir serviço, configurar proxy, túnel Cloudflare, processo gunicorn, 502/504, logs, permissão, firewall, certificado, deploy ou segurança do servidor."
metadata:
  category: infraestrutura
  sistema: ubuntu
  atualizado_em: 2026-10
---
# Infra Linux: nginx, cloudflared, gunicorn e segurança

Operação de servidor Ubuntu para a aplicação do projeto, do diagnóstico ao hardening. Regra de
ouro: **diagnostique antes de mexer, mude uma coisa por vez, verifique depois de cada mudança.**

## Quando usar

- Subir, reiniciar, configurar ou diagnosticar serviço (nginx, gunicorn, cloudflared, systemd).
- Erro 502/504/500, site fora do ar, TLS inválido, túnel caído, porta não responde.
- Deploy, rollback, log, permissão, firewall, SSH, atualização de segurança.

## Ambiente

- **Alvo:** Ubuntu 26.04 LTS. **Desenvolvimento remoto:** Windows 10 → Linux remoto; não assuma
  caminho do Windows nem que `localhost` seja o servidor do usuário.
- **Versões não são presumidas:** rode `nginx -v`, `cloudflared version`, `gunicorn --version`
  e `lsb_release -ds` antes de configurar; registre o que encontrou.
- **Segredos nunca no chat nem no repositório:** `chmod 600` no `.env`, fora do webroot, e fora
  do versionamento.

## Topologia padrão (túnel Cloudflare)

```
visitante → Cloudflare edge → cloudflared (saída, sem porta aberta)
         → nginx 127.0.0.1:8080 → gunicorn 127.0.0.1:8000 → app Django
```

Vantagem: o servidor não expõe 80/443 publicamente, o IP de origem não é descoberto e o WAF do
Cloudflare fica na frente. Alternativa com TLS ponta a ponta: nginx público + certificado
(Let's Encrypt via `certbot`, ou Origin Certificate do Cloudflare para o trecho origem-edge).

## Diagnóstico primeiro

```bash
systemctl status nginx gunicorn cloudflared --no-pager
journalctl -u gunicorn -u cloudflared -n 200 --no-pager
nginx -t                      # config antes de qualquer reload
ss -tlnp | grep -E ':(80|443|8000|8080)'
curl -sSI http://127.0.0.1:8000/health  || curl -sSI https://SEU-DOMINIO
cloudflared tunnel info <nome> | head
```

Leia a **primeira** linha de erro e corrija-a; erro seguinte costuma ser consequência.

## nginx

```nginx
upstream app { server 127.0.0.1:8000; keepalive 32; }

server {
  listen 127.0.0.1:8080;
  server_name _;
  client_max_body_size 20m;

  location / {
    proxy_pass         http://app;
    proxy_set_header   Host              $host;
    proxy_set_header   X-Real-IP         $remote_addr;
    proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header   Connection        "";
    proxy_read_timeout 60s;
    proxy_connect_timeout 5s;
  }

  location /static/ { alias /srv/app/static/; expires 30d; access_log off; }
  location /media/  { alias /srv/app/media/;  expires 7d;  access_log off; }

  # WebSocket
  location /ws/ {
    proxy_pass http://app;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400s;
  }
}
```

- **Sempre** `nginx -t` antes de `systemctl reload nginx` — reload com config quebrada derruba o
  site inteiro.
- Limites que evitam abuso: `limit_req_zone $binary_remote_addr zone=rl:10m rate=10r/s;` +
  `limit_req zone=rl burst=20 nodelay;` no `location`.
- Cabeçalhos de segurança: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` (ou CSP
  `frame-ancestors`), `Referrer-Policy`, HSTS **só depois** de HTTPS confirmado em todo o site.
- Regra de `proxy_pass` com barra final muda o caminho enviado — teste a URL que você espera.
- Logs em `/var/log/nginx/`; `access_log off` em assets para não inundar o disco.

## cloudflared

**Quick tunnel** (teste, URL efêmera, sem DNS):
```bash
cloudflared tunnel --url http://127.0.0.1:8080
```

**Named tunnel** (produção, domínio fixo):
```bash
cloudflared tunnel login
cloudflared tunnel create app
cloudflared tunnel route dns app app.seudominio.com
# ~/.cloudflared/config.yml
#   tunnel: <ID>
#   credentials-file: /root/.cloudflared/<ID>.json
#   ingress:
#     - hostname: app.seudominio.com
#       service: http://127.0.0.1:8080
#     - service: http_status:404
cloudflared tunnel run app
systemctl enable --now cloudflared   # ou: cloudflared service install
```

- A ordem da `ingress` importa: a primeira regra que casa vence; a última deve ser o catch-all.
- O túnel é **saída**: não abre porta no roteador nem no ufw.
- Se cair, `journalctl -u cloudflared -n 100` mostra falha de token/registro ou de rede.

## gunicorn

```bash
gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers $((2 * $(nproc) + 1)) \
  --timeout 30 --graceful-timeout 30 \
  --max-requests 1000 --max-requests-jitter 100 \
  --access-logfile - --error-logfile -
gunicorn --check-config config.wsgi:application   # valida antes de subir
```

- **ASGI** (async, websockets): use o worker `uvicorn` (`-k uvicorn.workers.UvicornWorker`) ou
  `daphne`; sync worker não atende WebSocket.
- Workers altos × pouca RAM = OOM. Meça antes: cada worker Django carrega o próprio peso.
- Recarga graciosa: `systemctl reload gunicorn` (SIGHUP) — corta conexões no meio? Não: espera o
  graceful-timeout.

## systemd (unidade do gunicorn)

```ini
[Unit]
Description=Gunicorn do app
After=network.target

[Service]
User=deploy
Group=deploy
WorkingDirectory=/srv/app
EnvironmentFile=/srv/app/.env
ExecStart=/srv/app/.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5
# hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/srv/app
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

- `systemctl daemon-reload` após editar unidade; `journalctl -u <nome> -f` para acompanhar.
- `ProtectSystem=strict` impede escrita fora de `ReadWritePaths` — é isso que impede um ataque
  de escrever no sistema.

## Segurança de sistema

1. **Usuário de deploy**, nunca `root` para rodar a aplicação; `sudo` reservado para operação.
2. **SSH:** só chave pública, `PermitRootLogin no`, `PasswordAuthentication no`, `AllowUsers`
   explícito; trocar porta é conforto, não segurança.
3. **fail2ban** ativo com jail de sshd (e de nginx, se exposto).
4. **ufw:** `default deny incoming`, `default allow outgoing`, liberar só o necessário — no modo
  túnel nem 80/443 são necessários.
   `ufw allow OpenSSH && ufw enable && ufw status verbose`
5. **Atualizações:** `unattended-upgrades` habilitado; kernel novo pede reboot agendado.
6. **Permissões:** `.env` e chaves `600`, dono do `/srv/app` é o usuário de deploy; webroot sem
   escrita pela aplicação.
7. **Mínimo de serviços:** cada daemon ligado é superfície de ataque; `systemctl list-units
   --state=running` e desligue o que não for usado.
8. **sysctl:** `net.ipv4.tcp_syncookies=1`, `net.ipv4.conf.all.rp_filter=1`,
   `net.ipv4.ip_forward=0`, `net.ipv4.icmp_echo_ignore_broadcasts=1`.
9. **AppArmor** no modo enforce; não desabilite para "fazer funcionar" — ajuste o perfil.
10. **Logs e tempo:** journald com limite de disco, `chrony`/`systemd-timesyncd` ativo (certificado
    e log sem hora certa atrapalham tudo).

## Segurança de rede e TLS

- TLS obrigatório na frente; redirecionar HTTP → HTTPS quando houver porta pública.
- Com túnel, o tráfego origem ↔ Cloudflare já é sobre TLS; não exponha porta pública sem motivo.
- HSTS só após confirmar HTTPS total (inclusive assets) — `max-age` curto primeiro.
- CSP avaliando as exceções da aplicação; sem `'unsafe-inline'` como padrão.
- Rate limit no nginx + WAF do Cloudflare; limite de corpo (`client_max_body_size`).
- Nunca registre token, cookie, Authorization ou corpo de requisição em log.

## Checklist de deploy

```
1. nginx -t                          → ok antes de reload
2. systemctl reload nginx             → systemctl status nginx
3. gunicorn --check-config            → ok
4. systemctl restart gunicorn          → status sem restart loop
5. journalctl -u gunicorn -n 50        → sem traceback
6. curl -sSI http://127.0.0.1:8000/health → 200
7. curl -sSI https://SEU-DOMINIO        → 200 e TLS ok
8. systemctl status cloudflared         → ativo (running)
9. ss -tlnp                             → nada exposto além do esperado
```

## Erros clássicos

- **502/504:** gunicorn parado, porta errada no `proxy_pass`, timeout menor que o tempo da
  aplicação, ou worker sem RAM. Confira `ss -tlnp` e o log do upstream.
- Reload sem `nginx -t` → derruba o site.
- `--workers` alto demais → OOM e loop de restart.
- `.env` legível por todos ou dentro do webroot.
- `chmod 777`, `ufw disable`, desativar AppArmor ou `setenforce 0` como "conserto": nunca.
- Trocar a porta do SSH sem registrar → trava de acesso remoto.

## Instruções

1. Carregue esta skill e diagnostique primeiro: status, log, porta, config test.
2. Faça **uma** mudança por vez e verifique logo em seguida com o comando de checagem dele.
3. Comando que altera sistema (apt, ufw, systemd, certificado, remoção) só com pedido explícito
   do usuário; registre o risco.
4. Nunca imprima segredo: diga qual arquivo precisa existir e com qual permissão, não o valor.
5. Reporte: diagnóstico → o que mudou → comandos com resultado → o que precisa de ação humana
   (DNS, login do Cloudflare, token, reboot).

## Fontes

- nginx: https://nginx.org/en/docs/
- Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
- gunicorn: https://docs.gunicorn.org
- systemd: https://www.freedesktop.org/software/systemd/man/systemd.service.html
- ufw: https://wiki.ubuntu.com/UncomplicatedFirewall
- Ubuntu security: https://ubuntu.com/security