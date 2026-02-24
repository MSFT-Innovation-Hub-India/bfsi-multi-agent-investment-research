import { useState, useEffect } from 'react'
import { 
  TrendingUp, 
  Building, 
  Shield, 
  ArrowDown,
  ArrowRight,
  ArrowLeft,
  CheckCircle, 
  Clock,
  PlayCircle,
  RotateCcw,
  Zap,
  Eye,
  Activity
} from 'lucide-react'
import { useVisualization } from '../../context/VisualizationContext'
import { fetchBlobJson, API_BASE_URL } from '../../config/appConfig'

interface AgentCardProps {
  name: string
  icon: React.ReactNode
  status: 'pending' | 'processing' | 'completed'
  description: string
  output?: string
  metrics?: { label: string; value: string; color: string }[]
  tasks?: string[]
}

function AgentCard({ name, icon, status, description, output, metrics, tasks }: AgentCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div 
      className="relative rounded-2xl border-2 transition-all duration-500 transform"
      style={{
        backgroundColor: 'white',
        borderColor: status === 'completed' ? '#126125' : status === 'processing' ? '#00246B' : '#CADCFC',
        opacity: status === 'pending' ? 0.6 : 1,
        transform: status === 'processing' ? 'scale(1.05)' : 'scale(1)',
        boxShadow: status === 'completed' ? '0 0 30px rgba(18, 97, 37, 0.4)' : status === 'processing' ? '0 0 30px rgba(0, 36, 107, 0.4)' : 'none'
      }}
    >
      {/* Animated Border Glow */}
      {status === 'processing' && (
        <div className="absolute inset-0 rounded-2xl bg-blue-500 opacity-20 blur-xl animate-pulse z-0" />
      )}

      {/* Status Indicator */}
      <div className="absolute -top-3 -right-3 z-20">
        {status === 'completed' && (
          <div className="rounded-full p-2 shadow-lg" style={{ backgroundColor: '#126125' }}>
            <CheckCircle className="h-5 w-5 text-white" />
          </div>
        )}
        {status === 'processing' && (
          <div className="bg-blue-500 text-white rounded-full p-2 shadow-lg animate-spin-slow">
            <Clock className="h-5 w-5" />
          </div>
        )}
        {status === 'pending' && (
          <div className="rounded-full p-2 shadow-lg" style={{ backgroundColor: '#9ca3af' }}>
            <Clock className="h-5 w-5 text-white" />
          </div>
        )}
      </div>

      <div className="relative p-6 z-10">
        {/* Header */}
        <div className="flex items-start gap-4 mb-4">
          {/* Icon */}
          <div 
            className="w-16 h-16 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{
              backgroundColor: status === 'completed' ? '#126125' : status === 'processing' ? '#00246B' : '#9ca3af',
              animation: status === 'processing' ? 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' : 'none'
            }}
          >
            {icon}
          </div>

          {/* Content */}
          <div className="flex-1">
            <h3 className="font-bold text-xl mb-1" style={{ color: '#00246B' }}>{name}</h3>
            <p className="text-sm mb-3" style={{ color: '#00246B', opacity: 0.8 }}>{description}</p>
            
            {/* Tasks */}
            {tasks && (
              <div className="flex flex-wrap gap-2 mb-3">
                {tasks.map((task, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium border"
                    style={{ backgroundColor: '#00246B', color: '#CADCFC', borderColor: '#00246B' }}
                  >
                    <CheckCircle className="h-3 w-3" />
                    {task}
                  </span>
                ))}
              </div>
            )}
            
            {/* Status Badge */}
            <div 
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border"
              style={{
                backgroundColor: status === 'completed' ? '#126125' : status === 'processing' ? '#00246B' : '#9ca3af',
                color: status === 'completed' ? 'white' : status === 'processing' ? '#CADCFC' : 'white',
                borderColor: status === 'completed' ? '#126125' : status === 'processing' ? '#00246B' : '#9ca3af'
              }}
            >
              {status === 'completed' && '✓ Analysis Complete'}
              {status === 'processing' && '⟳ Processing...'}
              {status === 'pending' && '⏸ Pending'}
            </div>
          </div>
        </div>

        {/* Output */}
        {output && status === 'completed' && (
          <div className="mt-4">
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-2 text-sm font-medium transition-colors"
              style={{ color: '#00246B' }}
            >
              <Eye className="h-4 w-4" />
              {expanded ? 'Hide Details' : 'Show Details'}
            </button>
            {expanded && (
              <div className="mt-3 p-5 rounded-xl border-2 text-sm leading-relaxed shadow-lg" style={{ backgroundColor: '#00246B', color: '#CADCFC', borderColor: '#CADCFC' }}>
                <div className="mb-4 pb-2 border-b" style={{ borderBottomColor: '#CADCFC', opacity: 0.5 }}>
                  <span className="text-xs font-semibold uppercase tracking-wider">Analysis Output</span>
                </div>
                
                {/* Metrics Grid inside details */}
                {metrics && (
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    {metrics.map((metric, idx) => (
                      <div 
                        key={idx}
                        className="rounded-xl p-4 border-2 shadow-md"
                        style={{ backgroundColor: '#CADCFC', borderColor: '#CADCFC' }}
                      >
                        <div className="text-xs mb-1 font-medium uppercase tracking-wide" style={{ color: '#00246B', opacity: 0.6 }}>{metric.label}</div>
                        <div className="text-xl font-bold" style={{ color: '#00246B' }}>{metric.value}</div>
                      </div>
                    ))}
                  </div>
                )}
                
                {output}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function WorkflowPage() {
  const { setVisualizationStarted, markWorkflowRun } = useVisualization()
  const [isRunning, setIsRunning] = useState(false)
  const [currentStage, setCurrentStage] = useState(0)
  const [completedStages, setCompletedStages] = useState<Set<number>>(new Set())
  const [workflowMetrics, setWorkflowMetrics] = useState<any>(null)
  const [_analysisId, setAnalysisId] = useState<string | null>(null)
  const [eventSource, setEventSource] = useState<EventSource | null>(null)
  const [progressLogs, setProgressLogs] = useState<Array<{timestamp: string, message: string, agent?: string, type: string}>>([])
  const [agentStates, setAgentStates] = useState<{[key: string]: 'pending' | 'processing' | 'completed'}>({
    'Stock Analyst': 'pending',
    'Company Analyst': 'pending',
    'Compliance Evaluator': 'pending'
  })
  const [showLogs, setShowLogs] = useState(false)

  useEffect(() => {
    // Load extracted workflow metrics from configured source (Azure Blob API or local)
    fetchBlobJson('workflow_metrics.json')
      .then(data => {
        console.log('Loaded workflow metrics:', data)
        setWorkflowMetrics(data)
      })
      .catch(err => {
        console.error('Error loading workflow metrics:', err)
        // Fallback to loading individual files if workflow_metrics.json doesn't exist
        console.log('Falling back to individual JSON files...')
        // You can add fallback logic here if needed
      })
  }, [])

  // Get agents data from workflow metrics
  const agents = (workflowMetrics?.agents || [
    {
      id: 'stock_analyst',
      name: 'Stock Analyst',
      description: 'Analyzing 30-day stock performance, volatility, and liquidity metrics',
      output: 'Loading stock analysis...',
      metrics: []
    },
    {
      id: 'investment_analyst',
      name: 'Company Analyst',
      description: 'Evaluating financial performance, debt ratios, and growth projections',
      output: 'Loading investment analysis...',
      metrics: []
    },
    {
      id: 'compliance_evaluator',
      name: 'Compliance Evaluator',
      description: 'Verifying trading classification and regulatory compliance',
      output: 'Loading compliance evaluation...',
      metrics: []
    }
  ]).map((agent: any, idx: number) => ({
    ...agent,
    icon: idx === 0 ? <TrendingUp className="h-8 w-8" /> : idx === 1 ? <Building className="h-8 w-8" /> : <Shield className="h-8 w-8" />
  }));

  const startWorkflow = async () => {
    setIsRunning(true)
    setVisualizationStarted(true)  // Mark visualization as started
    markWorkflowRun()
    setCurrentStage(0)
    setCompletedStages(new Set())
    setProgressLogs([])
    setAgentStates({
      'Stock Analyst': 'pending',
      'Company Analyst': 'pending',
      'Compliance Evaluator': 'pending'
    })
    
    try {
      // Trigger analysis via REST API
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      const data = await response.json()
      setAnalysisId(data.analysis_id)
      
      // Connect to SSE stream for real-time progress
      const es = new EventSource(`${API_BASE_URL}${data.stream_url}`)
      setEventSource(es)
      
      // Handle SSE messages
      es.onmessage = (e: MessageEvent) => {
        const event = JSON.parse(e.data)
        console.log('SSE Event:', event)
        setProgressLogs(prev => [...prev, event])
        
        // When GroupChat multi-agent discussion starts, trigger the workflow animation
        if (event.type === 'agent_running' && 
            event.agent === 'GroupChat' && 
            event.message.includes('Starting multi-agent discussion')) {
          console.log('🎬 GroupChat discussion started - triggering workflow animation')
          
          // Start workflow animation with delays
          setTimeout(() => {
            console.log('Stock Analyst -> processing')
            setAgentStates(prev => ({ ...prev, 'Stock Analyst': 'processing' }))
            setCurrentStage(0)
          }, 5000) // 5 seconds
          
          setTimeout(() => {
            console.log('Stock Analyst -> completed')
            setAgentStates(prev => ({ ...prev, 'Stock Analyst': 'completed' }))
            setCompletedStages(prev => new Set([...prev, 0]))
            
            console.log('Company Analyst -> processing')
            setAgentStates(prev => ({ ...prev, 'Company Analyst': 'processing' }))
            setCurrentStage(1)
          }, 20000) // 20 seconds (15 + 5)
          
          setTimeout(() => {
            console.log('Company Analyst -> completed')
            setAgentStates(prev => ({ ...prev, 'Company Analyst': 'completed' }))
            setCompletedStages(prev => new Set([...prev, 0, 1]))
            
            console.log('Compliance Evaluator -> processing')
            setAgentStates(prev => ({ ...prev, 'Compliance Evaluator': 'processing' }))
            setCurrentStage(2)
          }, 35000) // 35 seconds (25 + 10)
          
          setTimeout(() => {
            console.log('Compliance Evaluator -> completed')
            setAgentStates(prev => ({ ...prev, 'Compliance Evaluator': 'completed' }))
            setCompletedStages(prev => new Set([...prev, 0, 1, 2]))
          }, 50000) // 50 seconds (35 + 15)
        }
        
        if (event.type === 'complete') {
          console.log('Analysis complete!')
          setIsRunning(false)
          es.close()
        }
      }
      
      es.onerror = () => {
        console.error('EventSource connection error')
        setIsRunning(false)
        es.close()
      }
      
    } catch (error) {
      console.error('Failed to start analysis:', error)
      setIsRunning(false)
    }
  }

  const resetWorkflow = () => {
    if (eventSource) {
      eventSource.close()
      setEventSource(null)
    }
    setIsRunning(false)
    setCurrentStage(0)
    setCompletedStages(new Set())
    setAnalysisId(null)
    setProgressLogs([])
    setAgentStates({
      'Stock Analyst': 'pending',
      'Company Analyst': 'pending',
      'Compliance Evaluator': 'pending'
    })
  }
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close()
      }
    }
  }, [eventSource])

  const getAgentStatus = (index: number): 'pending' | 'processing' | 'completed' => {
    const agentName = agents[index]?.name
    if (agentName && agentStates[agentName]) {
      const state = agentStates[agentName]
      console.log(`getAgentStatus(${index}): ${agentName} -> ${state}`)
      return state // Direct return: 'pending' | 'processing' | 'completed'
    }
    return 'pending'
  }

  const progress = (completedStages.size / agents.length) * 100

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-8">
        {/* Progress Section */}
        <div className="rounded-2xl p-6 shadow-lg mb-8" style={{ backgroundColor: 'white', border: '2px solid #00246B' }}>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold" style={{ color: '#00246B' }}>GMR Airports Investment Analysis</h2>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowLogs(!showLogs)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all border-2"
                style={{ 
                  backgroundColor: showLogs ? '#00246B' : 'white',
                  color: showLogs ? '#CADCFC' : '#00246B',
                  borderColor: '#00246B'
                }}
              >
                <Activity className="h-4 w-4" />
                {showLogs ? 'Hide Logs' : 'View Logs'}
                {!showLogs && progressLogs.length > 0 && <span className="ml-1 px-2 py-0.5 rounded-full text-xs" style={{ backgroundColor: '#00246B', color: '#CADCFC' }}>{progressLogs.length}</span>}
              </button>
              {!isRunning && completedStages.size === 0 && (
                <button
                  onClick={startWorkflow}
                  className="group flex items-center gap-3 bg-slate-600 text-white px-6 py-3 rounded-xl font-semibold shadow-lg hover:shadow-2xl hover:scale-105 transition-all duration-300"
                >
                  <PlayCircle className="h-5 w-5" />
                  Start Analysis
                </button>
              )}

              {isRunning && progress < 100 && (
                <button
                  onClick={resetWorkflow}
                  className="flex items-center gap-3 bg-red-500/20 backdrop-blur-sm text-red-700 border-2 border-red-400 px-6 py-3 rounded-xl font-semibold hover:bg-red-500/30 transition-all duration-300"
                >
                  <RotateCcw className="h-5 w-5" />
                  Reset
                </button>
              )}
            </div>
          </div>
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 rounded-lg" style={{ backgroundColor: '#00246B' }}>
              <Zap className="h-6 w-6" style={{ color: '#CADCFC' }} />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <span className="text-lg font-semibold" style={{ color: '#00246B' }}>GMR Airports - Analysis Progress</span>
                <span className="text-2xl font-bold" style={{ color: '#00246B' }}>{Math.round(progress)}%</span>
              </div>
              <div className="w-full rounded-full h-4 overflow-hidden" style={{ backgroundColor: '#CADCFC' }}>
                <div 
                  className="h-4 rounded-full transition-all duration-500 relative overflow-hidden"
                  style={{ backgroundColor: '#00246B', width: `${progress}%` }}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse" />
                </div>
              </div>
            </div>
          </div>
          
          {/* Legend */}
          <div className="flex items-center gap-6 text-sm" style={{ color: '#00246B' }}>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#9ca3af' }} />
              <span>Pending</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse" />
              <span>Processing</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#126125' }} />
              <span>Completed</span>
            </div>
          </div>
        </div>

        {/* Workflow Visualization - Tiled Layout with Arrows */}
        <div className="relative">
          {/* Timeline connector line */}
          <div className="absolute left-1/2 top-0 bottom-0 w-1 -translate-x-1/2 hidden lg:block">
            {agents.map((_agent: any, index: number) => {
              const segmentHeight = index === agents.length - 1 ? '50%' : `${100 / agents.length}%`;
              const topPosition = `${(100 / agents.length) * index}%`;
              
              let backgroundColor = '#d1d5db'; // grey for pending
              
              if (completedStages.has(index)) {
                backgroundColor = '#126125'; // dark green for completed
              } else if (currentStage === index && isRunning) {
                backgroundColor = '#3b82f6'; // blue for processing
              }
              
              return (
                <div 
                  key={index}
                  className="transition-all duration-500"
                  style={{ 
                    height: segmentHeight,
                    top: topPosition,
                    backgroundColor: backgroundColor,
                    position: 'absolute',
                    width: '100%'
                  }}
                />
              );
            })}
          </div>

          {/* Agent tiles */}
          <div className="space-y-12 relative">
            {agents.map((agent: any, index: number) => (
              <div key={agent.name || agent.id} className="relative">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                  {/* Left side - odd indexes, Right side - even indexes for desktop */}
                  <div className={`lg:col-span-5 ${index % 2 === 0 ? 'lg:order-1' : 'lg:order-3'}`}>
                    <AgentCard
                      name={agent.name}
                      icon={agent.icon}
                      status={getAgentStatus(index)}
                      description={agent.description}
                      output={agent.output}
                      metrics={agent.metrics}
                    />
                  </div>

                  {/* Center - Timeline dot and arrow */}
                  <div className={`lg:col-span-2 flex justify-center items-center ${index % 2 === 0 ? 'lg:order-2' : 'lg:order-2'} hidden lg:flex`}>
                    <div className="relative flex items-center">
                      {/* Timeline dot */}
                      <div 
                        className="w-6 h-6 rounded-full border-4 z-10 transition-all duration-500"
                        style={{
                          backgroundColor: completedStages.has(index) ? '#126125' : currentStage === index ? '#3b82f6' : 'white',
                          borderColor: completedStages.has(index) ? '#126125' : currentStage === index ? '#3b82f6' : '#d1d5db',
                          boxShadow: completedStages.has(index) ? '0 0 15px rgba(18, 97, 37, 0.5)' : currentStage === index ? '0 0 15px rgba(59, 130, 246, 0.5)' : 'none',
                          animation: currentStage === index ? 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' : 'none'
                        }}
                      />
                      
                      {/* Horizontal arrow pointing to card */}
                      <div className={`absolute ${index % 2 === 0 ? 'right-6' : 'left-6'} flex items-center`}>
                        <div 
                          className="h-0.5 w-16 transition-all duration-500"
                          style={{
                            backgroundColor: completedStages.has(index) ? '#126125' : currentStage === index ? '#3b82f6' : '#d1d5db'
                          }}
                        />
                        <div 
                          className="transition-all duration-500"
                          style={{
                            color: completedStages.has(index) ? '#126125' : currentStage === index ? '#3b82f6' : '#d1d5db'
                          }}
                        >
                          {index % 2 === 0 ? (
                            <ArrowRight className="h-6 w-6" strokeWidth={2.5} />
                          ) : (
                            <ArrowLeft className="h-6 w-6" strokeWidth={2.5} />
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Empty space for alternating layout */}
                  <div className={`lg:col-span-5 ${index % 2 === 0 ? 'lg:order-3' : 'lg:order-1'} hidden lg:block`} />
                </div>

                {/* Mobile vertical arrow */}
                {index < agents.length - 1 && (
                  <div className="lg:hidden flex justify-center my-6">
                    <div 
                      className="transition-all duration-500"
                      style={{
                        color: completedStages.has(index) ? '#126125' : currentStage === index ? '#3b82f6' : '#d1d5db'
                      }}
                    >
                      <ArrowDown className="h-10 w-10" strokeWidth={2.5} />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Real-time Progress Log */}
        {showLogs && (
          <div className="mt-8 rounded-2xl p-6 shadow-lg border" style={{ backgroundColor: 'white', borderColor: '#00246B' }}>
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2" style={{ color: '#00246B' }}>
              <Activity className="h-5 w-5" />
              Live Progress Feed
            </h3>
            {progressLogs.length === 0 ? (
              <div className="text-center py-8" style={{ color: '#00246B', opacity: 0.6 }}>
                <p>No logs yet. Start an analysis to see real-time progress.</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
              {progressLogs.map((log, idx) => (
                <div 
                  key={idx} 
                  className="p-3 rounded-lg border-l-4 transition-all"
                  style={{
                    backgroundColor: '#CADCFC',
                    borderLeftColor: log.type === 'agent_completed' ? '#126125' : 
                                    log.type === 'agent_running' ? '#00246B' : 
                                    log.type === 'error' ? '#dc2626' : '#9ca3af'
                  }}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xs font-mono opacity-70" style={{ color: '#00246B' }}>
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    {log.agent && (
                      <span className="text-xs font-semibold px-2 py-1 rounded" style={{ backgroundColor: '#00246B', color: '#CADCFC' }}>
                        {log.agent}
                      </span>
                    )}
                    <span className="text-sm flex-1" style={{ color: '#00246B' }}>
                      {log.message}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            )}
          </div>
        )}

        {/* Completion Message */}
        {completedStages.size === agents.length && !isRunning && (
          <div className="mt-8 bg-gradient-to-br from-green-900/30 to-emerald-900/30 backdrop-blur-sm rounded-2xl shadow-2xl p-8 border border-green-500/50">
            <div className="flex items-center gap-6">
              <div className="bg-gradient-to-br from-green-500 to-emerald-600 text-white rounded-full p-4 shadow-lg">
                <CheckCircle className="h-10 w-10" />
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-white mb-2">
                  🎉 Analysis Complete!
                </h3>
                <p className="text-green-100 text-lg">
                  All agents have successfully completed their analysis. Navigate to the <span className="font-semibold text-white">Agents</span> page to explore detailed reports and visualizations.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        {workflowMetrics && (
          <div className="mt-12 text-center text-slate-400 text-sm">
            <p>{workflowMetrics.company_name} ({workflowMetrics.symbol}) • Multi-Agent Analysis Platform</p>
            <p className="mt-1">Generated: {new Date(workflowMetrics.generated_at || Date.now()).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })} • Data Source: NSE</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default WorkflowPage
