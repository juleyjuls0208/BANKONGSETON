# hostbox — multi-site host for the Oracle VM

A tiny, dependency-light platform that turns the BankongSeton Oracle VM into a
host for **as many sites as you want**: landing pages, CampusNav, the backend
API, and any future project. One wildcard DNS record feeds every subdomain;
Let's Encrypt issues/renews TLS per site automatically.

**DNS, free, no account:** this box uses `sslip.io` — any subdomain of
`149-118-60-251.sslip.io` resolves to the VM's IP for free
(`landing.149-118-60-251.sslip.io`, `campusnav.149-118-60-251.sslip.io`, …).
You never touch DNS and never pay. If you later buy a real domain, point
`A *.yourdomain.com → 149.118.60-251` and re-run `addsite` with your domain as
BASE_DOMAIN (or edit `/etc/hostbox.conf`).

It sits *alongside* `deploy/oracle/` (the BankongSeton backend) — no conflict.
The backend keeps its own nginx site + services; hostbox adds a `default_server`
and `sites-enabled/*.conf` per extra site.

## Model

```
*.149-118-60-251.sslip.io  ──(sslip.io wildcard, no config)──►  nginx
                                                            ├─ bankongseton  (existing backend, port 80 site)
                                                            ├─ landing.149-118-60-251.sslip.io     → /srv/hostbox/landing/public   (static)
                                                            ├─ campusnav.149-118-60-251.sslip.io   → /srv/hostbox/campusnav/public (node :3000)
                                                            └─ <any>.149-118-60-251.sslip.io       → /srv/hostbox/<any>/public
```

- **static**: drop files into `/srv/hostbox/<name>/public` → served over HTTPS.
- **node**: put the project in `/srv/hostbox/<name>/public`; it runs `npm install --omit=dev && npm start` on port 3000, nginx reverse-proxies it.

## Coexisting with the BankongSeton backend (`deploy/oracle/`)

The backend already deploys its own nginx site + 4 systemd services to this
same VM. To make them live side by side:

1. Install the BankongSeton backend **with a DOMAIN** (`DOMAIN=yourdomain.com`
   when running `deploy/oracle/deploy_backend.sh` or install.sh). That makes its
   nginx site a *named* vhost, leaving the `_` catch-all free for hostbox.
2. Run `bootstrap` (above) — it adds the `default_server` catch-all and the
   `*.149-118-60-251.sslip.io` sites.
3. In DNS, point both your backend domain and `*.149-118-60-251.sslip.io` at
   the VM's public IP. Apex/backend domain → BankongSeton backend; every
   subdomain → a hostbox site.

## One-time setup (on the VM, as root)

```bash
# upload this folder (deploy/host) to the VM, or clone the repo and use it
BASE_DOMAIN=149-118-60-251.sslip.io bash deploy/host/bootstrap
```

Then in your DNS (one record, never touch again):

```
A    *.149-118-60-251.sslip.io   <VM public IP>
```

## Daily use (your on-server agent, or you)

```bash
# 1. provision (creates dirs, nginx block, systemd unit if node, TLS)
addsite landing   static landing
addsite campusnav node    campusnav

# 2. paste the project files
cp -r ~/pasted/landing/*   /srv/hostbox/landing/public/
cp -r ~/pasted/campusnav/* /srv/hostbox/campusnav/public/

# 3. node sites: start/restart
systemctl restart campusnav
# static sites: files are live immediately, no restart needed
```

## Notes / ceilings (ponytail)

- **Single default port for node (3000).** If a project needs another port,
  edit `/etc/nginx/sites-available/<name>.conf` (`proxy_pass`) and the
  project's start command. One port per site, no dynamic port allocation.
- **certbot issues after DNS propagates.** If `addsite` warns that certbot
  failed, fix the DNS record and re-run `certbot --nginx -d <sub>.<base>`.
  Until then the site serves HTTP.
- **Node version** is whatever the VM's `node`/`npm` is. If you need a pinned
  version per site, wrap the `ExecStart` in `nvm`/`volta` yourself.
- **No CI/build step** — you paste built output (e.g. `dist/`, `build/`).
  If a project needs a build, run it locally and paste the output, or extend
  the node unit's `ExecStart`.
- **Shared VM, shared nginx** — one misconfigured site can 500 the whole
  `nginx -t`; `addsite` runs `nginx -t` before reload so a bad site won't
  take the box down.
- Auto-renew of certs is handled by the certbot systemd timer (installed with
  the package). Nothing to schedule.
