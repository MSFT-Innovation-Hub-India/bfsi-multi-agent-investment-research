"""PMS Fair-Valuation Compliance Agent - AI evaluator with file search"""

import json
from pathlib import Path
from datetime import datetime

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FilePurpose, FileSearchTool, ToolResources, FileSearchToolResource

# Import configuration from config.py
import config

# Use configuration from config module
PROJECT_CONNECTION_STRING = config.PROJECT_CONNECTION_STRING
MODEL_DEPLOYMENT = config.MODEL_DEPLOYMENT
TEMPLATES_DIR = config.TEMPLATES_DIR

def load_agent_instructions():
    """Load agent instructions from template file"""
    instructions_file = TEMPLATES_DIR / "instructions" / "compliance_agent_instructions.txt"
    return instructions_file.read_text(encoding="utf-8")

def load_compliance_queries():
    """Load compliance query templates from template file"""
    queries_file = TEMPLATES_DIR / "prompts" / "compliance_agent_queries.json"
    return json.loads(queries_file.read_text(encoding="utf-8"))


def create_compliance_agent():
    """Create Azure AI agent with access to all compliance files"""
    print("="*70)
    print("PMS FAIR-VALUATION COMPLIANCE AGENT")
    print("="*70)
    print("\n📂 Initializing AI Agent...\n")
    
    valuation_policy_file = config.VALUATION_POLICY_FILE
    company_analysis_file = config.COMPANY_ANALYSIS_FILE
    stock_report_file = config.STOCK_REPORT_FILE
    
    # Check files exist
    for file_path in [valuation_policy_file, company_analysis_file, stock_report_file]:
        if not file_path.exists():
            print(f"❌ Missing: {file_path.name}")
            return None, None, None
        print(f"✅ Found: {file_path.name}")
    
    # Create Azure AI client
    project_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=PROJECT_CONNECTION_STRING
    )
    
    # Upload all three files
    print(f"\n📤 Uploading files to Azure AI...")
    file_ids = []
    for file_path in [valuation_policy_file, company_analysis_file, stock_report_file]:
        uploaded_file = project_client.agents.upload_file_and_poll(
            file_path=str(file_path),
            purpose=FilePurpose.AGENTS
        )
        file_ids.append(uploaded_file.id)
        print(f"   ✅ {file_path.name}")
    
    # Create vector store
    print(f"\n📚 Creating vector store...")
    vector_store = project_client.agents.create_vector_store_and_poll(
        file_ids=file_ids,
        name="PMS_Compliance_VS"
    )
    print(f"   ✅ Vector Store ID: {vector_store.id}")
    
    agent_instructions = load_agent_instructions()
    
    file_search_tool = FileSearchTool(vector_store_ids=[vector_store.id])
    tool_resources = ToolResources(
        file_search=FileSearchToolResource(vector_store_ids=[vector_store.id])
    )
    
    print(f"\n🤖 Creating AI agent...")
    agent = project_client.agents.create_agent(
        model=MODEL_DEPLOYMENT,
        name="pms-compliance-evaluator",
        instructions=agent_instructions,
        tools=file_search_tool.definitions,
        tool_resources=tool_resources
    )
    print(f"   ✅ Agent ID: {agent.id}")
    
    # Create thread
    thread = project_client.agents.create_thread()
    print(f"   ✅ Thread ID: {thread.id}\n")
    
    return project_client, agent, thread


def ask_agent(project_client, agent, thread, query: str) -> str:
    """Ask agent a question and get response"""
    project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=query
    )
    
    run = project_client.agents.create_and_process_run(
        thread_id=thread.id,
        agent_id=agent.id
    )
    
    if run.status == "failed":
        print(f"❌ Agent failed: {run.last_error}")
        return ""
    
    messages = project_client.agents.list_messages(thread_id=thread.id)
    
    for msg in messages.data:
        if msg.role == "assistant":
            for item in msg.content:
                if hasattr(item, "text"):
                    return item.text.value
    
    return ""


def run_compliance_check():
    """Main compliance check workflow - 4 structured sections"""
    # Create agent
    project_client, agent, thread = create_compliance_agent()
    
    if not project_client:
        print("\n❌ Failed to create agent. Aborting.")
        return False
    
    print("="*70)
    print("🔍 RUNNING COMPLIANCE ANALYSIS (4 SECTIONS)")
    print("="*70 + "\n")
    
    queries = load_compliance_queries()
    
    print("📋 SECTION 1: Reading Valuation Policy Rules...\n")
    section1_query = queries["section_1_query"]
    section1_response = ask_agent(project_client, agent, thread, section1_query)
    
    print("="*70)
    print("SECTION 1: VALUATION POLICY RULES")
    print("="*70)
    print(section1_response)
    print("="*70 + "\n")
    
    print("📋 SECTION 2: Analyzing Trading Classification...\n")
    section2_query = queries["section_2_query"]
    section2_response = ask_agent(project_client, agent, thread, section2_query)
    
    print("="*70)
    print("SECTION 2: TRADING CLASSIFICATION")
    print("="*70)
    print(section2_response)
    print("="*70 + "\n")
    
    print("📋 SECTION 3: Evaluating Exceptional Events...\n")
    section3_query = queries["section_3_query"]
    section3_response = ask_agent(project_client, agent, thread, section3_query)
    
    print("="*70)
    print("SECTION 3: EXCEPTIONAL EVENTS")
    print("="*70)
    print(section3_response)
    print("="*70 + "\n")
    
    print("📋 SECTION 4: Generating Final Recommendation...\n")
    section4_query = queries["section_4_query"]
    section4_response = ask_agent(project_client, agent, thread, section4_query)
    
    print("="*70)
    print("SECTION 4: FINAL RECOMMENDATION")
    print("="*70)
    print(section4_response)
    print("="*70 + "\n")
    
    # Save outputs to frontend/public/data directory from config
    output_dir = config.PUBLIC_DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    findings_json = {
        "section_1_policy_rules": section1_response,
        "section_2_trading_classification": section2_response,
        "section_3_exceptional_events": section3_response,
        "generated_at": datetime.now().isoformat(),
        "source_files": [
            "valuationpolicy_processed.json",
            "company_analysis_output.json",
            "stock_report.json"
        ]
    }
    
    recommendation_json = {
        "section_4_final_recommendation": section4_response,
        "generated_at": datetime.now().isoformat()
    }
    
    findings_output = output_dir / "compliance_findings.json"
    recommendation_output = output_dir / "compliance_recommendation.json"
    
    findings_output.write_text(json.dumps(findings_json, indent=2), encoding="utf-8")
    recommendation_output.write_text(json.dumps(recommendation_json, indent=2), encoding="utf-8")
    
    print("💾 Outputs saved:")
    print(f"   - {findings_output.name} (Sections 1-3)")
    print(f"   - {recommendation_output.name} (Section 4)")
    print("\n" + "="*70)
    print("✅ COMPLIANCE CHECK COMPLETED - 4 SECTIONS")
    print("="*70)
    
    return True


def main():
    """Main entry point"""
    success = run_compliance_check()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
