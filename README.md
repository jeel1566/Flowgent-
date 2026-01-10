# Flowgent

**An AI-powered agentic assistant for n8n automation workflows**

## 🚀 Project Structure

This repository contains two main components:

### 1. Chrome Extension (`/extension`)
Lightweight UI that runs in the browser alongside n8n.

**Features:**
- AI Chat Assistant for workflow help
- Information Hand (node tooltips)
- Dashboard with execution logs and input/output forms

### 2. Python Backend (`/backend`)
AI agent logic powered by Google Agent Development Kit and n8n MCP.

**Tech Stack:**
- FastAPI
- Google Agent Development Kit
- Gemini 2.0 Flash
- n8n MCP Server

## 📦 Setup

### Extension Setup
```bash
cd extension
# Load unpacked extension in chrome://extensions/
```

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## 🚢 Deployment

Backend deploys to Google Cloud Run:
```bash
cd backend
gcloud run deploy flowgent-backend --source .
```

## 👥 Team

Built for Agentic+ Product Hackathon by Team Flowgent

## 📄 License

MIT
