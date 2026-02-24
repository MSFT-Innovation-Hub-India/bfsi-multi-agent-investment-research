import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  TrendingUp, 
  Building, 
  Shield,
  Eye,
  FileText,
  BarChart3,
  Activity,
  PlayCircle
} from 'lucide-react'
import { useVisualization } from '../../context/VisualizationContext'
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
  console.info(`[AgentsPage] Loaded ${filename} from API: ${url}`)
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
      console.info(`[AgentsPage] Loaded bundled JSON for ${filename} from public/data`)
      return data
    } catch (assetError) {
      console.error(`[AgentsPage] Unable to load packaged data for ${filename} under public/data.`, assetError)
      throw assetError
    }
  }
}

function AgentsPage() {
  const { hasWorkflowRun } = useVisualization()
  const [activeAgent, setActiveAgent] = useState<string | null>(null)
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

  const loadAgentData = async (agentId: string) => {
    setLoadError(null)

    if (agentId === 'stock') {
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

    if (agentId === 'investment') {
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

    if (agentId === 'compliance') {
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

  const agentTabs = [
    { id: 'stock', label: 'Stock Analyst', icon: <TrendingUp className="h-5 w-5" /> },
    { id: 'investment', label: 'Company Analyst', icon: <Building className="h-5 w-5" /> },
    { id: 'compliance', label: 'Compliance Evaluator', icon: <Shield className="h-5 w-5" /> }
  ]

  const getTabsForAgent = () => {
    if (activeAgent === 'stock' && stockData?.sections) {
      console.log('Stock sections:', stockData.sections)
      return stockData.sections.map((s: any) => ({
        id: s.id,
        label: s.name
      }))
    }
    if (activeAgent === 'investment' && investmentData?.sections) {
      console.log('Investment sections:', investmentData.sections)
      return investmentData.sections.map((s: any) => ({
        id: s.id,
        label: s.name
      }))
    }
    if (activeAgent === 'compliance') {
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
    if (activeAgent === 'stock' && activeTab && stockData?.sections) {
      const section = stockData.sections.find((s: any) => s.id === activeTab)
      console.log('Current stock section:', section)
      return section
    }
    if (activeAgent === 'investment' && activeTab && investmentData?.sections) {
      const section = investmentData.sections.find((s: any) => s.id === activeTab)
      console.log('Current investment section:', section)
      // Map 'images' array to 'image' if needed
      if (section && section.images && section.images.length > 0) {
        return { ...section, image: section.images[0] }
      }
      return section
    }
    if (activeAgent === 'compliance' && complianceData && activeTab) {
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

  const handleAgentChange = (agentId: string) => {
    if (!hasWorkflowRun) {
      setLoadError('Run the analysis workflow once before opening agent reports.')
      return
    }

    setLoadError(null)

    if (activeAgent === agentId && activeTab) {
      return
    }

    setActiveAgent(agentId)
    setActiveTab(null)
    void loadAgentData(agentId)
  }

  const currentSection = getCurrentSection()

  // Block access until the workflow has been initiated at least once this session
  if (!hasWorkflowRun) {
    return (
      <div className="min-h-screen py-8 flex items-center justify-center">
        <div className="max-w-2xl mx-auto px-8">
          <div className="rounded-3xl p-12 shadow-2xl text-center" style={{ backgroundColor: '#00246B' }}>
            <div className="p-4 rounded-2xl mx-auto w-fit mb-6" style={{ backgroundColor: '#CADCFC' }}>
              <PlayCircle className="w-16 h-16" style={{ color: '#00246B' }} />
            </div>
            <h1 className="text-4xl font-bold mb-4" style={{ color: '#CADCFC' }}>Start the Analysis Workflow</h1>
            <p className="text-lg mb-8" style={{ color: '#CADCFC', opacity: 0.9 }}>
              Run the multi-agent workflow at least once before exploring the agent reports. 
              We only surface these summaries after the workflow kicks off.
            </p>
            <Link
              to="/workflow"
              className="inline-flex items-center gap-3 px-8 py-4 rounded-2xl font-semibold text-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
              style={{ backgroundColor: '#CADCFC', color: '#00246B' }}
            >
              <PlayCircle className="w-6 h-6" />
              Go to Workflow Page
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-8">
        {/* Header */}
        <div className="rounded-3xl p-8 mb-8 shadow-2xl" style={{ backgroundColor: '#00246B' }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl" style={{ backgroundColor: '#CADCFC' }}>
                <FileText className="w-6 h-6" style={{ color: '#00246B' }} />
              </div>
              <h1 className="text-4xl font-bold" style={{ color: '#CADCFC' }}>Agent Analysis Reports</h1>
            </div>
            <button
              onClick={() => setShowJson(!showJson)}
              className="px-6 py-2.5 rounded-xl transition-all flex items-center gap-2 font-semibold shadow-lg border"
              style={{ backgroundColor: '#CADCFC', color: '#00246B', borderColor: '#CADCFC' }}
            >
              <Eye className="h-5 w-5" />
              {showJson ? 'Hide' : 'Show'} JSON
            </button>
          </div>
        </div>

        {/* Agent Selection Tabs */}
        <div className="flex gap-3 mb-6">
          {agentTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleAgentChange(tab.id)}
              className="flex items-center gap-2 px-8 py-3.5 font-semibold rounded-2xl transition-all shadow-lg border"
              style={
                activeAgent === tab.id
                  ? { backgroundColor: '#00246B', color: '#CADCFC', borderColor: '#00246B' }
                  : { backgroundColor: 'white', color: '#00246B', borderColor: '#00246B' }
              }
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Section Tabs */}
        <div className="mb-6 overflow-x-auto">
          <div className="flex gap-2 pb-2">
            {getTabsForAgent().map((tab: { id: string; label: string }) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className="px-6 py-2.5 font-medium whitespace-nowrap rounded-xl transition-all shadow-lg border"
                style={
                  activeTab === tab.id
                    ? { backgroundColor: '#00246B', color: '#CADCFC', borderColor: '#00246B' }
                    : { backgroundColor: 'white', color: '#00246B', borderColor: '#00246B' }
                }
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content Area */}
        {!activeAgent && (
          <div className="rounded-3xl border-2 border-dashed p-12 text-center shadow-inner" style={{ borderColor: '#00246B' }}>
            <h2 className="text-2xl font-semibold mb-2" style={{ color: '#00246B' }}>Select an agent to view its report</h2>
            <p style={{ color: '#00246B', opacity: 0.7 }}>Choose any agent above to load the latest findings from the packaged data files.</p>
          </div>
        )}

        {loadError && activeAgent && !loadingAgent && (
          <div className="rounded-3xl border-2 p-6 text-center shadow-inner" style={{ borderColor: '#B91C1C', backgroundColor: '#FEE2E2' }}>
            <p className="font-semibold mb-2" style={{ color: '#B91C1C' }}>{loadError}</p>
            <p className="text-sm" style={{ color: '#7F1D1D' }}>Please try selecting the agent again.</p>
          </div>
        )}

        {loadingAgent && (
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-3xl border border-blue-500 p-12 shadow-2xl text-center">
            <div className="animate-spin-slow inline-block mb-4">
              <Activity className="w-12 h-12 text-white" />
            </div>
            <p className="text-white text-lg">Loading {agentTabs.find(tab => tab.id === loadingAgent)?.label} report...</p>
          </div>
        )}

        {currentSection && !loadingAgent ? (
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

            {/* Footer */}
            <div className="text-center py-6 text-sm" style={{ color: '#00246B' }}>
              <p>GMR Airports Ltd (GMRAIRPORT.NS) • Multi-Agent Analysis Platform</p>
              <p className="mt-1">Generated: November 15, 2025 • Data Source: NSE</p>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}

export default AgentsPage
