import { clsx } from "clsx";
import type { ReactNode } from "react";

export function Table({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={clsx("overflow-x-auto", className)}>
      <table className="w-full text-sm">{children}</table>
    </div>
  );
}

export function Thead({ children }: { children: ReactNode }) {
  return (
    <thead className="border-b border-border bg-surface-secondary">
      {children}
    </thead>
  );
}

export function Th({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <th
      className={clsx(
        "px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-secondary",
        className
      )}
    >
      {children}
    </th>
  );
}

export function Td({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <td
      className={clsx("px-4 py-3 text-text-primary", className)}
    >
      {children}
    </td>
  );
}

export function Tr({
  children,
  className,
  onClick,
}: {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}) {
  return (
    <tr
      className={clsx(
        "border-b border-border last:border-0",
        onClick && "cursor-pointer hover:bg-surface-hover",
        className
      )}
      onClick={onClick}
    >
      {children}
    </tr>
  );
}
