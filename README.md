# Lab Demo Management System

A lightweight Python + Flask web application for centrally managing student demo links in a lab environment.

Admins create student accounts; students log in and register their running demo applications under structured public URLs: `https://demo.lab.domain/student-name/demo-name`.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Nginx (reverse proxy)             │
│         TLS termination + routing                   │
└──────────┬──────────────────────────┬───────────────┘
           │                          │
    ┌──────▼──────┐           ┌───────▼──────┐
    │  Flask App  │           │  Jinja2 HTML  │
    │  (backend)  │           │  (templates)  │
    └──────┬──────┘           └──────────────┘
           │
    ┌──────▼──────┐
    │  SQLite DB  │
    │  (or PG)    │
    └─────────────┘
```

**Stack:**
- **Backend:** Python 3.11+ / Flask 3.x
- **Frontend:** Jinja2 templates + Tailwind CSS (via CDN)
- **Database:** SQLite (development) / PostgreSQL-compatible via SQLAlchemy (production)
- **Auth:** Session-based login with bcrypt password hashing (Flask-Login + Flask-Bcrypt)
- **Redirect:** `/<student>/<demo>` → HTTP 302 to the registered `target_url`
- **Server:** Gunicorn (WSGI) behind Nginx (TLS)

---

## URL Reference

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/` | Public | Public homepage — all active demos grouped by student |
| GET | `/login` | Public | Login form |
| POST | `/login` | Public | Authenticate user |
| GET | `/logout` | Any | Clear session, redirect to login |
| GET | `/admin` | Admin | Admin dashboard: stats + recent demos |
| GET | `/admin/users` | Admin | Paginated list of student accounts |
| POST | `/admin/users/create` | Admin | Create new student account |
| POST | `/admin/users/<id>/reset-password` | Admin | Reset student password |
| POST | `/admin/users/<id>/toggle` | Admin | Enable/disable student account |
| POST | `/admin/users/<id>/delete` | Admin | Hard-delete student + their demos |
| GET | `/dashboard` | Student | Student demo CRUD dashboard |
| POST | `/dashboard/demos/create` | Student | Register a new demo |
| POST | `/dashboard/demos/<id>/update` | Student | Edit demo target URL / description |
| POST | `/dashboard/demos/<id>/toggle` | Student | Activate / deactivate demo |
| POST | `/dashboard/demos/<id>/delete` | Student | Soft-delete (deactivate) demo |
| GET | `/<student>/<demo>` | Public | HTTP 302 redirect to demo's target URL |
| GET | `/<student>/<demo>/<path:rest>` | Public | Redirect with path appended to target |

---

## Project Structure

```
LabDemosManagement/
├── app/
│   ├── __init__.py            # App factory, register blueprints, init extensions
│   ├── models.py              # SQLAlchemy models: User, Demo
│   ├── auth.py                # Blueprint: /login, /logout + decorators
│   ├── admin.py               # Blueprint: /admin/** routes
│   ├── student.py             # Blueprint: /dashboard/** routes
│   ├── proxy.py               # Blueprint: /<student>/<demo> redirect handler
│   ├── cli.py                 # Flask CLI commands
│   └── templates/
│       ├── base.html          # Shared layout with Tailwind CSS + nav
│       ├── index.html         # Public homepage
│       ├── login.html         # Login form
│       ├── 404.html           # Custom 404 page
│       ├── components/
│       │   ├── demo_card.html
│       │   ├── user_row.html
│       │   ├── flash_messages.html
│       │   ├── modal.html
│       │   └── pagination.html
│       ├── admin/
│       │   ├── dashboard.html
│       │   └── users.html
│       └── student/
│           └── dashboard.html
├── static/
│   └── app.js                 # Minimal JS for modal toggling
├── config.py                  # Config classes
├── schema.sql                 # Raw SQL reference schema
├── run.py                     # Dev entry point
├── wsgi.py                    # Production WSGI entry point
├── requirements.txt
├── .env.example
├── nginx.conf
├── gunicorn.conf.py
└── README.md
```

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/tmkhiem/LabDemosManagement.git
cd LabDemosManagement

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
cp .env.example .env
# Edit .env: set SECRET_KEY, DATABASE_URL, etc.

# 5. Initialise the database
flask --app run init-db

# 6. Create the first admin account
flask --app run create-admin --username admin --display-name "Lab Admin"
# (You will be prompted for the password)
```

---

## Development

```bash
# Run the development server
python run.py
# or
flask --app run run --debug
```

The app will be available at `http://127.0.0.1:5000`.

To populate sample data:

```bash
flask --app run seed-demo-data
```

---

## Production Deployment

### 1. Install and configure Gunicorn

```bash
pip install gunicorn
gunicorn -c gunicorn.conf.py wsgi:app
```

Or with systemd, create `/etc/systemd/system/lab-demos.service`:

```ini
[Unit]
Description=Lab Demo Manager
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/LabDemosManagement
ExecStart=/opt/LabDemosManagement/.venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable --now lab-demos
```

### 2. Configure Nginx

```bash
cp nginx.conf /etc/nginx/sites-available/demo.lab.domain
# Edit paths: ssl_certificate, ssl_certificate_key, alias for /static/
ln -s /etc/nginx/sites-available/demo.lab.domain /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 3. Environment variables for production

Edit `.env` (or set system environment variables):

```
FLASK_ENV=production
SECRET_KEY=<strong-random-secret>
DATABASE_URL=postgresql://user:pass@localhost/lab_demos
ALLOW_LOCAL_URLS=False
LAB_SUBNET=10.0.0.0/8
```

---

## Admin Guide

### Creating a Student Account

1. Log in as admin → navigate to **Manage Users** (`/admin/users`).
2. Click **Create Student**.
3. Fill in username (URL slug, e.g. `alice-smith`), display name, and initial password.
4. Click **Create Account**. The student can now log in.

### Resetting a Password

1. Find the student in the user table.
2. Click **Reset PW** → enter a new password → **Reset Password**.

### Enabling / Disabling an Account

Click **Disable** / **Enable** next to the student. Disabled students cannot log in and their demos return 404.

### Deleting a Student

Click **Delete** → confirm. This permanently removes the account and all their demos.

---

## Student Guide

### Logging In

Navigate to `https://demo.lab.domain/login`. Enter the username and password provided by your admin.

