import { clsx } from "clsx";
import type { ReactNode } from "react";

const variants = {
  success: "bg-green-100 text-green-800",
  warning: "bg-amber-100 text-amber-800",
  danger: "bg-red-100 text-red-800",
  info: "bg-blue-100 text-blue-800",
  neutral: "bg-gray-100 text-gray-700",
} as const;

interface BadgeProps {
  variant?: keyof typeof variants;
  children: ReactNode;
  className?: string;
}

export function Badge({ variant = "neutral", children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, keyof typeof variants> = {
    healthy: "success",
    up: "success",
    completed: "success",
    merged: "success",
    resolved: "success",
    closed: "neutral",
    running: "info",
    in_progress: "info",
    open: "info",
    pending: "warning",
    degraded: "warning",
    reopened: "warning",
    failed: "danger",
    unhealthy: "danger",
    down: "danger",
  };
  return <Badge variant={map[status] || "neutral"}>{status}</Badge>;
}
