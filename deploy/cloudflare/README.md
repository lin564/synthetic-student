# Deploy the Synthetic Persona Lab → questsim.persyna.com

This folder deploys the Persona Lab (repo root `index.html`) as a **static site on
Cloudflare Workers** (Static Assets — no Worker script, no build step), served
at **https://questsim.persyna.com**. The page is the single `public/index.html`.

> The deploy runs from a machine with Cloudflare credentials (`wrangler login`).
> It can't run from the Claude session: the Cloudflare tools there are read-only
> for Workers, and the sandbox has no `wrangler` and can't reach the Cloudflare
> API.

## Prerequisite: persyna.com on Cloudflare

`questsim.persyna.com` is created automatically **only if `persyna.com` is an
active zone on the same Cloudflare account** you deploy with. Check the
Cloudflare dashboard → **Account Home** — if `persyna.com` isn't listed, add it
(**Add a site**, then point your registrar's nameservers at the two Cloudflare
nameservers it gives you) before deploying. The `wrangler login` below should be
the account that already holds your `questsim-*` / `ultisim-*` Workers.

## Deploy

```bash
cd deploy/cloudflare
npm install            # installs wrangler locally
npx wrangler login     # one-time: authorize your Cloudflare account
npm run deploy         # syncs the latest page into public/ and deploys
```

`npm run deploy` runs `wrangler deploy`, which uploads `public/`, attaches the
custom domain, and the site goes live at:

```
https://questsim.persyna.com
```

Cloudflare provisions the DNS record and TLS certificate automatically (usually
live within a minute or two). Re-run `npm run deploy` any time to push an
update — it re-copies the latest root `index.html` first, so there's one
source of truth. A `questsim-persyna.<your-subdomain>.workers.dev` URL also
works as a fallback.

## Variations

- **Apex instead of subdomain:** change the route `pattern` in `wrangler.jsonc`
  to `"persyna.com"` (and/or add a second route for `"www.persyna.com"`).
- **Rename the Worker:** edit `name` in `wrangler.jsonc` and `package.json`.
- **Auto-deploy on push:** in the Cloudflare dashboard, connect this GitHub repo
  under Workers Builds with root directory `deploy/cloudflare`, build command
  `npm run sync`, deploy command `npx wrangler deploy`.

## If the custom domain step errors

If `persyna.com` isn't an active Cloudflare zone yet, `wrangler deploy` will
fail on the route with a message to that effect. Add the zone first (above), or
temporarily remove the `routes` block to deploy to the `*.workers.dev` URL, then
add the custom domain from the dashboard (the Worker → **Settings → Domains &
Routes → Add → Custom Domain**) once the zone is active.
