"""
PMS FAIR-VALUATION COMPLIANCE AGENT
====================================
AI-powered compliance evaluator for PMS policy validation

INPUT FILES (3 required):
1. valuationpolicy_processed.json
2. company_analysis_output.json
3. stock_report.json
"""

import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FilePurpose, FileSearchTool, ToolResources, FileSearchToolResource

# Configuration - Use environment variables (no hardcoded fallbacks)
ENDPOINT = os.getenv("AZURE_AI_ENDPOINT")
SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP")
PROJECT_NAME = os.getenv("AZURE_PROJECT_NAME")
MODEL_DEPLOYMENT = os.getenv("AZURE_MODEL_DEPLOYMENT", "gpt-4o-mini")

INSTRUCTIONS_DIR = Path(__file__).parent.parent / "instructions"


def load_instructions(file_name: str) -> str:
    """Load agent instructions from instructions directory."""
    instructions_path = INSTRUCTIONS_DIR / file_name
    if not instructions_path.exists():
        raise FileNotFoundError(f"Missing instructions file: {instructions_path}")
    return instructions_path.read_text(encoding="utf-8")

# Validate required environment variables
REQUIRED_ENV_VARS = ["AZURE_AI_ENDPOINT", "AZURE_SUBSCRIPTION_ID", "AZURE_RESOURCE_GROUP", "AZURE_PROJECT_NAME"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")


def create_compliance_agent():
    """Create Azure AI agent with access to all compliance files"""
    print("="*70)
    print("PMS FAIR-VALUATION COMPLIANCE AGENT")
    print("="*70)
    print("\n📂 Initializing AI Agent...\n")
    
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    
    # Input files
    valuation_policy_file = data_dir / "valuationpolicy_processed.json"
    company_analysis_file = data_dir / "company_analysis_output.json"
    stock_report_file = data_dir / "stock_report.json"
    
    # Check files exist
    for file_path in [valuation_policy_file, company_analysis_file, stock_report_file]:
        if not file_path.exists():
            print(f"❌ Missing: {file_path.name}")
            return None, None, None
        print(f"✅ Found: {file_path.name}")
    
    # Create Azure AI client
    project_client = AIProjectClient(
        endpoint=ENDPOINT,
        subscription_id=SUBSCRIPTION_ID,
        resource_group_name=RESOURCE_GROUP,
        project_name=PROJECT_NAME,
        credential=DefaultAzureCredential()
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
    
    agent_instructions = load_instructions("compliance_agent/instructions.txt")

    # Create agent
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
    project_client, agent, thread = create_compliance_agent()
    
    if not project_client:
        print("\n❌ Failed to create agent. Aborting.")
        return False
    
    print("="*70)
    print("🔍 RUNNING COMPLIANCE ANALYSIS (4 SECTIONS)")
    print("="*70 + "\n")
    
    # SECTION 1: Read Valuation Rules
    print("📋 SECTION 1: Reading Valuation Policy Rules...\n")
    section1_query = """SECTION 1 — Read & Summarize Valuation Rules

Extract from valuationpolicy_processed.json:
1. Definition of traded / thinly traded / non-traded securities
2. Price source rules (NSE/BSE requirements)
3. Exceptional events list
4. Committee review / deviation rules

Output as clean paragraphs with bullet points. List JSON keys used."""

    section1_response = ask_agent(project_client, agent, thread, section1_query)
    print("="*70)
    print("SECTION 1: VALUATION POLICY RULES")
    print("="*70)
    print(section1_response)
    
    # SECTION 2: Trading Classification
    print("\n📋 SECTION 2: Analyzing Trading Classification...\n")
    section2_query = """SECTION 2 — Trading Classification

Using stock_report.json and thresholds from Section 1:
- Extract 30-day total traded value, volume, avg daily volume
- Extract exchange name and timestamp
- Determine if security meets traded criteria

Output as paragraph with cited JSON keys."""

    section2_response = ask_agent(project_client, agent, thread, section2_query)
    print("="*70)
    print("SECTION 2: TRADING CLASSIFICATION")
    print("="*70)
    print(section2_response)
    
    # SECTION 3: Exceptional Events
    print("\n📋 SECTION 3: Evaluating Exceptional Events...\n")
    section3_query = """SECTION 3 — Exceptional Events Evaluation

Check policy-listed exceptional events against:
- company_analysis_output.json (financial risks)
- stock_report.json (trading data)

For each event, state: triggered (YES/NO/POSSIBLE) with evidence."""

    section3_response = ask_agent(project_client, agent, thread, section3_query)
    print("="*70)
    print("SECTION 3: EXCEPTIONAL EVENTS")
    print("="*70)
    print(section3_response)
    
    # SECTION 4: Final Recommendation
    print("\n📋 SECTION 4: Generating Final Recommendation...\n")
    section4_query = """SECTION 4 — Final Recommendation

Based on Sections 1-3, provide:
- Decision: ACCEPT VALUATION / REVIEW REQUIRED / ESCALATE / NON-COMPLIANT
- Justification (3-4 sentences citing evidence)
- Mandatory fixes (if any)"""

    section4_response = ask_agent(project_client, agent, thread, section4_query)
    print("="*70)
    print("SECTION 4: FINAL RECOMMENDATION")
    print("="*70)
    print(section4_response)
    
    # Save outputs
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    
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
    
    findings_output = data_dir / "compliance_findings.json"
    recommendation_output = data_dir / "compliance_recommendation.json"
    
    findings_output.write_text(json.dumps(findings_json, indent=2), encoding="utf-8")
    recommendation_output.write_text(json.dumps(recommendation_json, indent=2), encoding="utf-8")
    
    print("\n💾 Outputs saved:")
    print(f"   - {findings_output.name}")
    print(f"   - {recommendation_output.name}")
    print("\n" + "="*70)
    print("✅ COMPLIANCE CHECK COMPLETED")
    print("="*70)
    
    return True


def main():
    """Main entry point"""
    success = run_compliance_check()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
