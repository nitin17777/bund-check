import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ShieldCheck, Cpu, HardDrive } from "lucide-react";

export default function SettingsPage() {
  return (
    <AppShell>
      <div className="space-y-6 max-w-4xl">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">System Settings</h1>
          <p className="text-sm text-text-secondary mt-1">
            Execution parameters, LLM provider keys, and privacy configuration.
          </p>
        </div>

        <div className="space-y-6">
          {/* Privacy & Storage Section */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <ShieldCheck className="h-5 w-5 text-semantic-success" />
                  <CardTitle className="text-base font-semibold">Data Privacy & Retention</CardTitle>
                </div>
                <Badge variant="success">Strict Zero-Storage Active</Badge>
              </div>
              <CardDescription>
                Control whether uploaded documents and inspection transcripts are cached or discarded.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-text-secondary">
              <p>
                In compliance with AGENTS.md directives, all incoming files (PDF, DOCX, TXT) are parsed in transient
                memory buffers and deleted immediately upon request completion.
              </p>
              <div className="rounded border border-border-subtle bg-surface-base p-3 text-xs font-mono text-text-muted">
                PERSISTENCE_MODE = EPHEMERAL_IN_MEMORY
              </div>
            </CardContent>
          </Card>

          {/* Compute & Calibration Section */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2.5">
                <Cpu className="h-5 w-5 text-accent" />
                <CardTitle className="text-base font-semibold">Engine Partitioning</CardTitle>
              </div>
              <CardDescription>
                Hardware constraints and local model partition ceilings.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-text-secondary">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div className="rounded border border-border-subtle bg-surface-base p-3">
                  <div className="font-semibold text-text-primary">Local Compute Floor</div>
                  <div className="text-text-muted mt-1">CPU / RTX 2050 (4 GB VRAM ceiling)</div>
                </div>
                <div className="rounded border border-border-subtle bg-surface-base p-3">
                  <div className="font-semibold text-text-primary">Calibration Band</div>
                  <div className="text-text-muted mt-1">Abstain Lower: 0.40 / Upper: 0.60</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* LLM Provider Configuration */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2.5">
                <HardDrive className="h-5 w-5 text-semantic-info" />
                <CardTitle className="text-base font-semibold">Improver LLM Providers</CardTitle>
              </div>
              <CardDescription>
                Provider endpoints for stylistic enhancement (keys read strictly via server-side environment variables).
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-text-secondary">
              <p>
                Supported providers: Groq, OpenRouter, OpenAI, and local quantized small models. Keys are never exposed
                in client-side bundles.
              </p>
              <div className="rounded border border-border-subtle bg-surface-base p-3 font-mono text-text-muted">
                DEFAULT_PROVIDER = &quot;groq&quot; (llama-3.3-70b-versatile)
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
