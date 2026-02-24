import { Link, useLocation } from 'react-router-dom'
import { Activity, Zap, FileText, History } from 'lucide-react'

function Header() {
  const location = useLocation()

  const isActive = (path: string) => location.pathname === path

  return (
    <header className="backdrop-blur-sm border-b sticky top-0 z-50 shadow-lg" style={{ backgroundColor: '#00246B', borderBottomColor: '#00246B' }}>
      <div className="container mx-auto px-8">
        <div className="flex items-center justify-between h-20">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl shadow-md" style={{ backgroundColor: '#CADCFC' }}>
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold" style={{ color: '#CADCFC' }}>Corporate Investment Risk Analysis</h1>
              <p className="text-sm" style={{ color: '#CADCFC', opacity: 0.9 }}>Multi-Agent Orchestration</p>
            </div>
          </div>
          <nav className="flex gap-3">
            <Link
              to="/workflow"
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl transition-all font-semibold shadow-lg"
              style={isActive('/workflow') 
                ? { backgroundColor: '#CADCFC', color: '#00246B' }
                : { backgroundColor: 'transparent', color: '#CADCFC', border: '2px solid #CADCFC' }
              }
            >
              <Zap className="w-4 h-4" />
              Workflow
            </Link>
            <Link
              to="/agents"
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl transition-all font-semibold shadow-lg"
              style={isActive('/agents') 
                ? { backgroundColor: '#CADCFC', color: '#00246B' }
                : { backgroundColor: 'transparent', color: '#CADCFC', border: '2px solid #CADCFC' }
              }
            >
              <FileText className="w-4 h-4" />
              Agent Reports
            </Link>
            <Link
              to="/history"
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl transition-all font-semibold shadow-lg"
              style={isActive('/history') 
                ? { backgroundColor: '#CADCFC', color: '#00246B' }
                : { backgroundColor: 'transparent', color: '#CADCFC', border: '2px solid #CADCFC' }
              }
            >
              <History className="w-4 h-4" />
              Workflow History
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}

export default Header
