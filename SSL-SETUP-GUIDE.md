# Chinawheely HTTPS / SSL Setup Guide

## TL;DR

- **HTTPS is not a code change; it is a hosting/server setting.**
- The Chinawheely website code is already HTTPS-ready: all internal links, canonical tags, sitemap, Open Graph, and Schema.org data use `https://`.
- No hardcoded `http://` URLs (except XML namespace declarations, which are not real network requests) were found.
- You need to either (1) move the site to a host that gives free HTTPS, or (2) install an SSL certificate on your existing server.

---

## 1. Recommended: deploy on a platform with automatic HTTPS

### Option A — Vercel (recommended for this project)

This project already has a Vercel serverless function (`api/booking.js`).

1. Go to [vercel.com](https://vercel.com) and sign in.
2. Click **Add New Project → Import** and select this folder.
3. Vercel automatically issues an SSL certificate for the `.vercel.app` domain.
4. If you want a custom domain, add it in **Project Settings → Domains**. Vercel will auto-provision an SSL certificate.
5. Upload the code (`vercel --prod` or drag the folder in the web UI).

The `vercel.json` in this folder adds HSTS and security headers for every route.

### Option B — Netlify / Cloudflare Pages

- **Netlify**: drag the folder into a new site; HTTPS is enabled by default.
- **Cloudflare Pages**: upload the folder; enable **Always Use HTTPS** in the Cloudflare dashboard.
- **Cloudflare (reverse proxy)**: set DNS records to “Proxied” (orange cloud) and enable **SSL/TLS → Full (strict)** plus **Always Use HTTPS**.

---

## 2. If you already have your own server (Apache / Nginx / Caddy)

### Apache

The `.htaccess` file in this folder is already configured:

```apache
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}/$1 [R=301,L]
```

It also sets HSTS and security headers. Make sure:

- `mod_rewrite` and `mod_headers` are enabled.
- `.htaccess` is allowed in your Apache virtual host (`AllowOverride All`).
- An SSL certificate is installed (e.g., via Let's Encrypt / Certbot, see below).

### Nginx

Use the provided `nginx-ssl.conf` example:

1. Copy it to `/etc/nginx/sites-available/chinawheely`.
2. Adjust `server_name`, `root`, and certificate paths.
3. Enable it: `sudo ln -s /etc/nginx/sites-available/chinawheely /etc/nginx/sites-enabled/`
4. Install certificates with Certbot (see below).
5. Test and reload: `sudo nginx -t && sudo systemctl reload nginx`.

### Caddy (simplest for self-hosting)

Use the provided `Caddyfile`. Caddy automatically obtains and renews Let's Encrypt certificates.

```bash
caddy run --config Caddyfile
```

---

## 3. Let's Encrypt / Certbot quick install (for your own server)

### Nginx + Certbot

```bash
# Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Obtain certificate and auto-update Nginx config
sudo certbot --nginx -d chinawheely.com -d www.chinawheely.com

# Auto-renewal is enabled by default; test it with:
sudo certbot renew --dry-run
```

### Apache + Certbot

```bash
sudo apt install certbot python3-certbot-apache
sudo certbot --apache -d chinawheely.com -d www.chinawheely.com
sudo certbot renew --dry-run
```

### Standalone / any server

If you only want a certificate and handle the web server yourself:

```bash
sudo certbot certonly --standalone -d chinawheely.com -d www.chinawheely.com
```

Then point your Nginx/Apache config to:

```
/etc/letsencrypt/live/chinawheely.com/fullchain.pem
/etc/letsencrypt/live/chinawheely.com/privkey.pem
```

---

## 4. Verify after setup

1. Open your site with `https://www.chinawheely.com`.
2. Check the padlock in the browser address bar.
3. Use [SSL Labs Test](https://www.ssllabs.com/ssltest/) to verify the certificate and TLS settings.
4. Use [securityheaders.com](https://securityheaders.com/) to verify the headers.
5. Make sure `http://` requests redirect to `https://` with a 301.

```bash
curl -I http://www.chinawheely.com
# Expected: HTTP/1.1 301 Moved Permanently → Location: https://...
```

---

## 5. Files added/updated for HTTPS

| File | Purpose |
|------|---------|
| `.htaccess` | Updated CSP; keeps HTTPS redirect + security headers. |
| `vercel.json` | Vercel deployment config with HSTS and security headers. |
| `nginx-ssl.conf` | Nginx HTTPS server block example. |
| `Caddyfile` | Caddy automatic HTTPS example. |
| `SSL-SETUP-GUIDE.md` | This guide. |

---

## 6. If you still see “Not secure”

Common causes:

1. **Mixed content**: some page still loads an image/script over `http://`. Use browser DevTools → Console to find the exact URL. The Chinawheely code uses `https://` everywhere, so this should not happen after redirect is active.
2. **Missing certificate / wrong domain**: make sure the certificate covers both `chinawheely.com` and `www.chinawheely.com`.
3. **DNS not pointed**: the domain must resolve to the hosting/server IP before SSL can be issued.
4. **CDN/proxy**: if you use Cloudflare, choose **Full (strict)** SSL/TLS mode and have a valid certificate on the origin server.

---

## Next step

Tell me your hosting setup and I can give you the exact commands:

- Which server? (Vercel / Netlify / Cloudflare / Apache / Nginx / Caddy / shared hosting)
- Which OS? (Ubuntu / Debian / CentOS / Windows)
- Do you have root/SSH access?
- What is the domain?
