"""GMR Airports Investment Report Agent - 6-section analysis with dashboards"""

import json
import os
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
INVESTMENT_DOCUMENT = config.INVESTMENT_DOCUMENT
TEMPLATES_DIR = config.TEMPLATES_DIR

def load_agent_instructions():
    """Load agent instructions from template file"""
    instructions_file = TEMPLATES_DIR / "instructions" / "investment_report_agent_instructions.txt"
    return instructions_file.read_text(encoding="utf-8")

def load_dashboards():
    """Load dashboard specifications from template file"""
    dashboards_file = TEMPLATES_DIR / "prompts" / "investment_report_dashboards.json"
    return json.loads(dashboards_file.read_text(encoding="utf-8"))

def load_report_sections():
    """Load report sections from template file"""
    sections_file = TEMPLATES_DIR / "prompts" / "investment_report_sections.json"
    return json.loads(sections_file.read_text(encoding="utf-8"))

# Load configurations from templates
DASHBOARDS = load_dashboards()
REPORT_SECTIONS = load_report_sections()

def create_agent():
    """Create Azure AI agent"""
    project_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=PROJECT_CONNECTION_STRING
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
        instructions=load_agent_instructions(),
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
    
    # If section has a dashboard, prepend dashboard generation instructions
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
            img_filename = f"{section_key}_{idx}.png" if len(images) > 1 else f"{section_key}.png"
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
    
    return f"\n## {section['name']}\n\n{content}\n"

def generate_report():
    """Generate complete 6-section report"""
    print("\n" + "="*70)
    print("GMR AIRPORTS - INVESTMENT REPORT GENERATOR")
    print("6 Sections | Concise Analysis | Essential Dashboards")
    print("="*70 + "\n")
    
    project_client, agent, thread = create_agent()
    
    # Generate report header
    timestamp = datetime.now().strftime("%B %d, %Y")
    report = f"""# GMR Airports Limited - Investment Analysis
**Mutual Fund Investment Report | {timestamp}**

---
"""
    
    # Generate each section with delay to avoid rate limits
    import time
    for section_key in REPORT_SECTIONS.keys():
        section_content = generate_section(project_client, agent, thread, section_key)
        report += section_content
        report += "\n---\n"
        
        # Wait 25 seconds between sections to avoid rate limit
        time.sleep(25)
    
    report += "\n*Report generated by Azure AI Investment Analysis Agent*\n"
    
    # Save markdown report to frontend directory
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = config.FRONTEND_DIR / f"GMR_Investment_Report_{timestamp_str}.md"
    output_path.write_text(report, encoding="utf-8")
    
    # Save structured JSON output to frontend/public/data
    json_output = {
        "symbol": "GMRAIRPORT.NS",
        "company_name": "GMR Airports Ltd",
        "analysis_type": "investment_report",
        "generated_at": datetime.now().isoformat(),
        "report_file": output_path.name,
        "data_source": "investmentproposal_processed.json"
    }
    
    config.PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_output_path = config.PUBLIC_DATA_DIR / "company_analysis_output.json"
    json_output_path.write_text(json.dumps(json_output, indent=2), encoding="utf-8")
    
    print("="*70)
    print(f"✅ REPORT COMPLETE:")
    print(f"   - Markdown: {output_path.name}")
    print(f"   - JSON: {json_output_path.name}")
    print("="*70)
    
    return output_path

if __name__ == "__main__":
    generate_report()
