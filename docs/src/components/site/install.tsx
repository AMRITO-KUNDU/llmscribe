import { CopyButton } from "@/components/site/copy-button";
import { SITE } from "@/lib/site";

const SOURCE = `git clone https://github.com/AMRITO-KUNDU/LLMScribe.git
cd LLMScribe
pip install -e .`;

const BUILD_EXE = `# Build standalone LLMScribe-GUI.exe:
pip install pyinstaller
python build_exe.py`;

export function Install() {
  return (
    <section id="install" className="scroll-mt-20 border-t border-border">
      <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">Install</p>
        <h2 className="display mt-3 text-3xl sm:text-4xl">Available on PyPI or Standalone EXE.</h2>
        <p className="mt-4 max-w-xl text-muted">
          Install from PyPI using Python {SITE.python}, or download the pre-compiled
          LLMScribe-GUI.exe from GitHub Releases.
        </p>

        <div className="mt-10 overflow-hidden rounded-xl border border-border bg-surface">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-3">
            <span className="font-mono text-xs text-muted">From PyPI</span>
            <CopyButton text={SITE.install} />
          </div>
          <pre className="overflow-x-auto p-5 font-mono text-lg text-primary sm:text-xl">
            {SITE.install}
          </pre>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <CodePanel title="From source" code={SOURCE} />
          <CodePanel
            title="Build Standalone EXE"
            code={BUILD_EXE}
            note="Generates dist/LLMScribe-GUI.exe (PyInstaller executable for non-tech users)."
          />
        </div>

        <dl className="mt-10 grid gap-6 sm:grid-cols-4">
          <Fact term="llmscribe-mcp" def="MCP server for Cursor, Claude, and other MCP clients." />
          <Fact term="LLMScribe-GUI.exe" def="Standalone desktop app for local project exports." />
          <Fact term="llmscribe" def="CLI for map, overview, search, read, diff, and dependency checks." />
          <Fact term="pip install llmscribe[gui]" def="Optional GUI extras for desktop support." />
        </dl>
      </div>
    </section>
  );
}

function CodePanel({ title, code, note }: { title: string; code: string; note?: string }) {
  return (
    <div className="overflow-hidden rounded-xl border border-border bg-surface">
      <div className="flex items-center justify-between gap-3 border-b border-border px-5 py-3">
        <span className="font-mono text-xs text-muted">{title}</span>
        <CopyButton text={code} />
      </div>
      <pre className="overflow-x-auto p-5 font-mono text-sm leading-relaxed text-fg/90">{code}</pre>
      {note ? <p className="border-t border-border px-5 py-3 text-xs text-subtle">{note}</p> : null}
    </div>
  );
}

function Fact({ term, def }: { term: string; def: string }) {
  return (
    <div className="rounded-xl border border-border bg-bg p-5">
      <dt className="font-mono text-sm text-primary">{term}</dt>
      <dd className="mt-2 text-sm text-muted">{def}</dd>
    </div>
  );
}
