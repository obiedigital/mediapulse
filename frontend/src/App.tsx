import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import { AuthProvider, useAuth } from "./lib/auth"
import { Layout } from "./components/Layout"
import { Login } from "./pages/Login"
import { Overview } from "./pages/Overview"
import { StoryFeed } from "./pages/StoryFeed"
import { StoryDetail } from "./pages/StoryDetail"
import { ShareOfVoice } from "./pages/ShareOfVoice"
import { Briefs } from "./pages/Briefs"
import { Admin } from "./pages/Admin"

function ProtectedLayout() {
  const { user, loading } = useAuth()
  if (loading) {
    return <div className="flex min-h-screen items-center justify-center text-ink-muted">Loading…</div>
  }
  if (!user) return <Navigate to="/login" replace />
  return <Layout />
}

function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  if (user?.role !== "admin" && user?.role !== "platform_admin") {
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedLayout />}>
            <Route path="/" element={<Overview />} />
            <Route path="/feed" element={<StoryFeed />} />
            <Route path="/feed/:id" element={<StoryDetail />} />
            <Route path="/share-of-voice" element={<ShareOfVoice />} />
            <Route path="/briefs" element={<Briefs />} />
            <Route
              path="/admin"
              element={
                <RequireAdmin>
                  <Admin />
                </RequireAdmin>
              }
            />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
