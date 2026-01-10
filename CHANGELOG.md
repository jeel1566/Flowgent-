# Changelog

All notable changes to Flowgent will be documented in this file.

## [2.0.0] - 2025-01-10

### 🎉 Major Feature: WORKFLOW UPDATE/EDIT CAPABILITY

#### Added
- **UPDATE WORKFLOW functionality** - Complete workflow editing and fixing via chat
  - New agent tool: `update_workflow(workflow_id, updates_json)`
  - New API endpoint: `PUT /api/workflows/{workflow_id}`
  - New MCP client method: `update_workflow()`
  - New direct n8n client method: `update_workflow()`
  - New Pydantic schema: `UpdateWorkflowRequest`
  - New extension API method: `api.updateWorkflow()`

#### Enhanced
- **Agent capabilities** - Can now edit, modify, and fix existing workflows
  - Updated system instruction with edit/update guidelines
  - Agent responds to: "edit", "update", "modify", "fix" commands
  - Full workflow lifecycle: create → read → update → execute
  
- **Chat interactions** - Natural language workflow editing
  - Example: "Add an If node to workflow #123"
  - Example: "Fix the broken connection in workflow #456"
  - Example: "Rename workflow #789 to 'Daily Reports'"

#### Technical Details
- Updates can modify: name, nodes, connections, active status
- Partial updates supported (only update specified fields)
- Preserves unchanged workflow properties
- Full error handling and logging
- Works with both MCP and direct n8n API clients

### 📊 Feature Status
All 3 main features are now **FULLY OPERATIONAL**:
1. ✅ Chat - Create, Edit, Fix workflows
2. ✅ Dashboard - Full workflow management
3. ✅ Information Hand - Node previews

### 🔧 Technical Changes
- Added 6 new functions across 5 files
- Updated agent tools from 9 to 10
- Updated API endpoints from 8 to 9
- All code follows existing patterns and conventions
- Comprehensive logging and error handling
- Zero breaking changes

### 📝 Documentation
- Created `FEATURE_STATUS.md` - Comprehensive feature documentation
- Updated `README.md` - Added update workflow examples
- Updated agent system instruction
- In-code documentation for all new functions

---

## [1.0.0] - 2025-01-09

### Initial Release

#### Features
- **AI Chat Assistant** powered by Google Gemini 2.0 Flash
  - Natural language workflow creation
  - Node search and documentation
  - Workflow templates
  
- **Information Hand** - Hover tooltips for n8n nodes
  - Automatic node detection
  - Beautiful glassmorphism UI
  - Caching for performance
  
- **Dashboard** - Workflow and execution management
  - List all workflows
  - View execution history
  - Execute workflows with input data
  
#### Architecture
- FastAPI backend with Google ADK
- Chrome extension (Manifest V3)
- MCP integration for n8n
- Direct n8n API client
- Comprehensive logging

#### Infrastructure
- Google Cloud Run deployment ready
- Environment variable configuration
- Health check endpoint
- CORS support for extensions

---

## Legend
- ✨ NEW - New feature or capability
- 🎉 MAJOR - Major version release
- 🔧 TECHNICAL - Technical/internal changes
- 📝 DOCS - Documentation updates
- 🐛 FIX - Bug fixes
- ⚡ PERF - Performance improvements
