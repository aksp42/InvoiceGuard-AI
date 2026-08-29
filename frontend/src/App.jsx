import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Sidebar from './components/Sidebar.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import UploadInvoices from './pages/UploadInvoices.jsx'
import InvoiceDetails from './pages/InvoiceDetails.jsx'
import HighRisk from './pages/HighRisk.jsx'
import DuplicateInvoices from './pages/DuplicateInvoices.jsx'
import Reports from './pages/Reports.jsx'
import Settings from './pages/Settings.jsx'

function ProtectedLayout() {
  if (!localStorage.getItem('token')) return <Navigate to="/login" replace />
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Navbar />
        <main style={{ padding: 24, flex: 1 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<UploadInvoices />} />
            <Route path="/invoices/:id" element={<InvoiceDetails />} />
            <Route path="/high-risk" element={<HighRisk />} />
            <Route path="/duplicates" element={<DuplicateInvoices />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/*" element={<ProtectedLayout />} />
      </Routes>
    </BrowserRouter>
  )
}