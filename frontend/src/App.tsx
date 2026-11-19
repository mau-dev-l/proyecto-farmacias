import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { InventoryPage } from './pages/InventoryPage'
import { MedicinesPage } from './pages/MedicinesPage'
import { EntryPage } from './pages/EntryPage'
import { SalePage } from './pages/SalePage'
import { KardexPage } from './pages/KardexPage'
import { AlertsPage } from './pages/AlertsPage'
import { ReportsPage } from './pages/ReportsPage'
import { TelegramPage } from './pages/TelegramPage'
import { AdminPage } from './pages/AdminPage'
import { Layout } from './components/Layout'

function ProtectedRoutes() {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/inventario" element={<InventoryPage />} />
        <Route path="/medicamentos" element={<MedicinesPage />} />
        <Route path="/movimientos" element={<Navigate to="/movimientos/entrada" replace />} />
        <Route path="/movimientos/entrada" element={<EntryPage />} />
        <Route path="/movimientos/salida" element={<SalePage />} />
        <Route path="/kardex" element={<KardexPage />} />
        <Route path="/alertas" element={<AlertsPage />} />
        <Route path="/telegram" element={<TelegramPage />} />
        {user.role === 'ADMIN' && <Route path="/reportes" element={<ReportsPage />} />}
        {user.role === 'ADMIN' && <Route path="/admin" element={<AdminPage />} />}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}

export function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={<ProtectedRoutes />} />
      </Routes>
    </AuthProvider>
  )
}
