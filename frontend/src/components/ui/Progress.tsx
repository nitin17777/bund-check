import * as React from "react";
import { cn } from "@/lib/utils";

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number;
  max?: number;
  variant?: "default" | "success" | "warning" | "critical";
}

export function Progress({
  value,
  max = 100,
  variant = "default",
  className,
  ...props
}: ProgressProps) {
  const isIndeterminate = value === undefined;
  const percentage = isIndeterminate ? 100 : Math.min(Math.max((value / max) * 100, 0), 100);

  const fillVariants = {
    default: "bg-accent",
    success: "bg-semantic-success",
    warning: "bg-semantic-warning",
    critical: "bg-semantic-critical",
  };

  return (
    <div
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={isIndeterminate ? undefined : value}
      className={cn(
        "relative h-2 w-full overflow-hidden rounded-full bg-surface-base border border-border-subtle",
        className
      )}
      {...props}
    >
      <div
        className={cn(
          "h-full rounded-full transition-all duration-300 ease-out",
          fillVariants[variant],
          isIndeterminate && "animate-pulse"
        )}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}
