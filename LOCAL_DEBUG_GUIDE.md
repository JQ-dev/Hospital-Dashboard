# Local Debugging Guide for Render Deployment

This guide explains how to run the same application locally that's deployed on Render, enabling you to debug issues before deploying.

---

## Architecture Overview

Your Render deployment uses the following structure:

```
Render Deployment:
  ├─ app.py (entry point)
  │   └─ imports app_with_auth.py (authenticated dashboard)
  │       └─ imports dashboard.py (core dashboard logic)
  │
  ├─ Gunicorn (production WSGI server)
  └─ Environment variables from render.yaml
```

**Key Files:**
- **[app.py](app.py)** - Production entry point with environment-based config
- **[app_with_auth.py](app_with_auth.py)** - Dashboard with authentication layer
- **[dashboard.py](dashboard.py)** - Core dashboard without auth (what you've been using)
- **[render.yaml](render.yaml)** - Render deployment configuration
- **[Procfile](Procfile)** - Gunicorn startup command for Render

---

## Method 1: Run with Development Server (Recommended for Debugging)

This method uses Dash's built-in development server, which provides better error messages and auto-reload.

### Step 1: Create Local Environment File

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` to match your local setup:

```env
# Server Configuration
PORT=8050
HOST=0.0.0.0
DEBUG=true

# Database
DATABASE_PATH=data/auth.db

# Security (optional for local dev)
SECRET_KEY=local-dev-secret-key-change-in-production
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run the Application

**Option A: Run with environment variables from .env**

```bash
# Windows (PowerShell)
$env:DEBUG="true"; python app.py

# Windows (CMD)
set DEBUG=true && python app.py

# Linux/Mac
export DEBUG=true
python app.py
```

**Option B: Run directly (uses defaults from .env)**

```bash
python app.py
```

The app will start on `http://localhost:8050` in debug mode.

### What You Get:
- ✅ Auto-reload on code changes
- ✅ Detailed error messages in browser
- ✅ Stack traces in console
- ✅ Same authentication as production
- ✅ Same database structure

---

## Method 2: Run with Gunicorn (Production Simulation)

This method simulates the exact Render production environment using Gunicorn.

### Step 1: Install Gunicorn

```bash
pip install gunicorn
```

### Step 2: Run with Gunicorn

**Windows:**
```bash
# Note: Gunicorn doesn't officially support Windows
# Use waitress instead:
pip install waitress
waitress-serve --port=8050 app:server
```

**Linux/Mac:**
```bash
# Exact same command as Render uses
gunicorn app:server --bind 0.0.0.0:8050 --workers 1 --threads 2 --timeout 120
```

### What You Get:
- ✅ Exact production environment
- ✅ Tests multi-threading behavior
- ✅ Tests timeout handling
- ❌ No auto-reload (must restart manually)
- ❌ Less detailed error messages

---

## Method 3: Docker Local Testing (Advanced)

Simulate Render's container environment exactly.

### Step 1: Create Dockerfile (if not exists)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8050
ENV DEBUG=false

CMD gunicorn app:server --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120
```

### Step 2: Build and Run

```bash
# Build image
docker build -t hospital-dashboard .

# Run with debug mode
docker run -p 8050:8050 -e DEBUG=true hospital-dashboard

# Run in production mode
docker run -p 8050:8050 hospital-dashboard
```

---

## Debugging Different Scenarios

### Scenario 1: Test Authentication Flow

```bash
# Run with debug enabled to see auth logs
export DEBUG=true
python app.py
```

Then test:
1. Navigate to `http://localhost:8050`
2. Should redirect to `/login`
3. Create account → login → access dashboard

**Check auth database:**
```bash
sqlite3 data/auth.db
.tables
SELECT * FROM users;
SELECT * FROM sessions;
.quit
```

### Scenario 2: Test Database Connection Issues

```python
# Add to app.py for debugging
import os
print(f"Database path: {os.environ.get('DATABASE_PATH', 'data/auth.db')}")
print(f"Database exists: {os.path.exists('data/auth.db')}")
```

### Scenario 3: Test Environment Variable Loading

```python
# Add to app.py after imports
print("\n=== Environment Variables ===")
print(f"PORT: {os.environ.get('PORT', 'NOT SET')}")
print(f"HOST: {os.environ.get('HOST', 'NOT SET')}")
print(f"DEBUG: {os.environ.get('DEBUG', 'NOT SET')}")
print(f"DATABASE_PATH: {os.environ.get('DATABASE_PATH', 'NOT SET')}")
print("============================\n")
```

### Scenario 4: Test Without Authentication (Like dashboard.py)

If you want to test JUST the dashboard without auth:

```bash
# Run the original dashboard.py
python dashboard.py
```

This gives you the KPI dashboard without login requirements.

---

## Common Issues and Solutions

### Issue 1: "Module not found" errors

**Problem:** Missing dependencies
```
ModuleNotFoundError: No module named 'gunicorn'
```

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue 2: Database permission errors

**Problem:** Can't write to database
```
sqlite3.OperationalError: unable to open database file
```

**Solution:**
```bash
# Ensure data directory exists with proper permissions
mkdir -p data
chmod 755 data
```

### Issue 3: Port already in use

**Problem:** Another process using port 8050
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find and kill process on port 8050
# Windows:
netstat -ano | findstr :8050
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8050 | xargs kill -9

# Or use different port:
export PORT=8051
python app.py
```

### Issue 4: Environment variables not loading

**Problem:** .env file not being read

**Solution:**
```bash
# Install python-dotenv
pip install python-dotenv

# Add to app.py (if not already there):
from dotenv import load_dotenv
load_dotenv()
```

### Issue 5: Gunicorn won't start on Windows

**Problem:** Gunicorn doesn't support Windows

**Solution:** Use `waitress` instead:
```bash
pip install waitress
waitress-serve --port=8050 app:server
```

---

## Comparing Local vs Render Behavior

| Feature | Local (Debug) | Local (Gunicorn) | Render (Production) |
|---------|---------------|------------------|---------------------|
| **Server** | Dash dev server | Gunicorn/Waitress | Gunicorn |
| **Auto-reload** | ✅ Yes | ❌ No | ❌ No |
| **Debug mode** | ✅ On | ❌ Off | ❌ Off |
| **Error details** | Full stack trace | Basic error | Basic error |
| **Performance** | Slower | Fast | Fast |
| **Environment** | .env file | .env or export | render.yaml |
| **Database** | data/auth.db | data/auth.db | /opt/render/.../data/auth.db |

---

## Debugging Workflow

### 1. Develop Locally with Debug Mode

```bash
# Terminal 1: Run app in debug mode
export DEBUG=true
python app.py

# Terminal 2: Watch logs
tail -f logs/app.log  # if logging to file
```

### 2. Test Production Behavior Locally

```bash
# Disable debug mode
export DEBUG=false

# Run with Gunicorn (Linux/Mac) or Waitress (Windows)
gunicorn app:server --bind 0.0.0.0:8050 --workers 1 --threads 2 --timeout 120
# OR
waitress-serve --port=8050 app:server
```

### 3. Deploy to Render

```bash
# Commit changes
git add .
git commit -m "Fix: description of changes"
git push origin main

# Render auto-deploys from main branch
# Check logs at: https://dashboard.render.com
```

---

## Quick Reference: Running Different Versions

```bash
# 1. Original dashboard (no auth, quick testing)
python dashboard.py

# 2. Authenticated dashboard (development)
export DEBUG=true
python app.py

# 3. Authenticated dashboard (production simulation)
export DEBUG=false
gunicorn app:server --bind 0.0.0.0:8050 --workers 1 --threads 2

# 4. Authenticated dashboard (Windows production simulation)
waitress-serve --port=8050 app:server
```

---

## Environment Variables Reference

From [render.yaml](render.yaml#L11-L19):

| Variable | Render Value | Local Dev Value | Purpose |
|----------|--------------|-----------------|---------|
| `PYTHON_VERSION` | 3.11.0 | (system python) | Python version |
| `DEBUG` | false | true | Enable debug mode |
| `SECRET_KEY` | (auto-generated) | (any string) | Session encryption |
| `DATABASE_PATH` | /opt/render/.../data/auth.db | data/auth.db | Auth database location |
| `PORT` | (auto-set) | 8050 | Server port |

---

## Testing Checklist

Before deploying to Render, test locally:

- [ ] App starts without errors
- [ ] Login page loads
- [ ] Can create new account
- [ ] Can login with credentials
- [ ] Dashboard loads after login
- [ ] KPIs display correctly
- [ ] L2/L3 drill-down works
- [ ] Logout works
- [ ] Session persists across page refreshes
- [ ] Database writes succeed
- [ ] No console errors in browser

Run production simulation:
- [ ] Gunicorn starts successfully
- [ ] App works without DEBUG=true
- [ ] No development-only features used
- [ ] Performance is acceptable

---

## Additional Resources

- **Render Dashboard:** https://dashboard.render.com
- **Render Logs:** View real-time logs in Render dashboard
- **Local Logs:** Check console output where you ran `python app.py`
- **Database Browser:** Use DB Browser for SQLite to inspect `data/auth.db`

---

## Quick Start (TL;DR)

**Fastest way to debug locally:**

```bash
# 1. Set debug mode
export DEBUG=true  # Linux/Mac
# OR
$env:DEBUG="true"  # PowerShell

# 2. Run
python app.py

# 3. Open browser
# http://localhost:8050
```

**To match Render exactly (Linux/Mac):**

```bash
export DEBUG=false
gunicorn app:server --bind 0.0.0.0:8050 --workers 1 --threads 2 --timeout 120
```

**To match Render exactly (Windows):**

```bash
pip install waitress
waitress-serve --port=8050 app:server
```

---

**Last Updated:** 2025-11-16
**Deployment:** Render Free Tier
**Stack:** Python 3.11 + Dash + Gunicorn + SQLite
