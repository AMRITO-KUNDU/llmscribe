"use client";

import { useEffect, useRef, useState } from "react";
import { Check, Copy, FolderOpen, Save } from "lucide-react";
import { SAMPLE_FULL, SAMPLE_TREE } from "@/lib/site";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

type Status = "idle" | "scanning" | "done";

function downloadText(filename: string, text: string) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function GuiMock() {
  const [treeOnly, setTreeOnly] = useState(false);
  const [status, setStatus] = useState<Status>("idle");
  const [copied, setCopied] = useState(false);
  const timer = useRef<number | null>(null);

  const output = treeOnly ? SAMPLE_TREE : SAMPLE_FULL;
  const lines = output.trimEnd().split("\n").length;

  useEffect(() => {
    return () => {
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, []);

  function generate() {
    if (timer.current) window.clearTimeout(timer.current);
    setStatus("scanning");
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    timer.current = window.setTimeout(
      () => {
        setStatus("done");
      },
      reduced ? 0 : 720,
    );
  }

  async function copyOutput() {
    if (status !== "done") return;
    try {
      await navigator.clipboard.writeText(output);
      setCopied(true);
      toast.success("Output copied");
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      toast.error("Could not copy");
    }
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-surface shadow-panel">
      <div className="flex h-10 items-center gap-2 border-b border-border bg-elevated px-3">
        <span className="flex gap-1.5" aria-hidden="true">
          <span className="size-2.5 rounded-full bg-border" />
          <span className="size-2.5 rounded-full bg-border" />
          <span className="size-2.5 rounded-full bg-border" />
        </span>
        <p className="flex-1 text-center font-mono text-xs text-muted">LLMScribe</p>
        <span className="font-mono text-xs text-subtle">v1.0.0</span>
      </div>

      <div className="grid md:grid-cols-[220px_minmax(0,1fr)] lg:grid-cols-[240px_minmax(0,1fr)]">
        <aside className="flex flex-col gap-4 border-b border-border p-4 md:border-r md:border-b-0">
          <div>
            <p className="display text-lg leading-none">LLMScribe</p>
            <p className="mt-1 font-mono text-xs text-subtle">v1.0.0</p>
          </div>

          <label className="block">
            <span className="mb-1.5 block font-mono text-xs tracking-wider text-subtle uppercase">
              Project folder
            </span>
            <span className="flex h-10 items-center gap-2 rounded-md border border-border bg-input px-2">
              <span className="min-w-0 flex-1 truncate font-mono text-xs text-fg">
                ~/Documents/my-project
              </span>
              <FolderOpen className="size-3.5 shrink-0 text-muted" />
            </span>
          </label>

          <label className="block">
            <span className="mb-1.5 block font-mono text-xs tracking-wider text-subtle uppercase">
              Output file
            </span>
            <span className="flex h-10 items-center gap-2 rounded-md border border-border bg-input px-2">
              <span className="min-w-0 flex-1 truncate font-mono text-xs text-fg">
                project_overview.txt
              </span>
              <Save className="size-3.5 shrink-0 text-muted" />
            </span>
          </label>

          <label className="flex min-h-11 items-center gap-2 text-sm text-muted">
            <input
              type="checkbox"
              checked={treeOnly}
              onChange={(e) => {
                setTreeOnly(e.target.checked);
                if (status === "done") setStatus("idle");
              }}
              className="size-4 rounded border-border accent-primary"
            />
            Tree only
          </label>

          <button
            type="button"
            onClick={generate}
            className="flex h-11 w-full items-center justify-center rounded-md bg-primary text-sm font-medium text-primary-foreground transition-[opacity,transform] duration-150 hover:opacity-90 active:scale-[0.96]"
          >
            {status === "scanning" ? "Scanning…" : "Generate"}
          </button>

          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={copyOutput}
              disabled={status !== "done"}
              className="flex h-11 items-center justify-center gap-1.5 rounded-md border border-border text-xs font-medium text-fg disabled:opacity-40"
            >
              {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
              {copied ? "Copied" : "Copy"}
            </button>
            <button
              type="button"
              onClick={() => downloadText("project_overview.txt", output)}
              disabled={status !== "done"}
              className="flex h-11 items-center justify-center rounded-md border border-border text-xs font-medium text-fg disabled:opacity-40"
            >
              Open file
            </button>
          </div>

          <p
            className={cn(
              "font-mono text-xs",
              status === "done" ? "text-primary" : "text-subtle",
            )}
          >
            {status === "idle" && "Ready"}
            {status === "scanning" && "Walking project…"}
            {status === "done" && "Saved to project_overview.txt"}
          </p>
        </aside>

        <div className="flex min-h-72 flex-col bg-bg">
          <div className="flex items-center justify-between border-b border-border px-4 py-2">
            <span className="text-xs text-muted">Preview</span>
            <span className="font-mono text-xs tabular-nums text-subtle">
              {status === "done" ? `${lines} lines` : "—"}
            </span>
          </div>
          <div className="min-h-64 flex-1 overflow-auto p-4 sm:p-6">
            {status === "idle" ? (
              <p className="max-w-xs text-sm leading-relaxed text-muted">
                Select a project folder and press Generate. The output will appear here.
              </p>
            ) : null}
            {status === "scanning" ? (
              <p className="font-mono text-sm text-muted">
                Scanning text files · respecting .gitignore
              </p>
            ) : null}
            {status === "done" ? (
              <pre className="font-mono text-xs leading-relaxed text-fg/90 sm:text-sm">
                {output}
              </pre>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
