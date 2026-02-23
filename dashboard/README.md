# jordy-dashboard

A remote-accessible dashboard UI for the local **Jordy** FastAPI service.

- Frontend: Next.js (App Router) + Tailwind + shadcn/ui
- DB: Prisma + SQLite
- Auth: invite tokens → cookie session (ADMIN / VIEWER)
- Jordy access: authenticated proxy under `/api/jordy/*` (Jordy itself stays bound to localhost)

## Prereqs
- Node 18+ (or 20+ recommended)
- Jordy running locally at `http://127.0.0.1:8000`

## Setup

```bash
cp .env.example .env
npm install
npx prisma migrate dev
npm run dev
```

Open: `http://localhost:3000`

### Create the first admin

For MVP, create the first admin user via a one-off DB seed.

```bash
node - <<'NODE'
const { PrismaClient } = require('@prisma/client');
const crypto = require('crypto');
const prisma = new PrismaClient();

(async () => {
  const user = await prisma.user.create({ data: { role: 'ADMIN' } });
  console.log('ADMIN_USER_ID=', user.id);
  await prisma.$disconnect();
})();
NODE
```

Then go to `/admin/invites` and create invite links for trusted users.

## Remote access (recommended)

Keep this dashboard private. Two solid options:

### Option A: Tailscale (easy + secure)
- Install Tailscale on the Mac running Jordy + dashboard
- Enable MagicDNS (optional)
- Share access with trusted users (tailnet users)

### Option B: Cloudflare Tunnel (public URL, locked down)
- Create a Cloudflare Tunnel to `http://localhost:3000`
- Add Cloudflare Access policy (email allowlist)

> If you use Cloudflare/Tailscale, still keep app-level auth enabled.

## Notes
- All pages and `/api/*` routes require auth middleware.
- `/api/jordy/*` is an authenticated proxy; do **not** expose Jordy directly.
