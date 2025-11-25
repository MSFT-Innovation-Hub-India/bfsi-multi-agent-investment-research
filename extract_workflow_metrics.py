import os
import json
import sys
from pathlib import Path
from autogen import AssistantAgent, UserProxyAgent
import config

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

data_dir = config.PUBLIC_DATA_DIR
with open(data_dir / 'stock_report.json', 'r', encoding='utf-8') as f:
    stock_data = json.load(f)

with open(data_dir / 'company_analysis_output.json', 'r', encoding='utf-8') as f:
    investment_data = json.load(f)

with open(data_dir / 'compliance_findings.json', 'r', encoding='utf-8') as f:
    compliance_data = json.load(f)

# Configure LLM - load from environment variables
llm_config = {
    "config_list": [{
        "model": os.getenv("AUTOGEN_MODEL", "gpt-4o-mini"),
        "api_type": "azure",
        "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        "azure_deployment": os.getenv("AUTOGEN_DEPLOYMENT", "gpt-4o-mini")
    }],
    "temperature": float(os.getenv("AUTOGEN_TEMPERATURE", "0.3")),
    "max_tokens": int(os.getenv("AUTOGEN_MAX_TOKENS", "4000")),
    "timeout": int(os.getenv("AUTOGEN_TIMEOUT", "300"))
}

stock_extraction_prompt = f"""
Analyze the following stock report data and extract exactly these 4 metrics in JSON format:

Stock Data:
{json.dumps(stock_data, indent=2)}

Extract:
1. 30-Day Return (percentage value)
2. Volatility (annualized percentage)
3. Average Daily Volume (in millions, format as "X.XXM")
4. Total Traded Value in 30 days (in crores, format as "₹X,XXX Cr")

IMPORTANT: Return ONLY the JSON object. No code, no explanations, no markdown. Just the raw JSON.

Required JSON structure:
{{
  "30_day_return": "X.XX%",
  "volatility": "XX.XX%",
  "avg_volume": "XX.XXM",
  "traded_value": "₹X,XXX Cr"
}}
"""

investment_extraction_prompt = f"""
Analyze the following investment report data and extract exactly these 4 metrics in JSON format:

Investment Data:
{json.dumps(investment_data, indent=2)}

Extract from the financial performance and valuation sections:
1. Revenue Growth (FY24 to FY25, percentage)
2. EBITDA Margin (FY25P, percentage)
3. Debt-to-Equity Ratio (format as "X.XXx")
4. EV/EBITDA multiple (format as "XXXx")

IMPORTANT: Return ONLY the JSON object. No code, no explanations, no markdown. Just the raw JSON.

Required JSON structure:
{{
  "revenue_growth": "XX.X%",
  "ebitda_margin": "X.XX%",
  "debt_equity": "X.XXx",
  "ev_ebitda": "XXXx"
}}
"""

compliance_extraction_prompt = f"""
Analyze the following compliance findings and extract exactly these 4 metrics in JSON format:

Compliance Data:
{json.dumps(compliance_data, indent=2)}

Extract:
1. Trading Classification (Traded/Non-Traded/Thinly Traded)
2. 30-day Traded Value (in crores, format as "₹X,XXX Cr")
3. 30-day Volume (in millions, format as "XXM")
4. Verdict (Review/Approved based on exceptional events)

IMPORTANT: Return ONLY the JSON object. No code, no explanations, no markdown. Just the raw JSON.

Required JSON structure:
{{
  "classification": "Traded",
  "traded_value": "₹X,XXX Cr",
  "volume": "XXM",
  "verdict": "Review"
}}
"""

output_extraction_prompt = f"""
Based on the following analysis data, write concise 2-3 line summaries for each agent:

Stock Analysis:
{json.dumps(stock_data.get('sections', [{}])[0], indent=2)}

Investment Analysis:
{json.dumps(investment_data.get('sections', [{}])[0], indent=2)}

Compliance Analysis:
{json.dumps(compliance_data, indent=2)}

Write 3 separate summaries (2-3 sentences each) that capture the key findings:

IMPORTANT: Return ONLY the JSON object. No code, no explanations, no markdown. Just the raw JSON.

Required JSON structure:
{{
  "stock_summary": "2-3 sentences about stock performance and trading activity...",
  "investment_summary": "2-3 sentences about financial health and valuation...",
  "compliance_summary": "2-3 sentences about regulatory compliance and trading classification..."
}}
"""

print("Extracting Stock Analyst metrics...")
stock_assistant = AssistantAgent("stock_assistant", llm_config=llm_config)
stock_proxy = UserProxyAgent("stock_proxy", code_execution_config={"use_docker": False})
stock_result = stock_proxy.initiate_chat(
    stock_assistant,
    message=stock_extraction_prompt,
    max_turns=1
)

