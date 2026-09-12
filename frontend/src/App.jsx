import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import Dashboard from './pages/Dashboard'
import VesselWorkspace from './pages/VesselWorkspace'
import EnvironmentWorkspace from './pages/EnvironmentWorkspace'
import SarWorkspace from './pages/SarWorkspace'
import History from './pages/History'

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/vessels" element={<VesselWorkspace />} />
        <Route path="/environment" element={<EnvironmentWorkspace />} />
        <Route path="/analyze" element={<SarWorkspace />} />
        <Route path="/history" element={<Navigate to="/" replace />} />
        <Route path="/incidents" element={<Navigate to="/" replace />} />
        <Route path="/analytics" element={<Navigate to="/" replace />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App

