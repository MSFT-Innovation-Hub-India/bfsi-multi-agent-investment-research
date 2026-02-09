# === GMR Airports Limited - Investment Report Agent ===
"""
Investment Report with Financial Dashboards
Template-based structure for Azure AI deployment
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FilePurpose, FileSearchTool, CodeInterpreterTool

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

# Data file path
INVESTMENT_DOCUMENT = Path(__file__).parent.parent / "data" / "investmentproposal_processed.json"

# Dashboard configurations
DASHBOARDS = {
    "financial_overview": {
        "file": "dashboard_financial_overview.png",
        "prompt": """Create Financial Overview image (1200x800):
Panel A: Revenue & EBITDA dual-axis line chart (FY22-FY25P)
Panel B: Cash Flow bars (Operating CF vs Capex vs Free CF)
Save as dashboard_financial_overview.png."""
    },
    "debt_liquidity": {
        "file": "dashboard_debt_liquidity.png",
        "prompt": """Create Debt & Liquidity Dashboard (1100x800):
Panel A: Debt Composition Stacked Bar
Panel B: Debt Maturity Timeline
Panel C: Liquidity Gauge
Panel D: Leverage Metrics Table
Save as dashboard_debt_liquidity.png."""
    },
    "operations_capacity": {
        "file": "dashboard_operations_capacity.png",
        "prompt": """Create Operations & Capacity Dashboard (1100x800):
Panel A: Passenger Traffic Trend (FY22-FY25P)
Panel B: Capacity Utilization Heatmap per airport
Save as dashboard_operations_capacity.png."""
    },
    "projects_funding": {
        "file": "dashboard_projects_funding.png",
        "prompt": """Create Projects & Funding Dashboard (1100x700):
Panel A: Capex Allocation Donut + Funding Gap KPI
Panel B: Project Timeline (Gantt)
Save as dashboard_projects_funding.png."""
    },
    "valuation_risk": {
        "file": "dashboard_valuation_risk.png",
        "prompt": """Create Valuation & Risk Dashboard (1100x700):
Panel A: Valuation Multiples (Market Cap, P/B, EV/EBITDA)
Panel B: Risk Matrix (2x2)
Panel C: Sensitivity Table
Save as dashboard_valuation_risk.png."""
    }
}

# Report sections
REPORT_SECTIONS = {
    "executive_summary": {
        "name": "Executive Summary",
        "dashboard": None,
        "prompt": """Return a 4-5 line analytical paragraph including:
- Business intro, FY24 & FY25P revenue, EBITDA and margins
- Stock metrics: 30-day return %, volatility %, avg daily volume
- Footer: 'Keys used:' listing JSON keys"""
    },
    "financial_performance": {
        "name": "Financial Performance",
        "dashboard": "financial_overview",
        "prompt": """After generating dashboard, return 4-5 line paragraph:
- Revenue FY24 & FY25P, EBITDA, Interest Coverage
- Operating CF vs Capex analysis
- Footer: 'Keys used:' listing extraction keys"""
    },
    "balance_debt": {
        "name": "Balance Sheet & Debt",
        "dashboard": "debt_liquidity",
        "prompt": """After creating dashboard, return 4-5 line paragraph:
- Total Assets, Total Debt, Net Worth, Debt-to-Equity
- Short-term debt concentration and liquidity
- Footer: 'Keys used:' listing extraction keys"""
    },
    "operational_performance": {
        "name": "Operational Performance",
        "dashboard": "operations_capacity",
        "prompt": """After producing dashboard, return 4-5 line paragraph:
- Passenger traffic FY24 and FY25P with growth %
- Airport capacity utilization for Delhi and Hyderabad
- Footer: 'Keys used:' listing extraction keys"""
    },
    "projects_funding": {
        "name": "Projects & Funding",
        "dashboard": "projects_funding",
        "prompt": """After generating dashboard, return 4-5 line paragraph:
- Total Capex pipeline and top project amounts
- Funding Gap KPI and execution risk
- Footer: 'Keys used:' listing extraction keys"""
    },
    "valuation_risk": {
        "name": "Valuation & Risk",
        "dashboard": "valuation_risk",
        "prompt": """After creating dashboard, return 4-line insight:
- EV/EBITDA, P/B, Market Cap with valuation concern
- Top-2 risk drivers
- Footer: 'Keys used:' listing extraction keys"""
    },
    "governance_esg": {
        "name": "Governance & ESG",
        "dashboard": None,
        "prompt": """Return 4-5 line paragraph:
