import {
  AppWindow,
  FileCode2,
  FolderX,
  Bot,
  GitBranch,
  ShieldCheck,
} from "lucide-react";
import { EXTENSIONS, IGNORED } from "@/lib/site";

const FEATURES = [
  {
    icon: Bot,
    title: "MCP Server for AI Agents",
    body: "Built-in Model Context Protocol server featuring 7 composable tools (overview, map, search, batch file read, and git diff) with structured JSON envelopes.",
  },
  {
    icon: GitBranch,
    title: "Git Status & Diff",
    body: "Inspect modified files and unified diffs directly via project_diff tool, supporting staged, unstaged, and specific commit comparisons.",
  },
  {
    icon: AppWindow,
    title: "Four Interfaces",
    body: "MCP server for agents, standalone Windows EXE for non-tech users, modern CustomTkinter GUI, and CLI/CUI for terminal power users.",
  },
  {
    icon: FolderX,
    title: "Smart Ignore Rules",
    body: "Drops .git, node_modules, venv, build caches, IDE folders, OS junk, and anything listed in the project's own .gitignore.",
  },
  {
    icon: ShieldCheck,
    title: "Deterministic Size Guards",
    body: "Enforces 50-file batch caps, 400k character content limits, 200k diff character caps, and 13 closed, standardized error codes.",
  },
  {
    icon: FileCode2,
    title: "Embeddable Python Core",
    body: "Import llmscribe.core or llmscribe.mcp from Python. Use run(), build_project_summary(), or project_overview() programmatically.",
  },
];

export function Features() {
  return (
    <section id="features" className="scroll-mt-20 border-t border-border">
      <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">Capabilities</p>
        <h2 className="display mt-3 max-w-xl text-3xl sm:text-4xl">
          Built to give AI agents & developers predictable context.
        </h2>

        <div className="mt-12 grid gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <article key={f.title} className="bg-bg p-6 sm:p-7">
              <f.icon className="size-5 text-primary" strokeWidth={1.6} />
              <h3 className="mt-4 text-base font-medium">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{f.body}</p>
            </article>
          ))}
        </div>

        <div className="mt-12 grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-border bg-surface p-6 sm:p-8">
            <h3 className="text-base font-medium">Supported Text Files</h3>
            <p className="mt-1 text-sm text-muted">
              Common source code, configuration, scripts, and text extensions.
            </p>
            <ul className="mt-5 flex flex-wrap gap-2">
              {EXTENSIONS.map((ext) => (
                <li
                  key={ext}
                  className="rounded-full border border-border bg-bg px-3 py-1 font-mono text-xs text-fg"
                >
                  {ext}
                </li>
              ))}
              <li className="rounded-full border border-border px-3 py-1 font-mono text-xs text-muted">
                + many more
              </li>
            </ul>
          </div>
          <div className="rounded-xl border border-border bg-surface p-6 sm:p-8">
            <h3 className="text-base font-medium">Ignored Automatically</h3>
            <p className="mt-1 text-sm text-muted">
              Dependencies, build outputs, IDE config, binary assets, and your .gitignore.
            </p>
            <ul className="mt-5 flex flex-wrap gap-2">
              {IGNORED.map((item) => (
                <li
                  key={item}
                  className="rounded-full border border-border bg-bg px-3 py-1 font-mono text-xs text-muted"
                >
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
