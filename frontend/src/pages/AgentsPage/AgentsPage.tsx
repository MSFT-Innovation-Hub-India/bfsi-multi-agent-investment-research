import { useState, useEffect } from 'react'
import { 
  TrendingUp, 
  Building, 
  Shield,
  Eye,
  FileText,
  BarChart3,
  Activity
} from 'lucide-react'

function AgentsPage() {
  const [activeAgent, setActiveAgent] = useState('stock')
  const [activeTab, setActiveTab] = useState('executive_summary')
  const [showJson, setShowJson] = useState(false)
  
  // State for loaded JSON data
  const [stockData, setStockData] = useState<any>(null)
  const [investmentData, setInvestmentData] = useState<any>(null)
  const [complianceData, setComplianceData] = useState<any>(null)

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

  useEffect(() => {
    // Load all JSON files
    fetch('/data/stock_report.json')
      .then(r => r.json())
      .then(data => {
        console.log('Loaded stock data:', data)
        setStockData(data)
        // Set first tab if stock is active agent
        if (activeAgent === 'stock' && data.sections && data.sections.length > 0) {
          setActiveTab(data.sections[0].id)
        }
      })
      .catch(err => console.error('Error loading stock data:', err))

    fetch('/data/company_analysis_output.json')
      .then(r => r.json())
      .then(data => {
        console.log('Loaded investment data:', data)
        setInvestmentData(data)
        // Set first tab if investment is active agent
        if (activeAgent === 'investment' && data.sections && data.sections.length > 0) {
          setActiveTab(data.sections[0].id)
        }
      })
      .catch(err => console.error('Error loading investment data:', err))

    fetch('/data/compliance_findings.json')
      .then(r => r.json())
      .then(data => {
        // Merge with recommendation
        fetch('/data/compliance_recommendation.json')
          .then(r2 => r2.json())
          .then(rec => {
            const merged = { ...data, ...rec }
            console.log('Loaded compliance data:', merged)
            setComplianceData(merged)
          })
          .catch(() => setComplianceData(data))
      })
      .catch(err => console.error('Error loading compliance data:', err))
  }, [])

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
    if (activeAgent === 'stock' && stockData?.sections) {
      const section = stockData.sections.find((s: any) => s.id === activeTab)
      console.log('Current stock section:', section)
      return section
    }
    if (activeAgent === 'investment' && investmentData?.sections) {
      const section = investmentData.sections.find((s: any) => s.id === activeTab)
      console.log('Current investment section:', section)
      // Map 'images' array to 'image' if needed
      if (section && section.images && section.images.length > 0) {
        return { ...section, image: section.images[0] }
      }
      return section
    }
    if (activeAgent === 'compliance' && complianceData) {
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
    setActiveAgent(agentId)
    // Set first tab for new agent
    if (agentId === 'stock' && stockData?.sections?.[0]) {
      setActiveTab(stockData.sections[0].id)
    } else if (agentId === 'investment' && investmentData?.sections?.[0]) {
      setActiveTab(investmentData.sections[0].id)
    } else if (agentId === 'compliance') {
      setActiveTab('section_1')
    }
  }

  const currentSection = getCurrentSection()

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-8">
        <div className="rounded-3xl p-8 mb-8 shadow-2xl bg-[#00246B]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-[#CADCFC]">
                <FileText className="w-6 h-6 text-[#00246B]" />
              </div>
              <h1 className="text-4xl font-bold text-[#CADCFC]">Agent Analysis Reports</h1>
            </div>
            <button
              onClick={() => setShowJson(!showJson)}
              className="px-6 py-2.5 rounded-xl transition-all flex items-center gap-2 font-semibold shadow-lg border bg-[#CADCFC] text-[#00246B] border-[#CADCFC]"
            >
              <Eye className="h-5 w-5" />
              {showJson ? 'Hide' : 'Show'} JSON
            </button>
          </div>
        </div>

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

        {currentSection ? (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="rounded-3xl border shadow-2xl flex flex-col bg-white border-[#00246B]" style={{ maxHeight: 'calc(100vh - 400px)' }}>
                <div className="p-8 pb-4">
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-xl bg-[#00246B]">
                      <BarChart3 className="w-6 h-6 text-[#CADCFC]" />
                    </div>
                    <div>
                      <h2 className="text-3xl font-bold mb-2 text-[#00246B]">{currentSection.name}</h2>
                      <p className="text-[#00246B] opacity-70">Detailed analysis and insights</p>
                    </div>
                  </div>
                </div>
                
                <div className="px-8 pb-8 overflow-y-auto flex-1">
                  <div className="prose prose-invert prose-lg max-w-none">
                    {renderContent(currentSection.summary || currentSection.analysis)}
                  </div>

                  {currentSection.points && (
                    <ul className="list-disc list-inside space-y-2 mt-6 text-[#00246B]">
                      {currentSection.points.map((point: string, idx: number) => (
                        <li key={idx}>{point}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>


              {currentSection.image ? (
                <div className="rounded-3xl border shadow-2xl flex flex-col bg-white border-[#00246B]" style={{ maxHeight: 'calc(100vh - 400px)' }}>
                  <div className="p-8 pb-4">
                    <h3 className="text-xl font-semibold mb-6 flex items-center gap-2 text-[#00246B]">
                      <Eye className="w-5 h-5 text-[#00246B]" />
                      Visualization
                    </h3>
                  </div>
                  <div className="px-8 pb-8 overflow-y-auto flex-1">
                    <div className="bg-blue-800/30 rounded-2xl p-4 border border-blue-500">
                      <img
                        src={`/images/${currentSection.image}`}
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


            {showJson && (
              <div className="rounded-3xl border p-8 shadow-2xl bg-white border-[#00246B]">
                <h3 className="text-xl font-semibold mb-4 text-[#00246B]">Raw JSON Data</h3>
                <pre className="p-6 rounded-2xl overflow-x-auto text-sm max-h-96 overflow-y-auto border bg-[#CADCFC] text-[#00246B] border-[#00246B]">
                  {JSON.stringify(currentSection, null, 2)}
                </pre>
              </div>
            )}

            <div className="text-center py-6 text-sm text-[#00246B]">
              <p>GMR Airports Ltd (GMRAIRPORT.NS) • Multi-Agent Analysis Platform</p>
              <p className="mt-1">Generated: November 15, 2025 • Data Source: NSE</p>
            </div>
          </div>
        ) : (
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-3xl border border-blue-500 p-12 shadow-2xl text-center">
            <div className="animate-spin-slow inline-block mb-4">
              <Activity className="w-12 h-12 text-white" />
            </div>
            <p className="text-white text-lg">Loading analysis data...</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default AgentsPage