- Auditor opinion & board composition
- Regulatory compliance status (SEBI, AERA, DGCA)
- Litigation / contingent liabilities
- Footer: 'Keys used:' listing extraction keys"""
    }
}


def create_agent():
    """Create Azure AI agent"""
    project_client = AIProjectClient(
        endpoint=ENDPOINT,
        subscription_id=SUBSCRIPTION_ID,
        resource_group_name=RESOURCE_GROUP,
        project_name=PROJECT_NAME,
        credential=DefaultAzureCredential()
    )
    
    print(f"📊 Uploading: {INVESTMENT_DOCUMENT.name}")
    file = project_client.agents.upload_file_and_poll(
        file_path=str(INVESTMENT_DOCUMENT),
        purpose=FilePurpose.AGENTS
    )
    print(f"✅ File: {file.id}")
    
    vector_store = project_client.agents.create_vector_store_and_poll(
        file_ids=[file.id],
        name="GMR_Investment_VS"
    )
    print(f"✅ Vector Store: {vector_store.id}")
    
    from azure.ai.projects.models import ToolResources, FileSearchToolResource, CodeInterpreterToolResource
    
    file_search_tool = FileSearchTool(vector_store_ids=[vector_store.id])
    code_interpreter_tool = CodeInterpreterTool()
    all_tools = file_search_tool.definitions + code_interpreter_tool.definitions
    
    tool_resources = ToolResources(
        file_search=FileSearchToolResource(vector_store_ids=[vector_store.id]),
        code_interpreter=CodeInterpreterToolResource()
    )
    
    agent = project_client.agents.create_agent(
        model=MODEL_DEPLOYMENT,
        name="gmr-investment-report-agent",
        instructions=load_instructions("investment_report_agent/instructions.txt"),
        tools=all_tools,
        tool_resources=tool_resources
    )
    print(f"✅ Agent: {agent.id}")
    
    thread = project_client.agents.create_thread()
    print(f"✅ Thread: {thread.id}\n")
    
    return project_client, agent, thread


def generate_section(project_client, agent, thread, section_key):
    """Generate one report section"""
    section = REPORT_SECTIONS[section_key]
    print(f"\n{'='*70}")
    print(f"📝 {section['name']}")
    print('='*70)
    
    full_prompt = section['prompt']
    if section.get('dashboard'):
        dashboard_spec = DASHBOARDS[section['dashboard']]
        full_prompt = f"{dashboard_spec['prompt']}\n\n---\n\n{section['prompt']}"
        print(f"   📊 Dashboard: {dashboard_spec['file']}")
    
    project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=full_prompt
    )
    
    run = project_client.agents.create_and_process_run(
        thread_id=thread.id,
        agent_id=agent.id
    )
    
    if run.status == "failed":
        print(f"   ❌ Failed: {run.last_error}")
        return f"\n## {section['name']}\n\n*Section generation failed*\n"
    
    messages = project_client.agents.list_messages(thread_id=thread.id)
    
    content = ""
    images = []
    
    for msg in messages.data:
        if msg.role == "assistant":
            for item in msg.content:
                if hasattr(item, "text"):
                    content = item.text.value
                elif hasattr(item, "image_file"):
                    images.append(item.image_file.file_id)
                elif hasattr(item, "image"):
                    images.append(item.image.file_id)
            if content:
                break
    
    if content:
        print(f"\n📄 Agent Response:")
        print("-" * 70)
        print(content[:500] + "..." if len(content) > 500 else content)
        print("-" * 70)
    
    # Save images
    images_dir = Path(__file__).parent.parent / "data" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    saved_images = []
    for idx, img_id in enumerate(images, 1):
        try:
            img_filename = f"{section_key}_{idx}.png" if len(images) > 1 else f"{section_key}.png"
            project_client.agents.save_file(
                file_id=img_id,
                file_name=img_filename,
                target_dir=str(images_dir)
            )
            saved_images.append(img_filename)
            print(f"   💾 Saved: {img_filename}")
        except Exception as e:
            print(f"   ⚠️ Image save failed: {e}")
    
    print(f"   ✅ Complete ({len(saved_images)} images)")
    
    return f"\n## {section['name']}\n\n{content}\n"


def generate_report():
    """Generate complete investment report"""
    print("\n" + "="*70)
    print("GMR AIRPORTS - INVESTMENT REPORT GENERATOR")
    print("="*70 + "\n")
    
    project_client, agent, thread = create_agent()
    
    timestamp = datetime.now().strftime("%B %d, %Y")
    report = f"""# GMR Airports Limited - Investment Analysis
**Mutual Fund Investment Report | {timestamp}**

---
"""
    
    for section_key in REPORT_SECTIONS.keys():
        section_content = generate_section(project_client, agent, thread, section_key)
        report += section_content
        report += "\n---\n"
        time.sleep(25)  # Rate limit delay
    
    report += """
## Investment Recommendation

**HOLD for existing investors / WAIT for new investors**

GMR offers long-term growth potential tied to India's aviation expansion, but near-term challenges include negative profitability, weak interest coverage (0.71x), and elevated valuation (EV/EBITDA 177x).

---

*Report generated by Azure AI Investment Analysis Agent*
"""
    
    # Save outputs
    data_dir = Path(__file__).parent.parent / "data"
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    output_path = data_dir / f"GMR_Investment_Report_{timestamp_str}.md"
    output_path.write_text(report, encoding="utf-8")
    
    json_output = {
        "symbol": "GMRAIRPORT.NS",
        "company_name": "GMR Airports Ltd",
        "analysis_type": "investment_report",
        "generated_at": datetime.now().isoformat(),
        "report_file": output_path.name,
        "recommendation": "HOLD for existing investors / WAIT for new investors",
        "key_strengths": [
            "India's aviation growth potential",
            "Diversified airport portfolio",
            "Strong aeronautical revenue base"
        ],
        "key_challenges": [
            "Negative profitability",
            "Weak interest coverage (0.71x)",
            "Elevated valuation (EV/EBITDA 177x)",
            "₹32 Bn capex execution risk"
        ]
    }
    
    json_output_path = data_dir / "company_analysis_output.json"
    json_output_path.write_text(json.dumps(json_output, indent=2), encoding="utf-8")
    
    print("="*70)
    print(f"✅ REPORT COMPLETE:")
    print(f"   - Markdown: {output_path.name}")
    print(f"   - JSON: {json_output_path.name}")
    print("="*70)
    
    return output_path


if __name__ == "__main__":
    generate_report()
