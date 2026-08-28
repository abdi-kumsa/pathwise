# PathWise Deployment Guide for Render

This guide walks you through deploying PathWise to Render.com for production hosting.

## 🎯 What You'll Deploy

1. **PostgreSQL Database** (managed by Render)
2. **FastAPI Backend** (Python web service)
3. **React Frontend** (static site)

## 📋 Prerequisites

1. A [Render.com](https://render.com) account (free tier available)
2. Your PathWise code pushed to GitHub/GitLab/Bitbucket
3. About 15 minutes

---

## Step 1: Push Your Code to GitHub

If you haven't already, push your PathWise project to GitHub:

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit for Render deployment"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/PathWise.git
git branch -M main
git push -u origin main
```

---

## Step 2: Create a Render Account

1. Go to [https://render.com](https://render.com)
2. Click **Get Started** and sign up (free)
3. You can sign up with GitHub to make connecting repositories easier

---

## Step 3: Deploy Using render.yaml (Recommended)

### Option A: Blueprint Deployment (Easiest)

1. Go to your [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **Blueprint**
3. Connect your GitHub repository containing PathWise
4. Render will automatically detect the `render.yaml` file
5. Review the services:
   - `pathwise-db` (PostgreSQL)
   - `pathwise-backend` (Web Service)
   - `pathwise-frontend` (Static Site)
6. Click **Apply** to deploy all services

### Set Environment Variables

After deployment starts, you need to set these environment variables:

#### For `pathwise-backend`:
1. Go to the backend service in your dashboard
2. Click **Environment** tab
3. Add these variables:

```
FRONTEND_URL=https://pathwise-frontend.onrender.com
API_PORT=10000
```

#### For `pathwise-frontend`:
1. Go to the frontend service in your dashboard
2. Click **Environment** tab
3. Add this variable:

```
VITE_API_URL=https://pathwise-backend.onrender.com
```

4. Click **Manual Deploy** → **Clear build cache & deploy** to rebuild with the new variables

---

## Step 4: Manual Deployment (Alternative)

If you prefer manual setup:

### 4.1 Create PostgreSQL Database

1. In Render Dashboard, click **New** → **PostgreSQL**
2. Name: `pathwise-db`
3. Database: `pathwise`
4. User: `pathwise`
5. Region: Choose closest to you
6. Plan: **Free**
7. Click **Create Database**
8. Wait for it to provision (2-3 minutes)

### 4.2 Deploy Backend

1. Click **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `pathwise-backend`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: leave empty
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
4. Add Environment Variables:
   ```
   DATABASE_URL=<from your pathwise-db Internal Database URL>
   API_HOST=0.0.0.0
   API_PORT=10000
   FRONTEND_URL=<will add after frontend is deployed>
   JWT_SECRET=<generate a random 32+ character string>
   JWT_EXPIRE_MINUTES=10080
   DEMO_PASSWORD=pathwise123
   ```
5. Click **Create Web Service**

### 4.3 Deploy Frontend

1. Click **New** → **Static Site**
2. Connect the same repository
3. Configure:
   - **Name**: `pathwise-frontend`
   - **Branch**: `main`
   - **Root Directory**: leave empty
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`
4. Add Environment Variable:
   ```
   VITE_API_URL=<your backend URL from step 4.2>
   ```
5. Click **Create Static Site**

### 4.4 Update CORS Settings

1. Go back to your backend service
2. Update the `FRONTEND_URL` environment variable with your frontend URL
3. Click **Manual Deploy** → **Clear build cache & deploy**

---

## Step 5: Initialize Database Schema

After the backend deploys successfully, you need to run the database schema:

1. Go to your `pathwise-backend` service
2. Click **Shell** tab
3. Run these commands:

```bash
cd backend
python -c "
import os
os.environ.setdefault('DATABASE_URL', '$(echo $DATABASE_URL)')
from db.init_db import init_database
init_database()
print('Database initialized successfully!')
"
```

Alternatively, you can run the schema manually in the PostgreSQL dashboard:
1. Go to `pathwise-db` service
2. Click **Connect** → **External Connection**
3. Use the provided credentials with your favorite PostgreSQL client
4. Run the SQL from `backend/db/schema.sql`

---

## Step 6: Access Your Deployed App

Your frontend will be available at:
```
https://pathwise-frontend.onrender.com
```

Your backend API will be available at:
```
https://pathwise-backend.onrender.com
```

API docs (Swagger):
```
https://pathwise-backend.onrender.com/docs
```

---

## 🔐 Default Login Credentials

All accounts use the password: `pathwise123`

| Username | Role |
|----------|------|
| student | Student |
| mol | Ministry of Labour |
| moe | Ministry of Education |
| university | University |
| admin | Administrator |

**⚠️ Important**: Change the `DEMO_PASSWORD` environment variable and use the admin panel to create proper accounts before sharing with your client!

---

## 📊 Monitoring & Logs

### View Logs
- Go to your service in Render dashboard
- Click **Logs** tab
- Real-time logs will appear

### Monitor Performance
- Click **Metrics** tab to see:
  - CPU usage
  - Memory usage
  - Request count
  - Response times

---

## 🚨 Troubleshooting

### Backend fails to start
**Check logs for**:
- Database connection errors → Verify `DATABASE_URL` is correct
- Missing dependencies → Redeploy with "Clear build cache"
- Port issues → Ensure using `$PORT` environment variable

### Frontend can't connect to backend
**Fix**:
1. Check `VITE_API_URL` in frontend environment variables
2. Ensure backend URL is correct (no trailing slash)
3. Check backend CORS settings via `FRONTEND_URL`
4. Redeploy frontend with "Clear build cache & deploy"

### Database schema not initialized
**Fix**:
1. Use the Shell method in Step 5
2. Or manually connect to PostgreSQL and run `schema.sql`

### Free tier limitations
- Backend sleeps after 15 minutes of inactivity (first request will be slow)
- Database has 1GB storage limit
- 750 hours/month free (enough for one service running 24/7)

---

## 🔄 Updating Your Deployment

When you push changes to your GitHub repository:

1. **Automatic deployment**:
   - Render automatically deploys when you push to `main` branch
   - You can disable this in service settings

2. **Manual deployment**:
   - Go to service dashboard
   - Click **Manual Deploy** → **Deploy latest commit**

---

## 💰 Cost Breakdown (Free Tier)

✅ **PostgreSQL**: Free (1GB storage)
✅ **Backend**: Free (750 hours/month)
✅ **Frontend**: Free (100GB bandwidth/month)

**Total**: $0/month

For production with 24/7 uptime:
- PostgreSQL: $7/month (Starter plan)
- Backend: $7/month (Starter plan)
- Frontend: Free
**Total**: $14/month

---

## 🎉 You're Done!

Share this URL with your client:
```
https://pathwise-frontend.onrender.com
```

Remember to:
- [ ] Change default passwords
- [ ] Create proper user accounts via admin panel
- [ ] Update JWT_SECRET to a secure random value
- [ ] Monitor the logs for any issues
- [ ] Set up custom domain (optional, $0 on Render)

---

## 📞 Support

If you encounter issues:
1. Check Render's status page: https://status.render.com
2. Review Render docs: https://render.com/docs
3. Check your service logs in Render dashboard
