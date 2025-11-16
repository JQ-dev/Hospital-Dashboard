# Hospital Dashboard - Deployment Guide

## 🚀 Deploy to Free Cloud Services

This guide shows you how to deploy the Hospital KPI Dashboard to **100% free** cloud services for testing and production use.

## Quick Deploy Options

### ✨ Option 1: Render (Recommended - Easiest)

**Why Render?**
- ✅ Completely free tier (no credit card required)
- ✅ Automatic HTTPS
- ✅ One-click deploy from GitHub
- ✅ Auto-deploys on git push
- ✅ 750 hours/month free

**Deploy Steps:**

1. **Fork/Clone this repository to your GitHub account**

2. **Go to [Render.com](https://render.com)** and sign up (free)

3. **Click "New +" → "Web Service"**

4. **Connect your GitHub repository**

5. **Configure:**
   - **Name**: `hospital-kpi-dashboard`
   - **Branch**: `main` (or your branch)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:server --bind 0.0.0.0:$PORT`
   - **Instance Type**: `Free`

6. **Add Environment Variables:**
   ```
   DEBUG=false
   PYTHON_VERSION=3.11.0
   ```

7. **Click "Create Web Service"**

8. **Wait 5-10 minutes** for first deployment

9. **Access your app** at: `https://your-app-name.onrender.com`

**✅ Done!** Your dashboard is live with HTTPS and authentication!

---

### 🚂 Option 2: Railway

**Why Railway?**
- ✅ $5/month free credit
- ✅ Generous free tier
- ✅ Very fast deployments
- ✅ Great developer experience

**Deploy Steps:**

1. **Install Railway CLI** (optional but recommended):
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Or use Railway.app website:**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

3. **Railway auto-detects** the Procfile and requirements.txt

4. **Add Environment Variables** (in Railway dashboard):
   ```
   DEBUG=false
   ```

5. **Click "Deploy"**

6. **Get your URL** from Railway dashboard

**Using CLI:**
```bash
# From project directory
railway init
railway up
railway open
```

---

### ✈️ Option 3: Fly.io

**Why Fly.io?**
- ✅ Generous free tier
- ✅ Global edge deployment
- ✅ Excellent performance

**Deploy Steps:**

1. **Install Fly CLI:**
   ```bash
   # macOS/Linux
   curl -L https://fly.io/install.sh | sh

   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Launch app:**
   ```bash
   fly launch
   # Follow prompts:
   # - App name: hospital-kpi-dashboard
   # - Region: choose closest
   # - PostgreSQL: No
   # - Redis: No
   ```

4. **Configure fly.toml** (created automatically):
   ```toml
   app = "hospital-kpi-dashboard"

   [build]
     builder = "paketobuildpacks/builder:base"

   [[services]]
     internal_port = 8050
     protocol = "tcp"

     [[services.ports]]
       handlers = ["http"]
       port = 80

     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443
   ```

5. **Deploy:**
   ```bash
   fly deploy
   ```

6. **Open app:**
   ```bash
   fly open
   ```

---

### 🌐 Option 4: PythonAnywhere (Free, but limited)

**Why PythonAnywhere?**
- ✅ Free tier available
- ✅ Good for Python apps
- ❌ Limited to 100 seconds CPU/day on free tier

**Deploy Steps:**

1. **Sign up** at [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Open a Bash console:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Hospital-Dashboard.git
   cd Hospital-Dashboard
   pip install --user -r requirements.txt
   ```

3. **Go to Web tab** → "Add a new web app"
   - Python version: 3.11
   - Manual configuration

4. **Configure WSGI file** (`/var/www/yourusername_pythonanywhere_com_wsgi.py`):
   ```python
   import sys
   path = '/home/yourusername/Hospital-Dashboard'
   if path not in sys.path:
       sys.path.append(path)

   from app import server as application
   ```

5. **Reload web app**

---

## 📋 Pre-Deployment Checklist

Before deploying, make sure you have:

- ✅ **requirements.txt** - All dependencies listed
- ✅ **Procfile** - Gunicorn start command
- ✅ **runtime.txt** - Python version specified
- ✅ **app.py** - Production-ready entry point
- ✅ **.gitignore** - Database files excluded
- ✅ **Environment variables** - DEBUG=false for production

All these files are included in this repository!

---

## 🔒 Security for Production

### Important Security Settings:

1. **Set DEBUG=false** in production
   ```bash
   # In cloud platform dashboard
   DEBUG=false
   ```

2. **Use strong SECRET_KEY**
   ```bash
   # Most platforms auto-generate this
   SECRET_KEY=your-random-secret-key
   ```

3. **HTTPS is automatic** on Render, Railway, and Fly.io

4. **Database persistence:**
   - On free tiers, databases are **ephemeral** (reset on restart)
   - For persistent database, upgrade to paid tier or use external DB
   - Solution: Use PostgreSQL add-on (most platforms offer free tier)

### Persistent Database Setup (Optional):

**For Render:**
```bash
# Add PostgreSQL database (free tier available)
# In Render dashboard: New → PostgreSQL
# Connect to your web service
```

**For Railway:**
```bash
# Railway automatically offers PostgreSQL
# Click "New" → "Database" → "Add PostgreSQL"
```

---

## 🌍 Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8050` | Server port (auto-set by cloud platforms) |
| `HOST` | `0.0.0.0` | Server host |
| `DEBUG` | `false` | Debug mode (set to false in production) |
| `DATABASE_PATH` | `data/auth.db` | SQLite database path |
| `SECRET_KEY` | Auto | Flask secret key (auto-generated on platforms) |

---

## 📊 Free Tier Comparisons

| Platform | Free Tier | Auto-Deploy | Custom Domain | Database | Best For |
|----------|-----------|-------------|---------------|----------|----------|
| **Render** | 750 hrs/mo | ✅ | ✅ | SQLite only | **Easiest setup** |
| **Railway** | $5 credit/mo | ✅ | ✅ | PostgreSQL free | **Best features** |
| **Fly.io** | Generous | ✅ | ✅ | PostgreSQL | **Performance** |
| **PythonAnywhere** | Limited CPU | ❌ | ❌ | SQLite | Simple Python apps |

**Recommendation for Testing:** Start with **Render** - it's the easiest and completely free!

---

## 🔧 Local Testing Before Deploy

Test the production configuration locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run with gunicorn (production server)
gunicorn app:server --bind 127.0.0.1:8050

# Or run with debug mode
DEBUG=true python app.py
```

Access at: `http://localhost:8050`

---

## 🚨 Troubleshooting

### Application won't start

**Check logs:**
- **Render**: Dashboard → Logs tab
- **Railway**: Click on deployment → View logs
- **Fly.io**: `fly logs`

**Common issues:**
1. **Missing dependencies** → Check requirements.txt
2. **Port binding** → Gunicorn should bind to `0.0.0.0:$PORT`
3. **Database permissions** → Check data/ directory exists

### Database resets on restart

**This is normal** on free tiers with ephemeral storage.

**Solutions:**
1. Use PostgreSQL add-on (free on most platforms)
2. Upgrade to paid tier with persistent disk
3. For testing, re-register users after restart

### Slow cold starts

Free tiers **sleep after inactivity**:
- **Render**: 15 min inactivity
- **Railway**: Scales to zero
- **Fly.io**: Similar behavior

**Solution:** First request after sleep takes 30-60 seconds. Subsequent requests are fast.

**Workaround:** Use a service like [UptimeRobot](https://uptimerobot.com) (free) to ping your app every 5 minutes.

---

## 📱 Custom Domain Setup

### Render:
1. Dashboard → Settings → Custom Domains
2. Add your domain
3. Update DNS records as shown
4. HTTPS auto-configured

### Railway:
1. Project → Settings → Domains
2. Add custom domain
3. Update DNS
4. SSL auto-provisioned

### Fly.io:
```bash
fly certs add yourdomain.com
# Follow DNS instructions
```

---

## 🎯 Production Best Practices

1. **Monitor uptime** with [UptimeRobot](https://uptimerobot.com) (free)

2. **Set up error tracking** (optional):
   - [Sentry](https://sentry.io) (free tier)
   - Monitor crashes and errors

3. **Regular backups** of database:
   ```bash
   # Download auth.db regularly
   # Store in cloud storage (Google Drive, Dropbox, etc.)
   ```

4. **Use environment-specific configs:**
   - Development: DEBUG=true, local database
   - Production: DEBUG=false, persistent database

5. **Monitor costs:**
   - Most free tiers have usage limits
   - Set up billing alerts

---

## 🔄 Continuous Deployment

All platforms support **auto-deploy on git push**:

### Setup:
1. **Connect GitHub** to your cloud platform
2. **Select branch** (e.g., main or production)
3. **Enable auto-deploy**

### Workflow:
```bash
# Make changes locally
git add .
git commit -m "Update feature"
git push origin main

# Platform automatically:
# 1. Detects push
# 2. Runs build
# 3. Deploys new version
# 4. Zero-downtime update
```

---

## 📈 Scaling Up

When you outgrow free tiers:

### Render:
- Starter plan: $7/month (persistent disk)
- Standard: $25/month (more resources)

### Railway:
- Pay-as-you-go: $0.000231/GB-sec
- Starter: $5/month credit

### Fly.io:
- Pay for what you use
- ~$2/month for small app

---

## 🎉 Quick Start Summary

**Fastest way to deploy (< 5 minutes):**

1. **Fork this repo** on GitHub
2. **Sign up** on [Render.com](https://render.com)
3. **New Web Service** → Connect GitHub repo
4. **Set environment**: `DEBUG=false`
5. **Deploy!**

Your dashboard will be live at: `https://your-app.onrender.com`

Create an account and start analyzing hospital KPIs!

---

## 📞 Need Help?

- **Deployment issues**: Check platform-specific documentation
- **App errors**: Review logs in platform dashboard
- **Database issues**: See AUTHENTICATION_GUIDE.md
- **Feature requests**: Open GitHub issue

---

**Last Updated**: 2025-11-16
**Tested Platforms**: Render ✅ | Railway ✅ | Fly.io ✅
**Deployment Time**: 5-10 minutes
**Cost**: $0 (completely free for testing)
