# UMBRA — Zero-Cost Cloud Deployment Guide
## Target: Supabase (DB) + Render (Backend) + Vercel (Frontend)
## Total cost: $0

---

## Architecture (Deployed)

```
┌─────────────────────────────────────────────────────────┐
│                  DEMO USER (Browser)                     │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTPS
                           ▼
              ┌────────────────────────┐
              │  Vercel (Frontend)     │  FREE
              │  umbra-demo.vercel.app │
              │  Static HTML/React SPA │
              └──────────┬─────────────┘
                         │ REST API calls
                         ▼
              ┌────────────────────────┐
              │  Render (Backend)      │  FREE
              │  FastAPI + Python      │
              │  /api/* endpoints      │
              └──────────┬─────────────┘
                         │ SQL (asyncpg)
                         ▼
              ┌────────────────────────┐
              │  Supabase (Database)   │  FREE
              │  PostgreSQL 15         │
              │  500MB storage         │
              └────────────────────────┘
```

**Cold start note:** Render free tier sleeps after 15 min of inactivity.
First request takes ~30 seconds to wake up. The frontend handles this
gracefully — it shows mock data immediately and upgrades to live data
once the API responds.

---

## Step 1 — Set Up Supabase Database (5 minutes)

### 1.1 Create Account
1. Go to **https://supabase.com**
2. Click **Start your project** → sign in with GitHub
3. Click **New project**
4. Fill in:
   - **Name:** `umbra-demo`
   - **Database Password:** (generate a strong one — save it)
   - **Region:** choose closest to you
5. Click **Create new project** — wait ~2 minutes

### 1.2 Get Your Connection String
1. Go to: **Settings → Database**
2. Scroll to **Connection string**
3. Click **URI** tab
4. Copy the string — it looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres
   ```
5. **Important:** Replace `[YOUR-PASSWORD]` with your actual password
6. **Important:** Change `postgresql://` to `postgresql+asyncpg://`

Your final DATABASE_URL will look like:
```
postgresql+asyncpg://postgres:MyPassword123@db.abcdefgh.supabase.co:5432/postgres
```

### 1.3 Run the Schema
1. In Supabase, go to: **SQL Editor** (left sidebar)
2. Click **+ New query**
3. Open `data/01_migration.sql` from the UMBRA package
4. Paste the entire contents into the editor
5. Click **Run** (or Ctrl+Enter)
6. You should see: `UMBRA schema installed successfully ✓`

### 1.4 Run the Seed Data
1. Click **+ New query** again
2. Open `data/02_seed.sql` from the UMBRA package
3. Paste the entire contents
4. Click **Run**
5. You should see a table showing counts:
   - clients: 3
   - techniques: 25
   - rules: 27
   - log_sources: 18
   - rule_deps: 50+
   - deployments: 25+
   - decisions: 5

---

## Step 2 — Deploy Backend to Render (10 minutes)

### 2.1 Push Code to GitHub
1. Create a new GitHub repository (can be private)
2. Push the `umbra-deploy` folder:
   ```bash
   cd umbra-deploy
   git init
   git add .
   git commit -m "UMBRA v1.0 deploy"
   git remote add origin https://github.com/YOUR-USERNAME/umbra-deploy.git
   git push -u origin main
   ```

### 2.2 Create Render Web Service
1. Go to **https://render.com** → sign in with GitHub
2. Click **New +** → **Web Service**
3. Connect your GitHub repo
4. Select `umbra-deploy`
5. Configure:
   - **Name:** `umbra-backend`
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free`

### 2.3 Set Environment Variables
In Render → your service → **Environment** tab:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:YOUR-PASS@db.xxx.supabase.co:5432/postgres` |
| `APP_ENV` | `production` |
| `DEMO_MODE` | `true` |
| `ANTHROPIC_API_KEY` | your key (or leave blank for mock reasoning) |
| `CORS_ORIGINS` | `*` (update after Vercel deploy) |

6. Click **Create Web Service**
7. Watch the build logs — takes ~3 minutes
8. When you see `UMBRA ready.` in logs — it's live

### 2.4 Note Your Backend URL
Render gives you a URL like:
```
https://umbra-backend-xxxx.onrender.com
```
Save this — you need it for the frontend.

### 2.5 Test the Backend
```bash
curl https://umbra-backend-xxxx.onrender.com/health
# → {"status":"ok","service":"umbra","demo_mode":true}

curl https://umbra-backend-xxxx.onrender.com/health/db
# → {"status":"ok","clients_loaded":3}
```

### 2.6 Run Initial Analysis
Preload gap data for all 3 demo clients:
```bash
# Apex Financial
curl -X POST https://umbra-backend-xxxx.onrender.com/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"client_id":"a1000000-0000-0000-0000-000000000001"}'

# NovaMed Health
curl -X POST https://umbra-backend-xxxx.onrender.com/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"client_id":"a1000000-0000-0000-0000-000000000002"}'

# CoreGrid Energy
curl -X POST https://umbra-backend-xxxx.onrender.com/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"client_id":"a1000000-0000-0000-0000-000000000003"}'
```
Each call returns: gaps found, recommendations, coverage scores.

