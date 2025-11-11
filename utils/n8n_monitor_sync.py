"""
N8n Monitor utility class - synchronous version for FastMCP
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import requests
import traceback

logger = logging.getLogger(__name__)


class N8nMonitor:
    """Handler for n8n monitoring operations - synchronous version"""
    
    def __init__(self):
        self.webhook_url = os.getenv("N8N_WEBHOOK_URL", "")
        self.timeout = 30
        logger.info(f"n8n monitor initialized with webhook URL with a timeout of {self.timeout} seconds")
    
    def get_active_workflows(self) -> Dict[str, Any]:
        """Fetch all active workflows from n8n"""
        if not self.webhook_url:
            logger.error("Environment variable N8N_WEBHOOK_URL not configured")
            return {"error": "N8N_WEBHOOK_URL environment variable not set"}
        
        try:
            logger.info("Fetching active workflows from n8n")
            response = requests.post(
                self.webhook_url,
                json={"action": "get_active_workflows"},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            logger.debug(f"Response type: {type(data)}")
            
            # List of all workflows conteined 
            workflows = []
            if isinstance(data, list):
                workflows = [item for item in data if isinstance(item, dict)]
                if not workflows and data:
                    logger.error(f"Expected list of dictionaries, got list of {type(data[0]).__name__}")
                    return {"error": "Webhook returned invalid data format"}
            elif isinstance(data, dict):
                if "data" in data:
                    workflows = data["data"]
                else:
                    logger.error(f"Unexpected dict response with keys: {list(data.keys())} \n {traceback.format_exc()}")
                    return {"error": "Unexpected response format"}
            else:
                logger.error(f"Unexpected response type: {type(data)} \n {traceback.format_exc()}")
                return {"error": f"Unexpected response type: {type(data).__name__}"}
            
            logger.info(f"Successfully fetched {len(workflows)} active workflows")
            
            return {
                "total_active": len(workflows),
                "workflows": [
                    {
                        "id": wf.get("id", "unknown"),
                        "name": wf.get("name", "Unnamed"),
                        "created": wf.get("createdAt", ""),
                        "updated": wf.get("updatedAt", ""),
                        "archived": wf.get("isArchived", "false") == "true"
                    }
                    for wf in workflows
                ],
                "summary": {
                    "total": len(workflows),
                    "names": [wf.get("name", "Unnamed") for wf in workflows]
                }
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching workflows: {e} \n {traceback.format_exc()}")
            return {"error": f"Failed to fetch workflows: {str(e)} \n {traceback.format_exc()}"}
        except Exception as e:
            logger.error(f"Unexpected error fetching workflows: {e} \n {traceback.format_exc()}")
            return {"error": f"Unexpected error: {str(e)} \n {traceback.format_exc()}"}
    
    def get_workflow_executions(
        self, 
        limit: int = 50,
        includes_kpis: bool = False,
    ) -> Dict[str, Any]:
        """Fetch workflow executions of the last 'limit' executions with or without KPIs """
        if not self.webhook_url:
            logger.error("Environment variable N8N_WEBHOOK_URL not set")
            return {"error": "N8N_WEBHOOK_URL environment variable not set"}
        
        try:
            logger.info(f"Fetching the last {limit} executions")
            
            payload = {
                "action": "get_workflow_executions",
                "limit": limit
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            logger.info("Successfully fetched execution data")
            
            if includes_kpis and isinstance(data, dict):
                logger.info("Including KPIs in the execution data")

                if "summary" in data:
                    summary = data["summary"]
                    failure_rate = float(summary.get("failureRate", "0").rstrip("%"))
                    data["insights"] = {
                        "health_status": "🟢 Healthy" if failure_rate < 10 else 
                                    "🟡 Warning" if failure_rate < 25 else 
                                    "🔴 Critical",
                        "message": f"{summary.get('totalExecutions', 0)} executions with {summary.get('failureRate', '0%')} failure rate"
                    }
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error fetching executions: {e} \n {traceback.format_exc()}")
            return {"error": f"Failed to fetch executions: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error fetching executions: {e} \n {traceback.format_exc()}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def get_workflow_health_report(self, limit: int = 50) -> Dict[str, Any]:
        """Generate a comprehensive health report for all workflows"""
        try:
            logger.info(f"Generating health report for last {limit} executions")

            # Get executions with KPIs
            exec_data = self.get_workflow_executions(limit=limit, includes_kpis=True)

            if "error" in exec_data:
                return exec_data
            
            # Get active workflows for names
            workflows_data = self.get_active_workflows()
            
            if "error" in workflows_data:
                return workflows_data
            
            # Create workflow name mapping
            workflow_names = {
                wf["id"]: wf["name"] 
                for wf in workflows_data.get("workflows", [])
            }
            
            # Build comprehensive report
            report = {
                "generated_at": datetime.now().isoformat(),
                "overall_health": exec_data.get("insights", {}),
                "summary": exec_data.get("summary", {}),
                "execution_modes": exec_data.get("executionModes", {}),
                "timing_metrics": exec_data.get("timing", {}),
                "problematic_workflows": [],
                "healthy_workflows": [],
                "alerts": exec_data.get("alerts", {})
            }
            
            # Categorize workflows by health
            if "workflowPerformance" in exec_data and "allWorkflowMetrics" in exec_data["workflowPerformance"]:
                for wf_id, metrics in exec_data["workflowPerformance"]["allWorkflowMetrics"].items():
                    failure_rate = float(metrics.get("failureRate", "0%").rstrip("%"))
                    wf_info = {
                        "id": wf_id,
                        "name": workflow_names.get(wf_id, f"Unknown ({wf_id})"),
                        "metrics": metrics
                    }
                    
                    if failure_rate > 10:
                        report["problematic_workflows"].append(wf_info)
                    else:
                        report["healthy_workflows"].append(wf_info)
            
            # Sort problematic workflows by failure rate
            report["problematic_workflows"].sort(
                key=lambda x: float(x["metrics"].get("failureRate", "0%").rstrip("%")), 
                reverse=True
            )
            
            logger.info("Health report generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error generating health report: {e}")
            return {"error": f"Failed to generate health report: {str(e)}"}
        
    def get_error_executions(self, 
                             workflow_id: str,
                             limit: int = 5
                             ) -> Dict[str, Any]:
            """
            Fetch recent error executions for a specific workflow with detailed debugging info.
            
            Args:
                workflow_id: The ID of the workflow to check for errors
                limit: The maximum number of error executions to retrieve
            Returns:
                Dictionary with detailed error executions
            """
            if not workflow_id:
                return {"error": "workflow_id parameter is required"}
            
            try:
                logger.info(f"Fetching error executions for workflow {workflow_id}")
                
                response = requests.post(
                    self.webhook_url,
                    json={
                        "action": "get_execution_details",
                        "limit": limit,
                        "workflow_id": workflow_id
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Extract executions array
                if isinstance(data, list):
                    executions = data
                elif isinstance(data, dict) and "data" in data:
                    executions = data["data"]
                else:
                    return {"error": "Unexpected response format"}
                
                # Process executions with enhanced details
                error_details = []
                for exec in executions:
                    if not isinstance(exec, dict):
                        continue
                    
                    # Extract comprehensive error information
                    error_info = {}
                    failed_node_details = {}
                    
                    if isinstance(exec.get("data"), dict):
                        result_data = exec["data"].get("resultData", {})
                        
                        # Get error details
                        if isinstance(result_data, dict) and "error" in result_data:
                            err = result_data["error"]
                            error_info = {
                                "message": err.get("message", "Unknown error"),
                                "description": err.get("description"),
                                "http_code": err.get("httpCode"),
                                "level": err.get("level", "error"),  # warning, error, critical
                                "timestamp": err.get("timestamp")
                            }
                            
                            # Get failed node details
                            if isinstance(err.get("node"), dict):
                                node = err["node"]
                                failed_node_details = {
                                    "name": node.get("name"),
                                    "type": node.get("type"),
                                    "id": node.get("id"),
                                    "position": node.get("position")
                                }
                        
                        # Get last executed node if different
                        last_node = result_data.get("lastNodeExecuted")
                    
                    # Extract trigger information (what caused this execution)
                    trigger_info = {}
                    if isinstance(exec.get("data"), dict):
                        run_data = exec["data"].get("resultData", {}).get("runData", {})
                        if isinstance(run_data, dict) and "Webhook" in run_data:
                            webhook_data = run_data["Webhook"]
                            if isinstance(webhook_data, list) and len(webhook_data) > 0:
                                first_webhook = webhook_data[0]
                                if isinstance(first_webhook.get("data"), dict):
                                    main_data = first_webhook["data"].get("main", [[]])[0]
                                    if main_data and len(main_data) > 0:
                                        trigger_json = main_data[0].get("json", {})
                                        trigger_info = {
                                            "action": trigger_json.get("body", {}).get("action") if isinstance(trigger_json.get("body"), dict) else None,
                                            "parameters": trigger_json.get("body"),
                                            "execution_mode": trigger_json.get("executionMode", "production")
                                        }
                    
                    # Calculate duration
                    duration = None
                    if exec.get("startedAt") and exec.get("stoppedAt"):
                        try:
                            start = datetime.fromisoformat(exec["startedAt"].replace("Z", "+00:00"))
                            stop = datetime.fromisoformat(exec["stoppedAt"].replace("Z", "+00:00"))
                            duration = (stop - start).total_seconds()
                        except:
                            pass
                    
                    # Get workflow name
                    workflow_name = None
                    if isinstance(exec.get("workflowData"), dict):
                        workflow_name = exec["workflowData"].get("name")
                    
                    error_details.append({
                        "id": exec.get("id"),
                        "workflow_name": workflow_name,
                        "status": exec.get("status", "error"),
                        "mode": exec.get("mode"),
                        "started_at": exec.get("startedAt"),
                        "stopped_at": exec.get("stoppedAt"),
                        "duration_seconds": duration,
                        "finished": exec.get("finished", False),
                        "retry_of": exec.get("retryOf"),
                        "retry_success_id": exec.get("retrySuccessId"),
                        "error": error_info or {"message": "Error details not available"},
                        "failed_node": failed_node_details or {"name": last_node if 'last_node' in locals() else "Unknown"},
                        "trigger": trigger_info
                    })
                
                # Create summary with patterns
                error_patterns = {}
                node_failures = {}
                
                for detail in error_details:
                    # Group by error message
                    msg = detail["error"].get("message", "Unknown")
                    if msg not in error_patterns:
                        error_patterns[msg] = {"count": 0, "executions": []}
                    error_patterns[msg]["count"] += 1
                    error_patterns[msg]["executions"].append(detail["id"])
                    
                    # Count node failures
                    node_name = detail["failed_node"].get("name", "Unknown")
                    if node_name:
                        node_failures[node_name] = node_failures.get(node_name, 0) + 1
                
                return {
                    "workflow_id": workflow_id,
                    "workflow_name": error_details[0]["workflow_name"] if error_details else "Unknown",
                    "error_count": len(error_details),
                    "errors": error_details,
                    "summary": {
                        "total_errors": len(error_details),
                        "error_patterns": error_patterns,
                        "failed_nodes": node_failures,
                        "time_range": {
                            "oldest": error_details[-1]["started_at"] if error_details else None,
                            "newest": error_details[0]["started_at"] if error_details else None
                        }
                    }
                }
                
            except Exception as e:
                logger.error(f"Error fetching executions: {e}")
                return {"error": str(e)}