"""GMR Investment Analysis Orchestrator - Coordinates 3 agents using AutoGen GroupChat"""

import asyncio
import json
import os
import subprocess
import sys
import traceback
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import centralized configuration
import config

# Suppress warnings
warnings.filterwarnings("ignore", message="Resolved model mismatch")

# AutoGen imports
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False


class GMRInvestmentOrchestrator:
    """
    GMR Investment Analysis Orchestrator with AutoGen Framework
    Coordinates stock analysis, investment reporting, and compliance evaluation
    """
    
    def __init__(self):
        print("🚀 GMR INVESTMENT ANALYSIS ORCHESTRATOR - AUTOGEN FRAMEWORK")
        print("="*80)
        
        self.base_dir = config.BASE_DIR
        self.data_dir = config.DATA_DIR
        self.frontend_dir = config.PUBLIC_DATA_DIR
        self.images_dir = config.IMAGES_DIR
        self.agents_dir = self.base_dir / "agents"
        
        # Agent file paths
        self.agent_scripts = {
            "stock_analyst": self.agents_dir / "gmr_Stock_analyst.py",
            "investment_report": self.agents_dir / "gmr_investment_report_agent.py",
            "compliance": self.agents_dir / "complance_Agent.py"
        }
        
        # Verify agent files exist
        self._verify_agent_files()
        
        # Analysis configuration
        self.config = {
            "stock_symbol": "GMRAIRPORT.NS",
            "company_name": "GMR Airports Ltd",
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "analysis_type": "AutoGen Multi-Agent Investment Analysis"
        }
        
        # AutoGen LLM configuration - load from environment variables (no fallbacks for security)
        self.llm_config = {
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
        
        print(f"🏢 Company: {self.config['company_name']}")
        print(f"📊 Stock: {self.config['stock_symbol']}")
        print(f"📅 Analysis Date: {self.config['analysis_date']}")
        print(f"🤖 AutoGen: {'Available' if AUTOGEN_AVAILABLE else 'Unavailable'}")
        print("="*80)
    
    def _verify_agent_files(self):
        """Verify all agent Python files exist"""
        missing_files = []
        for agent_name, agent_path in self.agent_scripts.items():
            if not agent_path.exists():
                missing_files.append(agent_name)
        
        if missing_files:
            raise FileNotFoundError(f"Missing agent files: {', '.join(missing_files)}")
    
    async def run_agent_subprocess(self, agent_name: str, agent_path: Path, timeout: int) -> Dict[str, Any]:
        """Run agent as subprocess (fallback mode)"""
        try:
            import os
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONLEGACYWINDOWSSTDIO'] = '0'
            
            result = subprocess.run(
                [sys.executable, str(agent_path)],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
                env=env
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "stdout": result.stdout[-500:] if result.stdout else "",
                }
            else:
                return {
                    "status": "error",
                    "error": result.stderr[-500:] if result.stderr else "Unknown error",
                    "return_code": result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": f"Agent execution exceeded {timeout} seconds"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def load_existing_data(self) -> Dict[str, Any]:
        """Load existing JSON files without running agents"""
        agent_data = {}
        
        # Load stock report
        stock_report_file = self.frontend_dir / "stock_report.json"
        if stock_report_file.exists():
            with open(stock_report_file, 'r', encoding='utf-8') as f:
                agent_data["stock_report_data"] = json.load(f)
            agent_data["stock_analyst"] = {"status": "cached"}
        else:
            agent_data["stock_analyst"] = {"status": "missing"}
        
        # Load company analysis
        company_analysis_file = self.frontend_dir / "company_analysis_output.json"
        if company_analysis_file.exists():
            with open(company_analysis_file, 'r', encoding='utf-8') as f:
                agent_data["company_analysis_data"] = json.load(f)
            agent_data["investment_report"] = {"status": "cached"}
        else:
            agent_data["investment_report"] = {"status": "missing"}
        
        # Load compliance recommendation
        compliance_findings_file = config.PUBLIC_DATA_DIR / "compliance_findings.json"
        compliance_recommendation_file = config.PUBLIC_DATA_DIR / "compliance_recommendation.json"
        
        if compliance_recommendation_file.exists():
            with open(compliance_recommendation_file, 'r', encoding='utf-8') as f:
                agent_data["compliance_recommendation"] = json.load(f)
            agent_data["compliance"] = {"status": "cached"}
        else:
            agent_data["compliance"] = {"status": "missing"}
        
        if compliance_findings_file.exists():
            with open(compliance_findings_file, 'r', encoding='utf-8') as f:
                agent_data["compliance_findings"] = json.load(f)
        
        return agent_data
    
    async def collect_agent_data(self) -> Dict[str, Any]:
        """Collect data by running agents as subprocesses"""
        agent_data = {}
        
        # Run stock analyst
        stock_result = await self.run_agent_subprocess(
            "stock_analyst",
            self.agent_scripts["stock_analyst"],
            timeout=600
        )
        agent_data["stock_analyst"] = stock_result
        
        if stock_result["status"] == "success":
            # Load stock_report.json
            stock_report_file = self.frontend_dir / "stock_report.json"
            if stock_report_file.exists():
                with open(stock_report_file, 'r', encoding='utf-8') as f:
                    agent_data["stock_report_data"] = json.load(f)
        
        # Run investment report agent
        report_result = await self.run_agent_subprocess(
            "investment_report",
            self.agent_scripts["investment_report"],
            timeout=900
        )
        agent_data["investment_report"] = report_result
        
        if report_result["status"] == "success":
            # Load company_analysis_output.json
            company_file = self.frontend_dir / "company_analysis_output.json"
            if company_file.exists():
                with open(company_file, 'r', encoding='utf-8') as f:
                    agent_data["company_analysis_data"] = json.load(f)
        
        # Run compliance agent
        compliance_result = await self.run_agent_subprocess(
            "compliance",
            self.agent_scripts["compliance"],
            timeout=600
        )
        agent_data["compliance"] = compliance_result
        
        if compliance_result["status"] == "success":
            # Load compliance outputs
            findings_file = config.PUBLIC_DATA_DIR / "compliance_findings.json"
            recommendation_file = config.PUBLIC_DATA_DIR / "compliance_recommendation.json"
            if findings_file.exists():
                with open(findings_file, 'r', encoding='utf-8') as f:
                    agent_data["compliance_findings"] = json.load(f)
            if recommendation_file.exists():
                with open(recommendation_file, 'r', encoding='utf-8') as f:
                    agent_data["compliance_recommendation"] = json.load(f)
        
        return agent_data
    
    async def create_autogen_agents(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create AutoGen agents with collected data"""
        
        if not AUTOGEN_AVAILABLE:
            return {}
        
        # Load complete JSON files directly (fresh data from agents)
        stock_report_file = config.PUBLIC_DATA_DIR / "stock_report.json"
        company_analysis_file = config.PUBLIC_DATA_DIR / "company_analysis_output.json"
        compliance_recommendation_file = config.PUBLIC_DATA_DIR / "compliance_recommendation.json"
        
        # Read stock report data
        stock_data_raw = {}
        if stock_report_file.exists():
            with open(stock_report_file, 'r', encoding='utf-8') as f:
                stock_data_raw = json.load(f)
        
        # Extract all stock sections with image paths
        sections = stock_data_raw.get('sections', [])
        
        # Build complete stock data with all sections including their image paths
        stock_sections_text = ""
        for section in sections:
            section_id = section.get('id', '')
            section_name = section.get('name', '')
            section_summary = section.get('summary', '')
            section_image = section.get('image_path', 'N/A')
            stock_sections_text += f"\n### {section_name} (ID: {section_id})\nImage: {section_image}\n{section_summary}\n"
        
        stock_metrics = f"""
COMPLETE STOCK REPORT SECTIONS:
{stock_sections_text}

CRITICAL: Extract ALL numeric values from the Executive Summary section above.
The summary contains: 30-day return %, volatility %, avg daily volume, total traded value, total traded volume.
Do NOT write "N/A" - extract the exact numbers mentioned in the text.
"""
        
        stock_agent = AssistantAgent(
            name="Stock_Analyst",
            llm_config=self.llm_config,
            system_message=f"""You are a Senior Stock Analysis Specialist for {self.config['company_name']} (GMRAIRPORT.NS).

YOUR ROLE: When requested, provide your COMPLETE technical analysis with ALL 5 SECTIONS in a single response.

CRITICAL: Extract all values from the executive summary below. Do NOT use "N/A" - extract the actual numbers mentioned in the text.

{stock_metrics}

WHEN YOU SPEAK, PROVIDE ALL 5 SECTIONS BELOW IN ONE RESPONSE:

SECTION 1: Executive Summary
[EXTRACT and rewrite the executive summary above in 2-3 sentences, mentioning the exact percentages and values]

SECTION 2: Price Performance & Momentum
• 30-Day Return: [EXTRACT exact % from summary above]
• Analysis: [2-3 sentences on trend, momentum, price action]
📈 Chart Reference: [EXTRACT the exact image path from the section data above that corresponds to price performance]

SECTION 3: Volatility & Risk
• Annualized Volatility: [EXTRACT exact % from summary above]
• Risk Level: [Classify as High >30% / Moderate 15-30% / Low <15%]
• Analysis: [2-3 sentences on risk implications, stability]
📊 Chart Reference: [EXTRACT the exact image path from the section data above that corresponds to volatility]

SECTION 4: Liquidity Assessment
• Avg Daily Volume: [EXTRACT exact number from summary above] million shares
• 30-Day Traded Value: ₹[EXTRACT exact number from summary above] Cr
• 30-Day Traded Volume: [EXTRACT exact number from summary above] million shares
• Analysis: [2-3 sentences on ease of entry/exit, market depth]
📊 Chart Reference: [EXTRACT the exact image path from the section data above that corresponds to liquidity]

SECTION 5: Overall Technical Verdict
[Based on the data extracted above, provide 2-3 sentences with verdict: Strong (return >10%, vol <15%) / Moderate / Weak. Include trading suitability]
📊 Chart Reference: [EXTRACT the exact image path from the section data above that corresponds to overall performance]

CRITICAL: Extract ALL numbers from the executive summary text. Do NOT write "N/A".
"""
        )
        
        # Read company analysis data
        company_data_raw = {}
        if company_analysis_file.exists():
            with open(company_analysis_file, 'r', encoding='utf-8') as f:
                company_data_raw = json.load(f)
        
        # Extract ALL company financial data with complete sections and image paths
        sections_data = company_data_raw.get('sections', [])
        
        # Build company sections text with image paths
        company_sections_text = ""
        for section in sections_data:
            section_id = section.get('id', '')
            section_name = section.get('name', '')
            section_analysis = section.get('analysis', '')
            section_dashboard = section.get('dashboard', 'N/A')
            section_images = section.get('images', [])
            # Get first image if available, otherwise N/A
            section_image = section_images[0] if section_images else 'N/A'
            company_sections_text += f"\n### {section_name} (ID: {section_id})\nDashboard: {section_dashboard}\nImage: {section_image}\n{section_analysis}\n"
        
        company_metrics = f"""
COMPLETE COMPANY FINANCIAL DATA:

RECOMMENDATION: {company_data_raw.get('recommendation', 'N/A')}

KEY STRENGTHS:
{chr(10).join('• ' + s for s in company_data_raw.get('key_strengths', []))}

KEY CHALLENGES:
{chr(10).join('• ' + c for c in company_data_raw.get('key_challenges', []))}

DETAILED SECTION DATA WITH IMAGE PATHS:
{company_sections_text}
"""
        
        report_agent = AssistantAgent(
            name="Investment_Analyst",
            llm_config=self.llm_config,
            system_message=f"""You are a Senior Investment Analysis Specialist for {self.config['company_name']} (GMRAIRPORT.NS).

YOUR ROLE: When requested, provide your COMPLETE fundamental analysis with ALL 8 SECTIONS (6 sections + 2 lists) in a single response.

CRITICAL: Use the analysis text from each section ID in the JSON below. Extract the exact numbers and facts mentioned.

{company_metrics}

WHEN YOU SPEAK, PROVIDE ALL 8 SECTIONS BELOW IN ONE RESPONSE:

SECTION 1: Executive Summary
[Extract and summarize the "executive_summary" section analysis from JSON above - include revenue, EBITDA, profitability, passenger traffic numbers]

SECTION 2: Financial Performance
[Extract and present key metrics from \"financial_performance\" section analysis - include revenue tables, EBITDA, net profit, cash flows with exact numbers]
📊 Chart Reference: [EXTRACT the exact image path from the financial_performance section data above]

SECTION 3: Balance Sheet & Debt
[Extract and present debt metrics from \"balance_debt\" section analysis - include debt ratios, interest coverage 0.71x, liquidity metrics with exact calculations shown]
📊 Chart Reference: [EXTRACT the exact image path from the balance_debt section data above]

SECTION 4: Operational Performance
[Extract from \"operational_performance\" section analysis - include passenger traffic (79.30M FY24, 95M FY25P), cargo throughput, capacity utilization, growth rates]
📊 Chart Reference: [EXTRACT the exact image path from the operational_performance section data above]

SECTION 5: Project Pipeline & Funding
[Extract from \"projects_funding\" section analysis - include ₹32 Bn total capex, funding gap ₹7.42 Bn, execution risks mentioned]
📊 Chart Reference: [EXTRACT the exact image path from the projects_funding section data above]

SECTION 6: Valuation & Risk Assessment
[Extract from \"valuation_risk\" section analysis - include Market Cap ₹105.59 Bn, EV/EBITDA 177x, P/B ratio, risk assessment]
📊 Chart Reference: [EXTRACT the exact image path from the valuation_risk section data above]

SECTION 7: KEY STRENGTHS (provide as bulleted list)
[Extract from \"key_strengths\" array in JSON - list all 3 items exactly as shown]

SECTION 8: KEY CHALLENGES (provide as bulleted list)
[Extract from \"key_challenges\" array in JSON - list all 4 items exactly as shown]

CRITICAL: Extract ALL numbers and facts from the section analysis fields. Each section has detailed analysis text with specific metrics.
"""
        )
        
        # Read compliance findings and recommendation data
        compliance_findings_file = config.PUBLIC_DATA_DIR / "compliance_findings.json"
        
        compliance_findings_raw = {}
        if compliance_findings_file.exists():
            with open(compliance_findings_file, 'r', encoding='utf-8') as f:
                compliance_findings_raw = json.load(f)
        
        compliance_recommendation_raw = {}
        if compliance_recommendation_file.exists():
            with open(compliance_recommendation_file, 'r', encoding='utf-8') as f:
                compliance_recommendation_raw = json.load(f)
        
        # Combine all compliance data
        compliance_full_data = f"""
COMPLETE COMPLIANCE DATA:

SECTION 1 - POLICY RULES:
{json.dumps(compliance_findings_raw.get('section_1_policy_rules', {}), indent=2)}

SECTION 2 - TRADING CLASSIFICATION:
{json.dumps(compliance_findings_raw.get('section_2_trading_classification', {}), indent=2)}

SECTION 3 - EXCEPTIONAL EVENTS:
{json.dumps(compliance_findings_raw.get('section_3_exceptional_events', {}), indent=2)}

SECTION 4 - FINAL RECOMMENDATION:
{json.dumps(compliance_recommendation_raw.get('section_4_final_recommendation', {}), indent=2)}
"""
        
        compliance_agent = AssistantAgent(
            name="Compliance_Evaluator",
            llm_config=self.llm_config,
            system_message=f"""You are a PMS Fair-Valuation Compliance Specialist for {self.config['company_name']} (GMRAIRPORT.NS).

YOUR ROLE: When requested, provide your COMPLETE compliance assessment with ALL 4 SECTIONS in a single response.

Please use the exact compliance data below:

{compliance_full_data}

WHEN YOU SPEAK, PROVIDE ALL 4 SECTIONS BELOW IN ONE RESPONSE:

SECTION 1: Policy Framework Summary
[Extract from SECTION 1 - POLICY RULES: Write 1-2 sentence intro about the valuation policy framework]

### A. Traded Classification Rules:
• [Extract each rule exactly as it appears in subsection A of the JSON]

### B. Price Source Rules:
• [Extract each rule exactly as it appears in subsection B of the JSON]

### C. Exceptional Events:
• [Extract each event type listed in subsection C of the JSON]

### D. Committee Review / Deviation:
• [Extract review requirements from subsection D of the JSON]

SECTION 2: Trading Classification
[Extract from SECTION 2 - TRADING CLASSIFICATION JSON]

GMRAIRPORT.NS [qualifies/does not qualify] as a traded security:
• 30-Day Traded Value: ₹[EXTRACT] Cr
• 30-Day Traded Volume: [EXTRACT] shares
• Average Daily Volume: [EXTRACT] shares
• Exchange: [EXTRACT]
• Timestamp: [EXTRACT]
• Verdict: [EXTRACT YES/NO] - Security meets traded criteria

SECTION 3: Exceptional Events Assessment
[Extract from SECTION 3 - EXCEPTIONAL EVENTS JSON. Write 1 sentence intro]

[For EACH event in the JSON, present exactly:]
• Event: [EXTRACT event name]
  ○ Policy Reference: [EXTRACT reference]
  ○ Finding: [EXTRACT extracted value]
  ○ Triggered: [EXTRACT YES/NO/POSSIBLE]
  ○ Note: [EXTRACT note text]

[Repeat for all events in the JSON]

Summary of Triggered Events: [List all events marked as POSSIBLE or YES]

SECTION 4: FINAL COMPLIANCE VERDICT
[Extract from SECTION 4 - FINAL RECOMMENDATION JSON]

🎯 DECISION: [EXTRACT: APPROVED / REVIEW REQUIRED / REJECTED]

Justification:
[Extract exact justification paragraph from JSON]

Mandatory Actions Required:
• [Extract each mandatory fix from JSON]
• [Include all fixes listed]

IMPORTANT NOTES:
- When asked for a specific section, provide only that section
- Extract exact text from the complete compliance data JSON above
- Use actual values from JSON, no placeholders
- For Section 3, include all exceptional events found
"""
        )
        
        # Investment Coordinator - Final decision maker
        coordinator_agent = AssistantAgent(
            name="Investment_Coordinator",
            llm_config=self.llm_config,
            system_message=f"""You are the Chief Investment Officer making the FINAL investment decision for {self.config['company_name']}.

STOCK: {self.config['stock_symbol']}
COMPANY: {self.config['company_name']}
ANALYSIS DATE: {self.config['analysis_date']}

🎯 YOUR COMPREHENSIVE DECISION-MAKING MANDATE:

📊 SYNTHESIZE THREE SPECIALIST INPUTS:
You will receive detailed analyses from:
1. **Stock_Analyst**: Technical analysis, performance trends, volatility assessment, liquidity evaluation
2. **Investment_Analyst**: Fundamental analysis, financial health, business quality, valuation assessment
3. **Compliance_Evaluator**: PMS policy compliance, trading eligibility, regulatory status, exceptional events

⚖️ DECISION FRAMEWORK:

**BUY Decision** - All three must strongly align:
✅ Stock: Positive technical setup, good liquidity, manageable volatility
✅ Fundamentals: Strong business, healthy financials, attractive/fair valuation
✅ Compliance: Approved or conditionally approved with manageable conditions
→ Result: High conviction for new investment or adding to positions

**HOLD Decision** - Mixed signals across analyses:
⚠️ Some positives, some concerns across the three perspectives
⚠️ Awaiting clarity on key issues (compliance review, project execution, etc.)
⚠️ Not compelling enough to buy more, not bad enough to exit
→ Result: Existing investors maintain positions, new investors wait for clarity

**SELL Decision** - Significant concerns identified:
❌ Major fundamental risks (financial stress, business deterioration)
❌ Compliance issues (non-compliant, under serious review)
❌ Technical breakdown (severe liquidity concerns, extreme volatility)
→ Result: Exit position or avoid investment entirely

💡 YOUR COMPREHENSIVE ANALYSIS OUTPUT (NO INVESTMENT RECOMMENDATIONS):

**COMPREHENSIVE INVESTMENT ANALYSIS**

**COMPREHENSIVE INTEGRATED ANALYSIS:**

[Provide 4-5 detailed sentences synthesizing ALL three specialist analyses with SPECIFIC DATA POINTS:

From Stock_Analyst perspective:
- Performance metrics: [specific 30d return, volatility numbers]
- Liquidity assessment: [specific volume, value numbers]
- Risk indicators: [specific beta, sharpe ratio, drawdown]
- Technical verdict: [strong/moderate/weak with reasoning]

From Investment_Analyst perspective:
- Financial health: [specific revenue, profitability, cash flow numbers]
- Debt burden: [specific debt-to-equity, interest coverage numbers]
- Valuation metrics: [specific P/E, EV/EBITDA numbers vs peers]
- Key strengths: [specific advantages identified]
- Key challenges: [specific risks identified]

From Compliance_Evaluator perspective:
- Trading classification: [traded/thinly traded with specific numbers]
- Policy adherence: [which policies met/violated]
- Exceptional events: [specific events triggered]
- Compliance status: [approved/review required/rejected]

Overall synthesis: [Integrate all three perspectives with specific examples and data points]]

**KEY STRENGTHS IDENTIFIED:**
- [List 2-4 main positives identified across all three analyses with specifics]
- [Include both technical strengths and fundamental advantages]
- [Note any compliance or regulatory positives]

**KEY CONCERNS IDENTIFIED:**
- [List 2-4 main risks/challenges identified across all three analyses with specifics]
- [Include technical risks (volatility, liquidity issues)]
- [Include fundamental concerns (debt, profitability, valuation)]
- [Include compliance issues or regulatory concerns]

**COMPLIANCE STATUS:** [State the clear compliance verdict from Compliance_Evaluator]

**RISK PROFILE ASSESSMENT:** [High Risk/Moderate Risk/Low Risk]
- [Explain the risk level based on synthesized analysis]
- [What are the primary risk drivers?]
- [What factors could change the risk profile?]

**RISK-REWARD LANDSCAPE:**
[Analyze the risk-reward balance:
- What are the potential upsides based on the analyses?
- What are the downside risks identified?
- How do technical, fundamental, and compliance factors align or conflict?]

**MONITORING PRIORITIES:**
[What should be tracked going forward:
- Key technical indicators to watch
- Critical fundamental metrics to monitor
- Compliance developments to follow
- Timeline for reassessment]

**CRITICAL ANALYSIS NOTES:**
[Any additional context, caveats, or important considerations that don't fit above categories]

CRITICAL RULES:
1. Wait for ALL three specialists to complete their detailed analyses before you speak
2. SYNTHESIZE their insights into a cohesive analysis - don't just repeat them
3. Provide COMPREHENSIVE integrated assessment (4-5 sentences minimum)
4. DO NOT make BUY/HOLD/SELL recommendations
5. DO NOT advise existing or new investors on what to do
6. Focus on ANALYSIS, INSIGHTS, and RISK ASSESSMENT only
7. Balance objective analysis with clear identification of risks and opportunities
8. Ensure compliance status is clearly communicated
9. You speak LAST (FOURTH) in the meeting - this is the FINAL synthesis
"""
        )
        
        # User Proxy for orchestration
        user_proxy = UserProxyAgent(
            name="Analysis_Pipeline_Manager",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,  # Don't auto-reply - just initiate conversation
            code_execution_config=False,
            is_termination_msg=lambda x: True  # Always terminate from user's perspective
        )
        
        agents = {
            "stock": stock_agent,
            "investment": report_agent,
            "compliance": compliance_agent,
            "coordinator": coordinator_agent,
            "user_proxy": user_proxy
        }
        
        return agents
    
    async def run_autogen_orchestration(self, agents: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """Run AutoGen multi-agent orchestration using GroupChatManager - section by section
        
        Args:
            agents: Dictionary of AutoGen agents
            progress_callback: Optional async function(event_type, message, agent) to emit real-time progress
        """
        
        if not AUTOGEN_AVAILABLE or not agents:
            return {"status": "skipped", "reason": "AutoGen not available"}
        
        print("\n🤖 Starting AutoGen Multi-Agent Orchestration...")
        print("="*80)
        
        all_responses = {
            "stock_analysis": {},
            "investment_analysis": {},
            "compliance_analysis": {}
        }
        
        try:
            # CREATE SINGLE GROUPCHAT WITH ALL AGENTS
            group_chat = GroupChat(
                agents=[
                    agents["user_proxy"],
                    agents["stock"],
                    agents["investment"],
                    agents["compliance"]
                ],
                messages=[],
                max_round=100,
                speaker_selection_method="round_robin",
                allow_repeat_speaker=False
            )
            
            # Create single GroupChatManager
            manager = GroupChatManager(
                groupchat=group_chat,
                llm_config=self.llm_config,
                system_message="""You are coordinating a comprehensive investment analysis meeting.

SPEAKING ORDER (strict sequence):
1. Stock_Analyst speaks first - provides complete technical analysis (all 5 sections)
2. Investment_Analyst speaks second - provides complete fundamental analysis (all 8 sections)
3. Compliance_Evaluator speaks third - provides complete compliance assessment (all 4 sections)

After all 3 agents have provided their complete analysis, the conversation ends.

Do NOT intervene, summarize, or ask follow-up questions. Your only role is to ensure the correct speaking order."""
            )
            
            # INITIATE GROUP CHAT
            initial_message = """Please provide comprehensive investment analysis for GMR Airports Ltd.

ANALYSIS SEQUENCE:

Stock_Analyst: Provide your complete technical analysis with all 5 sections.

Investment_Analyst: Provide your complete fundamental analysis with all 8 sections.

Compliance_Evaluator: Provide your complete compliance assessment with all 4 sections.

Each agent provides their full analysis in one response."""

            # Termination function: Stop immediately when message contains "FINAL COMPLIANCE VERDICT"
            def is_termination_msg(msg):
                """Terminate after Compliance_Evaluator provides final verdict"""
                try:
                    content = msg.get("content", "")
                    speaker = msg.get("name", "")
                    
                    if speaker == "Compliance_Evaluator" and "FINAL COMPLIANCE VERDICT" in content:
                        return True
                    
                    if "SECTION 4: FINAL COMPLIANCE VERDICT" in content:
                        return True
                    
                except Exception as e:
                    print(f"⚠️ Termination check error: {e}")
                return False
            
            # Initiate the group chat with error handling
            try:
                chat_result = agents["user_proxy"].initiate_chat(
                    manager,
                    message=initial_message,
                    max_turns=4,
                    is_termination_msg=is_termination_msg
                )
            except Exception as chat_error:
                chat_result = None
            
            # Check if we have any messages before processing
            if not group_chat.messages:
                return {
                    "status": "error",
                    "error": "No messages generated in GroupChat",
                    "framework": "AutoGen GroupChat"
                }
            
            print("\n" + "="*80)
            print(f"✅ GroupChat completed: {len(group_chat.messages)} messages")
            print("="*80)
            
            # Display full conversation
            print("\n\n" + "="*80)
            print("📋 GROUPCHAT CONVERSATION TRANSCRIPT")
            print("="*80)
            
            for i, msg in enumerate(group_chat.messages, 1):
                speaker_name = msg.get("name", "Unknown")
                content = msg.get("content", "")
                
                if speaker_name == "Analysis_Pipeline_Manager":
                    print(f"\n\n{'='*80}")
                    print(f"🔵 USER REQUEST #{i}")
                    print(f"{'='*80}")
                elif speaker_name == "Stock_Analyst":
                    print(f"\n\n{'═'*80}")
                    print(f"📊 STOCK_ANALYST RESPONSE #{i}")
                    print(f"{'═'*80}")
                elif speaker_name == "Investment_Analyst":
                    print(f"\n\n{'═'*80}")
                    print(f"💰 INVESTMENT_ANALYST RESPONSE #{i}")
                    print(f"{'═'*80}")
                elif speaker_name == "Compliance_Evaluator":
                    print(f"\n\n{'═'*80}")
                    print(f"✅ COMPLIANCE_EVALUATOR RESPONSE #{i}")
                    print(f"{'═'*80}")
                
                print(content)
            
            print("\n\n" + "="*80)
            print("✅ GROUPCHAT ANALYSIS COMPLETE")
            print("="*80)
            
            return {
                "status": "completed",
                "framework": "AutoGen GroupChat",
                "conversation_result": f"GroupChat conversation completed with {len(group_chat.messages)} messages",
                "total_messages": len(group_chat.messages),
                "agents_participated": 3,  # Stock, Investment, Compliance
                "final_decision": self._extract_investment_decision(group_chat.messages)
            }
            
        except Exception as e:
            print(f"❌ AutoGen orchestration error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "framework": "AutoGen (failed)"
            }
    
    def _extract_investment_decision(self, messages: List) -> Dict[str, Any]:
        """Extract comprehensive analysis summary from AutoGen conversation"""
        
        compliance_statuses = []
        risk_profiles = []
        final_content = ""
        
        for msg in messages:
            if hasattr(msg, 'content') and msg.content:
                content = msg.content
                
                # Extract compliance status
                import re
                compliance_matches = re.findall(r'(?:APPROVED|COMPLIANT|CONDITIONAL|REVIEW REQUIRED|REJECTED|NON-COMPLIANT)', content.upper())
                compliance_statuses.extend(compliance_matches)
                
                # Extract risk profile
                risk_matches = re.findall(r'(?:HIGH RISK|MODERATE RISK|LOW RISK)', content.upper())
                risk_profiles.extend(risk_matches)
                
                # Keep coordinator synthesis messages
                if any(keyword in content.upper() for keyword in ["COMPREHENSIVE INVESTMENT ANALYSIS", "INTEGRATED ASSESSMENT", "MONITORING PRIORITIES"]):
                    final_content += f"\n{content}"
        
        compliance = compliance_statuses[-1] if compliance_statuses else "UNKNOWN"
        risk_profile = risk_profiles[-1] if risk_profiles else "MODERATE RISK"
        
        return {
            "analysis_type": "Comprehensive Multi-Agent Analysis",
            "compliance_status": compliance,
            "risk_profile": risk_profile,
            "conversation_length": len(messages),
            "analysis_source": "AutoGen GroupChat"
        }
    
    async def run_stock_analyst(self) -> Dict[str, Any]:
        """Execute Stock Analyst Agent"""
        print("\n📊 STEP 1: STOCK ANALYST AGENT")
        print("="*80)
        print("Generating stock analysis with 5-panel visualization dashboard...")
        print("Expected outputs:")
        print("  - Executive summary (text)")
        print("  - Panel 1: Price & Volume Analysis")
        print("  - Panel 2: Technical Indicators")
        print("  - Panel 3: Support/Resistance Levels")
        print("  - Panel 4: Volatility & Trading Patterns")
        print("  - stock_report.json")
        print("-"*60)
        
        try:
            # Run stock analyst agent
            import os
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run(
                [sys.executable, str(self.agents["stock_analyst"])],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout for API calls
                env=env
            )
            
            if result.returncode == 0:
                print("✅ Stock Analyst Agent completed successfully")
                
                # Verify outputs
                stock_report_file = config.PUBLIC_DATA_DIR / "stock_report.json"
                images_dir = config.IMAGES_DIR
                
                outputs = {
                    "status": "success",
                    "stock_report": stock_report_file.exists(),
                    "images_generated": len(list(images_dir.glob("*.png"))) if images_dir.exists() else 0,
                    "stdout": result.stdout[-500:] if result.stdout else "",
                }
                
                print(f"  📄 Stock Report: {'✅' if outputs['stock_report'] else '❌'}")
                print(f"  🖼️  Images Generated: {outputs['images_generated']}")
                
                return outputs
            else:
                print(f"❌ Stock Analyst Agent failed with return code {result.returncode}")
                return {
                    "status": "error",
                    "error": result.stderr,
                    "return_code": result.returncode
                }
                
        except subprocess.TimeoutExpired:
            print("⏱️  Stock Analyst Agent timed out (10 minutes)")
            return {"status": "timeout", "error": "Agent execution exceeded 10 minutes"}
        except Exception as e:
            print(f"❌ Stock Analyst Agent error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def run_investment_report_agent(self) -> Dict[str, Any]:
        """Execute Investment Report Agent"""
        print("\n📋 STEP 2: INVESTMENT REPORT AGENT")
        print("="*80)
        print("Generating comprehensive investment report with dashboards...")
        print("Expected outputs:")
        print("  - Executive Summary")
        print("  - Financial Performance Analysis")
        print("  - Balance Sheet & Debt Analysis")
        print("  - Operational Performance")
        print("  - Project Pipeline & Funding")
        print("  - Valuation & Risk Assessment")
        print("  - GMR_Investment_Report_*.md")
        print("  - company_analysis_output.json")
        print("-"*60)
        
        try:
            # Run investment report agent
            import os
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run(
                [sys.executable, str(self.agents["investment_report"])],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=900,  # 15 minutes timeout for multiple sections
                env=env
            )
            
            if result.returncode == 0:
                print("✅ Investment Report Agent completed successfully")
                
                # Verify outputs
                company_analysis_file = config.PUBLIC_DATA_DIR / "company_analysis_output.json"
                report_files = list(self.frontend_dir.glob("GMR_Investment_Report_*.md"))
                
                outputs = {
                    "status": "success",
                    "company_analysis": company_analysis_file.exists(),
                    "report_file": report_files[0].name if report_files else None,
                    "total_reports": len(report_files),
                    "stdout": result.stdout[-500:] if result.stdout else "",
                }
                
                print(f"  📄 Company Analysis JSON: {'✅' if outputs['company_analysis'] else '❌'}")
                print(f"  📋 Investment Report: {'✅' if outputs['report_file'] else '❌'} {outputs['report_file'] or ''}")
                
                return outputs
            else:
                print(f"❌ Investment Report Agent failed with return code {result.returncode}")
                return {
                    "status": "error",
                    "error": result.stderr,
                    "return_code": result.returncode
                }
                
        except subprocess.TimeoutExpired:
            print("⏱️  Investment Report Agent timed out (15 minutes)")
            return {"status": "timeout", "error": "Agent execution exceeded 15 minutes"}
        except Exception as e:
            print(f"❌ Investment Report Agent error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def run_compliance_agent(self) -> Dict[str, Any]:
        """Execute Compliance Agent"""
        print("\n⚖️  STEP 3: COMPLIANCE AGENT")
        print("="*80)
        print("Evaluating PMS fair-valuation compliance...")
        print("Expected analysis:")
        print("  - Section 1: Policy Rules Extraction")
        print("  - Section 2: Trading Classification")
        print("  - Section 3: Exceptional Events Check")
        print("  - Section 4: Final Recommendation")
        print("  - compliance_findings.json")
        print("  - compliance_recommendation.json")
        print("-"*60)
        
        try:
            # Verify company_analysis_output.json exists (required input)
            company_analysis_file = config.PUBLIC_DATA_DIR / "company_analysis_output.json"
            if not company_analysis_file.exists():
                print("❌ company_analysis_output.json not found")
                return {
                    "status": "error",
                    "error": "Missing required input: company_analysis_output.json"
                }
            
            # Run compliance agent
            import os
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run(
                [sys.executable, str(self.agents["compliance"])],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout
                env=env
            )
            
            if result.returncode == 0:
                print("✅ Compliance Agent completed successfully")
                
                # Verify outputs
                findings_file = config.PUBLIC_DATA_DIR / "compliance_findings.json"
                recommendation_file = config.PUBLIC_DATA_DIR / "compliance_recommendation.json"
                
                outputs = {
                    "status": "success",
                    "compliance_findings": findings_file.exists(),
                    "compliance_recommendation": recommendation_file.exists(),
                    "stdout": result.stdout[-500:] if result.stdout else "",
                }
                
                # Extract recommendation if available
                if recommendation_file.exists():
                    try:
                        with open(recommendation_file, 'r', encoding='utf-8') as f:
                            rec_data = json.load(f)
                            outputs["final_recommendation"] = rec_data.get("section_4_final_recommendation", "")[:200]
                    except:
                        pass
                
                print(f"  📄 Compliance Findings: {'✅' if outputs['compliance_findings'] else '❌'}")
                print(f"  📋 Final Recommendation: {'✅' if outputs['compliance_recommendation'] else '❌'}")
                
                return outputs
            else:
                print(f"❌ Compliance Agent failed with return code {result.returncode}")
                return {
                    "status": "error",
                    "error": result.stderr,
                    "return_code": result.returncode
                }
                
        except subprocess.TimeoutExpired:
            print("⏱️  Compliance Agent timed out (10 minutes)")
            return {"status": "timeout", "error": "Agent execution exceeded 10 minutes"}
        except Exception as e:
            print(f"❌ Compliance Agent error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def complete_orchestration(self, run_agents: bool = True) -> Dict[str, Any]:
        """Execute complete investment analysis pipeline with AutoGen
        
        Args:
            run_agents: If True, run agent scripts to generate fresh data.
                       If False, use existing JSON files.
        """
        start_time = datetime.now()
        
        print(f"\n🏢 COMPLETE GMR INVESTMENT ANALYSIS ORCHESTRATION")
        print(f"Company: {self.config['company_name']}")
        print(f"Stock: {self.config['stock_symbol']}")
        print("="*80)
        
        # Step 1: Collect data (either fresh or cached)
        if run_agents:
            print("\n🔄 Running agents to generate fresh data...")
            agent_data = await self.collect_agent_data()
        else:
            print("\n📁 Loading existing JSON files (cached data)...")
            agent_data = await self.load_existing_data()
        
        # Step 2: Create AutoGen agents with collected data
        autogen_agents = await self.create_autogen_agents(agent_data)
        
        # Step 3: Run AutoGen orchestration
        orchestration_results = await self.run_autogen_orchestration(autogen_agents)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Combine results
        results = {
            "stock_symbol": self.config["stock_symbol"],
            "company_name": self.config["company_name"],
            "analysis_date": self.config["analysis_date"],
            "orchestration_type": "AutoGen Multi-Agent Pipeline",
            "processing_time_seconds": processing_time,
            "agent_data_collection": agent_data,
            "autogen_orchestration": orchestration_results,
            "system_status": {
                "autogen_framework": "Available" if AUTOGEN_AVAILABLE else "Unavailable",
                "agents_executed": len([k for k, v in agent_data.items() if v.get("status") == "success"]),
                "data_collected": True
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Determine overall status (success includes both "success" and "cached" data)
        agent_statuses = [v.get("status") for v in agent_data.values() if isinstance(v, dict) and "status" in v]
        success_statuses = [s for s in agent_statuses if s in ["success", "cached"]]
        
        if len(success_statuses) == len(agent_statuses) and len(agent_statuses) > 0:
            results["overall_status"] = "success"
        elif len(success_statuses) > 0:
            results["overall_status"] = "partial_success"
        else:
            results["overall_status"] = "failure"
        
        return results
    

    
    def _print_summary(self, results: Dict[str, Any]):
        """Print orchestration summary"""
        print(f"\n{'='*80}")
        print(f"🎯 GMR INVESTMENT ANALYSIS ORCHESTRATION SUMMARY")
        print(f"{'='*80}")
        print(f"Company: {results['company_name']} ({results['stock_symbol']})")
        print(f"Processing Time: {results['processing_time_seconds']:.2f} seconds ({results['processing_time_seconds']/60:.1f} minutes)")
        print(f"Overall Status: {results['overall_status'].upper()}")
        print(f"Framework: {results['orchestration_type']}")
        
        print(f"\n🔧 SYSTEM STATUS:")
        system_status = results.get('system_status', {})
        for component, status in system_status.items():
            status_icon = "✅" if "Available" in str(status) or status is True else "⚠️" if "Unavailable" in str(status) else "📊"
            print(f"  {status_icon} {component.replace('_', ' ').title()}: {status}")
        
        print(f"\n🔄 AGENT DATA COLLECTION:")
        agent_data = results.get('agent_data_collection', {})
        for agent_name, agent_result in agent_data.items():
            if isinstance(agent_result, dict) and "status" in agent_result:
                status = agent_result.get("status", "unknown")
                status_icon = "✅" if status == "success" else "⏱️" if status == "timeout" else "❌"
                print(f"  {status_icon} {agent_name.replace('_', ' ').title()}: {status}")
        
        print(f"\n🤖 AUTOGEN ORCHESTRATION:")
        orchestration = results.get('autogen_orchestration', {})
        if orchestration:
            status_icon = "✅" if orchestration.get('status') == 'completed' else "⚠️" if orchestration.get('status') == 'skipped' else "❌"
            print(f"  {status_icon} Status: {orchestration.get('status', 'unknown')}")
            if orchestration.get('framework'):
                print(f"  🎯 Framework: {orchestration.get('framework')}")
            if orchestration.get('agents_participated'):
                print(f"  👥 Agents: {orchestration.get('agents_participated')} participated")
            if orchestration.get('total_messages'):
                print(f"  💬 Messages: {orchestration.get('total_messages')} exchanged")
            
            if orchestration.get('final_decision'):
                analysis = orchestration['final_decision']
                print(f"\n📋 COMPREHENSIVE ANALYSIS SUMMARY:")
                print(f"  📊 Type: {analysis.get('analysis_type', 'Unknown')}")
                print(f"  ⚖️  Compliance: {analysis.get('compliance_status', 'Unknown')}")
                print(f"  ⚠️  Risk Profile: {analysis.get('risk_profile', 'Unknown')}")
                print(f"  📝 Synthesis: {analysis.get('synthesis', 'No synthesis')[:150]}...")
        
        print(f"\n{'='*80}")
        
        if results["overall_status"] == "success":
            print("✅ ALL AGENTS COMPLETED SUCCESSFULLY")
        elif results["overall_status"] == "partial_success":
            print("⚠️  SOME AGENTS COMPLETED SUCCESSFULLY")
        else:
            print("❌ ORCHESTRATION FAILED")
        
        print(f"{'='*80}")
    
    def save_orchestration_report(self, results: Dict[str, Any], filename: str = None) -> str:
        """Save detailed orchestration report with all analysis and image paths"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gmr_autogen_orchestration_{timestamp}.json"
        
        output_path = self.base_dir / filename
        
        # Load complete data from JSON files for detailed report
        stock_report_file = self.frontend_dir / "stock_report.json"
        company_analysis_file = self.frontend_dir / "company_analysis_output.json"
        compliance_findings_file = self.frontend_dir / "compliance_findings.json"
        compliance_recommendation_file = self.frontend_dir / "compliance_recommendation.json"
        
        detailed_analysis = {}
        
        # Stock Analysis with image paths
        if stock_report_file.exists():
            with open(stock_report_file, 'r', encoding='utf-8') as f:
                stock_data = json.load(f)
                detailed_analysis["stock_analysis"] = {
                    "executive_summary": stock_data.get("executive_summary", {}),
                    "performance_metrics": {
                        "30_day_return": stock_data.get("returns_summary", {}).get("30_day_stock_return_percent"),
                        "volatility_annualized": stock_data.get("risk_metrics", {}).get("volatility_30d_annualized_percent"),
                        "sharpe_ratio": stock_data.get("risk_metrics", {}).get("sharpe_ratio")
                    },
                    "liquidity_metrics": stock_data.get("liquidity", {}),
                    "technical_indicators": stock_data.get("technical", {}),
                    "images": {
                        "panel_1": str(config.IMAGES_DIR / "panel_1.png") if (config.IMAGES_DIR / "panel_1.png").exists() else None,
                        "panel_2": str(config.IMAGES_DIR / "panel_2.png") if (config.IMAGES_DIR / "panel_2.png").exists() else None,
                        "panel_3": str(config.IMAGES_DIR / "panel_3.png") if (config.IMAGES_DIR / "panel_3.png").exists() else None,
                        "panel_4": str(config.IMAGES_DIR / "panel_4.png") if (config.IMAGES_DIR / "panel_4.png").exists() else None
                    },
                    "full_data_file": str(config.PUBLIC_DATA_DIR / "stock_report.json")
                }
        
        # Company Analysis with dashboard paths
        if company_analysis_file.exists():
            with open(company_analysis_file, 'r', encoding='utf-8') as f:
                company_data = json.load(f)
                
                # Collect all section analyses and their images
                sections_detail = []
                for section in company_data.get("sections", []):
                    section_info = {
                        "id": section.get("id"),
                        "name": section.get("name"),
                        "analysis": section.get("analysis"),
                        "dashboard": section.get("dashboard"),
                        "images": section.get("images", [])
                    }
                    # Add full image paths
                    if section_info["images"]:
                        section_info["image_paths"] = [f"frontend/images/{img}" for img in section_info["images"]]
                    sections_detail.append(section_info)
                
                detailed_analysis["company_analysis"] = {
                    "recommendation": company_data.get("recommendation"),
                    "key_strengths": company_data.get("key_strengths", []),
                    "key_challenges": company_data.get("key_challenges", []),
                    "sections": sections_detail,
                    "dashboards": {
                        "financial_overview": str(config.IMAGES_DIR / "dashboard_financial_overview.png") if (config.IMAGES_DIR / "dashboard_financial_overview.png").exists() else None,
                        "debt_liquidity": str(config.IMAGES_DIR / "dashboard_debt_liquidity.png") if (config.IMAGES_DIR / "dashboard_debt_liquidity.png").exists() else None,
                        "operations_capacity": str(config.IMAGES_DIR / "dashboard_operations_capacity.png") if (config.IMAGES_DIR / "dashboard_operations_capacity.png").exists() else None,
                        "projects_funding": str(config.IMAGES_DIR / "dashboard_projects_funding.png") if (config.IMAGES_DIR / "dashboard_projects_funding.png").exists() else None,
                        "valuation_risk": str(config.IMAGES_DIR / "dashboard_valuation_risk.png") if (config.IMAGES_DIR / "dashboard_valuation_risk.png").exists() else None
                    },
                    "full_data_file": str(config.PUBLIC_DATA_DIR / "company_analysis_output.json")
                }
        
        # Compliance Evaluation
        compliance_full = {}
        if compliance_findings_file.exists():
            with open(compliance_findings_file, 'r', encoding='utf-8') as f:
                compliance_full["findings"] = json.load(f)
        
        if compliance_recommendation_file.exists():
            with open(compliance_recommendation_file, 'r', encoding='utf-8') as f:
                compliance_full["recommendation"] = json.load(f)
        
        if compliance_full:
            detailed_analysis["compliance_evaluation"] = {
                "policy_rules": compliance_full.get("findings", {}).get("section_1_policy_rules"),
                "trading_classification": compliance_full.get("findings", {}).get("section_2_trading_classification"),
                "exceptional_events": compliance_full.get("findings", {}).get("section_3_exceptional_events"),
                "final_recommendation": compliance_full.get("recommendation", {}).get("section_4_final_recommendation"),
                "source_files": compliance_full.get("findings", {}).get("source_files", []),
                "full_data_files": {
                    "findings": str(config.PUBLIC_DATA_DIR / "compliance_findings.json"),
                    "recommendation": str(config.PUBLIC_DATA_DIR / "compliance_recommendation.json")
                }
            }
        
        # Build comprehensive report
        report = {
            "report_type": "GMR AutoGen Investment Analysis Orchestration - Detailed Report",
            "generated_at": datetime.now().isoformat(),
            "company_info": {
                "symbol": self.config["stock_symbol"],
                "name": self.config["company_name"],
                "analysis_date": self.config["analysis_date"]
            },
            "execution_mode": results.get("system_status", {}).get("execution_mode", "unknown"),
            "processing_time_seconds": results.get("processing_time_seconds"),
            "overall_status": results.get("overall_status"),
            
            # Detailed analysis from each agent
            "detailed_analysis": detailed_analysis,
            
            # AutoGen conversation results
            "autogen_orchestration": {
                "status": results.get("autogen_orchestration", {}).get("status"),
                "framework": results.get("autogen_orchestration", {}).get("framework"),
                "agents_participated": results.get("autogen_orchestration", {}).get("agents_participated"),
                "total_messages": results.get("autogen_orchestration", {}).get("total_messages"),
                "conversation_result": results.get("autogen_orchestration", {}).get("conversation_result"),
                "final_decision": results.get("autogen_orchestration", {}).get("final_decision")
            },
            
            # System status
            "system_status": results.get("system_status", {}),
            
            # Framework validation
            "framework_validation": {
                "autogen_framework": "Available" if AUTOGEN_AVAILABLE else "Unavailable",
                "agent_count": 3,
                "data_flow": "stock_analysis → investment_report → compliance → autogen_orchestration",
                "azure_ai_integration": True,
                "multi_agent_communication": AUTOGEN_AVAILABLE
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        return str(output_path)


async def main():
    """Main orchestration entry point"""
    
    try:
        # Initialize orchestrator
        orchestrator = GMRInvestmentOrchestrator()
        
        # User choice
        print("\n📋 SELECT MODE:")
        print("1. Run agents fresh (generates new data)")
        print("2. Use existing JSON files (cached data)")
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        run_agents = choice == "1"
        
        # Execute complete pipeline
        results = await orchestrator.complete_orchestration(run_agents=run_agents)
        
        # Save report
        report_file = orchestrator.save_orchestration_report(results)
        
        return orchestrator, results
        
    except Exception as e:
        print(f"❌ Orchestration failed: {e}")
        traceback.print_exc()
        return None, None


if __name__ == "__main__":
    # Run GMR investment analysis orchestration
    result = asyncio.run(main())
