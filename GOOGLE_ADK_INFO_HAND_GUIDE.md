# Google ADK & Information Hand Implementation Guide

This document describes the implementation of Google ADK (Agent Development Kit) integration and the enhanced Information Hand feature for the Flowgent Chrome extension.

## Table of Contents

1. [Google ADK Configuration](#google-adk-configuration)
2. [Information Hand Feature](#information-hand-feature)
3. [API Endpoints](#api-endpoints)
4. [Extension Changes](#extension-changes)
5. [Usage](#usage)

---

## Google ADK Configuration

### Backend Setup

The backend uses Google's Agent Development Kit (ADK) with Gemini 2.0 Flash for intelligent conversations about n8n workflows.

#### Files Modified:
- `backend/agent/flowgent_agent.py` - Core ADK agent configuration
- `backend/agent/config.py` - Agent settings and instructions
- `backend/api/routes.py` - API endpoints for chat and streaming

#### Key Features:
- **Async Streaming**: Support for real-time streaming responses using Server-Sent Events (SSE)
- **Session Management**: In-memory session service for conversation context
- **Tool Integration**: MCP tools wrapped as ADK tools for seamless integration
- **Error Handling**: Robust error handling with graceful degradation

#### Agent Configuration

```python
# Model Configuration
AGENT_MODEL = "gemini-2.0-flash"

# System Instruction
SYSTEM_INSTRUCTION = """You are Flowgent, an expert AI assistant for n8n workflow automation.
Your goal is to help users build, debug, and understand n8n workflows..."""
```

---

## Information Hand Feature

The Information Hand is an enhanced tooltip system that appears when hovering over n8n workflow nodes.

### Features

#### 1. Mouse-Following Tooltip
- Tooltip follows mouse position smoothly
- Intelligent positioning to stay on screen
- Throttled updates for performance (~60fps)

#### 2. Click-to-Expand
- Click "Show More" for detailed information
- Expanded view includes parameters table
- Documentation link for full reference

#### 3. Keyboard Navigation
- Press `Enter` or `Space` on focused node to show tooltip
- Press `Esc` to close tooltip
- Accessible via keyboard navigation

#### 4. Action Buttons
- **Show More/Less**: Toggle detailed view
- **Copy**: Copy node info to clipboard
- **Ask AI**: Open side panel for AI assistance

#### 5. Rich Preview Data
- Emoji icon based on node type
- Category badge (Core, Trigger, AI, etc.)
- Popularity indicator
- Use cases and best practices
- Parameters table (in expanded view)

### Node Detection

The system detects n8n nodes using multiple strategies:

1. **Vue Flow Selectors**: Modern n8n uses Vue Flow canvas
   - `.vue-flow__node`
   - `[class*="CanvasNode"]`
   - `[class*="NodeWrapper"]`

2. **Data Attributes**: n8n stores node metadata
   - `[data-node-type]`
   - `[data-node-name]`
   - `[data-test-id*="node"]`

3. **Class Name Parsing**: Fallback for legacy nodes
   - `.node-wrapper`
   - `.n8n-node`

4. **URL Patterns**: Detect n8n pages
   - `/workflow/`
   - `n8n.io`
   - `n8n.cloud`

### Node Type Normalization

Node types are normalized to n8n format:
```
httprequest → n8n-nodes-base.httpRequest
slack → n8n-nodes-base.slack
scheduleTrigger → n8n-nodes-base.scheduleTrigger
```

---

## API Endpoints

### Chat Endpoints

#### POST /api/chat
Standard chat endpoint with full response.

```json
// Request
{
    "message": "Create a workflow that sends Slack notifications",
    "context": { "session_id": "user_session" },
    "n8n_config": {
        "instance_url": "https://your-n8n.com",
        "api_key": "your-api-key"
    }
}

// Response
{
    "response": "I've created a workflow for you...",
    "workflow_data": { ... },
    "action": "workflow_created"
}
```

#### POST /api/chat/stream
Streaming chat endpoint using Server-Sent Events.

```javascript
// Usage
const response = await fetch('/api/chat/stream', {
    method: 'POST',
    body: JSON.stringify({ message: "Create a workflow..." })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

for await (const chunk of reader) {
    const lines = chunk.split('\n');
    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            if (data.chunk) {
                console.log(data.chunk); // AI response chunk
            }
        }
    }
}
```

### Information Hand Endpoints

#### GET /api/node-preview/{node_type}
Get optimized preview data for Information Hand tooltip.

```json
// Request
GET /api/node-preview/n8n-nodes-base.httpRequest?preview_type=brief

// Response
{
    "success": true,
    "preview": {
        "node_type": "n8n-nodes-base.httpRequest",
        "display_name": "HTTP Request",
        "short_description": "Make HTTP requests to external services...",
        "icon_emoji": "🌐",
        "category": "Core",
        "popularity": "⭐⭐⭐⭐⭐",
        "use_cases": [
            "Fetch data from APIs",
            "Send webhooks",
            "Integrate with external services"
        ],
        "best_practices": [
            "Always handle errors",
            "Use proper timeout settings"
        ]
    }
}
```

**Parameters:**
- `preview_type`: `"brief"` (default) for quick tooltip, `"full"` for detailed view

#### GET /api/node-search
Quick search for nodes with preview data.

```json
// Request
GET /api/node-search?query=http&limit=5

// Response
{
    "success": true,
    "query": "http",
    "previews": [
        {
            "node_type": "n8n-nodes-base.httpRequest",
            "display_name": "HTTP Request",
            "short_description": "...",
            "icon_emoji": "🌐",
            "category": "Core"
        }
    ]
}
```

### Node Info Endpoint (Legacy)

#### GET /api/node-info/{node_type}
Original node info endpoint (still available).

---

## Extension Changes

### Content Scripts

#### n8n-detector.js
- Enhanced node detection with Vue Flow selectors
- Exponential backoff for SPA detection
- Improved node type extraction
- Keyboard accessibility support

#### tooltip.js
- Complete rewrite with modern UI
- Mouse-following with throttled updates
- Click-to-expand functionality
- Copy to clipboard
- Ask AI integration
- Loading animations
- Error states

### Background Script

New handlers added:
- `fetchNodePreview`: Optimized endpoint for preview data
- `openSidePanelWithContext`: Open side panel with AI context
- `getNodePreview`: Cache management for previews
- `cacheNodePreview`: Cache preview data

### Side Panel

#### chat.js
- Context awareness for Information Hand integration
- Auto-populates chat input when opened from tooltip

---

## Usage

### Running the Backend

```bash
cd backend
python main.py
# Or with uvicorn:
uvicorn main:app --reload --port 8000
```

### Loading the Extension

1. Open Chrome: `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension` folder

### Testing Information Hand

1. Navigate to your n8n instance (e.g., n8n.cloud or local instance)
2. Open a workflow
3. Hover over any node
4. Information Hand tooltip should appear
5. Click "Show More" for detailed info
6. Click "Ask AI" to open side panel with context

### Testing Streaming Chat

```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a workflow that sends emails"}' \
  --no-buffer
```

---

## Performance Optimizations

1. **Throttled Mouse Events**: Tooltip position updates throttled to 60fps
2. **Debounced Scanning**: Node scanning debounced to avoid excessive DOM queries
3. **Smart Caching**: Different cache durations for brief (1hr) vs full (24hr) previews
4. **Lazy Loading**: Extended content only loaded on demand
5. **Minimal DOM Queries**: Cached element references

---

## Error Handling

1. **Graceful Degradation**: Falls back to basic info if MCP unavailable
2. **Timeout Handling**: 10s timeout for node info requests
3. **Cache Expiry**: Automatic cleanup of expired cache entries
4. **Network Errors**: User-friendly error messages in tooltips

---

## Security Considerations

1. **XSS Prevention**: All user content escaped in tooltips
2. **CORS Protection**: Backend validates origin headers
3. **API Key Security**: Keys stored in extension storage, not in code
4. **Content Security Policy**: Extension uses appropriate CSP headers

---

## Future Enhancements

1. **Pinned Tooltips**: Allow pinning tooltips for comparison
2. **Quick Actions**: Add buttons for common actions in tooltip
3. **Node Search**: Add search functionality in tooltip
4. **Favorites**: Allow saving frequently used nodes
5. **Dark/Light Mode**: Match system preference
6. **Accessibility**: Screen reader support with ARIA labels
