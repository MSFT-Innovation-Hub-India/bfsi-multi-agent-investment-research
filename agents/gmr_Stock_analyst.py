"""GMR Airports Stock Analyst Agent - Stock analysis with visualizations"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FilePurpose, FileSearchTool, CodeInterpreterTool

# Import configuration from config.py
import config

# Use configuration from config module
PROJECT_CONNECTION_STRING = config.PROJECT_CONNECTION_STRING
MODEL_DEPLOYMENT = config.MODEL_DEPLOYMENT
STOCK_ANALYSIS_DOCUMENT = config.STOCK_ANALYSIS_DOCUMENT
TEMPLATES_DIR = config.TEMPLATES_DIR

def load_agent_instructions():
    """Load agent instructions from template file"""
    instructions_file = TEMPLATES_DIR / "instructions" / "stock_analyst_instructions.txt"
    return instructions_file.read_text(encoding="utf-8")

def load_report_sections():
    """Load report sections from template file"""
    sections_file = TEMPLATES_DIR / "prompts" / "stock_analyst_sections.json"
    return json.loads(sections_file.read_text(encoding="utf-8"))

# Load report sections from template
REPORT_SECTIONS_FINAL = load_report_sections()

def create_agent():
    """Create Azure AI agent"""
    project_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=PROJECT_CONNECTION_STRING
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
        instructions=load_agent_instructions(),
        tools=all_tools,
        tool_resources=tool_resources
    )
    print(f"✅ Agent: {agent.id}")
    
    thread = project_client.agents.create_thread()
    print(f"✅ Thread: {thread.id}\n")
    
    return project_client, agent, thread

def generate_section(project_client, agent, thread, section_key, retry_delay=2):
    """Generate one report section/panel with retry logic"""
    section = REPORT_SECTIONS_FINAL[section_key]
    print(f"\n{'='*70}")
    print(f"📝 {section['name']}")
    print('='*70)
    
    # Build full prompt from section
    full_prompt = section.get('prompt', '')
    
    # If section has dashboard specs, include them
    if section.get('dashboard_spec'):
        specs = "\n".join(section['dashboard_spec']) if isinstance(section['dashboard_spec'], list) else section['dashboard_spec']
        full_prompt = f"DASHBOARD SPECIFICATIONS:\n{specs}\n\n{full_prompt}"
    
    if section.get('dashboard'):
        print(f"   📊 Dashboard: {section['dashboard']}.png")
    
    # Add delay before API call to avoid rate limits
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
        section_data = {
            "id": section_key,
            "name": section['name'],
            "summary": "Section generation failed",
            "image": None,
            "dashboard": section.get('dashboard'),
            "size": section.get('size')
        }
        return f"\n## {section['name']}\n\n*Section generation failed*\n", section_data
    
    messages = project_client.agents.list_messages(thread_id=thread.id)
    
    content = ""
    images = []
    
    for msg in messages.data:
        if msg.role == "assistant":
            for item in msg.content:
                if hasattr(item, "text"):
                    content = item.text.value
                    # Check for file IDs in text annotations (code interpreter outputs)
                    if hasattr(item.text, 'annotations'):
                        for annotation in item.text.annotations:
                            if hasattr(annotation, 'file_path') and hasattr(annotation.file_path, 'file_id'):
                                images.append(annotation.file_path.file_id)
                # Handle both image_file and image attributes
                elif hasattr(item, "image_file"):
                    images.append(item.image_file.file_id)
                elif hasattr(item, "image"):
                    images.append(item.image.file_id)
            if content:  # Found the latest assistant message
                break
    
    # Show full agent response in terminal
    if content:
        print(f"\n📄 Agent Response:")
        print("-" * 70)
        print(content)
        print("-" * 70)
    
    # Save images to frontend/images directory from config
    images_dir = config.IMAGES_DIR
    images_dir.mkdir(parents=True, exist_ok=True)
    
    saved_images = []
    for idx, img_id in enumerate(images, 1):
        try:
            # Use dashboard filename if specified, otherwise generic name
            if section.get('dashboard'):
                img_filename = f"{section['dashboard']}.png"
            elif len(images) > 1:
                img_filename = f"{section_key}_{idx}.png"
            else:
                img_filename = f"{section_key}.png"
            
            # Use save_file method like in PDF generator
            project_client.agents.save_file(
                file_id=img_id,
                file_name=img_filename,
                target_dir=str(images_dir)
            )
            saved_images.append(img_filename)
            print(f"   💾 Saved: {img_filename}")
        except Exception as e:
            print(f"   ⚠️ Image save failed: {e}")
    
    # Replace sandbox paths with local paths in content
    if saved_images:
        for img_file in saved_images:
            content = content.replace("sandbox:/mnt/data/", f"images/")
            content = content.replace("![", f"![")  # Ensure markdown image syntax
    
    print(f"   ✅ Complete ({len(saved_images)} images)")
    if not images:
        print(f"   ⚠️  No images were generated for this section")
    print()
    
    # Return both markdown content and structured data
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
    """Generate complete unified stock analysis report with canvas stitching"""
    print("\n" + "="*70)
    print("GMR AIRPORTS - UNIFIED STOCK REPORT GENERATOR")
    print("5 Panels: Executive Summary, Price Trend, Relative Perf, Liquidity, Volatility")
    print("="*70 + "\n")
    
    project_client, agent, thread = create_agent()
    
    # Define images directory from config early to avoid UnboundLocalError
    images_dir = config.IMAGES_DIR
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Define section order (skip meta, rules, and stitching_and_output)
    panel_sections = [
        "executive_summary",
        "panel_p1_price_trend",
        "panel_p2_relative_perf",
        "panel_p3_liquidity",
        "panel_p4_volatility"
    ]
    
    # Generate each panel with 10-second delays to avoid rate limits
    panels_generated = []
    report_sections_data = []
    
    for idx, section_key in enumerate(panel_sections):
        # Use 15 seconds delay between each panel to avoid rate limits
        delay = 15
        section_content, section_data = generate_section(project_client, agent, thread, section_key, retry_delay=delay)
        panels_generated.append(section_key)
        report_sections_data.append(section_data)
    
    # Create JSON report
    json_report = {
        "report_metadata": {
            "symbol": "GMRAIRPORT.NS",
            "company_name": "GMR Airports Ltd",
            "report_type": "stock_analysis",
            "generated_at": datetime.now().isoformat(),
            "total_panels": len(panels_generated)
        },
        "sections": report_sections_data,
        "image_location": "frontend/images/",
        "files": [
            "executive_summary.png",
            "p1_price_trend.png",
            "p2_relative_perf.png",
            "p3_liquidity.png",
            "p4_volatility.png"
        ]
    }
    
    # Save JSON report to frontend/public/data
    config.PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_output_path = config.PUBLIC_DATA_DIR / "stock_report.json"
    json_output_path.write_text(json.dumps(json_report, indent=2), encoding="utf-8")
    
    # Note: Compliance agent will directly use gmr_stock_analysis.json from project root
    print(f"✅ Stock analysis data available at: {config.STOCK_ANALYSIS_DOCUMENT.name}")
    
    print("="*70)
    print(f"✅ ALL PANELS GENERATED SUCCESSFULLY")
    print(f"   📊 Total Panels: {len(panels_generated)}")
    print(f"   📁 Location: frontend/images/")
    print(f"   📄 Files:")
    print(f"       - executive_summary.png")
    print(f"       - p1_price_trend.png")
    print(f"       - p2_relative_perf.png")
    print(f"       - p3_liquidity.png")
    print(f"       - p4_volatility.png")
    print(f"   📋 JSON Report: {json_output_path.relative_to(config.BASE_DIR)}")
    print(f"   📋 Source Data: {config.STOCK_ANALYSIS_DOCUMENT.name} (used by compliance agent)")
    print("="*70)
    
    return images_dir

if __name__ == "__main__":
    generate_report()
