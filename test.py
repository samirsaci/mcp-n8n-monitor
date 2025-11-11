import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

from utils.n8n_monitor_sync import N8nMonitor

load_dotenv()

def test_error_executions(problematic):
    """Test the get_error_executions endpoint"""
    monitor = N8nMonitor()
    
    print("=" * 60)
    print("Testing Error Executions Endpoint")
    print("=" * 60)
    
    # Take a workflow ID from the problematic workflows found in the previous test
    workflow_id = problematic[0]['workflowId']
    # workflow_id = "7uvA2XQPMB5l4kI5"  # Example workflow ID on my instance

    print(f"Testing get_error_executions with workflow: {workflow_id}")

    result = monitor.get_error_executions(workflow_id=workflow_id)
    
    if "error" in result:
        print(f"❌ There was an Error: {result['error']}")
        return False
    
    print("✅ Response without error:\n")
    print(f"  • Workflow ID: {result.get('workflow_id')}")
    print(f"  • Workflow Name: {result.get('workflow_name')}")
    print(f"  • Errors found: {result.get('error_count', 0)}")
    
    # How many errors in the workflow executions were found?
    if result.get('error_count', 0) == 0:
        print("\n⚠️  Zero errors were found, if you expected errors, please check if your webhook is set up correctly.")
    else:
        # Show error summary
        if "summary" in result and "error_patterns" in result["summary"]:
            print("\n📊 Error Patterns:")
            for msg, info in result["summary"]["error_patterns"].items():
                print(f"  • '{msg[:60]}...': {info['count']} occurrences")
        
        if "summary" in result and "failed_nodes" in result["summary"]:
            print("\n🔴 Failed Nodes:")
            for node, count in result["summary"]["failed_nodes"].items():
                print(f"  • {node}: {count} failures")
    
    # Save result for inspection
    output_file = Path("error_executions_test.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Results saved to: {output_file}")
    
    return True

def test_executions():
    monitor = N8nMonitor()
    
    print("=" * 60)
    print("Testing Workflow Executions Endpoint")
    print("=" * 60)
    
    # Test 1: Get executions for last 50 executions with KPIs
    print("Test 1: Fetching last 50 executions with KPIs...")
    result = monitor.get_workflow_executions(limit=50, includes_kpis=True)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    # Check if we got the expected structure
    print("✅ Successfully fetched execution data\n")
    
    # Display summary if available
    if "summary" in result:
        summary = result["summary"]
        print("📈 Execution Summary:")
        print(f"  • Total Executions: {summary.get('totalExecutions', 0)}")
        print(f"  • Successful: {summary.get('successfulExecutions', 0)}")
        print(f"  • Failed: {summary.get('failedExecutions', 0)}")
        print(f"  • Success Rate: {summary.get('successRate', 'N/A')}")
        print(f"  • Failure Rate: {summary.get('failureRate', 'N/A')}")
        print(f"  • Total Workflows Executed: {summary.get('totalWorkflowsExecuted', 0)}")
        print(f"  • Workflows with Failures: {summary.get('workflowsWithFailures', 0)}")
    
    # Display execution modes if available
    if "executionModes" in result:
        modes = result["executionModes"]
        print("\n🔄 Execution Modes:")
        for mode, count in modes.items():
            print(f"  • {mode}: {count}")
    
    # Display timing metrics
    if "timing" in result:
        timing = result["timing"]
        print("\n⏱️  Timing Metrics:")
        print(f"  • Average: {timing.get('averageExecutionTime', 'N/A')}")
        print(f"  • Min: {timing.get('minExecutionTime', 'N/A')}")
        print(f"  • Max: {timing.get('maxExecutionTime', 'N/A')}")
    
    # Display alerts
    if "alerts" in result:
        alerts = result["alerts"]
        if alerts.get("highFailureRate"):
            print(f"⚠️ ALERT: {alerts.get('failureRateThreshold', '')}")
        
        problematic = alerts.get("workflowsNeedingAttention", [])
        if problematic:
            print("\n🔴 Workflows Needing Attention:")
            for wf in problematic:
                print(f"  • {wf['workflowId']}: {wf['failureRate']} failure rate ({wf['failedCount']} failed)")
    
    # Report saved in the outputs
    output_file = Path("execution_data.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Report saved to: {output_file}")
    
    # Test 2: Health report
    print("\nTest 2: Generating Health Report")
    
    print("\n🏥 Generating health report for the last 50 executions")
    health_report = monitor.get_workflow_health_report(limit=50)
    
    if "error" in health_report:
        print(f"❌ Error: {health_report['error']}")
    else:
        print("✅ Health report generated successfully")
        
        if "overall_health" in health_report:
            health = health_report["overall_health"]
            print(f"\n  Overall Status: {health.get('health_status', 'N/A')}")
            print(f"  {health.get('message', '')}")
        
        if "problematic_workflows" in health_report:
            prob_count = len(health_report["problematic_workflows"])
            healthy_count = len(health_report.get("healthy_workflows", []))
            print(f"\n  Workflow Health:")
            print(f"  • Problematic: {prob_count}")
            print(f"  • Healthy: {healthy_count}")
            
            if prob_count > 0:
                print("\n  Top Issues:")
                for wf in health_report["problematic_workflows"][:3]:
                    print(f"  • {wf['name']}: {wf['metrics']['failureRate']} failure rate")
        
        # Save health report
        report_file = Path("health_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(health_report, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Health report saved to: {report_file}")
    
    print("✅ Executions function tested!")
    
    return problematic

if __name__ == "__main__":
    print(f"Starting test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    problematic = test_executions()
    test_error_executions(problematic)