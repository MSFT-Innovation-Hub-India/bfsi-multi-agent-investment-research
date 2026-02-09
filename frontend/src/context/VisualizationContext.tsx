import { createContext, useContext, useState, ReactNode, useEffect } from 'react'

interface VisualizationContextType {
  isVisualizationStarted: boolean
  setVisualizationStarted: (started: boolean) => void
  hasWorkflowRun: boolean
  markWorkflowRun: () => void
}

const VisualizationContext = createContext<VisualizationContextType | undefined>(undefined)

export function VisualizationProvider({ children }: { children: ReactNode }) {
  const [isVisualizationStarted, setIsVisualizationStarted] = useState<boolean>(() => {
    // Check localStorage on initial load
    const stored = localStorage.getItem('visualizationStarted')
    return stored === 'true'
  })
  const [hasWorkflowRun, setHasWorkflowRun] = useState<boolean>(() => {
    const stored = sessionStorage.getItem('hasWorkflowRun')
    return stored === 'true'
  })

  const setVisualizationStarted = (started: boolean) => {
    setIsVisualizationStarted(started)
    localStorage.setItem('visualizationStarted', String(started))
  }

  const markWorkflowRun = () => {
    setHasWorkflowRun(true)
    sessionStorage.setItem('hasWorkflowRun', 'true')
  }

  // Reset visualization state on page refresh/close (optional)
  useEffect(() => {
    const handleBeforeUnload = () => {
      // Optionally reset on page close - uncomment if needed
      // localStorage.removeItem('visualizationStarted')
      // sessionStorage.removeItem('hasWorkflowRun')
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [])

  return (
    <VisualizationContext.Provider value={{ isVisualizationStarted, setVisualizationStarted, hasWorkflowRun, markWorkflowRun }}>
      {children}
    </VisualizationContext.Provider>
  )
}

export function useVisualization() {
  const context = useContext(VisualizationContext)
  if (context === undefined) {
    throw new Error('useVisualization must be used within a VisualizationProvider')
  }
  return context
}
