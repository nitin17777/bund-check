import * as React from "react";
import { cn } from "@/lib/utils";

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
  headingLevel?: "h2" | "h3";
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
  headingLevel: Component = "h2",
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center p-8 rounded-lg border border-border-subtle bg-surface-card/40 my-4",
        className
      )}
    >
      {icon && (
        <div className="mb-4 rounded-full bg-surface-overlay p-4 border border-border-subtle text-text-secondary">
          {icon}
        </div>
      )}
      <Component className="text-base font-semibold text-text-primary tracking-tight">
        {title}
      </Component>
      <p className="text-sm text-text-secondary max-w-sm mt-1.5 leading-relaxed">
        {description}
      </p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
