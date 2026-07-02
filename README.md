# 🔗 Shortly — Advanced URL Shortener

A full-featured URL shortener built with **Django 6** and **MongoDB**, featuring real-time click analytics, QR code generation, custom aliases, and link expiration.

> Portfolio project — Django + MongoDB (django-mongodb-backend) + vanilla JS (AJAX, Chart.js) + Tailwind CSS.

## ✨ Features

- **🔐 User accounts** — sign up, login/logout, personal dashboard. Every link belongs to its owner.
- **⚡ Instant shortening** — AJAX form, no page reloads. Random 7-char codes via `shortuuid`.
- **🎯 Custom aliases** — pick your own code (`yoursite.com/portfolio`), with reserved-word and uniqueness validation.
- **📊 Click analytics** — every redirect is logged (time, referrer, browser, device). Per-link stats page with Chart.js: 30-day trend line, browser/device doughnut charts, recent clicks feed.
- **📱 QR codes** — server-generated PNG for any link, downloadable from a modal.
- **⏰ Link expiration** — optional expiry date; expired links return `410 Gone` with a friendly page.
- **🔄 Activate / deactivate** — pause a link anytime without deleting it.
- **🛡️ Security** — CSRF-protected AJAX, owner-only API access, XSS-safe rendering, production security headers (HSTS, secure cookies, SSL redirect).

## 🧱 Tech Stack

| Layer      | Technology |
|------------|------------|
| Backend    | Django 6, Python 3.13+ |
| Database   | MongoDB via [django-mongodb-backend](https://github.com/mongodb/django-mongodb-backend) |
| Frontend   | HTML, Tailwind CSS (CDN), vanilla JavaScript (fetch/AJAX) |
| Charts     | Chart.js 4 |
| Extras     | shortuuid, qrcode, python-dotenv, WhiteNoise, Gunicorn |
| Admin      | Django admin with Jazzmin theme |

## 📂 Project Structure

```
URL-shortener/
├── core/                  # Project settings, root URLconf
├── accounts/              # Auth: signup, login, logout, dashboard
├── main/                  # ShortURL & Click models, redirect, stats, QR, AJAX API
├── mongo_apps.py          # Contrib apps reconfigured for MongoDB (ObjectId PKs)
├── mongo_migrations/      # MongoDB-compatible migrations for admin/auth/contenttypes
├── templates/             # Base layout + page templates
├── static/                # CSS + JS (dashboard.js, stats.js)
├── railway.json           # Railway deploy config
├── Procfile               # Start command (fallback)
└── requirements.txt
```

## 🚀 Local Setup

**Prerequisites:** Python 3.13+, MongoDB running locally (or an Atlas URI).

```bash
git clone <your-repo-url>
cd URL-shortener

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env: set SECRET_KEY (see .env.example for the generator command)

python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

Open <http://127.0.0.1:8000> 🎉

**Run tests:**

```bash
python manage.py test
```

## ⚙️ Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key (**required**) | `x$3k...` |
| `DEBUG` | Debug mode | `True` / `False` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated HTTPS origins (production) | `https://myapp.up.railway.app` |
| `MONGODB_URI` | MongoDB connection URI | `mongodb://localhost:27017` |
| `MONGODB_NAME` | Database name | `url_shortener_db` |
| `TIME_ZONE` | Time zone | `Asia/Tashkent` |

## ☁️ Deploying to Railway

The repo ships ready for [Railway](https://railway.com): `railway.json` (build & start command), `Procfile` (fallback), `.python-version`, WhiteNoise for static files, and Gunicorn as the app server.

### 1. Push the project to GitHub

```bash
git init
git add .
git commit -m "Shortly — advanced URL shortener"
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

> `.env` is git-ignored — secrets never leave your machine. Railway gets them as service variables (step 4).

### 2. Create the Railway project

1. Sign in at [railway.com](https://railway.com) (GitHub login is easiest).
2. **New Project → Deploy from GitHub repo** → select your repository.
3. Railway detects Python and starts the first build (it will crash until the variables in step 4 are set — that's expected).

### 3. Add a MongoDB database

**Option A — Railway MongoDB (simplest):**

1. In your project canvas: **Create → Database → Add MongoDB**.
2. Open the MongoDB service → **Variables** tab → copy the `MONGO_URL` value (or reference it, step 4).

**Option B — MongoDB Atlas (free M0 tier):**

1. Create a cluster at [mongodb.com/atlas](https://www.mongodb.com/atlas), add a database user.
2. **Network Access** → allow `0.0.0.0/0` (Railway has no static IPs on the default plan).
3. Copy the connection string: `mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/`

### 4. Set service variables

Open your **app service → Variables** and add:

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | generate a fresh one — don't reuse your local key |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `<your-app>.up.railway.app` |
| `CSRF_TRUSTED_ORIGINS` | `https://<your-app>.up.railway.app` |
| `MONGODB_URI` | `${{MongoDB.MONGO_URL}}` (Railway reference) or your Atlas URI |
| `MONGODB_NAME` | `url_shortener_db` |
| `TIME_ZONE` | `Asia/Tashkent` |

> Tip: `${{MongoDB.MONGO_URL}}` is a [reference variable](https://docs.railway.com/guides/variables) — it always stays in sync with the database service.

### 5. Generate a public domain

App service → **Settings → Networking → Generate Domain**. Copy the generated
`*.up.railway.app` domain into `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` (step 4) if you haven't already.

### 6. Deploy & verify

1. Railway redeploys automatically when variables change (or press **Deploy**).
2. The start command runs `migrate` → `collectstatic` → `gunicorn` (see `railway.json`).
3. Open `https://<your-app>.up.railway.app` — sign up, shorten a link, check the stats page.

**Create an admin user** (Railway CLI):

```bash
npm i -g @railway/cli
railway login
railway link          # select your project & service
railway run python manage.py createsuperuser
```

### Troubleshooting

| Symptom | Fix |
|---------|-----|
| `DisallowedHost` error | Add the exact Railway domain to `ALLOWED_HOSTS` |
| CSRF error on login | Add `https://<domain>` to `CSRF_TRUSTED_ORIGINS` (with the `https://` scheme) |
| `ServerSelectionTimeoutError` | Check `MONGODB_URI`; for Atlas verify the IP allowlist (`0.0.0.0/0`) |
| Static files missing | Check deploy logs — `collectstatic` runs in the start command |
| Build fails on Python version | Ensure `.python-version` (3.13) is committed |

## 📝 License

MIT — free to use for learning and portfolios.
