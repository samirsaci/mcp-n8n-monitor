from mcp.server.fastmcp import FastMCP
import logging
from typing import Optional, Dict, Any
from utils.n8n_monitor_sync import N8nMonitor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("n8n_monitor.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

mcp = FastMCP("n8n-monitor")

monitor = N8nMonitor()

@mcp.tool()
def get_active_workflows() -> Dict[str, Any]:
    """
    Get all active workflows in the n8n instance.
    
    Returns:
        Dictionary with list of active workflows and their details
    """
    try:
        logger.info("Fetching active workflows")
        result = monitor.get_active_workflows()
        
        if "error" in result:
            logger.error(f"Failed to get workflows: {result['error']}")
        else:
            logger.info(f"Found {result.get('total_active', 0)} active workflows")
        
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"error": str(e)}


@mcp.tool()
def get_workflow_executions(
    limit: int = 50,
    include_kpis: bool = True
) -> Dict[str, Any]:
    """
    Get workflow execution logs and KPIs for the last N executions.
    
    Args:
        limit: Number of executions to retrieve (default: 50)
        include_kpis: Include calculated KPIs (default: true)
    
    Returns:
        Dictionary with execution data and KPIs
    """
    try:
        logger.info(f"Fetching the last {limit} executions")
        
        result = monitor.get_workflow_executions(
            limit=limit,
            includes_kpis=include_kpis
        )
        
        if "error" in result:
            logger.error(f"Failed to get executions: {result['error']}")
        else:
            if "summary" in result:
                summary = result["summary"]
                logger.info(f"Executions: {summary.get('totalExecutions', 0)}, "
                          f"Failure rate: {summary.get('failureRate', 'N/A')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"error": str(e)}


@mcp.tool()
def get_workflow_health_report(limit: int = 50) -> Dict[str, Any]:
    """
    Generate a comprehensive health report for all workflows.
    
    Args:
        limit: Number of recent executions to analyze (default: 50)
    
    Returns:
        Dictionary with health report including problematic workflows and metrics
    """
    try:
        logger.info(f"Generating health report for last {limit} executions")
        
        result = monitor.get_workflow_health_report(limit=limit)
        
        if "error" in result:
            logger.error(f"Failed to generate report: {result['error']}")
        else:
            if "overall_health" in result:
                health = result["overall_health"]
                logger.info(f"Health status: {health.get('health_status', 'N/A')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"error": str(e)}
    
    
@mcp.tool()
def get_error_executions(workflow_id: str) -> Dict[str, Any]:
    """
    Retrieve detailed error execution data for debugging workflow failures in n8n.
    
    This tool fetches recent executions with errors for a specific workflow, providing
    comprehensive debugging information including error messages, failed nodes, trigger
    data, and execution patterns. The n8n workflow controls the limit of returned errors
    (typically the last 5 error executions).
    
    Args:
        workflow_id: The unique identifier of the n8n workflow to analyze.
                    Example: "CGvCrnUyGHgB7fi8"
    
    Returns:
        Dict containing:
            - workflow_id (str): The analyzed workflow's ID
            - workflow_name (str): Human-readable workflow name
            - error_count (int): Total number of errors found
            - errors (List[Dict]): Detailed list of error executions, each containing:
                - id: Execution ID for reference
                - workflow_name: Name of the workflow
                - status: Execution status (typically "error")
                - mode: How it was triggered ("manual", "trigger", "webhook")
                - started_at: ISO timestamp when execution began
                - stopped_at: ISO timestamp when execution failed
                - duration_seconds: How long the execution ran before failing
                - finished: Whether the execution completed
                - retry_of: ID of execution this is retrying (if applicable)
                - retry_success_id: ID of successful retry (if exists)
                - error: Detailed error information
                    - message: Primary error message
                    - description: Additional error context
                    - http_code: HTTP status code if applicable
                    - level: Error severity ("warning", "error", "critical")
                    - timestamp: Unix timestamp of error
                - failed_node: Information about the node that failed
                    - name: Node's display name
                    - type: Node type (e.g., "n8n-nodes-base.httpRequest")
                    - id: Unique node identifier
                    - position: [x, y] coordinates in workflow
                - trigger: What triggered this execution
                    - action: The action that was requested
                    - parameters: Request body/parameters
                    - execution_mode: "test" or "production"
            - summary: Aggregated analysis
                - total_errors: Count of errors
                - error_patterns: Groups errors by message with counts
                - failed_nodes: Frequency count by node name
                - time_range: Oldest and newest error timestamps
    
    Example Usage:
        "Show me errors in workflow CGvCrnUyGHgB7fi8"
        "Debug the failures in my n8n Instance Monitor workflow"
        "What's causing errors in my data processing workflow?"
        "Analyze the failed executions for workflow ID xyz"
    
    Use Cases:
        - Debugging recurring workflow failures
        - Identifying problematic nodes in workflows
        - Understanding error patterns and frequencies
        - Analyzing trigger data that causes failures
        - Tracking error resolution through retry information
    
    Note:
        The number of returned errors is controlled by the n8n workflow configuration,
        typically limited to the 5 most recent errors to keep responses focused and
        actionable. The tool provides rich debugging context including the exact
        parameters that triggered failures, making it easy to reproduce and fix issues.
    """
    try:
        logger.info(f"Fetching error executions for workflow {workflow_id}")
        
        result = monitor.get_error_executions(workflow_id=workflow_id)
        
        if "error" in result:
            logger.error(f"Failed to get error executions: {result['error']}")
        else:
            error_count = result.get('error_count', 0)
            logger.info(f"Found {error_count} error executions for workflow {workflow_id}")
            
            # Log summary information for debugging
            if error_count > 0 and "summary" in result:
                patterns = result["summary"].get("error_patterns", {})
                if patterns:
                    most_common = max(patterns.items(), key=lambda x: x[1]["count"])
                    logger.info(f"Most common error: '{most_common[0]}' ({most_common[1]['count']} occurrences)")
        
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error in get_error_executions: {str(e)}")
        return {"error": str(e)}


# Resource for the agent (Samir: update it each time you add a tool)
@mcp.resource("n8n://help")
def get_help() -> str:
    """Get help documentation for the n8n monitoring tools"""
    return """
    📊 N8N MONITORING TOOLS
    =======================
    
    WORKFLOW MONITORING:
    • get_active_workflows()
      List all active workflows with names and IDs
    
    EXECUTION TRACKING:
    • get_workflow_executions(limit=50, include_kpis=True)
      Get execution logs with detailed KPIs
      - limit: Number of recent executions to retrieve (1-100)
      - include_kpis: Calculate performance metrics
    
    ERROR DEBUGGING:
    • get_error_executions(workflow_id)
      Retrieve detailed error information for a specific workflow
      - Returns last 5 errors with comprehensive debugging data
      - Shows error messages, failed nodes, trigger data
      - Identifies error patterns and problematic nodes
      - Includes HTTP codes, error levels, and timing info
    
    HEALTH REPORTING:
    • get_workflow_health_report(limit=50)
      Generate comprehensive health analysis based on recent executions
      - Identifies problematic workflows
      - Shows success/failure rates
      - Provides execution timing metrics
    
    KEY METRICS PROVIDED:
    • Total executions
    • Success/failure rates
    • Execution times (avg, min, max)
    • Workflows with failures
    • Execution modes (manual, trigger, integrated)
    • Error patterns and frequencies
    • Failed node identification
    
    HEALTH STATUS INDICATORS:
    • 🟢 Healthy: <10% failure rate
    • 🟡 Warning: 10-25% failure rate
    • 🔴 Critical: >25% failure rate
    
    USAGE EXAMPLES:
    - "Show me all active workflows"
    - "What workflows have been failing?"
    - "Generate a health report for my n8n instance"
    - "Show execution metrics for the last 48 hours"
    - "Debug errors in workflow CGvCrnUyGHgB7fi8"
    - "What's causing failures in my data processing workflow?"
    
    DEBUGGING WORKFLOW:
    1. Use get_workflow_executions() to identify problematic workflows
    2. Use get_error_executions() for detailed error analysis
    3. Check error patterns to identify recurring issues
    4. Review failed node details and trigger data
    5. Use workflow_id and execution_id for targeted fixes
    """

if __name__ == "__main__":
    logger.info("🚀 Starting n8n Monitor MCP Server")
    logger.info("Server ready for connections from Claude Desktop")
    
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    finally:
        logger.info("Server stopped")