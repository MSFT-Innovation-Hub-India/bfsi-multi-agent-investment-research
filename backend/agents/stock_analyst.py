# === GMR Airports Limited - Stock Analyst Agent ===
"""
Stock Analysis with 5-Panel Visualization Dashboard
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
STOCK_ANALYSIS_DOCUMENT = Path(__file__).parent.parent / "data" / "gmr_stock_analysis.json"

# Report sections configuration
REPORT_SECTIONS_FINAL = {
    "meta": {
        "report_name": "final_stock_report",
        "canvas_size": {"width": 2400, "height": 3200},
        "final_png": "final_stock_report.png",
        "timestamp_key": "generated_at"
    },
    "executive_summary": {
        "name": "Executive Summary",
        "dashboard": "null",
        "size": {"width": 2400, "height": 200},
        "prompt": """Generate an analytical paragraph with stock metrics including:
- symbol, 30-day return %, volatility %, avg daily volume, total traded value, total traded volume
- Price provenance (exchange + timestamp)
Output only the paragraph text - NO IMAGE generation for this section."""
    },
    "panel_p1_price_trend": {
        "name": "P1 - Price Trend & Momentum",
        "dashboard": "p1_price_trend",
        "size": {"width": 1100, "height": 800},
        "prompt": """Create 1100x800 panel with OHLC Candlestick chart, Volume bars, SMA lines, and text summary.
Save as p1_price_trend.png."""
    },
    "panel_p2_relative_perf": {
        "name": "P2 - Relative Performance vs Benchmarks",
        "dashboard": "p2_relative_perf",
        "size": {"width": 1100, "height": 800},
        "prompt": """Create 1100x800 panel with bar chart comparing 30d returns (Stock, NIFTY, SENSEX),
Alpha visualization, and Beta/Correlation table. Save as p2_relative_perf.png."""
    },
    "panel_p3_liquidity": {
        "name": "P3 - Liquidity Profile",
        "dashboard": "p3_liquidity",
        "size": {"width": 1100, "height": 800},
        "prompt": """Create 1100x800 panel with volume comparison bars, KPI badges,
high volume timeline, and liquidity table. Save as p3_liquidity.png."""
    },
    "panel_p4_volatility": {
        "name": "P4 - Volatility & Drawdown",
        "dashboard": "p4_volatility",
        "size": {"width": 1100, "height": 800},
        "prompt": """Create 1100x800 panel with volatility gauge, max drawdown bar,
and gap risk panel. Save as p4_volatility.png."""
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
    
    print(f"📊 Uploading: {STOCK_ANALYSIS_DOCUMENT.name}")
    file = project_client.agents.upload_file_and_poll(
        file_path=str(STOCK_ANALYSIS_DOCUMENT),
        purpose=FilePurpose.AGENTS
    )
    print(f"✅ File: {file.id}")
    
    vector_store = project_client.agents.create_vector_store_and_poll(
        file_ids=[file.id],
        name="GMR_Stock_Analysis_VS"
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
        name="gmr-stock-unified-report-agent",
        instructions=load_instructions("stock_analyst/instructions.txt"),
        tools=all_tools,
        tool_resources=tool_resources
    )
    print(f"✅ Agent: {agent.id}")
    
    thread = project_client.agents.create_thread()
    print(f"✅ Thread: {thread.id}\n")
    
    return project_client, agent, thread


def generate_section(project_client, agent, thread, section_key, retry_delay=15):
    """Generate one report section/panel"""
    section = REPORT_SECTIONS_FINAL[section_key]
    print(f"\n{'='*70}")
    print(f"📝 {section['name']}")
    print('='*70)
    
    full_prompt = section.get('prompt', '')
    
    if section.get('dashboard'):
        print(f"   📊 Dashboard: {section['dashboard']}.png")
    
    time.sleep(retry_delay)
    
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
        return f"\n## {section['name']}\n\n*Section generation failed*\n", {
            "id": section_key,
            "name": section['name'],
            "summary": "Section generation failed",
            "image": None
        }
    
    messages = project_client.agents.list_messages(thread_id=thread.id)
    
    content = ""
    images = []
    
    for msg in messages.data:
        if msg.role == "assistant":
            for item in msg.content:
                if hasattr(item, "text"):
                    content = item.text.value
                    if hasattr(item.text, 'annotations'):
                        for annotation in item.text.annotations:
                            if hasattr(annotation, 'file_path') and hasattr(annotation.file_path, 'file_id'):
                                images.append(annotation.file_path.file_id)
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
    
    # Save images - for deployment, images go to blob storage
    images_dir = Path(__file__).parent.parent / "data" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    saved_images = []
    for idx, img_id in enumerate(images, 1):
        try:
            if section.get('dashboard'):
                img_filename = f"{section['dashboard']}.png"
            else:
                img_filename = f"{section_key}.png"
            
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
    
    section_data = {
        "id": section_key,
        "name": section['name'],
        "summary": content.strip(),
        "image": saved_images[0] if saved_images else None,
        "dashboard": section.get('dashboard'),
        "size": section.get('size')
    }
    
    return f"\n## {section['name']}\n\n{content}\n", section_data


def generate_report():
    """Generate complete stock analysis report"""
    print("\n" + "="*70)
    print("GMR AIRPORTS - STOCK REPORT GENERATOR")
    print("="*70 + "\n")
    
    project_client, agent, thread = create_agent()
    
    images_dir = Path(__file__).parent.parent / "data" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    panel_sections = [
        "executive_summary",
        "panel_p1_price_trend",
        "panel_p2_relative_perf",
        "panel_p3_liquidity",
        "panel_p4_volatility"
    ]
    
    report_sections_data = []
    
    for section_key in panel_sections:
        _, section_data = generate_section(project_client, agent, thread, section_key, retry_delay=15)
        report_sections_data.append(section_data)
    
    # Create JSON report
    json_report = {
        "report_metadata": {
            "symbol": "GMRAIRPORT.NS",
            "company_name": "GMR Airports Ltd",
            "report_type": "stock_analysis",
            "generated_at": datetime.now().isoformat(),
            "total_panels": len(report_sections_data)
        },
        "sections": report_sections_data,
        "image_location": "data/images/"
    }
    
    # Save JSON report
    json_output_path = Path(__file__).parent.parent / "data" / "stock_report.json"
    json_output_path.write_text(json.dumps(json_report, indent=2), encoding="utf-8")
    
    print("="*70)
    print(f"✅ STOCK REPORT COMPLETE")
    print(f"   📄 JSON: {json_output_path.name}")
    print("="*70)
    
    return images_dir


if __name__ == "__main__":
    generate_report()