### Registering a Demo

1. Click **Register New Demo**.
2. Enter a **Demo Name** (lowercase, letters, numbers, hyphens — this becomes the URL slug).
3. Enter the **Target URL** where your demo app is running (e.g. `http://10.0.0.5:8080`).
4. Optionally add a description.
5. Click **Register Demo**. Your public URL is `https://demo.lab.domain/<your-username>/<demo-name>`.

### Editing a Demo

Click **Edit** on any demo card to update the target URL or description.

### Activating / Deactivating a Demo

Click **Deactivate** / **Activate** to control whether the public URL works.

### Deleting a Demo

Click **Delete** on a card → confirm. This deactivates the demo (soft delete).

---

## Demo App Requirements

For the redirect to work correctly, your demo app must:

1. **Accept any Host header** — since the browser is redirected to the original `target_url`, the Host header will be the IP/hostname of your server, not `demo.lab.domain`. Most frameworks do this by default.
2. **Handle paths correctly** — if a visitor hits `/alice/my-app/dashboard`, the system redirects to `<target_url>/dashboard`. Your app must serve that path.
3. **Be reachable from the browser** — the redirect sends the user's browser directly to the target URL; the management server never proxies traffic. Your demo app only needs to be reachable by the end user's browser.

---

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | `development` or `production` |
| `SECRET_KEY` | `dev-secret-key-…` | Session signing key. **Must be changed in production.** |
| `DATABASE_URL` | `sqlite:///lab_demos.db` | SQLAlchemy database URI |
| `LAB_SUBNET` | `10.0.0.0/8` | Allowed subnet for target URLs (informational; future use) |
| `ALLOW_LOCAL_URLS` | `True` in dev, `False` in prod | Allow `localhost`/`127.x` as target URLs (development only) |

---

## Security Notes

| Concern | Implementation |
|---------|---------------|
| Password storage | `flask-bcrypt` (bcrypt hashing) |
| SSRF on target URLs | Reject `localhost`, `127.x`, `0.0.0.0`, `::1` unless `ALLOW_LOCAL_URLS=True` |
| Slug injection | Regex `^[a-z0-9-]+$` on `username` and `demo_name` at creation |
| Reserved slugs | `admin`, `login`, `logout`, `dashboard`, `static` are blocked |
| Ownership checks | All student demo mutations verify `demo.owner_id == current_user.id` |
| Session cookies | `SESSION_COOKIE_HTTPONLY=True`; `SESSION_COOKIE_SECURE=True` in production |
| Open redirect | Redirects only go to student-registered URLs; URL is validated at registration time |

---

## Database Schema

### `users`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `username` | TEXT UNIQUE | URL slug. Lowercase, letters/numbers/hyphens |
| `password_hash` | TEXT | bcrypt hash |
| `display_name` | TEXT | Human-readable name |
| `role` | TEXT | `admin` or `student` |
| `is_active` | BOOLEAN | Whether the account can log in |
| `created_at` | DATETIME | UTC timestamp |

### `demos`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `owner_id` | INTEGER FK | References `users.id` |
| `demo_name` | TEXT | URL slug. Unique per user |
| `target_url` | TEXT | Full URL of the running demo app |
| `description` | TEXT | Optional description |
| `is_active` | BOOLEAN | Controls 302 vs 404 on public URL |
| `created_at` | DATETIME | UTC timestamp |
| `updated_at` | DATETIME | UTC timestamp, updated on edit |

---

## CLI Commands

```bash
# Initialise the database (create all tables)
flask --app run init-db

# Create an admin user
flask --app run create-admin --username admin --display-name "Lab Admin"
# Prompts for password interactively

# Seed sample student + demo data (development)
flask --app run seed-demo-data
```

---

## Template / Component System

Templates use **Jinja2 macros** (defined in `app/templates/components/`) for reusable UI elements.

### Using a macro

```jinja2
{% from 'components/demo_card.html' import render_card %}
{{ render_card(demo, editable=True) }}
```

### Available macros

| File | Macro | Purpose |
|------|-------|---------|
| `flash_messages.html` | `render_flash()` | Render flash message list |
| `demo_card.html` | `render_card(demo, editable)` | Demo card with optional edit/delete |
| `user_row.html` | `render_row(user)` | Admin user table row with actions |
| `modal.html` | `render_modal(id, title)` | Overlay modal (uses `{% call %}` block) |
| `pagination.html` | `render_pagination(pagination, endpoint)` | Page navigation controls |

### Adding a new component

1. Create `app/templates/components/my_component.html`.
2. Define a macro: `{% macro render_my_component(args) %} ... {% endmacro %}`.
3. Import and use it in any template: `{% from 'components/my_component.html' import render_my_component %}`.

---

## Contributing / Extending

### Adding a new blueprint

1. Create `app/my_feature.py` with `my_bp = Blueprint('my_feature', __name__, url_prefix='/my-feature')`.
2. Register in `app/__init__.py`: `from .my_feature import my_bp; app.register_blueprint(my_bp)`.

### Adding a new role

1. Add the role value to the `User.role` column in `models.py`.
2. Create a decorator similar to `admin_required` in `auth.py`.
3. Add navigation links for the new role in `base.html`.
