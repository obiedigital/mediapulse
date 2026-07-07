import { NavLink, Outlet } from "react-router-dom"
import { useAuth } from "../lib/auth"

const NAV_ITEMS = [
  { to: "/", label: "Overview", end: true },
  { to: "/feed", label: "Story Feed" },
  { to: "/share-of-voice", label: "Share of Voice" },
  { to: "/briefs", label: "Daily Brief" },
]

export function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-60 shrink-0 flex-col border-r border-gridline bg-surface-card">
        <div className="flex items-center gap-2 px-5 py-5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-sm font-bold text-black">
            MP
          </span>
          <span className="text-sm font-semibold tracking-tight">MediaPulse BW</span>
        </div>
        <nav className="flex flex-col gap-0.5 px-3">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-brand/10 text-brand"
                    : "text-ink-secondary hover:bg-gridline/40 hover:text-ink-primary"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
          {(user?.role === "admin" || user?.role === "platform_admin") && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-brand/10 text-brand"
                    : "text-ink-secondary hover:bg-gridline/40 hover:text-ink-primary"
                }`
              }
            >
              Admin
            </NavLink>
          )}
        </nav>
        <div className="mt-auto border-t border-gridline p-4">
          <div className="text-sm font-medium">{user?.name}</div>
          <div className="text-xs text-ink-muted capitalize">{user?.role.replace("_", " ")}</div>
          <button
            onClick={logout}
            className="mt-3 text-xs font-medium text-ink-secondary underline underline-offset-2 hover:text-ink-primary"
          >
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl px-8 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
