# Deploy the Synthetic Persona Lab to Cloudflare

This folder deploys [`persona-lab/`](../../persona-lab/) as a **static site on
Cloudflare Workers** (Static Assets — no Worker script, no build step). The page
is the single `public/index.html`, served at `/`.

> The deploy has to run from a machine with Cloudflare credentials (`wrangler`
> login). It can't run from the Claude session: the connected Cloudflare tools
> there are read-only for Workers, and the sandbox has no `wrangler` and can't
> reach the Cloudflare API.

## 1. Deploy (gives a live `*.workers.dev` URL immediately)

```bash
cd deploy/cloudflare
npm install            # installs wrangler locally
npx wrangler login     # one-time: authorize your Cloudflare account
npm run deploy         # copies the latest page into public/ and deploys
```

`npm run deploy` runs `wrangler deploy`, which uploads `public/` and prints the
live URL:

```
https://questsim-synthetic-students.<your-account-subdomain>.workers.dev
```

That is live, global, and free on the Workers free plan. Re-run `npm run deploy`
any time to push an update (it re-copies the latest `persona-lab/index.html`
first, so there's one source of truth).

## 2. Put it on `questsim.synthetic-students.<tld>`

A custom hostname needs a domain you own **and have added to this Cloudflare
account as a zone**. Assuming you own `synthetic-students.<tld>` on Cloudflare:

**Dashboard (simplest):** Cloudflare dashboard → Workers & Pages →
`questsim-synthetic-students` → **Settings → Domains & Routes → Add → Custom
Domain** → enter `questsim.synthetic-students.<tld>` → Add. Cloudflare creates
the DNS record and certificate automatically; it's live in a minute or two.

**or add it to `wrangler.jsonc`** and redeploy:

```jsonc
{
  "name": "questsim-synthetic-students",
  "compatibility_date": "2026-11-12",
  "assets": { "directory": "./public" },
  "routes": [
    { "pattern": "questsim.synthetic-students.<tld>", "custom_domain": true }
  ]
}
```

```bash
npm run deploy
```

If you don't own `synthetic-students.<tld>` yet, register it (Cloudflare
Registrar, or any registrar then add the zone to Cloudflare) before step 2. The
`*.workers.dev` URL from step 1 works in the meantime.

## Notes

- **Account:** Cloudflare is already connected to this workspace — the account
  holds Workers like `questsim-algebra1` and the `ultisim-*` set, so the
  `wrangler login` above should land in the right place. Pick the matching
  account if `wrangler` prompts.
- **Change the Worker name** by editing `name` in `wrangler.jsonc` (it becomes
  the `*.workers.dev` subdomain).
- **One source of truth:** the canonical page is `persona-lab/index.html`.
  `public/index.html` is a copy that `npm run sync` / `npm run deploy` refresh,
  so edit the lab, then redeploy.
- **Auto-deploy on push** (optional): in the Cloudflare dashboard, connect this
  GitHub repo under Workers Builds with root directory `deploy/cloudflare`,
  build command `npm run sync`, deploy command `npx wrangler deploy`.
