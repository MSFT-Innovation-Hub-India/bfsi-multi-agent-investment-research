# BFSI Multi-Agent Investment Research
AI-powered investment analysis platform using Azure AI services for automated stock analysis, compliance review, and comprehensive investment report generation.

## 🚀 Features

- **Multi-Agent Architecture** — 3 specialized AI agents for comprehensive investment analysis
- **Real-Time Processing** — Live agent progress tracking and updates
- **Azure Integration** — Leverages Azure AI, OpenAI, and Azure AI Services
- **Container-Ready** — Docker support with Azure Container Apps deployment

## ️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.9+, FastAPI, Uvicorn, Azure AI Projects SDK |
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS |
| **AI** | Azure OpenAI, Azure AI Services |
| **Data** | JSON file storage, Azure AI integration |
| **Infra** | Docker, Azure Container Apps, Azure Container Registry |

## 📦 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Azure subscription with required services

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/bfsi-multi-agent-investment-research.git
   cd bfsi-multi-agent-investment-research
   ```

2. **Set up environment variables**
   ```bash
   # Backend
   cd backend
   copy .env.example .env
   # Edit .env with your Azure credentials
   
   # Frontend
   cd ../frontend
   copy .env.example .env
   # Edit .env with backend URL
   ```

3. **Install and run backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Install and run frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Access the application**
   - Frontend: `http://localhost:5173`
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`


## ☁️ Deployment

### Azure Container Apps

#### Prerequisites
- Azure CLI installed (`az --version`)
- Azure subscription with required services

#### Deploy Backend and Frontend

```bash
# 1. Login to Azure
az login

# 2. Create resource group
az group create --name bfsi-investment-rg --location eastus

# 3. Create container registry
az acr create --resource-group bfsi-investment-rg \
  --name bfsiinvestmentacr --sku Basic --admin-enabled true

# 4. Create Container Apps environment
az containerapp env create \
  --name bfsi-investment-env \
  --resource-group bfsi-investment-rg \
  --location eastus

# 5. Build and deploy backend
az acr build --registry bfsiinvestmentacr --image bfsi-backend:latest ./backend

az containerapp create \
  --name bfsi-backend \
  --resource-group bfsi-investment-rg \
  --environment bfsi-investment-env \
  --image bfsiinvestmentacr.azurecr.io/bfsi-backend:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server bfsiinvestmentacr.azurecr.io \
  --cpu 1.0 --memory 2.0Gi \
  --env-vars \
    AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com/" \
    AZURE_OPENAI_API_KEY="your-api-key" \
    AZURE_SUBSCRIPTION_ID="your-sub-id" \
    AZURE_RESOURCE_GROUP="your-rg" \
    AZURE_PROJECT_NAME="your-project" \
    AZURE_MODEL_DEPLOYMENT="gpt-4o-mini"

