import { NavLink } from "react-router-dom";
import { clsx } from "clsx";
import { useAuth } from "@/context/AuthContext";
import {
  LayoutDashboard,
  Search,
  GitBranch,
  Network,
  GitPullRequest,
  Bug,
  UserCircle,
  Workflow,
  Calendar,
  HeartPulse,
  ChevronLeft,
  ChevronRight,
  Zap,
} from "lucide-react";
import { useState } from "react";

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  { to: "/", label: "Dashboard", icon: <LayoutDashboard size={20} /> },
  { to: "/search", label: "Search", icon: <Search size={20} /> },
  { to: "/features", label: "Features", icon: <GitBranch size={20} /> },
  { to: "/graph", label: "Graph Explorer", icon: <Network size={20} /> },
  { to: "/pull-requests", label: "PR Intelligence", icon: <GitPullRequest size={20} /> },
  { to: "/forensics", label: "Defect Forensics", icon: <Bug size={20} /> },
  { to: "/profile", label: "Developer Profile", icon: <UserCircle size={20} /> },
];

const adminItems: NavItem[] = [
  { to: "/admin/workflows", label: "Workflows", icon: <Workflow size={20} />, adminOnly: true },
  { to: "/admin/schedules", label: "Schedules", icon: <Calendar size={20} />, adminOnly: true },
  { to: "/admin/health", label: "System Health", icon: <HeartPulse size={20} />, adminOnly: true },
];

export function Sidebar() {
  const { isAdmin } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={clsx(
        "flex h-screen flex-col border-r border-border bg-surface transition-all duration-200",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-border px-4">
        <Zap size={24} className="shrink-0 text-primary-600" />
        {!collapsed && (
          <span className="text-base font-bold text-text-primary truncate">
            Eng Intelligence
          </span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-1">
        {navItems.map((item) => (
          <SidebarLink key={item.to} item={item} collapsed={collapsed} />
        ))}

        {isAdmin && (
          <>
            <div className="my-3 border-t border-border" />
            {!collapsed && (
              <p className="px-3 pb-1 text-[10px] font-bold uppercase tracking-widest text-text-muted">
                Admin
              </p>
            )}
            {adminItems.map((item) => (
              <SidebarLink key={item.to} item={item} collapsed={collapsed} />
            ))}
          </>
        )}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex h-12 items-center justify-center border-t border-border text-text-muted hover:text-text-primary"
      >
        {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
      </button>
    </aside>
  );
}

function SidebarLink({
  item,
  collapsed,
}: {
  item: NavItem;
  collapsed: boolean;
}) {
  return (
    <NavLink
      to={item.to}
      end={item.to === "/"}
      className={({ isActive }) =>
        clsx(
          "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
          isActive
            ? "bg-primary-50 text-primary-700"
            : "text-text-secondary hover:bg-surface-hover hover:text-text-primary"
        )
      }
      title={collapsed ? item.label : undefined}
    >
      <span className="shrink-0">{item.icon}</span>
      {!collapsed && <span className="truncate">{item.label}</span>}
    </NavLink>
  );
}
