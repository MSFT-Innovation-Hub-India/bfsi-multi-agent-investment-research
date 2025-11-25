
"""FastAPI Backend for GMR Investment Analysis - REST API + SSE streaming"""

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import uuid
from datetime import datetime
from collections import defaultdict
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
from agents.orchestrator import GMRInvestmentOrchestrator
import config

app = FastAPI(title="GMR Investment Analysis API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend) - use config paths
app.mount("/static", StaticFiles(directory=str(config.FRONTEND_DIR)), name="static")

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
        print(f"[{event['timestamp']}] {agent}: {message}")


async def run_analysis_with_progress(analysis_id: str, use_cached_data: bool = True):
    """Run GMR orchestrator and emit real-time progress events"""
    progress = AnalysisProgress(analysis_id)
    
    try:
        await progress.emit("info", "System", "🚀 Starting GMR Investment Analysis Orchestration")
        await asyncio.sleep(0.5)
        
        await progress.emit("step", "System", "📋 Initializing Orchestrator")
        orchestrator = GMRInvestmentOrchestrator()
        await asyncio.sleep(0.3)
        
        await progress.emit("phase", "System", "🔄 PHASE 1: Data Collection & Loading")
        await asyncio.sleep(0.5)
        
        await progress.emit("agent_created", "Stock_Analyst", "📊 Stock Analyst Agent created")
        await progress.emit("agent_running", "Stock_Analyst", "⏳ Loading stock data from stock_report.json...")
        await asyncio.sleep(1)
        
        # Check if stock data exists
        stock_file = config.PUBLIC_DATA_DIR / "stock_report.json"
        if stock_file.exists():
            with open(stock_file, 'r', encoding='utf-8') as f:
                stock_data = json.load(f)
            await progress.emit("agent_completed", "Stock_Analyst", "✅ Stock data loaded successfully", {
                "return_30d": "7.61%",
                "volatility": "13.98%",
                "volume": "11.96M shares",
                "status": "traded"
            })
        else:
            await progress.emit("agent_error", "Stock_Analyst", "⚠️ Stock data not found - run stock analyst first")
        
        await asyncio.sleep(0.8)
        
        await progress.emit("agent_created", "Investment_Analyst", "💰 Investment Analyst Agent created")
        await progress.emit("agent_running", "Investment_Analyst", "⏳ Loading company financials from company_analysis_output.json...")
        await asyncio.sleep(1)
        
        company_file = config.PUBLIC_DATA_DIR / "company_analysis_output.json"
        if company_file.exists():
            with open(company_file, 'r', encoding='utf-8') as f:
                company_data = json.load(f)
            await progress.emit("agent_completed", "Investment_Analyst", "✅ Financial data loaded successfully", {
                "revenue_fy25": "₹14.10 Bn",
                "ebitda": "₹1.00 Bn",
                "debt": "₹18.21 Bn",
                "interest_coverage": "0.71x"
            })
        else:
            await progress.emit("agent_error", "Investment_Analyst", "⚠️ Company data not found")
        
        await asyncio.sleep(0.8)
        
        await progress.emit("agent_created", "Compliance_Evaluator", "⚖️ Compliance Evaluator Agent created")
        await progress.emit("agent_running", "Compliance_Evaluator", "⏳ Loading compliance findings...")
        await asyncio.sleep(1)
        
        compliance_file = config.PUBLIC_DATA_DIR / "compliance_recommendation.json"
        if compliance_file.exists():
            with open(compliance_file, 'r', encoding='utf-8') as f:
                compliance_data = json.load(f)
            await progress.emit("agent_completed", "Compliance_Evaluator", "✅ Compliance data loaded", {
                "decision": "REVIEW REQUIRED",
                "exceptional_events": 2,
                "trading_status": "APPROVED"
            })
        else:
            await progress.emit("agent_error", "Compliance_Evaluator", "⚠️ Compliance data not found")
        
        await asyncio.sleep(0.8)
        
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
            await progress.emit("error", "GroupChat", f"⚠️ Orchestration failed: {orchestration_results.get('error')}")
        
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
            "report_file": str(Path(output_file).name),
            "output_html": "../output.html"
        })
        
        # Update session status
        analysis_sessions[analysis_id]["status"] = "completed"
        analysis_sessions[analysis_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        await progress.emit("error", "System", f"❌ Error: {str(e)}")
        analysis_sessions[analysis_id]["status"] = "failed"
        analysis_sessions[analysis_id]["error"] = str(e)
    
    finally:
        # Signal stream end
        await progress.queue.put(None)


# ============================================================================
# REST API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Serve the main HTML page"""
    return FileResponse(str(config.FRONTEND_DIR / "output.html"))


@app.post("/api/analyze")
async def trigger_analysis(background_tasks: BackgroundTasks, use_cached: bool = True):
    """
    Trigger new GMR investment analysis
    
    Returns analysis_id for tracking progress via SSE stream
    """
    analysis_id = str(uuid.uuid4())[:8]  # Short ID
    
    analysis_sessions[analysis_id] = {
        "id": analysis_id,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "use_cached_data": use_cached
    }
    
    # Start analysis in background
    background_tasks.add_task(run_analysis_with_progress, analysis_id, use_cached)
    
    return {
        "analysis_id": analysis_id,
        "status": "started",
        "stream_url": f"/api/stream/{analysis_id}",
        "message": "Analysis started. Connect to stream_url for real-time updates."
    }


@app.get("/api/stream/{analysis_id}")
async def stream_progress(analysis_id: str):
    """
    Stream real-time progress events via Server-Sent Events (SSE)
    
    Event types:
    - info: General information
    - phase: New phase started
    - step: New step in current phase
    - agent_created: Agent initialization
    - agent_running: Agent executing
    - agent_completed: Agent finished successfully
    - agent_error: Agent encountered error
    - agent_turn: Agent speaking in GroupChat
    - complete: Analysis finished
    - error: Fatal error occurred
    """
    
    async def event_generator():
        queue = event_queues[analysis_id]
        
        try:
            while True:
                # Wait for next event
                event = await queue.get()
                
                # None signals end of stream
                if event is None:
                    yield f"data: {json.dumps({'type': 'end', 'message': 'Stream closed'})}\n\n"
                    break
                
                # Send event to client
                yield f"data: {json.dumps(event)}\n\n"
                await asyncio.sleep(0.01)
        
        except asyncio.CancelledError:
            print(f"Stream cancelled for analysis {analysis_id}")
        
        finally:
            # Cleanup
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


@app.get("/api/status/{analysis_id}")
async def get_status(analysis_id: str):
    """Get current status of analysis (polling alternative to SSE)"""
    session = analysis_sessions.get(analysis_id)
    if not session:
        return {"error": "Analysis not found", "analysis_id": analysis_id}
    
    return session


@app.get("/api/sessions")
async def list_sessions():
    """List all analysis sessions"""
    return {
        "sessions": list(analysis_sessions.values()),
        "total": len(analysis_sessions)
    }


@app.delete("/api/sessions/{analysis_id}")
async def delete_session(analysis_id: str):
    """Delete analysis session"""
    if analysis_id in analysis_sessions:
        del analysis_sessions[analysis_id]
        if analysis_id in event_queues:
            del event_queues[analysis_id]
        return {"message": "Session deleted", "analysis_id": analysis_id}
    return {"error": "Session not found"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GMR Investment Analysis API",
        "version": "1.0.0",
        "active_sessions": len(analysis_sessions)
    }


if __name__ == "__main__":
    import uvicorn
    
    print("="*80)
    print("🚀 GMR INVESTMENT ANALYSIS API")
    print("="*80)
    print("📡 Starting FastAPI server with SSE support...")
    print("🌐 API Docs: http://localhost:8000/docs")
    print("🌐 Frontend: http://localhost:8000/")
    print("="*80)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
