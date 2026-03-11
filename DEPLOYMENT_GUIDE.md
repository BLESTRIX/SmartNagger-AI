# 🚀 SmartNaggar AI - Deployment Guide

This guide covers deploying SmartNaggar AI to various platforms using **FREE** resources.

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure you have:

- ✅ Supabase account created
- ✅ Database schema setup complete
- ✅ Storage bucket created
- ✅ Gmail app password generated
- ✅ All secrets/credentials ready
- ✅ Code tested locally

---

## 🌐 Option 1: Streamlit Community Cloud (Recommended)

**Cost:** 100% FREE
**Best For:** Quick deployment, demos, hackathons

### Step-by-Step:

#### 1. Prepare Repository

```bash
# Initialize git if not already
git init

# Create .gitignore
cat > .gitignore << EOL
venv/
__pycache__/
*.pyc
.env
.streamlit/secrets.toml
*.db
.DS_Store
EOL

# Commit all files
git add .
git commit -m "Initial commit for deployment"
```

#### 2. Push to GitHub

```bash
# Create new repo on GitHub first, then:
git remote add origin https://github.com/yourusername/smartnaggar-ai.git
git branch -M main
git push -u origin main
```

#### 3. Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect GitHub account
4. Select your repository
5. Set main file: `app.py`
6. Click "Advanced settings"
7. Add secrets (paste from your local `.streamlit/secrets.toml`)
8. Click "Deploy"!

Your app will be live at: `https://smartnaggar-ai.streamlit.app`

#### 4. Setup Admin Page

After main app deploys:
1. Go to app settings
2. Add `pages/admin.py` as additional page
3. Redeploy

---

## 🤗 Option 2: Hugging Face Spaces

**Cost:** 100% FREE
**Best For:** AI/ML projects, good visibility

### Step-by-Step:

#### 1. Create Space

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Name: `smartnaggar-ai`
4. License: MIT
5. SDK: **Streamlit**
6. Hardware: CPU Basic (free)

#### 2. Upload Files

```bash
# Clone your space
git clone https://huggingface.co/spaces/yourusername/smartnaggar-ai
cd smartnaggar-ai

# Copy project files
cp -r /path/to/your/project/* .

# Create README for Space
cat > README.md << EOL
---
title: SmartNaggar AI
emoji: 🧠
colorFrom: purple
colorTo: pink
sdk: streamlit
sdk_version: 1.29.0
app_file: app.py
pinned: false
---

# SmartNaggar AI - Civic Problem Reporter
[Your README content]
EOL

# Push
git add .
git commit -m "Initial deployment"
git push
```

#### 3. Add Secrets

1. Go to Space settings
2. Click "Repository secrets"
3. Add each secret:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SENDER_EMAIL`
   - `SENDER_PASSWORD`
   - etc.

#### 4. Access

Your app: `https://huggingface.co/spaces/yourusername/smartnaggar-ai`

---

## ⚡ Option 3: Railway.app

**Cost:** FREE tier with $5/month credit
**Best For:** Production-like environment

### Step-by-Step:

#### 1. Create Account
- Go to https://railway.app
- Sign up with GitHub

#### 2. Create Project
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize
railway init

# Link to project
railway link
```

#### 3. Configure

Create `railway.json`:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "streamlit run app.py --server.port $PORT",
    "healthcheckPath": "/_stcore/health"
  }
}
```

#### 4. Add Environment Variables

```bash
railway variables set SUPABASE_URL="your_url"
railway variables set SUPABASE_KEY="your_key"
railway variables set SENDER_EMAIL="your_email"
railway variables set SENDER_PASSWORD="your_password"
```

#### 5. Deploy

```bash
railway up
```

---

## 🐳 Option 4: Docker Deployment

**For:** Self-hosting, VPS, cloud platforms

### Dockerfile

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose (with secrets)

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  streamlit:
    build: .
    ports:
      - "8501:8501"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - SENDER_EMAIL=${SENDER_EMAIL}
      - SENDER_PASSWORD=${SENDER_PASSWORD}
    env_file:
      - .env
    restart: unless-stopped
```

### Deploy:

```bash
# Build
docker build -t smartnaggar-ai .

# Run
docker run -p 8501:8501 --env-file .env smartnaggar-ai

