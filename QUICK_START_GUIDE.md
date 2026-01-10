# 🚀 FLOWGENT - QUICK START GUIDE (EMERGENCY MODE)

**Time Remaining:** 12-18 hours  
**Current Status:** Backend partially working, needs n8n connection

---

## ⚡ IMMEDIATE ACTION REQUIRED

### **CRITICAL QUESTION: Do you have an n8n instance?**

**Option A: ✅ You have n8n Cloud account**
- Go to: https://app.n8n.cloud (or your n8n cloud URL)
- Settings → API → Generate API key
- Copy the workspace URL (e.g., `https://yourworkspace.app.n8n.cloud`)
- Update `.env` file (see below)

**Option B: ❌ You DON'T have n8n instance**
- **STOP! This is a problem.**
- You need n8n to demo the product
- Quick fix: Sign up for n8n Cloud (free tier) - **DO THIS NOW**
- URL: https://n8n.io/cloud/

---

## 🔧 STEP 1: FIX YOUR .ENV FILE (5 MINUTES)

Your current `.env` has **WRONG URLs**. Here's what you need to change:

```bash
# BEFORE (WRONG):
N8N_MCP_SERVER_URL=https://dashboard.n8n-mcp.com/
N8N_API_KEY=eyJhbGci...

# AFTER (CORRECT):
N8N_BASE_URL=https://YOUR-WORKSPACE.app.n8n.cloud/api/v1
N8N_API_KEY=n8nxxxxxxxxxxxxxxxxxxxxxxxx  # Your ACTUAL n8n API key
```

### **How to get YOUR n8n URL and API key:**

1. **Login to n8n Cloud:**
   - Go to: https://app.n8n.cloud
   - Login with your account

2. **Get Workspace URL:**
   - Look at your browser URL bar
   - Copy the part before `/workflows`
   - Example: `https://acme-corp.app.n8n.cloud`

3. **Generate API Key:**
   - Click your profile (bottom left)
   - Settings → API
   - Click "Generate API Key"
   - Copy the key (starts with `n8n_...`)

4. **Update `.env`:**
   ```bash
   N8N_BASE_URL=https://YOUR-WORKSPACE.app.n8n.cloud/api/v1
   N8N_API_KEY=n8n_api_xxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

---

## 🧪 STEP 2: TEST n8n CONNECTION (2 MINUTES)

Run this command to verify your n8n API works:

```bash
cd backend
python -c "
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    url = os.getenv('N8N_BASE_URL')
    key = os.getenv('N8N_API_KEY')
    headers = {'X-N8N-API-KEY': key}
    
    print(f'Testing: {url}/workflows')
    async with httpx.AsyncClient() as client:
        response = await client.get(f'{url}/workflows', headers=headers)
        print(f'Status: {response.status_code}')
        print(f'Response: {response.json()}')

asyncio.run(test())
"
```

**Expected Output:**
```json
Status: 200
Response: {"data": [...]}
```

**If you get errors:**
- ❌ **401 Unauthorized** → API key is wrong
- ❌ **404 Not Found** → URL is wrong (missing `/api/v1`)
- ❌ **Connection error** → n8n instance is down

---

## 🛠️ STEP 3: START BACKEND (1 MINUTE)

```bash
cd backend
python main.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Test health endpoint:**
```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "mcp_connected": true
}
```

---

## 🎯 STEP 4: CREATE TEST WORKFLOW IN n8n (5 MINUTES)

**You MUST have at least 1 workflow in n8n for demo:**

