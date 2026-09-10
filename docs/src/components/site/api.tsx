import { CopyButton } from "@/components/site/copy-button";
import { PYTHON_API } from "@/lib/site";

export function Api() {
  return (
    <section id="api" className="scroll-mt-20 border-t border-border">
      <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24">
        <div className="grid gap-10 lg:grid-cols-2 lg:items-start">
          <div>
            <p className="font-mono text-xs tracking-widest text-primary uppercase">
              Python API
            </p>
            <h2 className="display mt-3 text-3xl sm:text-4xl">
              Use the core from your own code.
            </h2>
            <p className="mt-4 text-muted">
              The same writer the CLI uses is importable. Write a file, or keep the summary as a
              string and send it wherever you need context.
            </p>
          </div>
          <div className="overflow-hidden rounded-xl border border-border bg-surface">
            <div className="flex items-center justify-between border-b border-border px-5 py-3">
              <span className="font-mono text-xs text-muted">llmscribe.core.writer</span>
              <CopyButton text={PYTHON_API} />
            </div>
            <pre className="overflow-x-auto p-5 font-mono text-sm leading-relaxed text-fg/90">
              {PYTHON_API}
            </pre>
          </div>
        </div>
      </div>
    </section>
  );
}
