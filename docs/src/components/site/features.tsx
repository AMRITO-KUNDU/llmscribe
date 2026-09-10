import {
  AppWindow,
  FileCode2,
  FolderX,
  Globe2,
  Package,
  TerminalSquare,
} from "lucide-react";
import { EXTENSIONS, IGNORED } from "@/lib/site";

const FEATURES = [
  {
    icon: AppWindow,
    title: "Three ways in",
    body: "A desktop GUI for people who would rather click, a numbered CUI for the terminal, and a full CLI for scripts and muscle memory.",
  },
  {
    icon: FolderX,
    title: "Smart ignore",
    body: "Drops .git, node_modules, venv, caches, IDE folders, OS junk, and anything already listed in the project's own .gitignore.",
  },
  {
    icon: FileCode2,
    title: "Source, not noise",
    body: "Includes common source and text extensions — Python, JavaScript, TypeScript, Go, Rust, Java, Markdown, JSON, YAML, HTML, CSS, shell, and more.",
  },
  {
    icon: TerminalSquare,
    title: "Tree-only mode",
    body: "Need structure without the files? Pass --tree-only, or tick the box in the GUI, and you get the directory tree alone.",
  },
  {
    icon: Package,
    title: "Embeddable core",
    body: "Import llmscribe.core from Python. run() writes a file; build_project_summary() returns the text so you can pipe it elsewhere.",
  },
  {
    icon: Globe2,
    title: "Anywhere Python runs",
    body: "Windows, macOS, and Linux. Python 3.10 or newer. The CLI works even if Tkinter is missing; the GUI needs it on some Linux setups.",
  },
];

export function Features() {
  return (
    <section id="features" className="scroll-mt-20 border-t border-border">
      <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">Capabilities</p>
        <h2 className="display mt-3 max-w-xl text-3xl sm:text-4xl">
          Built to stay out of the way.
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
            <h3 className="text-base font-medium">Included</h3>
            <p className="mt-1 text-sm text-muted">
              Common source and text extensions. Many more than the chips below.
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
                + more
              </li>
            </ul>
          </div>
          <div className="rounded-xl border border-border bg-surface p-6 sm:p-8">
            <h3 className="text-base font-medium">Ignored automatically</h3>
            <p className="mt-1 text-sm text-muted">
              Dependency trees, caches, IDE folders, OS junk, and your .gitignore.
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
