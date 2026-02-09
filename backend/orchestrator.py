"""
GMR Investment Analysis Orchestrator
=====================================
Coordinates three specialized agents using AutoGen framework:
1. Stock Analyst Agent - Generates stock analysis with visualizations
2. Investment Report Agent - Creates comprehensive investment report
3. Compliance Agent - Evaluates PMS fair-valuation compliance

Uses AutoGen GroupChat for multi-agent orchestration.
"""

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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Validate required environment variables
REQUIRED_ENV_VARS = ["AZURE_OPENAI_ENDPOINT", "AZURE_MODEL_DEPLOYMENT"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Suppress warnings
warnings.filterwarnings("ignore", message="Resolved model mismatch")

# Force Entra ID authentication (no API key support)
if os.getenv("AZURE_OPENAI_API_KEY"):
    print("⚠️ AZURE_OPENAI_API_KEY detected but will be ignored - using Entra ID")
    os.environ.pop("AZURE_OPENAI_API_KEY", None)

# Azure authentication imports (required)
try:
    from azure.identity import DefaultAzureCredential  # type: ignore
    from azure.core.credentials import TokenCredential
    from autogen_ext.auth.azure import AzureTokenProvider  # type: ignore
    from autogen_ext.models.openai import AzureOpenAIChatCompletionClient  # type: ignore
    AZURE_AUTH_AVAILABLE = True
    print("✅ Azure authentication libraries loaded")
except ImportError as e:
    raise ImportError(
        "Required packages not installed. Install with:\n"
        "pip install azure-identity autogen-ext[azure]"
    ) from e

# AutoGen imports
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
    AUTOGEN_AVAILABLE = True
    print("✅ AutoGen framework loaded successfully")
except ImportError:
    AUTOGEN_AVAILABLE = False
    print("❌ AutoGen framework not available - falling back to subprocess mode")


class GMRInvestmentOrchestrator:
    """
    GMR Investment Analysis Orchestrator with AutoGen Framework
    Coordinates stock analysis, investment reporting, and compliance evaluation
    """
    
    def __init__(self):
        print("🚀 GMR INVESTMENT ANALYSIS ORCHESTRATOR - AUTOGEN FRAMEWORK")
        print("="*80)
        
        self.base_dir = Path(__file__).parent
        self.data_dir = self.base_dir / "data"
        self.agents_dir = self.base_dir / "agents"
        
        # For deployment, frontend data is served from blob storage
        # This is the local fallback path
        self.frontend_dir = self.base_dir / "data"
        
        # Agent file paths
        self.agent_scripts = {
            "stock_analyst": self.agents_dir / "stock_analyst.py",
            "investment_report": self.agents_dir / "investment_report_agent.py",
            "compliance": self.agents_dir / "compliance_agent.py"
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
        
        # Azure authentication setup (Entra ID only)
        self._setup_azure_auth()
        
        # Configure agents to use Azure chat client (no API key fallback)
        if not self.azure_chat_client:
            raise ValueError("Azure authentication failed - cannot proceed without valid credentials")
        
        # Get deployment name for llm_config
        azure_deployment = os.getenv("AZURE_MODEL_DEPLOYMENT", "gpt-4o-mini")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        # Configure for autogen with token provider (no model_client - not supported in old autogen)
        self.llm_config = {
            "config_list": [{
                "model": azure_deployment,
                "api_type": "azure",
                "api_version": "2024-10-01-preview",
                "azure_endpoint": azure_endpoint,
                "azure_deployment": azure_deployment,
                "azure_ad_token_provider": self.token_provider
            }],
            "temperature": 0.3,
            "timeout": 300
        }
        self.agent_llm_kwargs = {"llm_config": self.llm_config}
        
        print(f"🏢 Company: {self.config['company_name']}")
        print(f"📊 Stock: {self.config['stock_symbol']}")
        print(f"📅 Analysis Date: {self.config['analysis_date']}")
        print(f"🤖 AutoGen: Available")
        print(f"🔐 Azure Auth: Entra ID (DefaultAzureCredential)")
        print("="*80)
    
    def _setup_azure_auth(self):
        """Setup Azure DefaultAzureCredential authentication (Entra ID)"""
        print("\n🔐 Setting up Azure Entra ID authentication...")
        
        try:
            # Create DefaultAzureCredential (tries multiple auth methods in order)
            # Order: Environment → Managed Identity → Azure CLI → Azure PowerShell → VS Code
            credential = DefaultAzureCredential(
                exclude_shared_token_cache_credential=True,  # Skip cached tokens
                exclude_visual_studio_code_credential=False  # Allow VS Code auth
            )
            print("   ✅ DefaultAzureCredential created")
            
            # Create token provider for Cognitive Services scope
            try:
                self.token_provider = AzureTokenProvider(
                    credential=credential,
                    scopes=["https://cognitiveservices.azure.com/.default"]
                )
            except TypeError:
                # Fallback for older autogen-ext versions
                self.token_provider = AzureTokenProvider(
                    credential,
                    "https://cognitiveservices.azure.com/.default"
                )
            print("   ✅ Azure token provider configured")
            
            # Get Azure OpenAI configuration from environment
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            azure_deployment = os.getenv("AZURE_MODEL_DEPLOYMENT")
            
            if not azure_endpoint or not azure_deployment:
                raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_MODEL_DEPLOYMENT must be set")
            
            # Create Azure OpenAI chat client with token authentication
            self.azure_chat_client = AzureOpenAIChatCompletionClient(
                azure_endpoint=azure_endpoint,
                model=azure_deployment,
                azure_deployment=azure_deployment,
                azure_ad_token_provider=self.token_provider,
                api_version="2024-10-01-preview"
            )
            print(f"   ✅ Azure OpenAI client configured")
            print(f"      Endpoint: {azure_endpoint}")
            print(f"      Deployment: {azure_deployment}")
            print(f"      Auth: Entra ID (DefaultAzureCredential)")
            
        except Exception as e:
            print(f"❌ Azure authentication failed: {e}")
            print("\n💡 TROUBLESHOOTING:")
            print("   1. Run 'az login' to authenticate with Azure CLI")
            print("   2. Ensure you have access to the Azure OpenAI resource")
            print("   3. Check that the endpoint and deployment name are correct")
            print("   4. Verify the resource is in the same tenant as your login")
            raise
    
    def _verify_agent_files(self):
        """Verify all agent Python files exist"""
        missing_files = []
        for agent_name, agent_path in self.agent_scripts.items():
            if not agent_path.exists():
                missing_files.append(agent_name)
        
        if missing_files:
            print(f"⚠️ Missing agent files: {', '.join(missing_files)} - will use cached data mode")
    
    async def load_existing_data(self) -> Dict[str, Any]:
        """Load existing JSON files without running agents"""
        agent_data = {}
        
        # Load stock report
        stock_report_file = self.data_dir / "stock_report.json"
        if stock_report_file.exists():
            with open(stock_report_file, 'r', encoding='utf-8') as f:
                agent_data["stock_report_data"] = json.load(f)
            agent_data["stock_analyst"] = {"status": "cached"}
        else:
            agent_data["stock_analyst"] = {"status": "missing"}
        
        # Load company analysis
        company_analysis_file = self.data_dir / "company_analysis_output.json"
        if company_analysis_file.exists():
            with open(company_analysis_file, 'r', encoding='utf-8') as f:
                agent_data["company_analysis_data"] = json.load(f)
            agent_data["investment_report"] = {"status": "cached"}
        else:
            agent_data["investment_report"] = {"status": "missing"}
        
        # Load compliance recommendation
        compliance_findings_file = self.data_dir / "compliance_findings.json"
        compliance_recommendation_file = self.data_dir / "compliance_recommendation.json"
        
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
    
    async def create_autogen_agents(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create AutoGen agents with collected data"""
        
        if not AUTOGEN_AVAILABLE:
            print("\n⚠️  AutoGen not available, skipping agent creation")
            return {}
        
        print("\n🤖 STEP 2: Creating AutoGen Agents...")
        print("="*80)
        
        # Load complete JSON files directly (fresh data from agents)
        stock_report_file = self.data_dir / "stock_report.json"
        company_analysis_file = self.data_dir / "company_analysis_output.json"
        compliance_recommendation_file = self.data_dir / "compliance_recommendation.json"
        
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
            system_message=f"""You are a Senior Stock Analysis Specialist for {self.config['company_name']} (GMRAIRPORT.NS).

YOUR ROLE: Provide technical analysis STATUS and key insights without generating files or images.

Available data summary:
{stock_metrics}

WHEN REQUESTED, PROVIDE ANALYSIS STATUS IN THIS FORMAT:

🔍 STOCK ANALYSIS STATUS:
• Data Source: Available/Cached stock report data
• Analysis Type: Technical analysis with key metrics
• Status: COMPLETED

📊 KEY INSIGHTS:
• 30-Day Return: [Extract from data if available]
• Volatility: [Extract from data if available] 
• Risk Level: [High/Moderate/Low based on volatility]
• Trading Volume: [Extract from data if available]
• Overall Verdict: [Strong/Moderate/Weak with brief reasoning]

NOTE: Analysis is based on available cached data. No new files or charts generated.
""",
        **self.agent_llm_kwargs,
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
            system_message=f"""You are a Senior Investment Analysis Specialist for {self.config['company_name']} (GMRAIRPORT.NS).

YOUR ROLE: Provide investment analysis STATUS and key financial insights without generating files or images.

Available data summary:
{company_metrics}

WHEN REQUESTED, PROVIDE ANALYSIS STATUS IN THIS FORMAT:

🏦 INVESTMENT ANALYSIS STATUS:
• Data Source: Available/Cached company analysis data
• Analysis Type: Fundamental analysis with financial metrics
• Status: COMPLETED

💰 KEY FINANCIAL INSIGHTS:
• Recommendation: [Extract from available data]
• Revenue/EBITDA: [Key financial figures if available]
• Debt Position: [Key debt metrics if available]
• Operational Performance: [Key operational metrics if available]
• Valuation: [Key valuation metrics if available]

✅ KEY STRENGTHS:
[List key strengths from available data]

⚠️ KEY CHALLENGES:
[List key challenges from available data]

NOTE: Analysis is based on available cached data. No new files or reports generated.
""",
        **self.agent_llm_kwargs,
    )
        
        # Read compliance findings and recommendation data
        compliance_findings_file = self.data_dir / "compliance_findings.json"
        
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
            system_message=f"""You are a Senior Compliance Officer for PMS (Portfolio Management Services) evaluation of {self.config['company_name']} (GMRAIRPORT.NS).

YOUR ROLE: Provide compliance evaluation STATUS and key decisions without generating files or reports.

Available data summary:
{compliance_full_data}

WHEN REQUESTED, PROVIDE COMPLIANCE STATUS IN THIS FORMAT:

⚖️ COMPLIANCE EVALUATION STATUS:
• Data Source: Available/Cached compliance findings and recommendations
• Evaluation Type: PMS compliance assessment
• Status: COMPLETED

🔍 COMPLIANCE FINDINGS:
• Overall Decision: [Extract final recommendation if available]
• Risk Level: [Extract risk assessment if available]
• Trading Status: [Extract trading approval status if available]
• Key Concerns: [List main compliance issues if available]
• Mitigation Required: [List required actions if available]

✅ FINAL RECOMMENDATION:
[Extract the final compliance decision and reasoning from available data]

NOTE: Evaluation is based on available cached data. No new compliance reports generated.
""",
        **self.agent_llm_kwargs,
    )
        
        # User Proxy for orchestration
        user_proxy = UserProxyAgent(
            name="Analysis_Pipeline_Manager",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config=False
        )
        
        agents = {
            "stock": stock_agent,
            "investment": report_agent,
            "compliance": compliance_agent,
            "user_proxy": user_proxy
        }
        
        print(f"✅ Created {len(agents)-1} AutoGen agents with GMR analysis data")
        return agents
    
    async def run_autogen_orchestration(self, agents: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """Run AutoGen multi-agent orchestration using GroupChatManager"""
        
        if not AUTOGEN_AVAILABLE or not agents:
            return {"status": "skipped", "reason": "AutoGen not available"}
        
        print("\n🤖 Starting AutoGen Multi-Agent Orchestration...")
        print("="*80)
        
        try:
            # CREATE SINGLE GROUPCHAT WITH ALL AGENTS
            print("\n🤖 Creating AutoGen Agents...")
            
            # Create single GroupChat with all analyst agents
            group_chat = GroupChat(
                agents=[
                    agents["stock"],
                    agents["investment"],
                    agents["compliance"]
                ],
                messages=[],
                max_round=10,
                speaker_selection_method="auto",
                allow_repeat_speaker=False
            )
            print("   ✅ Stock_Analyst Agent created")
            print("   ✅ Investment_Analyst Agent created")
            print("   ✅ Compliance_Evaluator Agent created")
            print("   ✅ GroupChat Manager created")
            
            # Create single GroupChatManager with llm_config
            manager = GroupChatManager(
                groupchat=group_chat,
                llm_config=self.llm_config,  # Use llm_config for autogen
                system_message="""You are coordinating a comprehensive investment analysis meeting.

SPEAKING ORDER (STRICT):
1. Stock_Analyst speaks ONCE - complete technical analysis
2. Investment_Analyst speaks ONCE - complete fundamental analysis  
3. Compliance_Evaluator speaks ONCE - complete compliance assessment
4. After all three agents speak, END the conversation

CRITICAL RULES:
- Each agent speaks ONLY ONCE
- Follow the strict order: Stock -> Investment -> Compliance
- Terminate after Compliance_Evaluator provides final verdict"""
            )
            
            # INITIATE GROUP CHAT
            print("\n💬 Starting Agent Conversation...")
            print("-" * 80)
            
            initial_message = """Please provide comprehensive investment analysis for GMR Airports Ltd.

ANALYSIS SEQUENCE:
1. Stock_Analyst: Complete technical analysis (all 5 sections)
2. Investment_Analyst: Complete fundamental analysis (all 8 sections)
3. Compliance_Evaluator: Complete compliance assessment (all 4 sections)

Stock_Analyst: Please begin with your complete technical analysis."""

            # Termination function
            def is_termination_msg(msg):
                """Terminate after Compliance_Evaluator provides final verdict"""
                try:
                    content = msg.get("content", "")
                    speaker = msg.get("name", "")
                    
                    if speaker == "Compliance_Evaluator" and "FINAL COMPLIANCE VERDICT" in content:
                        print("\n✅ All 3 agents completed - terminating conversation")
                        return True
                    
                    if "SECTION 4: FINAL COMPLIANCE VERDICT" in content:
                        print("\n✅ Compliance verdict received - terminating conversation")
                        return True
                    
                except Exception as e:
                    print(f"⚠️ Termination check error: {e}")
                return False
            
            # Initiate the group chat
            try:
                chat_result = agents["user_proxy"].initiate_chat(
                    manager,
                    message=initial_message,
                    max_turns=3,
                    is_termination_msg=is_termination_msg
                )
            except Exception as chat_error:
                print(f"\n⚠️ GroupChat error encountered: {chat_error}")
                print("Attempting to extract any completed responses...")
                chat_result = None
            
            # Check if we have any messages
            if not group_chat.messages:
                print("\n⚠️ No messages generated - possible API error")
                return {
                    "status": "error",
                    "error": "No messages generated in GroupChat",
                    "framework": "AutoGen GroupChat"
                }
            
            print("\n\n" + "="*80)
            print("✅ GroupChat conversation completed!")
            print("="*80)
            print(f"💬 Total messages: {len(group_chat.messages)}")
            print(f"👥 Agents participated: {len([a for a in group_chat.agents if a.name != 'Analysis_Pipeline_Manager'])}")
            
            return {
                "status": "completed",
                "framework": "AutoGen GroupChat",
                "conversation_result": f"GroupChat conversation completed with {len(group_chat.messages)} messages",
                "total_messages": len(group_chat.messages),
                "agents_participated": 3,
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
        
        for msg in messages:
            if hasattr(msg, 'content') and msg.content:
                content = msg.content
                
                import re
                compliance_matches = re.findall(r'(?:APPROVED|COMPLIANT|CONDITIONAL|REVIEW REQUIRED|REJECTED|NON-COMPLIANT)', content.upper())
                compliance_statuses.extend(compliance_matches)
                
                risk_matches = re.findall(r'(?:HIGH RISK|MODERATE RISK|LOW RISK)', content.upper())
                risk_profiles.extend(risk_matches)
        
        compliance = compliance_statuses[-1] if compliance_statuses else "UNKNOWN"
        risk_profile = risk_profiles[-1] if risk_profiles else "MODERATE RISK"
        
        return {
            "analysis_type": "Comprehensive Multi-Agent Analysis",
            "compliance_status": compliance,
            "risk_profile": risk_profile,
            "conversation_length": len(messages),
            "analysis_source": "AutoGen GroupChat"
        }
    
    async def complete_orchestration(self, run_agents: bool = False) -> Dict[str, Any]:
        """Execute complete investment analysis pipeline with AutoGen
        
        Args:
            run_agents: If True, run agent scripts to generate fresh data.
                       If False (default for deployment), use existing JSON files.
        """
        start_time = datetime.now()
        
        print(f"\n🏢 COMPLETE GMR INVESTMENT ANALYSIS ORCHESTRATION")
        print(f"Company: {self.config['company_name']}")
        print(f"Stock: {self.config['stock_symbol']}")
        print("="*80)
        
        # Load existing data (cached) - default for deployment
        print("\n📁 Loading existing JSON files (cached data)...")
        agent_data = await self.load_existing_data()
        
        # Create AutoGen agents with collected data
        autogen_agents = await self.create_autogen_agents(agent_data)
        
        # Run AutoGen orchestration
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
                "agents_executed": len([k for k, v in agent_data.items() if v.get("status") in ["success", "cached"]]),
                "data_collected": True
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Determine overall status
        agent_statuses = [v.get("status") for v in agent_data.values() if isinstance(v, dict) and "status" in v]
        success_statuses = [s for s in agent_statuses if s in ["success", "cached"]]
        
        if len(success_statuses) == len(agent_statuses) and len(agent_statuses) > 0:
            results["overall_status"] = "success"
        elif len(success_statuses) > 0:
            results["overall_status"] = "partial_success"
        else:
            results["overall_status"] = "failure"
        
        return results
    
    def save_orchestration_report(self, results: Dict[str, Any], filename: str = None) -> str:
        """Save detailed orchestration report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gmr_autogen_orchestration_{timestamp}.json"
        
        output_path = self.base_dir / filename
        
        report = {
            "report_type": "GMR AutoGen Investment Analysis Orchestration",
            "generated_at": datetime.now().isoformat(),
            "company_info": {
                "symbol": self.config["stock_symbol"],
                "name": self.config["company_name"],
                "analysis_date": self.config["analysis_date"]
            },
            "processing_time_seconds": results.get("processing_time_seconds"),
            "overall_status": results.get("overall_status"),
            "autogen_orchestration": results.get("autogen_orchestration", {}),
            "system_status": results.get("system_status", {}),
            "framework_validation": {
                "autogen_framework": "Available" if AUTOGEN_AVAILABLE else "Unavailable",
                "agent_count": 3,
                "azure_ai_integration": True
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
        
        # Execute complete pipeline with cached data (deployment mode)
        results = await orchestrator.complete_orchestration(run_agents=False)
        
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
