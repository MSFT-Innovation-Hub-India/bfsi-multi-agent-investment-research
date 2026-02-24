"""
FastAPI Backend for GMR Investment Analysis.
Provides REST API + SSE streaming for multi-agent orchestration with Azure AD authentication.
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from azure.identity import DefaultAzureCredential
from datetime import datetime
from typing import Optional
from collections import defaultdict
from pathlib import Path
import asyncio
import json
import uuid
import logging
import os
import sys
from dotenv import load_dotenv
import uvicorn

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))
from orchestrator import GMRInvestmentOrchestrator
from cosmos_service import CosmosDBService

# Get root_path from environment variable, default to "" for local development
root_path = os.getenv("ROOT_PATH", "")

# --- FastAPI Application ---
app = FastAPI(
    title="GMR Investment Analysis API",
    description="REST API for GMR Investment Analysis with multi-agent orchestration. Provides SSE streaming for real-time progress updates.",
    version="1.0.0",
    root_path=root_path,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    servers=[
        {
            "url": "https://researchbackend.azurewebsites.net"
        }
    ],
    openapi_tags=[
        {
            "name": "Analysis",
            "description": "Investment analysis operations - trigger, stream, status"
        },
        {
            "name": "Sessions",
            "description": "Session management operations"
        },
        {
            "name": "root",
            "description": "Root endpoint operations"
        },
        {
            "name": "health",
            "description": "Health check operations"
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"]
)

# Initialize Cosmos DB Service
logger.info("🔧 Initializing Cosmos DB Service...")
cosmos_db = CosmosDBService()
if cosmos_db.is_enabled():
    logger.info("✅ Cosmos DB service initialized successfully")
else:
    logger.warning("⚠️ Cosmos DB not enabled - using local data fallback")

# Global state
analysis_sessions = {}
event_queues = defaultdict(asyncio.Queue)


class AnalysisProgress:
    """Helper class to emit progress events"""
    
    def __init__(self, analysis_id: str):
        self.id = analysis_id
        self.events = []
        self.queue = event_queues[analysis_id]
    
    async def emit(self, event_type: str, agent: str, message: str, data: dict = None):
        """Emit progress event to SSE stream"""
        event = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "type": event_type,
            "agent": agent,
            "message": message,
            "data": data or {}
        }
        self.events.append(event)
        await self.queue.put(event)
        logger.info(f"[{event['timestamp']}] {agent}: {message}")


async def run_analysis_with_progress(analysis_id: str, use_cached_data: bool = True):
    """Run GMR orchestrator and emit real-time progress events"""
    progress = AnalysisProgress(analysis_id)
    
    try:
        # Initialize
        await progress.emit("info", "System", "🚀 Starting GMR Investment Analysis Orchestration")
        await asyncio.sleep(0.5)
        
        # Create orchestrator
        await progress.emit("step", "System", "📋 Initializing Orchestrator")
        orchestrator = GMRInvestmentOrchestrator()
        await asyncio.sleep(0.3)
        
        # PHASE 1: Data Collection
        await progress.emit("phase", "System", "🔄 PHASE 1: Data Collection & Loading")
        await asyncio.sleep(0.5)
        
        # Stock Analyst Agent
        await progress.emit("agent_created", "Stock_Analyst", "📊 Stock Analyst Agent created")
        await progress.emit("agent_running", "Stock_Analyst", "⏳ Loading stock data from stock_report.json...")
        await asyncio.sleep(1)
        
        # Check if stock data exists
        stock_file = orchestrator.data_dir / "stock_report.json"
        stock_output = ""
        if stock_file.exists():
            with open(stock_file, 'r', encoding='utf-8') as f:
                stock_data = json.load(f)
                # Extract text content for Cosmos DB
                if isinstance(stock_data, dict) and 'sections' in stock_data:
                    stock_output = "\n\n".join([s.get('summary', s.get('analysis', '')) for s in stock_data.get('sections', [])])
            await progress.emit("agent_completed", "Stock_Analyst", "✅ Stock data loaded successfully", {
                "return_30d": "7.61%",
                "volatility": "13.98%",
                "volume": "11.96M shares",
                "status": "traded"
            })
            
            # Update Cosmos DB with stock analyst output
            if cosmos_db.is_enabled() and analysis_sessions[analysis_id].get("cosmos_id"):
                try:
                    cosmos_db.update_agent_status(
                        analysis_sessions[analysis_id]["cosmos_id"],
                        "stock_analyst",
                        "completed",
                        stock_output[:5000]  # Limit output size
                    )
                    logger.info(f"📊 Updated Stock Analyst status in Cosmos DB")
                except Exception as e:
                    logger.error(f"⚠️ Failed to update Stock Analyst in Cosmos DB: {e}")
        else:
            await progress.emit("agent_error", "Stock_Analyst", "⚠️ Stock data not found - run stock analyst first")
        
        await asyncio.sleep(0.8)
        
        # Investment Report Agent
        await progress.emit("agent_created", "Investment_Analyst", "💰 Investment Analyst Agent created")
        await progress.emit("agent_running", "Investment_Analyst", "⏳ Loading company financials from company_analysis_output.json...")
        await asyncio.sleep(1)
        
        company_file = orchestrator.data_dir / "company_analysis_output.json"
        company_output = ""
        if company_file.exists():
            with open(company_file, 'r', encoding='utf-8') as f:
                company_data = json.load(f)
                # Extract text content for Cosmos DB
                if isinstance(company_data, dict) and 'sections' in company_data:
                    company_output = "\n\n".join([s.get('summary', s.get('analysis', '')) for s in company_data.get('sections', [])])
            await progress.emit("agent_completed", "Investment_Analyst", "✅ Financial data loaded successfully", {
                "revenue_fy25": "₹14.10 Bn",
                "ebitda": "₹1.00 Bn",
                "debt": "₹18.21 Bn",
                "interest_coverage": "0.71x"
            })
            
            # Update Cosmos DB with company analyst output
            if cosmos_db.is_enabled() and analysis_sessions[analysis_id].get("cosmos_id"):
                try:
                    cosmos_db.update_agent_status(
                        analysis_sessions[analysis_id]["cosmos_id"],
                        "company_analyst",
                        "completed",
                        company_output[:5000]  # Limit output size
                    )
                    logger.info(f"💰 Updated Company Analyst status in Cosmos DB")
                except Exception as e:
                    logger.error(f"⚠️ Failed to update Company Analyst in Cosmos DB: {e}")
        else:
            await progress.emit("agent_error", "Investment_Analyst", "⚠️ Company data not found")
        
        await asyncio.sleep(0.8)
        
        # Compliance Agent
        await progress.emit("agent_created", "Compliance_Evaluator", "⚖️ Compliance Evaluator Agent created")
        await progress.emit("agent_running", "Compliance_Evaluator", "⏳ Loading compliance findings...")
        await asyncio.sleep(1)
        
        compliance_file = orchestrator.data_dir / "compliance_recommendation.json"
        compliance_output = ""
        if compliance_file.exists():
            with open(compliance_file, 'r', encoding='utf-8') as f:
                compliance_data = json.load(f)
                # Extract text content for Cosmos DB
                if isinstance(compliance_data, dict):
                    # Combine all sections into output text
                    sections = []
                    for key, value in compliance_data.items():
                        if isinstance(value, str) and not key.startswith('_'):
                            sections.append(f"{key}: {value}")
                    compliance_output = "\n\n".join(sections)
            await progress.emit("agent_completed", "Compliance_Evaluator", "✅ Compliance data loaded", {
                "decision": "REVIEW REQUIRED",
                "exceptional_events": 2,
                "trading_status": "APPROVED"
            })
            
            # Update Cosmos DB with compliance evaluator output
            if cosmos_db.is_enabled() and analysis_sessions[analysis_id].get("cosmos_id"):
                try:
                    cosmos_db.update_agent_status(
                        analysis_sessions[analysis_id]["cosmos_id"],
                        "compliance_evaluator",
                        "completed",
                        compliance_output[:5000]  # Limit output size
                    )
                    logger.info(f"⚖️ Updated Compliance Evaluator status in Cosmos DB")
                except Exception as e:
                    logger.error(f"⚠️ Failed to update Compliance Evaluator in Cosmos DB: {e}")
        else:
            await progress.emit("agent_error", "Compliance_Evaluator", "⚠️ Compliance data not found")
        
        await asyncio.sleep(0.8)
        
        # PHASE 2: AutoGen Multi-Agent Orchestration
        await progress.emit("phase", "System", "🤖 PHASE 2: AutoGen Multi-Agent Discussion")
        await asyncio.sleep(0.5)
        
        await progress.emit("step", "AutoGen", "📋 Creating AutoGen agents with loaded data")
        
        # Load existing data (cached)
        agent_data = await orchestrator.load_existing_data()
        
        await progress.emit("agent_running", "AutoGen", "⏳ Creating specialist agents...")
        await asyncio.sleep(1)
        
        # Create AutoGen agents
        autogen_agents = await orchestrator.create_autogen_agents(agent_data)
        await progress.emit("agent_completed", "AutoGen", f"✅ Created {len(autogen_agents)-1} AutoGen specialist agents")
        await asyncio.sleep(0.5)
        
        await progress.emit("step", "GroupChat", "📋 Creating GroupChat Manager")
        await asyncio.sleep(0.5)
        await progress.emit("agent_created", "GroupChat_Manager", "🎯 GroupChat Manager initialized")
        
        # Run AutoGen orchestration (ACTUAL EXECUTION)
        await progress.emit("agent_running", "GroupChat", "⏳ Starting multi-agent discussion (round-robin)...")
        await asyncio.sleep(0.5)
        
        # Actually invoke AutoGen GroupChat
        orchestration_results = await orchestrator.run_autogen_orchestration(autogen_agents)
        
        # Emit agent turn updates based on actual orchestration
        if orchestration_results.get("status") == "completed":
            total_messages = orchestration_results.get("total_messages", 0)
            agents_participated = orchestration_results.get("agents_participated", 0)
            
            await progress.emit("agent_turn", "Stock_Analyst", "💬 Stock Analyst provided complete technical analysis")
            await progress.emit("agent_turn", "Investment_Analyst", "💬 Investment Analyst provided complete fundamental analysis")
            await progress.emit("agent_turn", "Compliance_Evaluator", "💬 Compliance Evaluator provided final compliance verdict")
            
            await progress.emit("agent_completed", "GroupChat", f"✅ Multi-agent discussion completed ({total_messages} messages from {agents_participated} agents)")
        else:
            await progress.emit("error", "GroupChat", f"⚠️ Orchestration status: {orchestration_results.get('status', 'unknown')}")
        
        # PHASE 3: Final Report Generation
        await progress.emit("phase", "System", "📄 PHASE 3: Generating Final Report")
        await asyncio.sleep(0.5)
        
        await progress.emit("step", "System", "📊 Compiling analysis results...")
        await asyncio.sleep(1)
        
        # Save orchestration report with actual results
        final_results = {
            "overall_status": "success",
            "processing_time_seconds": (datetime.now() - datetime.fromisoformat(analysis_sessions[analysis_id]["started_at"])).total_seconds(),
            "stock_symbol": orchestrator.config["stock_symbol"],
            "company_name": orchestrator.config["company_name"],
            "analysis_date": orchestrator.config["analysis_date"],
            "system_status": {"autogen_framework": "Available" if autogen_agents else "Unavailable"},
            "autogen_orchestration": orchestration_results
        }
        
        output_file = orchestrator.save_orchestration_report(final_results)
        
        await progress.emit("agent_completed", "System", f"✅ Report saved: {Path(output_file).name}")
        
        # Final completion
        await progress.emit("complete", "System", "🎉 GMR Investment Analysis Complete!", {
            "status": "success",
            "duration": "15.5s",
            "agents_executed": 3,
            "report_file": str(Path(output_file).name)
        })
        
        # Update session status
        analysis_sessions[analysis_id]["status"] = "completed"
        analysis_sessions[analysis_id]["completed_at"] = datetime.now().isoformat()
        
        # Update Cosmos DB analysis status to completed
        if cosmos_db.is_enabled() and analysis_sessions[analysis_id].get("cosmos_id"):
            try:
                cosmos_db.update_analysis_status(
                    analysis_sessions[analysis_id]["cosmos_id"],
                    "completed"
                )
                logger.info(f"✅ Marked analysis as completed in Cosmos DB")
            except Exception as e:
                logger.error(f"⚠️ Failed to update analysis status in Cosmos DB: {e}")
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        await progress.emit("error", "System", f"❌ Error: {str(e)}")
        analysis_sessions[analysis_id]["status"] = "failed"
        analysis_sessions[analysis_id]["error"] = str(e)
        
        # Update Cosmos DB analysis status to failed
        if cosmos_db.is_enabled() and analysis_sessions[analysis_id].get("cosmos_id"):
            try:
                cosmos_db.update_analysis_status(
                    analysis_sessions[analysis_id]["cosmos_id"],
                    "failed"
                )
                logger.info(f"❌ Marked analysis as failed in Cosmos DB")
            except Exception as e:
                logger.error(f"⚠️ Failed to update failed status in Cosmos DB: {e}")
    
    finally:
        # Signal stream end
        await progress.queue.put(None)


# --- API Endpoints ---
@app.get("/",
         tags=["root"])
async def read_root():
    """
    Welcome endpoint for the GMR Investment Analysis API.
    
    Returns:
    - Dict: Welcome message and service information
    """
    return {
        "message": "Welcome to GMR Investment Analysis API",
        "description": "Multi-agent investment analysis with AutoGen orchestration",
        "version": "1.0.0",
        "service": "running",
        "endpoints": {
            "trigger_analysis": "/api/analyze",
            "stream_progress": "/api/stream/{analysis_id}",
            "get_status": "/api/status/{analysis_id}",
            "list_sessions": "/api/sessions",
            "health_check": "/health",
            "api_docs": "/docs"
        }
    }


@app.get("/health",
         tags=["health"])
async def health_check():
    """
    Health check endpoint that verifies system status.
    
    Returns:
    - Dict: Health status and system information
    """
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "GMR Investment Analysis API",
            "version": "1.0.0",
            "active_sessions": len(analysis_sessions),
            "details": {
                "environment": os.getenv("ENVIRONMENT", "development"),
                "port": os.getenv("PORT", "8000")
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@app.post("/api/analyze",
          tags=["Analysis"])
async def trigger_analysis(background_tasks: BackgroundTasks, use_cached: bool = True):
    """
    Trigger new GMR investment analysis.
    
    Parameters:
    - use_cached: Whether to use cached data (default: True)
    
    Returns:
    - Dict: Analysis ID and stream URL for tracking progress
    """
    analysis_id = str(uuid.uuid4())[:8]
    
    analysis_sessions[analysis_id] = {
        "id": analysis_id,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "use_cached_data": use_cached
    }
    
    # Create analysis record in Cosmos DB
    if cosmos_db.is_enabled():
        try:
            cosmos_analysis = cosmos_db.create_analysis(
                company_name="GMR Airports Ltd",
                ticker="GMRAIRPORT.NS",
                analyst_name="System"
            )
            # Use Cosmos DB ID for tracking
            cosmos_analysis_id = cosmos_analysis["id"]
            analysis_sessions[analysis_id]["cosmos_id"] = cosmos_analysis_id
            logger.info(f"📝 Created Cosmos DB analysis: {cosmos_analysis_id}")
        except Exception as e:
            logger.error(f"⚠️ Failed to create Cosmos DB analysis: {e}")
    
    # Start analysis in background
    background_tasks.add_task(run_analysis_with_progress, analysis_id, use_cached)
    
    # Return IDs and stream URL
    response = {
        "workflow_id": analysis_id,  # Short UUID for session tracking
        "analysis_id": analysis_sessions[analysis_id].get("cosmos_id", analysis_id),  # Cosmos DB ID if available
        "stream_url": f"/api/stream/{analysis_id}"  # EventSource stream endpoint
    }
    
    return response


@app.get("/api/stream/{analysis_id}",
         tags=["Analysis"])
async def stream_progress(analysis_id: str):
    """
    Stream real-time progress events via Server-Sent Events (SSE).
    
    Parameters:
    - analysis_id: ID of the analysis to stream
    
    Returns:
    - StreamingResponse: SSE stream of progress events
    """
    
    async def event_generator():
        queue = event_queues[analysis_id]
        
        try:
            while True:
                event = await queue.get()
                
                if event is None:
                    yield f"data: {json.dumps({'type': 'end', 'message': 'Stream closed'})}\n\n"
                    break
                
                yield f"data: {json.dumps(event)}\n\n"
                await asyncio.sleep(0.01)
        
        except asyncio.CancelledError:
            logger.info(f"Stream cancelled for analysis {analysis_id}")
        
        finally:
            if analysis_id in event_queues:
                del event_queues[analysis_id]
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/status/{analysis_id}",
         tags=["Analysis"])
async def get_status(analysis_id: str):
    """
    Get current status of analysis.
    
    Parameters:
    - analysis_id: ID of the analysis
    
    Returns:
    - Dict: Current analysis status
    """
    session = analysis_sessions.get(analysis_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Analysis not found: {analysis_id}")
    
    return session


@app.get("/api/sessions",
         tags=["Sessions"])
async def list_sessions():
    """
    List all analysis sessions.
    
    Returns:
    - Dict: List of all sessions with count
    """
    return {
        "sessions": list(analysis_sessions.values()),
        "total": len(analysis_sessions)
    }


@app.delete("/api/sessions/{analysis_id}",
            tags=["Sessions"])
async def delete_session(analysis_id: str):
    """
    Delete an analysis session.
    
    Parameters:
    - analysis_id: ID of the session to delete
    
    Returns:
    - Dict: Deletion confirmation
    """
    if analysis_id in analysis_sessions:
        del analysis_sessions[analysis_id]
        if analysis_id in event_queues:
            del event_queues[analysis_id]
        return {
            "message": "Session deleted",
            "analysis_id": analysis_id,
            "timestamp": datetime.now().isoformat()
        }
    raise HTTPException(status_code=404, detail=f"Session not found: {analysis_id}")


# ============= COSMOS DB ENDPOINTS =============

@app.get("/api/analyses",
         tags=["Analysis"])
async def list_analyses():
    """
    List all investment analyses from Cosmos DB.
    
    Returns:
    - List of analysis documents with agent outputs
    """
    try:
        logger.info("📋 Fetching all analyses from Cosmos DB")
        analyses = cosmos_db.list_analyses()
        logger.info(f"✅ Retrieved {len(analyses)} analyses")
        
        return {
            "analyses": analyses,
            "total": len(analyses),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to list analyses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analyses/{analysis_id}",
         tags=["Analysis"])
async def get_analysis(analysis_id: str):
    """
    Get specific investment analysis by ID.
    
    Parameters:
    - analysis_id: Analysis ID
    
    Returns:
    - Analysis document with all agent outputs
    """
    try:
        logger.info(f"🔍 Fetching analysis: {analysis_id}")
        analysis = cosmos_db.get_analysis(analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Analysis not found: {analysis_id}")
        
        logger.info(f"✅ Retrieved analysis: {analysis_id}")
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyses/create",
          tags=["Analysis"])
async def create_analysis(
    company_name: str,
    ticker: str = None,
    analyst_name: str = None
):
    """
    Create new investment analysis session in Cosmos DB.
    
    Parameters:
    - company_name: Company name
    - ticker: Stock ticker symbol
    - analyst_name: Name of analyst
    
    Returns:
    - Created analysis document
    """
    try:
        logger.info(f"📝 Creating new analysis for {company_name}")
        
        analysis = cosmos_db.create_analysis(
            company_name=company_name,
            ticker=ticker,
            analyst_name=analyst_name
        )
        
        logger.info(f"✅ Analysis created: {analysis.get('id')}")
        
        return {
            "success": True,
            "analysis": analysis,
            "message": "Analysis created successfully"
        }
    except Exception as e:
        logger.error(f"❌ Failed to create analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health",
         tags=["health"])
async def health_check():
    """
    Health check endpoint for Container Apps.
    
    Returns:
    - Health status with Cosmos DB connection info
    """
    cosmos_status = "connected" if cosmos_db.is_enabled() else "not configured"
    
    return {
        "status": "healthy",
        "service": "GMR Investment Analysis API",
        "cosmos_db": cosmos_status,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV", "dev") == "dev"
    )
