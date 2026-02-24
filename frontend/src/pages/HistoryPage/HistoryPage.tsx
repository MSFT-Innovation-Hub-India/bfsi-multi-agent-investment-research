import { useState, useEffect } from 'react'
import { History, Eye, TrendingUp, Building, Shield, Calendar, CheckCircle, Loader2, AlertCircle, ArrowLeft, BarChart3, FileText } from 'lucide-react'
import { API_BASE_URL, fetchBlobJson, getImageUrl } from '../../config/appConfig'

const API_JSON_ENDPOINT = '/api/fetchjson'

const fetchFromApi = async (filename: string): Promise<any> => {
  if (!API_BASE_URL) {
    throw new Error('API endpoint not configured')
  }

  const url = `${API_BASE_URL}${API_JSON_ENDPOINT}?file=${encodeURIComponent(filename)}`
  const response = await fetch(url, {
    headers: { Accept: 'application/json' }
  })

  if (!response.ok) {
    throw new Error(`API unavailable for ${filename} (${url})`)
  }

  const payload = await response.json()
  console.info(`[HistoryPage] Loaded ${filename} from API: ${url}`)
  return payload
}

const loadAgentJson = async (filename: string): Promise<any> => {
  try {
    return await fetchFromApi(filename)
  } catch (apiError) {
    const url = API_BASE_URL
      ? `${API_BASE_URL}${API_JSON_ENDPOINT}?file=${encodeURIComponent(filename)}`
      : '(no API configured)'
    console.warn(
      `API request attempted at ${url}.`,
      apiError
    )

    try {
      const data = await fetchBlobJson(filename)
      console.info(`[HistoryPage] Loaded bundled JSON for ${filename} from public/data`)
      return data
    } catch (assetError) {
      console.error(`[HistoryPage] Unable to load packaged data for ${filename} under public/data.`, assetError)
      throw assetError
    }
  }
}

interface WorkflowRun {
  id: string
  workflowId: string
  company: string
  symbol: string
  startedAt: string
  completedAt: string
  status: 'completed' | 'running' | 'failed'
  agents: {
    id: string
    name: string
    status: string
  }[]
}