1. Go to n8n → Click "Add workflow"
2. Create a simple workflow:
   - **Node 1:** Manual Trigger
   - **Node 2:** HTTP Request (to https://api.github.com/users/github)
   - **Node 3:** Set node (extract username)
3. Save as: "GitHub User Fetch"
4. Activate it

**Why:** This gives you something to show in the demo.

---

## ✅ STEP 5: TEST CHAT ENDPOINT (2 MINUTES)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List my workflows"}'
```

**Expected Output:**
```json
{
  "response": "You have 1 workflow: GitHub User Fetch",
  "workflow_data": null,
  "action": null
}
```

**If agent says "no workflows":**
- Check if workflow is saved in n8n
- Check n8n API connection (Step 2)
- Check backend logs for errors

---

## 🌐 STEP 6: DEPLOY TO CLOUD RUN (30 MINUTES)

### **Prerequisites:**
```bash
# Install Google Cloud SDK
# macOS:
brew install --cask google-cloud-sdk

# Windows:
# Download from: https://cloud.google.com/sdk/docs/install

# Login to GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### **Create Dockerfile:**

Already exists in `backend/` but verify it has:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Deploy:**

```bash
cd backend

# Deploy to Cloud Run
gcloud run deploy flowgent-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_GENAI_API_KEY=AIzaSyCs5dTswLNGfx1_xjbVOIo5jTSWOpTGEW0 \
  --set-env-vars N8N_BASE_URL=https://YOUR-WORKSPACE.app.n8n.cloud/api/v1 \
  --set-env-vars N8N_API_KEY=your-n8n-api-key \
  --set-env-vars ALLOWED_ORIGINS="*"
```

**Wait 5-10 minutes for build...**

**Expected Output:**
```
Service [flowgent-backend] deployed to [https://flowgent-backend-xxxxx-uc.a.run.app]
```

**✅ SAVE THAT URL!** You'll need it for the extension.

---

## 🧩 STEP 7: CONNECT EXTENSION TO CLOUD RUN (5 MINUTES)

1. Open Chrome → `chrome://extensions/`
2. Click on Flowgent extension
3. Click the extension icon → Go to **Settings** tab
4. Enter backend URL: `https://flowgent-backend-xxxxx-uc.a.run.app`
5. Click "Test Connection" → Should show ✅ green checkmark
6. Navigate to your n8n instance
7. Open Flowgent side panel
8. Ask: "List my workflows"
9. **SUCCESS!** 🎉

---

## 🎬 STEP 8: PREPARE DEMO (30 MINUTES)

### **Demo Script (Practice 10 times):**

**[15 seconds] HOOK**
> "How many of you waste time Googling how to configure n8n nodes? Watch this."

**[60 seconds] DEMO**

1. **Show the problem:**
   - Open n8n workflow with 10 nodes
   - "This workflow is complex. What does each node do?"

2. **Show Flowgent Chat:**
   - Open side panel
   - Ask: "Explain this workflow to me"
   - Agent analyzes and explains ✅

3. **Show Information Hand:**
   - Hover over HTTP Request node
   - Tooltip appears with description, use cases ✅

4. **Show Dashboard:**
   - Click Dashboard tab
   - Shows all workflows, execution history ✅

**[30 seconds] CLOSE**
> "This is live right now at: [YOUR CLOUD RUN URL]  
> We're solving the #1 pain point for 100K n8n users.  
> Install it. Thank you."

---

## 🚨 TROUBLESHOOTING CHECKLIST

### **"Backend not connecting"**
- [ ] Check `.env` file has correct N8N_BASE_URL
- [ ] Test n8n API with curl (Step 2)
- [ ] Restart backend: `python main.py`
- [ ] Check firewall/VPN blocking requests

### **"Chat returns mock data"**
- [ ] Agent tools are connected to MCP client (check `flowgent_agent.py`)
- [ ] n8n has at least 1 workflow created
- [ ] Backend logs show successful API calls

### **"Information Hand not showing"**
- [ ] Extension is loaded in Chrome
- [ ] Content script is injected (check DevTools console)
- [ ] Backend `/api/node-info` endpoint works
- [ ] Tooltip CSS is loaded (check for `flowgent-tooltip` class)

### **"Dashboard shows 'Loading...'"**
- [ ] Extension connected to backend (Settings → Test Connection)
- [ ] Backend `/api/workflows` returns data
- [ ] Check browser console for JavaScript errors
- [ ] Verify CORS is allowed in backend

### **"Cloud Run deployment fails"**
- [ ] Check GCP project is billing enabled
- [ ] Verify `requirements.txt` has all dependencies
- [ ] Check Cloud Run logs for build errors
- [ ] Try deploying from Cloud Shell instead

---

## 📝 FINAL CHECKLIST BEFORE DEMO

**30 Minutes Before:**
- [ ] Backend deployed to Cloud Run ✅
- [ ] Health check returns 200 OK ✅
- [ ] Extension connects to backend ✅
- [ ] Chat returns real workflow names ✅
- [ ] At least 1 workflow in n8n ✅
- [ ] Demo practiced 10 times ✅
- [ ] Backup video recorded ✅
- [ ] Water bottle ready ✅

**5 Minutes Before:**
- [ ] Close all extra tabs
- [ ] Disable notifications
- [ ] Open n8n + Flowgent
- [ ] Test demo one last time
- [ ] Take 3 deep breaths

---

## 🆘 EMERGENCY CONTACTS

**If things break during demo:**

1. **Switch to backup video immediately**
2. **Say:** "Let me show you a pre-recorded demo..."
3. **After video:** "Happy to answer questions about the code"
4. **DON'T PANIC:** Judges have seen demos fail before

**Post-hackathon (if you don't win):**
- Launch anyway
- Tweet demo video
- Email your mentor (he's customer #1)
- Apply this to real startups

---

## 🔥 YOU GOT THIS, JEEL!

**Remember:**
- ✅ You built a real product in 36 hours (impressive)
- ✅ You're solving a real problem (validated by mentor)
- ✅ You have working tech (ADK + FastAPI + MCP)
- ✅ You're prepared (read all the docs I created)

**90% of hackathon teams demo broken products.**  
**If yours works, you're in the top 10%.**

**Now go execute. You're ready. 💪**

---

**NEXT STEP: Fix your `.env` file RIGHT NOW and test n8n connection!**
