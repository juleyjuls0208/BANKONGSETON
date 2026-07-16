# BANKONGSETON — Oracle Cloud Free Tier (ARM) Deployment

Targets 1× always-free ARM VM (Ubuntu 22.04/24.04 recommended). Hosts the Flask
**API** (`/api/*`) and the **web dashboard** (admin/finance/cashier POS) behind
nginx + HTTPS. The physical RFID money-card reader (Arduino R4 + serial bridge)
stays **on-prem** — it is not deployed to the cloud.

## Topology

```
Internet
   │  :80 / :443  (HTTPS via certbot)
   ▼
nginx  (reverse proxy, TLS termination)
   ├── /api/*  ──►  gunicorn 1× sync worker  → api_server:app   (127.0.0.1:5001)
   └── /*      ──►  gunicorn 1× eventlet     → web_app:app     (127.0.0.1:5000)
                                                         (Flask + SocketIO)
```

Both gunicorn processes bind to localhost only; nginx is the sole public face.
No Docker required. Python venv at `/opt/bankongseton/venv`, code at
`/opt/bankongseton`, runs as system user `banko`.

## 0. Before you start (OCI console)

1. **Reserve the public IP** so it doesn't change on stop/start:
   OCI Console → Networking → Reserved Public IPs → Reserve (free, always-free eligible).
2. **Open the VCN Security List** for ingress: `22/tcp`, `80/tcp`, `443/tcp`
   (and you can drop 5000/5001 since nginx proxies locally). This is *separate*
   from the VM's own firewall — both must allow the traffic.
3. SSH into the VM as the default user (`ubuntu` on Ubuntu images).

## 1. First-time install

Upload the contents of this folder to the VM (or clone the repo and run from
`deploy/oracle/`):

```bash
# from your Windows machine, e.g. with scp:
scp -r deploy/oracle ubuntu@<VM_PUBLIC_IP>:/tmp/oracle

# on the VM:
sudo bash /tmp/oracle/install.sh
```

`install.sh` will prompt for:
- `DOMAIN` (optional). If you have a domain, set it — certbot issues a real
  Let's Encrypt cert and forces HTTPS. If left blank, the site is served over
  HTTP on the public IP (fine for internal testing; **not** for real payments).
- `ADMIN_EMAIL` (needed for the TLS cert; ignored if no domain).

It then: installs nginx/certbot/git/uv, creates user `banko`, clones the repo,
builds the venv, generates strong `JWT_SECRET`/`FLASK_SECRET_KEY`, writes the
env file, installs the systemd units + nginx site, opens the firewall, and
(optionally) runs certbot.

## 2. Deploy key for git pull (one-time)

`deploy.sh` does `git pull` as the `banko` user. Set up a read-only GitHub
deploy key so the VM can pull without a password:

```bash
# on the VM, as banko:
sudo -u banko ssh-keygen -t ed25519 -N "" -f /opt/bankongseton/.ssh/id_ed25519
sudo -u banko cat /opt/bankongseton/.ssh/id_ed25519.pub
```

Add that public key as a **Deploy Key** (read-only) on the GitHub repo
(Settings → Deploy keys → Add). Then test:

```bash
sudo -u banko git -C /opt/bankongseton remote set-url origin git@github.com:<you>/BANKONGSETON.git
sudo -u banko git -C /opt/bankongseton pull --ff-only
```

## 3. Redeploy after code changes

```bash
sudo bash /opt/bankongseton/deploy/oracle/deploy.sh
```

Pulls latest, reinstalls any new pip deps, restarts both services, shows status.

## 4. Verify

```bash
sudo systemctl status bankongseton-api bankongseton-web nginx
curl -k https://localhost/api/health        # API health
curl -kI https://<DOMAIN-or-IP>/            # dashboard
journalctl -u bankongseton-web -n 50 --no-pager
```

## 5. On-prem RFID reader (separate, not on this VM)

`web_app.py` is the hardware-free build — it does **not** open a serial port, so
the cloud instance never sees physical card taps. To keep the canteen working:

- Run `arduino_bridge.py` + the R4 on a **school machine** that has the USB
  reader and network access to this VM's API.
- Or flash `bankongseton_r4.ino` in WiFi mode: it posts card reads to the
  cloud via `ARDUINO_API_KEY` instead of serial. (Enhancement — out of scope here.)

In both cases the cloud API is the source of truth (Supabase), so the reader
machine is stateless and replaceable.

## 6. Notes / gotchas

- **Single worker is mandatory.** Both apps abort startup if
  `WEB_CONCURRENCY>1`. Do not "scale up" workers — move session/lock state to
  Redis/Postgres first if you ever need more throughput.
- **ARM/aarch64:** all wheels used (`psycopg2-binary`, `cryptography`, `bcrypt`,
  `eventlet`) have aarch64 builds; `pip install` works without a compiler.
- **Cold start:** always-free ARM never sleeps, so there's no cold-start lag
  (unlike Render). Good for a live POS.
- **DB is Supabase**, not local. The `DATABASE_URL` in `/opt/bankongseton/.env`
  already points at the live project (`db.pmzaxwqygzuuiawdrkvv.supabase.co`,
  ap-southeast-1). The DB host publishes **only an IPv6 AAAA record** — the
  direct `:5432` URL works if the Oracle VM has IPv6 egress (always-free ARM
  instances do). If the VM can't reach IPv6, switch to the commented IPv4
  session-pooler URL in `.env` (port `6543`, same password) — note some older
  Oracle shapes block outbound 5432, in which case the pooler is required.
  Either way: add the VM's public IP to Supabase → Database → Network
  Restrictions, or the connection is refused.
- **Secrets** live only in `/opt/bankongseton/.env` (chmod 600, owned by `banko`).
  Never commit it. `.env.production.example` is the template.