---

## Step 3 — Deploy Frontend to Vercel (5 minutes)

### 3.1 Update vercel.json
Open `vercel.json` and replace the placeholder:
```json
"UMBRA_API_URL": "https://umbra-backend-xxxx.onrender.com"
```
Commit and push this change.

### 3.2 Deploy to Vercel
1. Go to **https://vercel.com** → sign in with GitHub
2. Click **Add New** → **Project**
3. Import your `umbra-deploy` repo
4. Configure:
   - **Framework Preset:** `Other`
   - **Root Directory:** `frontend`
   - **Build Command:** *(leave empty)*
   - **Output Directory:** `.`
5. Add Environment Variable:
   - Key: `UMBRA_API_URL`
   - Value: `https://umbra-backend-xxxx.onrender.com`
6. Click **Deploy**
7. Takes ~30 seconds

### 3.3 Your Live URL
Vercel gives you:
```
https://umbra-deploy.vercel.app
```
(or a custom name you choose)

### 3.4 Tighten CORS (recommended)
Go back to Render → Environment and update:
```
CORS_ORIGINS=https://umbra-deploy.vercel.app,http://localhost:3000
```

---

## Step 4 — Verify Everything Works

### Checklist:
```
□ Open https://umbra-deploy.vercel.app
□ Sidebar shows: Apex Financial Services, NovaMed, CoreGrid
□ Dashboard shows coverage illusion banner (orange)
□ Real coverage % < Apparent coverage %
□ MITRE Matrix loads with coloured cells
□ Gap Explorer shows gaps with attacker paths
□ API status indicator shows "online" (bottom left sidebar)
□ Switch between clients — data changes
□ "Run Analysis" button works when API is online
```

### What to expect on first load:
- Page loads instantly with **mock data** (always visible)
- After ~1-3 seconds (or ~30s on cold start), API connects
- Live data replaces mock data automatically
- "DEMO DATA" badge disappears when live API responds
- Bottom-left sidebar shows "● API CONNECTED"

---

## Step 5 — Share the Demo Link

Send this to anyone:
```
https://umbra-deploy.vercel.app
```

They open it → see UMBRA working immediately (mock data loads in <1s).
If the Render backend is warm → live database data loads in 2-3 seconds.
If Render is cold-starting → mock data stays visible for ~30s, then upgrades.

**The demo never shows a blank screen or error.**

---

## Troubleshooting

### "API offline" / stuck on mock data
```bash
# Wake up the backend manually
curl https://umbra-backend-xxxx.onrender.com/health
# Wait 30 seconds, then refresh the UMBRA page
```

### Database not connecting
1. Check Supabase → Project Settings → Database → Status is "Active"
2. Verify DATABASE_URL has `postgresql+asyncpg://` (not just `postgresql://`)
3. Confirm password has no special chars that need URL-encoding
4. Check Render logs: look for "Database connected (Supabase)"

### Coverage matrix empty after analysis
```bash
# Run analysis for all clients
curl -X POST https://your-backend.onrender.com/api/analyze/all-demo
# Returns: {"status":"completed","clients":[...]}
```

### CORS errors in browser console
Update `CORS_ORIGINS` in Render to include your exact Vercel URL:
```
https://your-app.vercel.app
```

### Supabase "too many connections"
Free tier = 60 connections max. The backend pool is set to 3+5=8 max.
If you see connection errors, restart the Render service.

---

## Optional: Add Claude Reasoning

1. Get API key from https://console.anthropic.com
2. In Render → Environment:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-xxxx
   ```
3. Re-run analysis — top 5 gaps per client get real Claude attacker paths
4. Gap Explorer "Attacker Path" sections show live Claude analysis

Without the key, UMBRA uses structured mock reasoning (same schema, same UX).

---

## Keeping the Demo Alive

Render free tier sleeps after 15 min idle. Options:

**Option A — Manual wake (simplest):**
Bookmark `https://your-backend.onrender.com/health` and open it
before a demo.

**Option B — UptimeRobot ping (free, automatic):**
1. Sign up at https://uptimerobot.com (free)
2. Add monitor: HTTP(s), your `/health` URL, every 5 minutes
3. This keeps Render awake indefinitely on free tier

**Option C — Render cron (if you upgrade to paid):**
```yaml
# Add to render.yaml:
- type: cron
  name: umbra-keepalive
  schedule: "*/10 * * * *"
  command: "curl https://umbra-backend-xxxx.onrender.com/health"
```

---

## Final State

| Component | Platform | URL | Cost |
|-----------|----------|-----|------|
| Frontend  | Vercel   | `https://umbra-demo.vercel.app` | $0 |
| Backend   | Render   | `https://umbra-backend.onrender.com` | $0 |
| Database  | Supabase | Managed PostgreSQL | $0 |
| **Total** | | | **$0/month** |
