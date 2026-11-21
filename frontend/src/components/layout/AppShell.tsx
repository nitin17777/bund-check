"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  ScanText,
  FileEdit,
  History,
  Settings,
  Menu,
  X,
  ShieldCheck,
  ExternalLink,
  Activity,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";

interface AppShellProps {
  children: React.ReactNode;
}

const NAV_ITEMS = [
  {
    name: "Overview",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Content Checker",
    href: "/checker",
    icon: ScanText,
  },
  {
    name: "Writing Improver",
    href: "/humanizer",
    icon: FileEdit,
  },
  {
    name: "Audit History",
    href: "/history",
    icon: History,
  },
  {
    name: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  // Close mobile drawer on route change
  React.useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  // Handle escape key to close mobile menu
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && mobileMenuOpen) {
        setMobileMenuOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mobileMenuOpen]);

  return (
    <div className="flex min-h-screen bg-background text-text-primary">
      {/* Skip to Content for Accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-accent focus:text-white focus:rounded focus:outline-none"
      >
        Skip to main content
      </a>

      {/* Desktop Sidebar */}
      <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 border-r border-border-subtle bg-surface-base">
        <div className="flex flex-col flex-1 min-h-0">
          {/* Brand header */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-border-subtle">
            <Link
              href="/"
              className="flex items-center gap-2.5 font-semibold text-text-primary tracking-tight group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded"
            >
              <div className="rounded bg-accent p-1.5 text-white transition-transform group-hover:scale-105">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <span className="text-base font-bold">BundCheck</span>
            </Link>
            <Badge variant="outline" className="text-[10px] tracking-wider uppercase font-mono px-1.5 py-0">
              v0.1
            </Badge>
          </div>

          {/* Navigation links */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" aria-label="Sidebar navigation">
            <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-text-muted uppercase">
              Application
            </div>
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                    isActive
                      ? "bg-surface-card text-text-primary font-semibold border border-border-subtle shadow-sm"
                      : "text-text-secondary hover:text-text-primary hover:bg-surface-card/50"
                  )}
                  aria-current={isActive ? "page" : undefined}
                >
                  <Icon className={cn("h-4 w-4", isActive ? "text-accent" : "text-text-muted")} />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Sidebar Footer with System Status */}
          <div className="p-4 border-t border-border-subtle bg-surface-base">
            <div className="flex items-center justify-between text-xs text-text-muted">
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-semantic-success opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-semantic-success"></span>
                </span>
                <span>ML Engine Ready</span>
              </div>
              <span className="font-mono text-[11px]">CPU/RTX</span>
            </div>
            <Link
              href="/"
              className="mt-3 flex items-center justify-between text-xs text-text-secondary hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded px-1 py-0.5"
            >
              <span>Methodology & Ethics</span>
              <ExternalLink className="h-3 w-3 text-text-muted" />
            </Link>
          </div>
        </div>
      </aside>

      {/* Mobile Drawer Backdrop */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/80 md:hidden backdrop-blur-sm transition-opacity"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile Sidebar */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-72 bg-surface-base border-r border-border-subtle p-6 flex flex-col justify-between transition-transform duration-300 ease-in-out md:hidden",
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        )}
        role="dialog"
        aria-modal="true"
        aria-label="Mobile Navigation"
      >
        <div>
          <div className="flex items-center justify-between pb-4 border-b border-border-subtle">
            <Link href="/" className="flex items-center gap-2 font-bold text-text-primary">
              <div className="rounded bg-accent p-1 text-white">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <span>BundCheck</span>
            </Link>
            <button
              onClick={() => setMobileMenuOpen(false)}
              aria-label="Close navigation menu"
              className="p-1 rounded text-text-secondary hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <nav className="mt-6 space-y-1.5" aria-label="Mobile menu">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-md transition-colors",
                    isActive
                      ? "bg-surface-card text-text-primary font-semibold border border-border-subtle"
                      : "text-text-secondary hover:text-text-primary hover:bg-surface-card/40"
                  )}
                  aria-current={isActive ? "page" : undefined}
                >
                  <Icon className={cn("h-4 w-4", isActive ? "text-accent" : "text-text-muted")} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="pt-4 border-t border-border-subtle">
          <p className="text-xs text-text-muted">
            Probabilistic inspection. Verification preserves meaning and protected spans.
          </p>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 md:pl-64">
        {/* Top Header */}
        <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 sm:px-6 md:px-8 border-b border-border-subtle bg-surface-base/90 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open sidebar menu"
              className="p-2 -ml-2 rounded text-text-secondary hover:text-text-primary hover:bg-surface-card md:hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-text-muted">
              <span>BUNDCHECK</span>
              <span>/</span>
              <span className="text-text-secondary uppercase">
                {pathname.replace("/", "") || "home"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 text-xs text-text-muted border border-border-subtle rounded-md px-2.5 py-1 bg-surface-card">
              <Activity className="h-3.5 w-3.5 text-semantic-success" />
              <span>Zero-Storage Mode Active</span>
            </div>
            <Link
              href="/checker"
              className="inline-flex items-center justify-center h-8 px-3 text-xs font-medium rounded bg-accent text-white hover:bg-accent-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              New Inspection
            </Link>
          </div>
        </header>

        {/* Routed Page Content */}
        <main id="main-content" className="flex-1 p-4 sm:p-6 md:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