print("\nExtracting Investment Analyst metrics...")
investment_assistant = AssistantAgent("investment_assistant", llm_config=llm_config)
investment_proxy = UserProxyAgent("investment_proxy", code_execution_config={"use_docker": False})
investment_result = investment_proxy.initiate_chat(
    investment_assistant,
    message=investment_extraction_prompt,
    max_turns=1
)

print("\nExtracting Compliance Evaluator metrics...")
compliance_assistant = AssistantAgent("compliance_assistant", llm_config=llm_config)
compliance_proxy = UserProxyAgent("compliance_proxy", code_execution_config={"use_docker": False})
compliance_result = compliance_proxy.initiate_chat(
    compliance_assistant,
    message=compliance_extraction_prompt,
    max_turns=1
)

print("\nGenerating agent summaries...")
output_assistant = AssistantAgent("output_assistant", llm_config=llm_config)
output_proxy = UserProxyAgent("output_proxy", code_execution_config={"use_docker": False})
output_result = output_proxy.initiate_chat(
    output_assistant,
    message=output_extraction_prompt,
    max_turns=1
)

def extract_json_from_response(response_text):
    """Extract JSON object from response that may contain code blocks or extra text"""
    import re
    
    # Remove Python code that's not JSON
    # Look for lines that are clearly Python code (import, print, etc.)
    lines = response_text.split('\n')
    json_lines = []
    in_json = False
    brace_count = 0
    
    for line in lines:
        # Skip Python code lines
        if any(keyword in line for keyword in ['import ', 'print(', '# filename:', 'def ', 'class ']):
            continue
        
        # Check if this line starts or contains JSON
        if '{' in line:
            in_json = True
            brace_count += line.count('{') - line.count('}')
            json_lines.append(line)
        elif in_json:
            brace_count += line.count('{') - line.count('}')
            json_lines.append(line)
            if brace_count <= 0:
                break
    
    # Try to parse the extracted JSON
    if json_lines:
        json_text = '\n'.join(json_lines)
        # Remove markdown code fence markers
        json_text = re.sub(r'```(?:json)?', '', json_text)
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON in code blocks
    code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Find all occurrences of { } and try to parse the largest valid JSON
    brace_positions = []
    depth = 0
    for i, char in enumerate(response_text):
        if char == '{':
            if depth == 0:
                brace_positions.append(i)
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0 and brace_positions:
                start = brace_positions.pop()
                try:
                    return json.loads(response_text[start:i+1])
                except json.JSONDecodeError:
                    continue
    
    # Last resort: try parsing the entire response
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return None

