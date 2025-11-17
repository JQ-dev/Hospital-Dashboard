# Quick Start: Debug Render Deployment Locally

## The Fastest Way to Debug

### Windows Users:

**Double-click this file:**
```
debug_local.bat
```

OR in terminal:
```bash
python debug_local.py
```

### Linux/Mac Users:

```bash
python debug_local.py
```

**That's it!** The app will start at http://localhost:8050 with the same configuration as Render.

---

## What This Does

The debug launcher (`debug_local.py`):
- ✅ Loads environment variables from `.env`
- ✅ Sets DEBUG mode to `true` (enables hot-reload & detailed errors)
- ✅ Uses same database structure as Render (`data/auth.db`)
- ✅ Runs same authentication system as production
- ✅ Auto-reloads when you change code
- ✅ Shows detailed error messages in browser

---

## File Structure

```
Your App Files:
├── app.py                 ← Production entry point (what Render uses)
├── app_with_auth.py       ← Dashboard with authentication
├── dashboard.py           ← Core KPI dashboard (no auth)
├── debug_local.py         ← **LOCAL DEBUG LAUNCHER** ⭐
├── debug_local.bat        ← Windows launcher
├── .env                   ← Your local config (created from .env.example)
└── requirements.txt       ← Dependencies
```

---

## Different Ways to Run

### 1. Debug Mode (Recommended for Development)
**Use when:** Developing features, fixing bugs, testing changes

```bash
python debug_local.py
```

**Benefits:**
- Auto-reload on code changes
- Detailed error messages
- Debug toolbar in browser

---

### 2. Production Simulation (Test Before Deploy)
**Use when:** Testing before pushing to Render

**Linux/Mac:**
```bash
export DEBUG=false
gunicorn app:server --bind 0.0.0.0:8050 --workers 1 --threads 2
```

**Windows:**
```bash
pip install waitress
waitress-serve --port=8050 app:server
```

**Benefits:**
- Matches Render exactly
- Tests production behavior
- Tests performance

---

### 3. Original Dashboard (Quick KPI Testing)
**Use when:** Testing just KPI calculations without auth

```bash
python dashboard.py
```

**Benefits:**
- Fastest startup
- No authentication required
- Direct access to KPI dashboard

---

## Troubleshooting

### Port already in use?

```bash
# Windows:
netstat -ano | findstr :8050
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8050 | xargs kill -9
```

### Missing dependencies?

```bash
pip install -r requirements.txt
```

### Database errors?

```bash
# Delete and recreate auth database
rm data/auth.db
python debug_local.py
# Will create new database on first run
```

---

## Comparing Run Methods

| Method | Use Case | Auto-Reload | Auth | Speed |
|--------|----------|-------------|------|-------|
| `debug_local.py` | Development | ✅ Yes | ✅ Yes | Medium |
| `python app.py` | Testing auth | ✅ Yes | ✅ Yes | Medium |
| `gunicorn app:server` | Pre-deploy test | ❌ No | ✅ Yes | Fast |
| `python dashboard.py` | Quick KPI test | ✅ Yes | ❌ No | Fast |

---

## Environment Variables

Edit `.env` to customize:

```env
# Server
PORT=8050           # Change if 8050 is in use
HOST=0.0.0.0        # 0.0.0.0 = all interfaces, 127.0.0.1 = localhost only
DEBUG=true          # true = dev mode, false = production mode

# Database
DATABASE_PATH=data/auth.db  # Where to store user accounts
```

---

## Next Steps

1. **Start debugging:**
   ```bash
   python debug_local.py
   ```

2. **Make changes to code**
   - Edit any `.py` file
   - Browser auto-refreshes
   - See changes immediately

3. **Test before deploying:**
   ```bash
   export DEBUG=false
   python app.py
   ```

4. **Deploy to Render:**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```
   Render auto-deploys from `main` branch

---

## Full Documentation

See [LOCAL_DEBUG_GUIDE.md](LOCAL_DEBUG_GUIDE.md) for:
- Detailed debugging techniques
- Docker testing
- Common issues and solutions
- Advanced configuration
- Testing checklist

---

**Last Updated:** 2025-11-16
**Quick Support:** Check [LOCAL_DEBUG_GUIDE.md](LOCAL_DEBUG_GUIDE.md) for detailed help