# 6. Get backend URL
BACKEND_URL=$(az containerapp show --name bfsi-backend \
  --resource-group bfsi-investment-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "Backend URL: https://$BACKEND_URL"

# 7. Build and deploy frontend
az acr build --registry bfsiinvestmentacr \
  --image bfsi-frontend:latest \
  --build-arg VITE_API_BASE_URL=https://$BACKEND_URL \
  ./frontend

az containerapp create \
  --name bfsi-frontend \
  --resource-group bfsi-investment-rg \
  --environment bfsi-investment-env \
  --image bfsiinvestmentacr.azurecr.io/bfsi-frontend:latest \
  --target-port 80 \
  --ingress external \
  --registry-server bfsiinvestmentacr.azurecr.io \
  --cpu 0.5 --memory 1.0Gi

# 8. Get frontend URL
FRONTEND_URL=$(az containerapp show --name bfsi-frontend \
  --resource-group bfsi-investment-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "Frontend URL: https://$FRONTEND_URL"
echo "Deployment complete!"
```

#### Useful Commands

```bash
# View logs
az containerapp logs show --name bfsi-backend --resource-group bfsi-investment-rg --follow

# Update backend after code changes
az acr build --registry bfsiinvestmentacr --image bfsi-backend:latest ./backend
az containerapp update --name bfsi-backend --resource-group bfsi-investment-rg \
  --image bfsiinvestmentacr.azurecr.io/bfsi-backend:latest

# Delete all resources
az group delete --name bfsi-investment-rg --yes
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed step-by-step instructions.

## 🔧 Configuration

### Required Azure Resources

| Resource | Purpose | Setup |
|----------|---------|-------|
| **Azure AI Project** | AI agent orchestration | Create in Azure AI Studio |
| **Azure OpenAI** | GPT model deployment | Deploy GPT-4o-mini or GPT-4o |
| **Azure Container Registry** | Docker image storage | Create ACR with admin enabled |
| **Azure Container Apps** | Application hosting | Create environment for apps |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | ✅ | Azure OpenAI service endpoint |
| `AZURE_OPENAI_API_KEY` | ✅ | Azure OpenAI API key |
| `AZURE_SUBSCRIPTION_ID` | ✅ | Azure subscription ID |
| `AZURE_RESOURCE_GROUP` | ✅ | Azure resource group name |
| `AZURE_PROJECT_NAME` | ✅ | Azure AI project name |
| `AZURE_MODEL_DEPLOYMENT` | ✅ | Model deployment name (default: `gpt-4o-mini`) |
| `PORT` | ⬜ | API server port (default: `8000`) |
| `ENVIRONMENT` | ⬜ | Environment mode (`development`/`production`) |
| `VITE_API_BASE_URL` | ✅ | Frontend: Backend API URL |

## 📖 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/fetchjson?file=<name>` | Fetch analysis data from storage |
| `POST` | `/api/orchestrate` | Trigger multi-agent workflow |
| `GET` | `/docs` | Interactive Swagger UI |

Interactive documentation available at: `/docs` (Swagger UI)

## 🏗️ Project Structure

```
bfsi-multi-agent-investment-research/
├── backend/                    # FastAPI backend
│   ├── agents/                 # AI agent implementations
│   │   ├── stock_analyst.py    #   Stock analysis agent
│   │   ├── compliance_agent.py #   Compliance review agent
│   │   └── investment_report_agent.py  # Report generation agent
│   ├── data/                   # JSON artifacts
│   ├── instructions/           # Agent prompt templates
│   ├── main.py                 # API entry point
│   ├── orchestrator.py         # Workflow orchestration
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Backend container image
│   └── .env.example            # Environment template
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/         # UI components
│   │   ├── pages/              # Application pages
│   │   │   ├── WorkflowPage/   #   Workflow monitor
│   │   │   └── AgentsPage/     #   Agent outputs
│   │   ├── context/            # React context providers
│   │   └── types/              # TypeScript types
│   ├── public/                 # Static assets
│   ├── Dockerfile              # Frontend container image
│   ├── package.json            # Node dependencies
│   └── .env.example            # Environment template
├── docker-compose.yml          # Local development
├── DEPLOYMENT_GUIDE.md         # Detailed deployment guide
└── README.md                   # This file
```

## 🔒 Security

- **Environment Variables** — Credentials stored in Azure Container Apps configuration (never in code)
- **Azure Key Vault** — Use for production secrets management
- **CORS** — Properly configured for frontend access only
- **HTTPS** — Enforced on all Azure deployments
- **.gitignore** — Sensitive files and credentials excluded from source control

## 📊 Monitoring

- **Health Check** — `GET /` endpoint for availability monitoring
- **Structured Logging** — Console logs with detailed agent execution tracking
- **Azure Monitor** — Container Apps built-in metrics and log streaming
- **Real-time Logs** — `az containerapp logs show --follow`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📚 Additional Resources

- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Azure AI Studio Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [Azure OpenAI Service](https://learn.microsoft.com/azure/ai-services/openai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)