function HistoryPage() {
  const [workflowHistory, setWorkflowHistory] = useState<WorkflowRun[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowRun | null>(null)
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<string | null>(null)
  const [showJson, setShowJson] = useState(false)
  
  // State for loaded JSON data
  const [stockData, setStockData] = useState<any>(null)
  const [investmentData, setInvestmentData] = useState<any>(null)
  const [complianceData, setComplianceData] = useState<any>(null)
  const [loadingAgent, setLoadingAgent] = useState<string | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  // Function to parse markdown tables and render as HTML
  const renderContent = (text: string) => {
    if (!text) return null

    // Split content by markdown table patterns
    const parts: any[] = []
    let currentIndex = 0
    
    // Regex to match markdown tables
    const tableRegex = /(\|[^\n]+\|\n\|[-:\s|]+\|\n(?:\|[^\n]+\|\n)+)/g
    let match

    while ((match = tableRegex.exec(text)) !== null) {
      // Add text before table
      if (match.index > currentIndex) {
        parts.push({
          type: 'text',
          content: text.substring(currentIndex, match.index)
        })
      }

      // Parse table
      const tableText = match[1]
      const rows = tableText.trim().split('\n').filter(row => row.trim())
      const headers = rows[0].split('|').filter(cell => cell.trim()).map(cell => cell.trim())
      const dataRows = rows.slice(2).map(row => 
        row.split('|').filter(cell => cell.trim()).map(cell => cell.trim())
      )

      parts.push({
        type: 'table',
        headers,
        rows: dataRows
      })

      currentIndex = match.index + match[0].length
    }

    // Add remaining text
    if (currentIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.substring(currentIndex)
      })
    }

    // If no tables found, return as single text block
    if (parts.length === 0) {
      return <p className="leading-relaxed whitespace-pre-wrap text-base" style={{ color: '#00246B' }}>{text}</p>
    }

    return (
      <div className="space-y-6">
        {parts.map((part, idx) => {
          if (part.type === 'text') {
            return (
              <div key={idx} className="leading-relaxed whitespace-pre-wrap text-base" style={{ color: '#00246B' }}>
                {part.content}
              </div>
            )
          } else if (part.type === 'table') {
            return (
              <div key={idx} className="overflow-x-auto">
                <table className="w-full border-collapse rounded-lg overflow-hidden" style={{ backgroundColor: '#CADCFC' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#00246B', borderBottom: '2px solid #00246B' }}>
                      {part.headers.map((header: string, hIdx: number) => (
                        <th key={hIdx} className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#CADCFC' }}>
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {part.rows.map((row: string[], rIdx: number) => (
                      <tr key={rIdx} className="border-b transition-colors" style={{ borderBottomColor: '#00246B' }}>
                        {row.map((cell: string, cIdx: number) => (
                          <td key={cIdx} className="px-4 py-3 text-sm" style={{ color: '#00246B' }}>
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          }
          return null
        })}
      </div>
    )
  }

  // Fetch workflows from API
  useEffect(() => {
    const fetchWorkflows = async () => {
      try {
        setLoading(true)
        setError(null)
        
        const response = await fetch(`${API_BASE_URL}/api/analyses`)
        if (!response.ok) {
          throw new Error(`Failed to fetch analyses: ${response.statusText}`)
        }
        
        const data = await response.json()
        
        // Transform API response to WorkflowRun format with GMR Airports data
        const workflows: WorkflowRun[] = data.analyses.map((analysis: any) => ({
          id: analysis.id,
          workflowId: analysis.workflowid || analysis.workflowId || analysis.id,
          company: analysis.companyName || 'GMR Airports Ltd',
          symbol: analysis.ticker || 'GMRAIRPORT.NS',
          startedAt: analysis.createdAt || analysis.created_at || new Date().toISOString(),
          completedAt: analysis.updatedAt || analysis.updated_at || new Date().toISOString(),
          status: analysis.status || 'completed',
          agents: [
            {
              id: 'stock_analyst',
              name: 'Stock Analyst',
              status: analysis.agents?.stock_analyst?.status || 'completed'
            },
            {
              id: 'company_analyst',
              name: 'Company Analyst',
              status: analysis.agents?.company_analyst?.status || 'completed'
            },
            {
              id: 'compliance_evaluator',
              name: 'Compliance Evaluator',
              status: analysis.agents?.compliance_evaluator?.status || 'completed'
            }
          ]
        }))
        
        setWorkflowHistory(workflows)
        setLoading(false)
      } catch (err) {
        console.error('Error fetching workflows:', err)
        setError(err instanceof Error ? err.message : 'Failed to load workflow history')
        setLoading(false)
      }
    }
    
    fetchWorkflows()
  }, [])

  // Load agent data from JSON files (same as AgentsPage)
  const loadAgentData = async (agentId: string) => {
    setLoadError(null)

    if (agentId === 'stock_analyst') {
      if (stockData) {
        setActiveTab(stockData.sections?.[0]?.id ?? null)
        return
      }

      setLoadingAgent(agentId)
      try {
        const data = await loadAgentJson('stock_report.json')
        console.log('Loaded stock data:', data)
        setStockData(data)
        setActiveTab(data.sections?.[0]?.id ?? null)
      } catch (err) {
        console.error('Error loading stock data:', err)
        setLoadError('Unable to load stock analyst report right now.')
      } finally {
        setLoadingAgent(null)
      }
      return
    }

    if (agentId === 'company_analyst') {
      if (investmentData) {
        setActiveTab(investmentData.sections?.[0]?.id ?? null)
        return
      }

      setLoadingAgent(agentId)
      try {
        const data = await loadAgentJson('company_analysis_output.json')
        console.log('Loaded investment data:', data)
        setInvestmentData(data)
        setActiveTab(data.sections?.[0]?.id ?? null)
      } catch (err) {
        console.error('Error loading investment data:', err)
        setLoadError('Unable to load company analyst report right now.')
      } finally {
        setLoadingAgent(null)
      }
      return
    }

    if (agentId === 'compliance_evaluator') {
      if (complianceData) {
        setActiveTab('section_1')
        return
      }

      setLoadingAgent(agentId)
      try {
        const findings = await loadAgentJson('compliance_findings.json')
        let merged = findings
        try {
          const recommendation = await loadAgentJson('compliance_recommendation.json')
          merged = { ...findings, ...recommendation }
        } catch (recErr) {
          console.warn('Recommendation data missing, using findings only.', recErr)
        }

        console.log('Loaded compliance data:', merged)
        setComplianceData(merged)
        setActiveTab('section_1')
      } catch (err) {
        console.error('Error loading compliance data:', err)
        setLoadError('Unable to load compliance evaluator report right now.')
      } finally {
        setLoadingAgent(null)
      }
    }
  }

  const getTabsForAgent = () => {
    if (selectedAgent === 'stock_analyst' && stockData?.sections) {
      console.log('Stock sections:', stockData.sections)
      return stockData.sections.map((s: any) => ({
        id: s.id,
        label: s.name
      }))
    }
    if (selectedAgent === 'company_analyst' && investmentData?.sections) {
      console.log('Investment sections:', investmentData.sections)
      return investmentData.sections.map((s: any) => ({
        id: s.id,
        label: s.name
      }))
    }
    if (selectedAgent === 'compliance_evaluator') {
      return [
        { id: 'section_1', label: 'Policy Rules' },
        { id: 'section_2', label: 'Trading Classification' },
        { id: 'section_3', label: 'Exceptional Events' },
        { id: 'section_4', label: 'Final Verdict' }
      ]
    }
    return []
  }

  const getCurrentSection = () => {
    if (selectedAgent === 'stock_analyst' && activeTab && stockData?.sections) {
      const section = stockData.sections.find((s: any) => s.id === activeTab)
      console.log('Current stock section:', section)
      return section
    }
    if (selectedAgent === 'company_analyst' && activeTab && investmentData?.sections) {
      const section = investmentData.sections.find((s: any) => s.id === activeTab)
      console.log('Current investment section:', section)
      // Map 'images' array to 'image' if needed
      if (section && section.images && section.images.length > 0) {
        return { ...section, image: section.images[0] }
      }
      return section
    }
    if (selectedAgent === 'compliance_evaluator' && complianceData && activeTab) {
      const sectionMap: Record<string, any> = {
        'section_1': { 
          name: 'Policy Rules Compliance',
          analysis: complianceData.section_1_policy_rules,
          image: null
        },
        'section_2': { 
          name: 'Trading Classification',
          analysis: complianceData.section_2_trading_classification,
          image: null
        },
        'section_3': { 
          name: 'Exceptional Events',
          analysis: complianceData.section_3_exceptional_events,
          image: null
        },
        'section_4': { 
          name: 'Final Compliance Verdict',
          analysis: complianceData.section_4_final_recommendation,
          image: null
        }
      }
      return sectionMap[activeTab]
    }
    return null
  }

  const getAgentIcon = (agentId: string) => {
    if (agentId === 'stock_analyst') return <TrendingUp className="h-6 w-6" />
    if (agentId === 'company_analyst') return <Building className="h-6 w-6" />
    if (agentId === 'compliance_evaluator') return <Shield className="h-6 w-6" />
    return <Eye className="h-6 w-6" />
  }

  const handleAgentClick = (agentId: string) => {
    setSelectedAgent(agentId)
    void loadAgentData(agentId)
  }

  const handleBackToWorkflow = () => {
    setSelectedAgent(null)
    setActiveTab(null)
  }

  const currentSection = getCurrentSection()

  // Agent Detail View - Same as AgentsPage
  if (selectedAgent && selectedWorkflow) {
    const agentTabs = [
      { id: 'stock_analyst', label: 'Stock Analyst', icon: <TrendingUp className="h-5 w-5" /> },
      { id: 'company_analyst', label: 'Company Analyst', icon: <Building className="h-5 w-5" /> },
      { id: 'compliance_evaluator', label: 'Compliance Evaluator', icon: <Shield className="h-5 w-5" /> }
    ]
    const activeAgentTab = agentTabs.find(t => t.id === selectedAgent)
    const sections = getTabsForAgent()

    return (
      <div className="min-h-screen py-8" style={{ backgroundColor: '#CADCFC' }}>
        <div className="max-w-7xl mx-auto px-8">
          {/* Header with Back Button */}
          <div className="rounded-3xl p-8 mb-8 shadow-2xl" style={{ backgroundColor: '#00246B' }}>
            <button
              onClick={handleBackToWorkflow}
              className="mb-4 flex items-center gap-2 px-4 py-2 rounded-xl transition-all font-semibold"
              style={{ backgroundColor: '#CADCFC', color: '#00246B' }}
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Analysis List
            </button>
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl" style={{ backgroundColor: '#CADCFC' }}>
                {getAgentIcon(selectedAgent)}
              </div>
              <div>
                <h1 className="text-4xl font-bold" style={{ color: '#CADCFC' }}>
                  {activeAgentTab?.label} Report
                </h1>
                <p className="text-sm mt-1" style={{ color: '#CADCFC', opacity: 0.8 }}>
                  {selectedWorkflow.company} • {selectedWorkflow.symbol}
                </p>
              </div>
            </div>
          </div>

          {/* Section Tabs */}
          <div className="mb-6 overflow-x-auto">
            <div className="flex gap-2 pb-2">
              {sections.map((section: { id: string; label: string }) => (
                <button
                  key={section.id}
                  onClick={() => setActiveTab(section.id)}
                  className="px-6 py-2.5 font-medium whitespace-nowrap rounded-xl transition-all shadow-lg border"
                  style={
                    activeTab === section.id
                      ? { backgroundColor: '#00246B', color: '#CADCFC', borderColor: '#00246B' }
                      : { backgroundColor: 'white', color: '#00246B', borderColor: '#00246B' }
                  }
                >
                  {section.label}
                </button>
              ))}
            </div>
          </div>

          {/* Content - Same layout as AgentsPage */}
          {loadingAgent && (
            <div className="rounded-3xl border p-12 shadow-2xl text-center" style={{ backgroundColor: 'white', borderColor: '#00246B' }}>
              <Loader2 className="h-16 w-16 mx-auto mb-4 animate-spin" style={{ color: '#00246B' }} />
              <h2 className="text-2xl font-semibold mb-2" style={{ color: '#00246B' }}>
                Loading Report...
              </h2>
            </div>
          )}

          {currentSection && !loadingAgent && (
            <div className="space-y-6">
              {/* Main Content - Side by Side */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left: Text Analysis */}
                <div className="rounded-3xl border shadow-2xl flex flex-col" style={{ backgroundColor: 'white', borderColor: '#00246B', maxHeight: 'calc(100vh - 400px)' }}>
                  <div className="p-8 pb-4">
                    <div className="flex items-start gap-4">
                      <div className="p-3 rounded-xl" style={{ backgroundColor: '#00246B' }}>
                        <BarChart3 className="w-6 h-6" style={{ color: '#CADCFC' }} />
                      </div>
                      <div>
                        <h2 className="text-3xl font-bold mb-2" style={{ color: '#00246B' }}>{currentSection.name}</h2>
                        <p style={{ color: '#00246B', opacity: 0.7 }}>Detailed analysis and insights</p>
                      </div>
                    </div>
                  </div>

                  <div className="px-8 pb-8 overflow-y-auto flex-1">
                    <div className="prose prose-invert prose-lg max-w-none">
                      {renderContent(currentSection.summary || currentSection.analysis)}
                    </div>

                    {/* Bullet points for lists */}
                    {currentSection.points && (
                      <ul className="list-disc list-inside space-y-2 mt-6" style={{ color: '#00246B' }}>
                        {currentSection.points.map((point: string, idx: number) => (
                          <li key={idx}>{point}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>

                {/* Right: Visualization */}
                {currentSection.image ? (
                  <div className="rounded-3xl border shadow-2xl flex flex-col" style={{ backgroundColor: 'white', borderColor: '#00246B', maxHeight: 'calc(100vh - 400px)' }}>
                    <div className="p-8 pb-4">
                      <h3 className="text-xl font-semibold mb-6 flex items-center gap-2" style={{ color: '#00246B' }}>
                        <Eye className="w-5 h-5" style={{ color: '#00246B' }} />
                        Visualization
                      </h3>
                    </div>
                    <div className="px-8 pb-8 overflow-y-auto flex-1">
                      <div className="bg-blue-800/30 rounded-2xl p-4 border border-blue-500">
                        <img
                          src={getImageUrl(currentSection.image)}
                          alt={currentSection.name}
                          className="w-full h-auto rounded-xl"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none'
                            const placeholder = e.currentTarget.nextElementSibling as HTMLElement
                            if (placeholder) placeholder.style.display = 'flex'
                          }}
                        />
                        <div className="hidden flex-col items-center justify-center h-64 rounded-xl" style={{ backgroundColor: '#CADCFC' }}>
                          <FileText className="w-12 h-12 mb-3" style={{ color: '#00246B' }} />
                          <p style={{ color: '#00246B' }}>No visualization available</p>
                          <p className="text-sm mt-2" style={{ color: '#00246B', opacity: 0.7 }}>This section contains text analysis only</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-3xl border p-12 shadow-2xl flex items-center justify-center" style={{ backgroundColor: 'white', borderColor: '#00246B', maxHeight: 'calc(100vh - 400px)' }}>
                    <div className="flex flex-col items-center justify-center text-center">
                      <FileText className="w-16 h-16 mb-4" style={{ color: '#00246B' }} />
                      <p className="text-lg font-medium" style={{ color: '#00246B' }}>No visualization available</p>
                      <p className="text-sm mt-2" style={{ color: '#00246B', opacity: 0.7 }}>This section contains text analysis only</p>
                    </div>
                  </div>
                )}
              </div>

              {/* JSON Viewer */}
              {showJson && (
                <div className="rounded-3xl border p-8 shadow-2xl" style={{ backgroundColor: 'white', borderColor: '#00246B' }}>
                  <h3 className="text-xl font-semibold mb-4" style={{ color: '#00246B' }}>Raw JSON Data</h3>
                  <pre className="p-6 rounded-2xl overflow-x-auto text-sm max-h-96 overflow-y-auto border" style={{ backgroundColor: '#CADCFC', color: '#00246B', borderColor: '#00246B' }}>
                    {JSON.stringify(currentSection, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen py-8" style={{ backgroundColor: '#CADCFC' }}>
      <div className="max-w-7xl mx-auto px-8">
        {/* Header */}
        <div className="rounded-3xl p-8 mb-8 shadow-2xl" style={{ backgroundColor: '#00246B' }}>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl" style={{ backgroundColor: '#CADCFC' }}>
              <History className="w-6 h-6" style={{ color: '#00246B' }} />
            </div>
            <div>
              <h1 className="text-4xl font-bold" style={{ color: '#CADCFC' }}>Workflow History</h1>
              <p className="text-sm mt-1" style={{ color: '#CADCFC', opacity: 0.8 }}>
                View past analysis runs and agent outputs
              </p>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="rounded-2xl p-12 text-center shadow-lg" style={{ backgroundColor: 'white', border: '2px solid #00246B' }}>
            <Loader2 className="h-16 w-16 mx-auto mb-4 animate-spin" style={{ color: '#00246B' }} />
            <h2 className="text-2xl font-semibold mb-2" style={{ color: '#00246B' }}>
              Loading Workflows...
            </h2>
          </div>
        ) : error ? (
          <div className="rounded-2xl p-12 text-center shadow-lg" style={{ backgroundColor: 'white', border: '2px solid #00246B' }}>
            <AlertCircle className="h-16 w-16 mx-auto mb-4" style={{ color: '#00246B', opacity: 0.3 }} />
            <h2 className="text-2xl font-semibold mb-2" style={{ color: '#00246B' }}>
              Error Loading Workflows
            </h2>
            <p style={{ color: '#00246B', opacity: 0.7 }}>{error}</p>
          </div>
        ) : workflowHistory.length === 0 ? (
          <div className="rounded-2xl p-12 text-center shadow-lg" style={{ backgroundColor: 'white', border: '2px solid #00246B' }}>
            <History className="h-16 w-16 mx-auto mb-4" style={{ color: '#00246B', opacity: 0.3 }} />
            <h2 className="text-2xl font-semibold mb-2" style={{ color: '#00246B' }}>
              No Workflow History
            </h2>
            <p style={{ color: '#00246B', opacity: 0.7 }}>
              Start an analysis from the Workflow page to see history here
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Workflow List - Horizontal Scroll */}
            <div className="rounded-2xl p-6 shadow-lg" style={{ backgroundColor: 'white', border: '2px solid #00246B' }}>
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2" style={{ color: '#00246B' }}>
                <Calendar className="h-5 w-5" />
                Analysis Runs
              </h2>
              <div className="flex gap-4 overflow-x-auto pb-2">
                {workflowHistory.map((workflow) => (
                  <button
                    key={workflow.id}
                    onClick={() => {
                      setSelectedWorkflow(workflow)
                      setSelectedAgent(null)
                      setActiveTab(null)
                    }}
                    className="flex-shrink-0 text-left p-4 rounded-xl transition-all border-2"
                    style={{
                      backgroundColor: selectedWorkflow?.id === workflow.id ? '#00246B' : 'white',
                      color: selectedWorkflow?.id === workflow.id ? '#CADCFC' : '#00246B',
                      borderColor: '#00246B',
                      minWidth: '280px'
                    }}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-semibold text-sm">{workflow.company}</div>
                        <div className="text-xs opacity-70 mt-1">{workflow.symbol}</div>
                        <div className="text-xs opacity-60 mt-1">
                          {new Date(workflow.completedAt).toLocaleDateString()}
                        </div>
                      </div>
                      {workflow.status === 'completed' && (
                        <CheckCircle className="h-4 w-4 flex-shrink-0" style={{ color: '#126125' }} />
                      )}
                    </div>
                    <div className="text-xs mt-2 font-mono opacity-70 truncate">
                      {workflow.workflowId}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Agent Overview - Full Width */}
            {selectedWorkflow && (
              <div className="space-y-4">{/* Workflow Info Card */}
                <div className="rounded-2xl p-6 shadow-lg" style={{ backgroundColor: '#00246B' }}>
                  <h2 className="text-2xl font-bold mb-2" style={{ color: '#CADCFC' }}>
                    {selectedWorkflow.company}
                  </h2>
                  <div className="grid grid-cols-2 gap-4 text-sm" style={{ color: '#CADCFC' }}>
                    <div>
                      <span className="opacity-70">Symbol:</span> <span className="font-semibold">{selectedWorkflow.symbol}</span>
                    </div>
                    <div>
                      <span className="opacity-70">Status:</span>{' '}
                      <span className="font-semibold inline-flex items-center gap-1">
                        <CheckCircle className="h-4 w-4" style={{ color: '#126125' }} />
                        Completed
                      </span>
                    </div>
                    <div>
                      <span className="opacity-70">Started:</span> <span className="font-semibold">{new Date(selectedWorkflow.startedAt).toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="opacity-70">Completed:</span> <span className="font-semibold">{new Date(selectedWorkflow.completedAt).toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                {/* Agent Cards - Clickable */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {selectedWorkflow.agents.map((agent) => (
                    <button
                      key={agent.id}
                      onClick={() => handleAgentClick(agent.id)}
                      className="rounded-2xl p-6 shadow-lg border-2 transition-all hover:scale-105 text-left"
                      style={{ backgroundColor: 'white', borderColor: '#00246B' }}
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <div className="p-3 rounded-xl" style={{ backgroundColor: '#00246B' }}>
                          <div style={{ color: '#CADCFC' }}>
                            {getAgentIcon(agent.id)}
                          </div>
                        </div>
                        <h3 className="text-lg font-bold" style={{ color: '#00246B' }}>
                          {agent.name}
                        </h3>
                      </div>
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-xs px-2 py-1 rounded-full" style={{ backgroundColor: '#126125', color: 'white' }}>
                          ✓ Completed
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-sm font-semibold" style={{ color: '#00246B' }}>
                        <Eye className="h-4 w-4" />
                        View Full Report
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default HistoryPage
