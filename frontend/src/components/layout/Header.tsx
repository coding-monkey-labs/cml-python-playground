import { useAuth } from "@/context/AuthContext";
import { Badge } from "@/components/ui/Badge";
import { LogOut } from "lucide-react";

export function Header() {
  const { user, isAdmin, logout } = useAuth();

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-surface px-6">
      <div />

      <div className="flex items-center gap-4">
        {user && (
          <>
            <Badge variant={isAdmin ? "info" : "neutral"}>
              {user.role}
            </Badge>
            <span className="text-sm text-text-secondary">{user.full_name}</span>
            <button
              onClick={logout}
              className="flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm text-text-secondary hover:bg-surface-hover hover:text-text-primary"
              title="Logout"
            >
              <LogOut size={16} />
            </button>
          </>
        )}
      </div>
    </header>
  );
}