# Or with docker-compose
docker-compose up -d
```

---

## 🌍 Option 5: Heroku

**Cost:** FREE tier available
**Best For:** Easy scaling

### Step-by-Step:

#### 1. Create Files

**Procfile:**
```
web: sh setup.sh && streamlit run app.py
```

**setup.sh:**
```bash
mkdir -p ~/.streamlit/

echo "\
[general]\n\
email = \"your-email@domain.com\"\n\
" > ~/.streamlit/credentials.toml

echo "\
[server]\n\
headless = true\n\
enableCORS=false\n\
port = $PORT\n\
" > ~/.streamlit/config.toml
```

#### 2. Deploy

```bash
# Login to Heroku
heroku login

# Create app
heroku create smartnaggar-ai

# Add buildpack
heroku buildpacks:add --index 1 heroku/python

# Set config vars
heroku config:set SUPABASE_URL="your_url"
heroku config:set SUPABASE_KEY="your_key"

# Deploy
git push heroku main
```

---

## 🔒 Security Best Practices

### Never Commit Secrets!

Always add to `.gitignore`:
```
.env
.streamlit/secrets.toml
*.db
__pycache__/
venv/
```

### Use Environment Variables

```python
# Good ✅
supabase_url = os.getenv("SUPABASE_URL")

# Bad ❌
supabase_url = "https://hardcoded-url.supabase.co"
```

### Rotate Credentials

- Change passwords regularly
- Use different passwords for each service
- Enable 2FA where possible

---

## 📊 Post-Deployment

### Monitor Your App

1. **Streamlit Cloud:**
   - Check logs in dashboard
   - Monitor usage stats

2. **Supabase:**
   - Check database usage
   - Monitor API requests
   - Review storage usage

### Update Your App

```bash
# Make changes locally
git add .
git commit -m "Update: feature description"
git push origin main

# Auto-deploys on most platforms!
```

### Custom Domain (Optional)

1. **Streamlit Cloud:** Settings > Custom domain
2. **Heroku:** `heroku domains:add yourdomain.com`
3. **Railway:** Settings > Domains

---

## 🐛 Common Deployment Issues

### Issue: App won't start
**Solution:** Check logs for missing dependencies or environment variables

### Issue: Database connection fails
**Solution:** Verify Supabase URL and key are correct

### Issue: Email not sending
**Solution:** Check Gmail app password and SMTP settings

### Issue: Out of memory
**Solution:** 
- Use smaller Whisper model (`tiny` instead of `base`)
- Reduce batch sizes
- Upgrade to paid tier if needed

---

## 💰 Cost Comparison

| Platform | Free Tier | Limits | Best For |
|----------|-----------|--------|----------|
| **Streamlit Cloud** | Yes | 1GB RAM, 1 app | Demos, MVPs |
| **Hugging Face** | Yes | CPU Basic | AI projects |
| **Railway** | $5 credit | 500 hours | Production |
| **Heroku** | Yes | 550 hours/month | Scaling |
| **Docker/VPS** | Varies | Your server | Full control |

---

## 📈 Scaling Tips

### For High Traffic:

1. **Upgrade to paid tier**
2. **Use caching:**
   ```python
   @st.cache_data
   def expensive_function():
       pass
   ```
3. **Optimize queries**
4. **Use CDN for images**
5. **Implement rate limiting**

---

## ✅ Deployment Checklist

Before going live:

- [ ] Test all features locally
- [ ] All secrets configured
- [ ] Database schema applied
- [ ] Storage bucket created
- [ ] Email notifications working
- [ ] Admin login works
- [ ] PDF generation works
- [ ] Maps displaying correctly
- [ ] AI models loading
- [ ] Error handling tested
- [ ] Mobile responsive
- [ ] Documentation complete

---

## 🎉 You're Live!

Once deployed, share your app:
- 📱 Post on social media
- 🏆 Submit to hackathon judges
- 📧 Email stakeholders
- 💼 Add to portfolio

---

## 📞 Support

Need help deploying?
- 📚 Check platform-specific docs
- 💬 Join Streamlit community
- 🐛 Open GitHub issue
- 📧 Contact support

---

**Happy Deploying! 🚀**

*SmartNaggar AI - Making Cities Better Together* 🏙️