import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import WorkflowPage from './pages/WorkflowPage/WorkflowPage'
import AgentsPage from './pages/AgentsPage/AgentsPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/workflow" replace />} />
        <Route path="/workflow" element={<WorkflowPage />} />
        <Route path="/agents" element={<AgentsPage />} />
      </Routes>
    </Layout>
  )
}

export default App
