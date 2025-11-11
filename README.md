# N8N Monitor MCP Server

A Model Context Protocol (MCP) server that provides real-time monitoring, health analysis, and error debugging for n8n workflow automation instances.

## 🎯 Overview

This MCP server connects Claude AI to your n8n instance, enabling intelligent monitoring and debugging of workflow executions through natural language conversations.

**Key Capabilities:**
- 📊 Real-time workflow health monitoring
- 🔍 Detailed error forensics and debugging
- 📈 Execution metrics and KPI tracking
- 🚨 Automated failure detection and alerting

## 🏗️ Architecture
```
Claude Desktop ←→ MCP Server ←→ N8nMonitor ←→ n8n Webhook ←→ n8n API
```

The server acts as a bridge between Claude and your n8n instance, translating natural language requests into structured API calls.

## 📦 Installation

### Prerequisites
- Python 3.10+
- Self-hosted n8n instance
- Claude Desktop app

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd mcp_n8n
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
# or using uv
uv pip install -r requirements.txt
```

3. **Configure environment variables**

Create a `.env` file in the project root:
```bash
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/your-webhook-id
```

4. **Configure n8n webhook**

Use the n8n workflow shared [here] that contains three webhooks connected to to your n8n instance to handles these actions:
- `get_active_workflows`: get all the workflows that are currently active in your instancce
- `get_workflow_executions`
- `get_execution_details`

See [n8n API reference](https://docs.n8n.io/api/api-reference/#tag/execution/get/executions) for implementation details.

5. **Add to Claude Desktop**

Edit your Claude Desktop config file that you can reach in Claude Desktop UI: `File > Settings > Developer > Edit Config`


```json
{
"n8n-monitor": {
    "command": "wsl",
    "args": [
    "-d",
    "Ubuntu",
    "bash",
    "-lc",
    "cd ~/path/to/mcp_n8n && uv run --with mcp[cli] mcp run server.py"
    ]
}
```

## 🚀 Usage

Once configured, you can interact with your n8n instance through Claude using natural language:

### Example Queries

**Health Monitoring:**
- "Show me all active workflows"
- "What's the health status of my n8n instance?"
- "Generate a health report for the last 100 executions"

**Error Debugging:**
- "Debug errors in workflow `7uvA2XQPMB5l4kI5`"
- "What's causing failures in my data processing workflow?"
- "Show me error patterns across all workflows"

**Execution Tracking:**
- "Show me execution metrics for the last 50 runs"
- "Which workflows are failing most frequently?"
- "What's the average execution time?"

## 🛠️ Available Tools

### 1. `get_active_workflows()`
Lists all active workflows with IDs, names, and metadata.

**Returns:**
- Total active workflows count
- Workflow details (ID, name, created/updated dates)
- Summary statistics

### 2. `get_workflow_executions(limit=50, include_kpis=True)`
Fetches recent workflow executions with performance metrics.

**Parameters:**
- `limit`: Number of executions to retrieve (1-100)
- `include_kpis`: Include calculated KPIs (default: true)

**Returns:**
- Execution summary (total, success/failure counts)
- Success/failure rates
- Execution timing metrics (avg, min, max)
- Execution modes (manual, trigger, webhook)
- Health status indicators
- Workflows needing attention

### 3. `get_workflow_health_report(limit=50)`
Generates comprehensive health analysis for all workflows.

**Parameters:**
- `limit`: Number of recent executions to analyze

**Returns:**
- Overall health status (🟢 Healthy / 🟡 Warning / 🔴 Critical)
- Problematic workflows list
- Healthy workflows list
- Timing metrics and execution modes
- Actionable alerts

### 4. `get_error_executions(workflow_id)`
Retrieves detailed error debugging information for a specific workflow.

**Parameters:**
- `workflow_id`: The workflow ID to analyze (e.g., "CGvCrnUyGHgB7fi8")

**Returns:**
- Error count and detailed error list
- Failed node information (name, type, position)
- Error messages and severity levels
- Trigger context (what caused the failure)
- Error patterns and frequencies
- Node failure statistics
- Time range of errors

## 📊 Health Status Indicators

- 🟢 **Healthy**: <10% failure rate
- 🟡 **Warning**: 10-25% failure rate
- 🔴 **Critical**: >25% failure rate

## 🧪 Testing

Run the test suite to validate functionality:
```bash
python test.py
```

This will execute three test scenarios:
1. Execution tracking with KPIs
2. Health report generation
3. Error execution debugging

Test results are saved to:
- `execution_data.json`
- `health_report.json`
- `error_executions_test.json`

## 📝 Logging

All operations are logged to `n8n_monitor.log`. 

**View live logs:**
```bash
tail -n 100 -f n8n_monitor.log
```

**Check recent activity:**
```bash
tail -n 50 n8n_monitor.log
```

## 📁 Project Structure
```
.
├── server.py                    # MCP server with tool definitions
├── utils/
│   └── n8n_monitor_sync.py     # Core n8n monitoring logic
├── test_n8n.py                 # Test suite
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project metadata
├── n8n_monitor.log             # Runtime logs
└── README.md                   # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `N8N_WEBHOOK_URL` | Your n8n webhook endpoint | Yes |

### n8n Webhook Requirements

The n8n webhook accepts POST requests with the following action payloads:

**Get Active Workflows:**
```json
{
  "action": "get_active_workflows"
}
```

**Get Executions:**
```json
{
  "action": "get_workflow_executions",
  "limit": 50
}
```

**Get Error Details:**
```json
{
  "action": "get_execution_details",
  "limit": 5,
  "workflow_id": "your-workflow-id"
}
```

## 🐛 Troubleshooting

### Server not connecting
- Verify webhook URL is correct in `.env`
- Check n8n instance is accessible
- Review logs: `tail -f n8n_monitor.log`

### No executions returned
- Ensure your n8n instance has execution history
- Check webhook is properly configured
- Verify webhook action routes are working

### Error executions showing 0 results
- Confirm workflow ID is correct
- Check if workflow actually has failed executions
- Verify `get_execution_details` webhook route works

## 📚 Resources

- [n8n API Documentation](https://docs.n8n.io/api/api-reference/#tag/execution/get/executions)
- [My n8n creator profile](https://n8n.io/creators/samirsaci/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Tests pass: `python test.py`
- Logs are comprehensive
- Documentation is updated
- Functions are compatible (and do not overload) with the n8n workflow.

## 📄 License

MIT License - feel free to use this in your own projects!

## About me 🤓

Senior Supply Chain and Data Science consultant with international experience working on Logistics and Transportation operations.
For consulting or advising on analytics and sustainable supply chain transformation, feel free to contact me via [Logigreen Consulting](https://logi-green.com) or [LinkedIn](https://linkedin.com/in/samir-saci)