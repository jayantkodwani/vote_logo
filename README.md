# LTC Capital Call — Logo Vote

A small, self-contained Flask app that lets your team vote on the new portal
logo. The five finished logo designs from the brand deck are embedded as-is
(no colours or artwork changed); votes are stored server-side and everyone
shares one live tally. One vote per person, changeable, with an optional comment.

- **Live page:** `/`
- **Results JSON:** `/api/results`
- **Health check:** `/healthz`

---

## What's in here

```
.
├── app/
│   ├── __init__.py        # app factory, config, DB init (auto-creates tables)
│   ├── models.py          # LogoVote model
│   ├── concepts.py        # the logo options + their inline SVG logos
│   ├── views.py           # routes, identity, CSRF, tally
│   ├── templates/         # base.html + vote.html
│   └── static/            # favicon.svg
├── wsgi.py                # entry point: `app = create_app()`
├── requirements.txt
├── Procfile               # gunicorn start command
├── startup.txt            # same command, for the Azure "Startup Command" box
├── .github/workflows/azure-webapp.yml   # CI/CD to Azure
└── .gitignore
```

No database server is required to start: it defaults to a SQLite file on
Azure's **persistent** `/home` storage, so votes survive restarts.

---

## Deploy to Azure App Service (from GitHub)

### 1. Push this code to a GitHub repo
```bash
git init
git add .
git commit -m "LTC Fund Swift logo vote"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

### 2. Create the Web App
Azure Portal → **Create a resource → Web App**:
- **Publish:** Code
- **Runtime stack:** Python 3.11
- **Operating System:** Linux
- Pick a region/plan (B1 is plenty).

### 3. Connect the repo (pick ONE)
- **Easiest — Deployment Center:** Web App → *Deployment Center* → Source =
  GitHub → choose your repo/branch → Save. Azure builds and deploys on every push.
- **Or use the included workflow:** add a GitHub secret
  `AZURE_WEBAPP_PUBLISH_PROFILE` (download the publish profile from the Web App),
  set `AZURE_WEBAPP_NAME` in `.github/workflows/azure-webapp.yml`, then push.

### 4. Set the startup command
Web App → *Configuration → General settings → Startup Command*:
```
gunicorn --bind=0.0.0.0 --timeout 600 wsgi:app
```

### 5. App settings (Configuration → Application settings)
| Name           | Value                                   | Required |
|----------------|-----------------------------------------|----------|
| `SECRET_KEY`   | a long random string                    | **yes**  |
| `ADMIN_EMAILS` | comma-separated admins (for Reset)      | optional |
| `DATABASE_URL` | Postgres URL to use a managed DB        | optional |

Restart the app after saving. Browse to the site URL — done.

---

## One vote per employee (recommended)

Turn on **Azure App Service Authentication** ("Easy Auth"):
Web App → *Authentication* → Add identity provider → **Microsoft (Entra ID)** →
require authentication. No code changes needed — the app automatically reads the
signed-in user from the `X-MS-CLIENT-PRINCIPAL-NAME` header and gives each
person a single, changeable vote. Put those same emails in `ADMIN_EMAILS` to
grant the **Reset** button.

Without Easy Auth, the app falls back to a per-browser cookie (fine for a quick
open poll, but not strictly one-per-person).

---

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export SECRET_KEY=dev ADMIN_EMAILS=you@example.com   # Windows: set ...
python wsgi.py
# open http://localhost:8000
```

---

## Switching to PostgreSQL (optional)
Create an Azure Database for PostgreSQL, then set
`DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require`.
`psycopg2-binary` is already in `requirements.txt`. Tables are created
automatically on first start.

## Notes
- Tables are created on startup via `db.create_all()` — no migrations needed.
- The logos in `app/concepts.py` are the exact SVGs from the design review, so
  the page and any exported assets stay in sync.
