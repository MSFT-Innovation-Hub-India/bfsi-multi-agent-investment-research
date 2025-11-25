# GMR Investment Analysis Frontend

Professional React + TypeScript frontend for displaying multi-agent analysis results.

## Features

- **Workflow Page**: Animated visualization of the 3-agent analysis pipeline
  - Stock Analyst → Investment Analyst → Compliance Evaluator
  - Real-time processing animations with status indicators
  - Expandable agent cards showing detailed outputs
  
- **Agents Page**: Tabbed interface for detailed analysis
  - Stock Analysis: 5 panels (Executive Summary + P1-P4 charts)
  - Investment Analysis: 8 sections (Financial, Debt, Operations, Valuation, etc.)
  - Compliance: 4 sections (Policy Rules, Trading, Events, Verdict)
  - Toggle JSON viewer for raw backend data

## Tech Stack

- React 18.2
- TypeScript 5.2
- React Router 6.20
- Tailwind CSS 3.3
- Vite 5.0
- Lucide React Icons

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Data Sources

The application loads data from:
- `/public/data/stock_report.json` - Stock analysis data
- `/public/data/company_analysis_output.json` - Investment analysis data
- `/public/data/compliance_findings.json` - Compliance findings
- `/public/data/compliance_recommendation.json` - Final verdict
- `/public/images/` - Dashboard charts and visualizations

## Project Structure

```
src/
├── components/
│   ├── Header/          # Navigation header
│   ├── Layout/          # Main layout wrapper
│   ├── Tabs/            # Reusable tab component
│   ├── OutputSection/   # Content display with images
│   └── JsonViewer/      # Raw JSON display
├── pages/
│   ├── WorkflowPage/    # Animated workflow visualization
│   └── AgentsPage/      # Detailed agent outputs
├── types/
│   └── models.ts        # TypeScript interfaces
├── App.tsx              # Routing configuration
└── main.tsx             # Application entry point
```

## Animations

- **Pulse**: Processing agents have slow pulsing animation
- **Bounce**: Arrows animate when transitioning between agents
- **Fade-in**: Content smoothly appears when loaded
- **Spin**: Processing indicators rotate

## Color Scheme

- Primary Blue: #1F3A93 (professional, corporate)
- Success Green: #10B981
- Warning Yellow: #F59E0B
- Processing Blue: #3B82F6
- Gray scale for neutral elements
