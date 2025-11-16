# 🚀 Deploy in 5 Minutes - Quick Start

## Fastest Way to Deploy (Render - 100% Free)

### Step 1: Prepare Repository
```bash
# If you haven't already, push this code to GitHub
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Deploy to Render

1. Go to **[render.com](https://render.com)** and sign up (free, no credit card)

2. Click **"New +"** → **"Web Service"**

3. Connect your **GitHub repository**

4. Render auto-detects the configuration! Just click:
   - ✅ **"Create Web Service"**

5. **Wait 5-10 minutes** (first build takes time)

6. **Done!** Your app is live at: `https://your-app-name.onrender.com`

### Step 3: Create Your First Account

1. Open your deployed app
2. Click **"Sign up here"**
3. Choose **"Individual Account"** (easiest)
4. Fill in:
   - Name: John Doe
   - Email: john@example.com
   - Password: **TestPass123** (needs uppercase, lowercase, digit)
5. Click **"Create Account"**
6. **Sign in!**

## 🎉 You're Live!

Your Hospital KPI Dashboard is now:
- ✅ Deployed to the cloud
- ✅ Accessible via HTTPS
- ✅ Has working authentication
- ✅ 100% free
- ✅ Auto-deploys on git push

## 📱 Access Your Dashboard

- **Your URL**: `https://your-app-name.onrender.com`
- **Share with team**: Send them the URL
- **Company accounts**: Register as company, share Company ID with employees

## ⚡ Alternative Platforms

### Railway (Also Free)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

### Fly.io
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch
fly deploy
```

## 🔧 Customization

Want to customize before deploying?

1. **Change app name**: Edit `render.yaml` → change `name:`
2. **Add features**: Edit code, commit, push (auto-deploys!)
3. **Environment vars**: Add in Render dashboard → Environment

## 📚 Full Documentation

- **Complete deployment guide**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Authentication setup**: See [AUTH_QUICKSTART.md](AUTH_QUICKSTART.md)
- **Full auth docs**: See [AUTHENTICATION_GUIDE.md](AUTHENTICATION_GUIDE.md)

## 🐛 Issues?

**App won't start?**
- Check Render logs: Dashboard → Logs tab
- Most common: Wait for first build to complete (10 min)

**Database issues?**
- Free tier has ephemeral storage (resets on sleep)
- Users need to re-register after 15 min inactivity
- For persistent DB: Add PostgreSQL in Render (also free!)

## 💡 Pro Tips

1. **Keep app awake**: Use [UptimeRobot](https://uptimerobot.com) to ping every 5 min
2. **Custom domain**: Add in Render dashboard (free HTTPS included)
3. **Monitor**: Render dashboard shows all activity
4. **Update**: Just `git push` - auto-deploys!

---

**Deployment Time**: 5 minutes
**Cost**: $0
**Difficulty**: ⭐ Easy
**URL**: Your own HTTPS URL

Need help? Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions!
