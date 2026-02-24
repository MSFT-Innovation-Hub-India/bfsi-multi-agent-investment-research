"""
Cosmos DB Service for Investment Research Analysis
Handles analysis session persistence using Azure Managed Identity
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CosmosDBService:
    """Service for managing investment analysis data in Cosmos DB"""
    
    def __init__(self):
        """Initialize Cosmos DB client with Managed Identity or connection string"""
        
        # Load agents responses from JSON file
        self.agents_data = self._load_agents_responses()
        
        # Load analyses data from JSON file
        self.analyses_data = self._load_analyses_data()
        
        # Option 1: Use Managed Identity (production)
        if os.getenv('AZURE_COSMOS_ENDPOINT'):
            endpoint = os.getenv('AZURE_COSMOS_ENDPOINT')
            credential = DefaultAzureCredential()
            self.client = CosmosClient(endpoint, credential=credential)
            logger.info("✅ Cosmos DB connected using Managed Identity")
        
        # Option 2: Use connection string (fallback)
        elif os.getenv('COSMOS_CONNECTION_STRING'):
            connection_string = os.getenv('COSMOS_CONNECTION_STRING')
            self.client = CosmosClient.from_connection_string(connection_string)
            logger.info("✅ Cosmos DB connected using connection string")
        
        else:
            logger.warning("⚠️ No Cosmos DB credentials found in environment")
            self.client = None
            self.database = None
            self.container = None
            return
        
        # Database and container configuration
        self.database_name = os.getenv('COSMOS_DATABASE_NAME', 'investmentresearch_d')
        self.container_name = os.getenv('COSMOS_CONTAINER_NAME', 'investmentresearch_c')
        
        try:
            self.database = self.client.get_database_client(self.database_name)
            self.container = self.database.get_container_client(self.container_name)
            logger.info(f"✅ Cosmos DB service ready: {self.database_name}/{self.container_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Cosmos DB: {e}")
            self.database = None
            self.container = None
    
    def _load_agents_responses(self) -> Dict:
        """Load agent responses from JSON file"""
        try:
            json_path = Path(__file__).parent / "agents_responses.json"
            if json_path.exists():
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    logger.info(f"📄 Loaded agents data with {data.get('responseCount', 0)} responses")
                    return data
            else:
                logger.warning("⚠️ agents_responses.json not found")
                return {"agents": {}, "messageCount": 0, "responseCount": 0}
        except Exception as e:
            logger.error(f"❌ Failed to load agents responses: {e}")
            return {"agents": {}, "messageCount": 0, "responseCount": 0}
    
    def _load_analyses_data(self) -> Dict:
        """Load analyses data from JSON file"""
        try:
            json_path = Path(__file__).parent / "analyses_data.json"
            if json_path.exists():
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    logger.info(f"📄 Loaded analyses data with {len(data.get('analyses', []))} analyses")
                    return data
            else:
                logger.warning("⚠️ analyses_data.json not found")
                return {"analyses": []}
        except Exception as e:
            logger.error(f"❌ Failed to load analyses data: {e}")
            return {"analyses": []}
    
    def is_enabled(self) -> bool:
        """Check if Cosmos DB is enabled and connected"""
        return self.container is not None
    
    def generate_analysis_id(self) -> str:
        """Generate unique analysis ID"""
        import random
        import string
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"analysis-{timestamp}-{random_suffix}"
    
    def create_analysis(self, company_name: str, analyst_name: str = None, ticker: str = None, additional_data: Dict = None) -> Dict:
        """
        Create new analysis workflow with predefined agent responses
        
        Args:
            company_name: Company being analyzed
            analyst_name: Name of analyst initiating analysis
            ticker: Stock ticker symbol
            additional_data: Additional data to merge into workflow
            
        Returns:
            Analysis document with merged agent responses
        """
        analysis_id = self.generate_analysis_id()
        timestamp = datetime.now().astimezone().isoformat()
        
        # Create analysis document with dual partition key fields
        analysis_doc = {
            "id": analysis_id,
            "workflowid": analysis_id,  # Partition key (lowercase)
            "workflowId": analysis_id,  # For frontend compatibility (camelCase)
            "companyName": company_name,
            "ticker": ticker or "GMRAIRPORT.NS",
            "analystName": analyst_name or "System",
            "status": "in_progress",
            "createdAt": timestamp,
            "updatedAt": timestamp
        }
        
        # Add additional data if provided
        if additional_data:
            analysis_doc.update(additional_data)
        
        # If Cosmos DB is enabled, store the document
        if self.is_enabled():
            try:
                logger.info(f"📝 Creating analysis: {analysis_id}")
                logger.info(f"   Company: {company_name}")
                logger.info(f"   Partition Key: workflowid={analysis_id}")
                
                created_doc = self.container.create_item(
                    body=analysis_doc,
                    enable_automatic_id_generation=False
                )
                
                # Merge with agents data before returning
                created_doc.update(self.agents_data)
                
                logger.info(f"✅ Analysis created in Cosmos DB: {analysis_id}")
                return created_doc
            except Exception as e:
                logger.error(f"❌ Failed to create analysis in Cosmos DB: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Return local document with agents data if Cosmos DB fails
                analysis_doc.update(self.agents_data)
                return analysis_doc
        else:
            logger.info(f"📋 Cosmos DB not enabled, returning local analysis: {analysis_id}")
            return analysis_doc
    
    def get_analysis(self, analysis_id: str) -> Optional[Dict]:
        """
        Get analysis by ID
        
        Args:
            analysis_id: Analysis ID
            
        Returns:
            Analysis document or None
        """
        if not self.is_enabled():
            # Return from loaded data if Cosmos DB not available
            for analysis in self.analyses_data.get("analyses", []):
                if analysis.get("id") == analysis_id or analysis.get("analysisId") == analysis_id:
                    return analysis
            return None
        
        try:
            logger.info(f"🔍 Fetching analysis: {analysis_id}")
            logger.info(f"   Partition Key: workflowid={analysis_id}")
            
            item = self.container.read_item(
                item=analysis_id,
                partition_key=analysis_id
            )
            
            # Merge with agents data from JSON file
            item.update(self.agents_data)
            
            logger.info(f"✅ Retrieved analysis: {analysis_id}")
            return item
        except Exception as e:
            logger.error(f"❌ Failed to get analysis: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Try to return from loaded data
            for analysis in self.analyses_data.get("analyses", []):
                if analysis.get("id") == analysis_id or analysis.get("analysisId") == analysis_id:
                    return analysis
            return None
    
    def list_analyses(self) -> List[Dict]:
        """
        List all analyses
        
        Returns:
            List of analysis documents
        """
        if not self.is_enabled():
            logger.info("📋 Cosmos DB not enabled, returning loaded analyses")
            return self.analyses_data.get("analyses", [])
        
        try:
            logger.info(f"📊 Listing all analyses from {self.container_name}")
            
            query = "SELECT * FROM c ORDER BY c.createdAt DESC"
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            logger.info(f"✅ Retrieved {len(items)} analyses")
            
            # If no items in Cosmos DB, return loaded data
            if not items:
                logger.info("📋 No analyses in Cosmos DB, returning loaded data")
                return self.analyses_data.get("analyses", [])
            
            # Merge agents data into each analysis
            for analysis in items:
                analysis.update(self.agents_data)
            
            return items
        except Exception as e:
            logger.error(f"❌ Failed to list analyses: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self.analyses_data.get("analyses", [])
    
    def update_analysis_status(self, analysis_id: str, status: str) -> Optional[Dict]:
        """Update analysis status"""
        if not self.is_enabled():
            return None
        
        try:
            analysis = self.get_analysis(analysis_id)
            if not analysis:
                return None
            
            analysis["status"] = status
            analysis["updatedAt"] = datetime.utcnow().isoformat() + 'Z'
            if status == "completed":
                analysis["completedAt"] = analysis["updatedAt"]
            
            updated = self.container.replace_item(
                item=analysis_id,
                body=analysis
            )
            
            logger.info(f"✅ Updated analysis status: {analysis_id} -> {status}")
            return updated
        except Exception as e:
            logger.error(f"❌ Failed to update analysis status: {e}")
            return None
    
    def update_agent_status(self, analysis_id: str, agent_key: str, status: str, output: str = None) -> Optional[Dict]:
        """Update agent status and output"""
        if not self.is_enabled():
            return None
        
        try:
            analysis = self.get_analysis(analysis_id)
            if not analysis:
                return None
            
            if agent_key not in analysis.get("agents", {}):
                logger.warning(f"⚠️ Agent {agent_key} not found in analysis {analysis_id}")
                return None
            
            timestamp = datetime.utcnow().isoformat() + 'Z'
            analysis["agents"][agent_key]["status"] = status
            analysis["updatedAt"] = timestamp
            
            if status == "running" and not analysis["agents"][agent_key].get("startedAt"):
                analysis["agents"][agent_key]["startedAt"] = timestamp
            elif status == "completed":
                analysis["agents"][agent_key]["completedAt"] = timestamp
                if output:
                    analysis["agents"][agent_key]["output"] = output
            
            updated = self.container.replace_item(
                item=analysis_id,
                body=analysis
            )
            
            logger.info(f"✅ Updated agent {agent_key} status: {status}")
            return updated
        except Exception as e:
            logger.error(f"❌ Failed to update agent status: {e}")
            return None
