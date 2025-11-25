"""Configuration Manager - Loads secrets from .env file"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Base directory
BASE_DIR = Path(__file__).parent

# Azure AI Configuration (loaded from .env file)
PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
MODEL_DEPLOYMENT = os.getenv("MODEL_DEPLOYMENT", "gpt-4o-mini")

# File Paths (source data files in data folder)
INVESTMENT_DOCUMENT = BASE_DIR / os.getenv("INVESTMENT_DOCUMENT", "data/investmentproposal_processed.json")
STOCK_ANALYSIS_DOCUMENT = BASE_DIR / os.getenv("STOCK_ANALYSIS_DOCUMENT", "data/gmr_stock_analysis.json")
VALUATION_POLICY_FILE = BASE_DIR / os.getenv("VALUATION_POLICY_FILE", "data/valuationpolicy_processed.json")
COMPANY_ANALYSIS_FILE = BASE_DIR / os.getenv("COMPANY_ANALYSIS_FILE", "frontend/company_analysis_output.json")
STOCK_REPORT_FILE = BASE_DIR / os.getenv("STOCK_REPORT_FILE", "stock_report.json")

# Data Directory (source JSON files)
DATA_DIR = BASE_DIR / "data"

# Agents Directory
AGENTS_DIR = BASE_DIR / "agents"

# Template Directory
TEMPLATES_DIR = BASE_DIR / "templates"

# Output Directories
FRONTEND_DIR = BASE_DIR / "frontend"
IMAGES_DIR = FRONTEND_DIR / "images"
PUBLIC_DATA_DIR = FRONTEND_DIR / "public" / "data"

def validate_config():
    """Validate that required configuration is present"""
    if not PROJECT_CONNECTION_STRING:
        raise ValueError("PROJECT_CONNECTION_STRING is required")
    if not MODEL_DEPLOYMENT:
        raise ValueError("MODEL_DEPLOYMENT is required")
    return True

def get_config_summary():
    """Return configuration summary for debugging"""
    return {
        "PROJECT_CONNECTION_STRING": PROJECT_CONNECTION_STRING[:30] + "..." if PROJECT_CONNECTION_STRING else None,
        "MODEL_DEPLOYMENT": MODEL_DEPLOYMENT,
        "INVESTMENT_DOCUMENT": str(INVESTMENT_DOCUMENT),
        "STOCK_ANALYSIS_DOCUMENT": str(STOCK_ANALYSIS_DOCUMENT),
        "VALUATION_POLICY_FILE": str(VALUATION_POLICY_FILE),
        "COMPANY_ANALYSIS_FILE": str(COMPANY_ANALYSIS_FILE),
        "STOCK_REPORT_FILE": str(STOCK_REPORT_FILE),
        "DATA_DIR": str(DATA_DIR),
        "TEMPLATES_DIR": str(TEMPLATES_DIR),
    }
