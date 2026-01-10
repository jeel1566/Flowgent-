# Flowgent Troubleshooting Guide

This guide helps you diagnose and fix common issues with Flowgent.

## Quick Diagnosis

### 1. Backend Health Check

```bash
cd backend
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "mcp_connected": true
}
```

**If `mcp_connected: false`:**
- Check N8N_MCP_API_KEY in backend/.env
- Verify N8N_MCP_URL is correct
- Check network connectivity to MCP server

### 2. Common Error Messages

#### "GOOGLE_GENAI_API_KEY environment variable not set"

**Solution:**
1. Get API key from https://aistudio.google.com/apikey
2. Add to `backend/.env`:
   ```
   GOOGLE_GENAI_API_KEY=your-key-here
   ```
3. Restart backend

#### "N8N_MCP_API_KEY not set - MCP features may not work"

**Solution:**
1. Get n8n MCP API key from https://dashboard.n8n-mcp.com
2. Add to `backend/.env`:
   ```
   N8N_MCP_API_KEY=your-mcp-key-here
   ```
3. Restart backend

#### "Failed to list workflows"

**Causes:**
- n8n instance not accessible
- Invalid n8n API credentials
- CORS issues

**Solution:**
1. Verify n8n instance URL and API key in extension settings
2. Test n8n API directly:
   ```bash
   curl https://your-n8n-instance.com/api/v1/workflows \
     -H "X-N8N-API-KEY: your-api-key"
   ```
3. Check backend logs for detailed error

## Extension Issues

### Dashboard Shows "Loading..." Forever

**Causes:**
- Backend not running
- Wrong backend URL in settings
- CORS issues
- No n8n credentials configured

**Solution:**
1. Open extension Settings tab
2. Verify backend URL (should be http://localhost:8000 or your Cloud Run URL)
3. Click "Test Connection" - should show green checkmark
4. Configure n8n instance URL and API key
5. Check browser console for errors (F12)

### Information Hand Tooltips Not Showing

**Causes:**
- Not on n8n page
- Content script not loaded
- Backend not accessible

**Solution:**
1. Make sure you're on an n8n workflow page
2. Check browser console (F12) for errors
3. Look for "Flowgent: n8n page detected" message
4. Reload page
5. Check if backend /api/node-info endpoint works:
   ```bash
   curl http://localhost:8000/api/node-info/n8n-nodes-base.httpRequest
   ```

### Chat Returns Errors

**Common Errors:**

1. **"API Key Not Configured"**
   - Add GOOGLE_GENAI_API_KEY to backend/.env
   - Restart backend

2. **"Failed to retrieve workflows"**
   - Configure n8n credentials in extension settings
   - Or set N8N_MCP_API_KEY in backend/.env

3. **"Connection refused"**
   - Start backend: `cd backend && python main.py`
   - Check backend URL in extension settings

## Backend Issues

### Backend Won't Start

**Error: "Module not found"**
```bash
cd backend
pip install -r requirements.txt
```

**Error: "Port already in use"**
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9
# Or use different port
PORT=8001 python main.py
```

**Error: "ImportError: google.adk"**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install google-adk google-genai
```

### Backend Running but Endpoints Fail

**Check logs:**
```bash
cd backend
python main.py
```

Look for:
- ✅ "Environment variables loaded"
- ✅ "INFO:     Started server process"
- ❌ Any ERROR or WARNING messages

**Test endpoints manually:**
```bash
# Health check
curl http://localhost:8000/health

# List workflows (requires n8n config)
curl http://localhost:8000/api/workflows \
  -H "X-N8N-Instance-URL: https://your-n8n.com" \
  -H "X-N8N-API-Key: your-key"

# Chat (requires Gemini API key)
curl http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "context": null, "n8n_config": null}'
```

## Environment Variables

### Required for Basic Operation

```bash
# backend/.env
GOOGLE_GENAI_API_KEY=your-gemini-api-key  # Required for AI chat
```

### Optional but Recommended

```bash
# backend/.env
N8N_MCP_API_KEY=your-mcp-key              # For MCP-based n8n access
N8N_MCP_URL=https://api.n8n-mcp.com/mcp   # MCP server URL
ALLOWED_ORIGINS=*                          # CORS config
PORT=8000                                  # Server port
HOST=0.0.0.0                              # Server host
```

## Debugging Steps

### 1. Enable Debug Logging

Edit `backend/main.py`:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. Check Browser Console

1. Open extension side panel
2. Press F12 to open DevTools
3. Look for errors in Console tab
4. Check Network tab for failed requests

### 3. Check Backend Logs

Run backend in foreground to see all logs:
```bash
cd backend
python main.py
```

### 4. Test with Curl

Test each endpoint individually:
```bash
# Health
curl -v http://localhost:8000/health

# Node info
curl -v http://localhost:8000/api/node-info/n8n-nodes-base.httpRequest

# Workflows (with headers)
curl -v http://localhost:8000/api/workflows \
  -H "X-N8N-Instance-URL: https://n8n.example.com" \
  -H "X-N8N-API-Key: your-key"
```

## Still Having Issues?

### Collect Debug Information

1. Backend version:
   ```bash
   curl http://localhost:8000/health
   ```

2. Backend logs (last 50 lines):
   ```bash
   # If running with systemd/docker:
   journalctl -u flowgent-backend -n 50
   # Or check your log file
   ```

3. Browser console errors:
   - Open DevTools (F12)
   - Copy any red errors from Console

4. Extension version:
   - Go to chrome://extensions
   - Find Flowgent
   - Note the version number

### Create Issue Report

Include:
- What you were trying to do
- What happened instead
- Error messages from backend logs
- Error messages from browser console
- Steps to reproduce
- Your environment (OS, Chrome version, etc.)

## Performance Issues

### Backend is Slow

- **Gemini API Rate Limits:** Wait a few seconds between requests
- **MCP Timeouts:** Check N8N_MCP_URL connectivity
- **Large Workflows:** Workflow operations may take time

### Extension is Slow

- **Clear Cache:**
  - Open chrome://extensions
  - Find Flowgent
  - Click "Clear data"
  - Reload extension

- **Reduce Polling:** Dashboard auto-refreshes every 30s
- **Check Network:** Slow backend connection

## Security Notes

- Never commit API keys to git
- Use environment variables for secrets
- Backend should only accept requests from trusted origins
- Use HTTPS in production
- Rotate API keys regularly

## Getting Help

- Check this troubleshooting guide first
- Review backend logs for specific errors
- Test endpoints with curl to isolate issues
- Check browser console for frontend errors
- Ensure all environment variables are set correctly
