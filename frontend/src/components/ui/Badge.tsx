import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?:
    | "default"
    | "secondary"
    | "outline"
    | "info"
    | "success"
    | "warning"
    | "critical";
}

export function Badge({
  className,
  variant = "default",
  children,
  ...props
}: BadgeProps) {
  const variantStyles = {
    default: "bg-surface-active text-text-primary border-border",
    secondary: "bg-surface-card text-text-secondary border-border-subtle",
    outline: "border-border text-text-secondary bg-transparent",
    info: "bg-semantic-info-subtle text-semantic-info border-semantic-info/20",
    success: "bg-semantic-success-subtle text-semantic-success border-semantic-success/20",
    warning: "bg-semantic-warning-subtle text-semantic-warning border-semantic-warning/20",
    critical: "bg-semantic-critical-subtle text-semantic-critical border-semantic-critical/20",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors",
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
