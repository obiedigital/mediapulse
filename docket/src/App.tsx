import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { AppShell } from './components/layout/AppShell';
import { Landing } from './pages/marketing/Landing';
import { Login } from './pages/auth/Login';
import { Dashboard } from './pages/app/Dashboard';
import { DocumentManager } from './pages/app/DocumentManager';
import { SmartScan } from './pages/app/SmartScan';
import { Workflows } from './pages/app/Workflows';
import { ESignature } from './pages/app/ESignature';
import { Reports } from './pages/app/Reports';
import { Settings } from './pages/app/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/app" element={<AppShell />}>
              <Route index element={<Dashboard />} />
              <Route path="documents" element={<DocumentManager />} />
              <Route path="scan" element={<SmartScan />} />
              <Route path="workflows" element={<Workflows />} />
              <Route path="esignature" element={<ESignature />} />
              <Route path="reports" element={<Reports />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