try:
    # Extract JSON from assistant responses
    # AutoGen chat_history is a list of message dicts
    # Get the last message from each chat (should be assistant's response)
    # AutoGen stores messages as dicts with 'content' and 'role' keys
    stock_response = stock_result.chat_history[-1]['content']
    investment_response = investment_result.chat_history[-1]['content']
    compliance_response = compliance_result.chat_history[-1]['content']
    output_response = output_result.chat_history[-1]['content']
    
    # Parse JSON directly since AI now returns pure JSON
    if not stock_response:
        raise ValueError("Stock response is None or empty")
    if not investment_response:
        raise ValueError("Investment response is None or empty")
    if not compliance_response:
        raise ValueError("Compliance response is None or empty")
    if not output_response:
        raise ValueError("Output response is None or empty")
    
    try:
        stock_metrics = json.loads(stock_response.strip())
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse stock response as JSON: {e}")
        print(f"Stock response: {stock_response}")
        raise
    
    try:
        investment_metrics = json.loads(investment_response.strip())
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse investment response as JSON: {e}")
        print(f"Investment response: {investment_response}")
        raise
    
    try:
        compliance_metrics = json.loads(compliance_response.strip())
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse compliance response as JSON: {e}")
        print(f"Compliance response: {compliance_response}")
        raise
    
    try:
        output_summaries = json.loads(output_response.strip())
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse output response as JSON: {e}")
        print(f"Output response: {output_response}")
        raise
    
    # Validate extractions
    if not stock_metrics:
        print("❌ Failed to extract stock metrics")
        print(f"Full Response:\n{stock_response}")
        raise ValueError("Stock metrics extraction failed")
    else:
        print(f"✅ Stock metrics: {stock_metrics}")
    
    if not investment_metrics:
        print("❌ Failed to extract investment metrics")
        print(f"Full Response:\n{investment_response}")
        raise ValueError("Investment metrics extraction failed")
    else:
        print(f"✅ Investment metrics: {investment_metrics}")
    
    if not compliance_metrics:
        print("❌ Failed to extract compliance metrics")
        print(f"Full Response:\n{compliance_response}")
        raise ValueError("Compliance metrics extraction failed")
    else:
        print(f"✅ Compliance metrics: {compliance_metrics}")
    
    if not output_summaries:
        print("❌ Failed to extract output summaries")
        print(f"Full Response:\n{output_response}")
        raise ValueError("Output summaries extraction failed")
    else:
        print(f"✅ Output summaries extracted")
    
    print("✅ All metrics extracted successfully")
    
    # Create the workflow metrics structure
    workflow_metrics = {
        "generated_at": stock_data.get('report_metadata', {}).get('generated_at'),
        "company_name": stock_data.get('report_metadata', {}).get('company_name'),
        "symbol": stock_data.get('report_metadata', {}).get('symbol'),
        "agents": [
            {
                "id": "stock_analyst",
                "name": "Stock Analyst",
                "description": "Analyzing 30-day stock performance, volatility, and liquidity metrics",
                "status": "completed",
                "tasks": [
                    "GMR Stock Data Collection",
                    "Price & Volume Analysis",
                    "Technical Indicators",
                    "Support/Resistance Levels",
                    "Volatility & Trading Patterns"
                ],
                "metrics": [
                    {"label": "30-Day Return", "value": stock_metrics["30_day_return"], "color": "from-green-600/20 to-emerald-600/20"},
                    {"label": "Volatility", "value": stock_metrics["volatility"], "color": "from-blue-600/20 to-cyan-600/20"},
                    {"label": "Avg Volume", "value": stock_metrics["avg_volume"], "color": "from-purple-600/20 to-pink-600/20"},
                    {"label": "Traded Value", "value": stock_metrics["traded_value"], "color": "from-orange-600/20 to-red-600/20"}
                ],
                "output": output_summaries.get("stock_summary", stock_data['sections'][0]['summary'][:200] + "...")
            },
            {
                "id": "investment_analyst",
                "name": "Company Analyst",
                "description": "Evaluating financial performance, debt ratios, and growth projections",
                "status": "completed",
                "tasks": [
                    "Financial Performance Analysis",
                    "Balance Sheet & Debt Analysis",
                    "Operational Performance",
                    "Project Pipeline & Funding",
                    "Valuation & Risk Assessment"
                ],
                "metrics": [
                    {"label": "Revenue Growth", "value": investment_metrics["revenue_growth"], "color": "from-green-600/20 to-emerald-600/20"},
                    {"label": "EBITDA Margin", "value": investment_metrics["ebitda_margin"], "color": "from-blue-600/20 to-cyan-600/20"},
                    {"label": "Debt/Equity", "value": investment_metrics["debt_equity"], "color": "from-orange-600/20 to-red-600/20"},
                    {"label": "EV/EBITDA", "value": investment_metrics["ev_ebitda"], "color": "from-red-600/20 to-pink-600/20"}
                ],
                "output": output_summaries.get("investment_summary", investment_data['sections'][0]['analysis'][:200] + "...")
            },
            {
                "id": "compliance_evaluator",
                "name": "Compliance Evaluator",
                "description": "Verifying trading classification and regulatory compliance",
                "status": "completed",
                "tasks": [
                    "Policy Rules Extraction",
                    "Trading Classification",
                    "Exceptional Events Check",
                    "Final Recommendation"
                ],
                "metrics": [
                    {"label": "Classification", "value": compliance_metrics["classification"], "color": "from-green-600/20 to-emerald-600/20"},
                    {"label": "Traded Value", "value": compliance_metrics["traded_value"], "color": "from-blue-600/20 to-cyan-600/20"},
                    {"label": "Volume", "value": compliance_metrics["volume"], "color": "from-purple-600/20 to-pink-600/20"},
                    {"label": "Verdict", "value": compliance_metrics["verdict"], "color": "from-yellow-600/20 to-orange-600/20" if compliance_metrics["verdict"] == "Review" else "from-green-600/20 to-emerald-600/20"}
                ],
                "output": output_summaries.get("compliance_summary", compliance_data.get('section_4_final_recommendation', compliance_data['section_1_policy_rules'][:200] + "..."))
            }
        ]
    }
    
    # Save to frontend public data folder
    output_path = data_dir / 'workflow_metrics.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow_metrics, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Successfully extracted and saved metrics to {output_path}")
    print("\nExtracted Metrics:")
    print(json.dumps(workflow_metrics, indent=2, ensure_ascii=False))
    
except Exception as e:
    print(f"\n❌ Error parsing responses: {e}")
    print("Please check the assistant responses and try again.")
