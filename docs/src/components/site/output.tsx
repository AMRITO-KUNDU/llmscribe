import { CopyButton } from "@/components/site/copy-button";
import { SAMPLE_FULL } from "@/lib/site";

export function Output() {
  return (
    <section id="output" className="scroll-mt-20 border-t border-border">
      <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24">
        <div className="grid gap-10 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:items-start">
          <div>
            <p className="font-mono text-xs tracking-widest text-primary uppercase">
              The output
            </p>
            <h2 className="display mt-3 text-3xl sm:text-4xl">
              A directory tree, then every file, in one document.
            </h2>
            <p className="mt-4 text-muted">
              The export is plain text. No wrappers, no JSON schema, no extra markup — so you can
              paste the whole file straight into an AI chat.
            </p>
            <ul className="mt-6 space-y-3 text-sm text-muted">
              <li className="flex gap-3">
                <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                Tree first, so the model sees structure before contents.
              </li>
              <li className="flex gap-3">
                <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                Each file headed with its path, then the full source.
              </li>
              <li className="flex gap-3">
                <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                Default filename:{" "}
                <code className="font-mono text-fg">project_overview.txt</code>
              </li>
            </ul>
            <div className="mt-6">
              <CopyButton text={SAMPLE_FULL} label="Copy sample" size="default" />
            </div>
          </div>

          <div className="overflow-hidden rounded-xl border border-border bg-surface">
            <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
              <span className="font-mono text-xs text-muted">project_overview.txt</span>
              <span className="font-mono text-xs text-subtle">sample</span>
            </div>
            <pre className="max-h-[28rem] overflow-auto p-5 font-mono text-xs leading-relaxed text-fg/90 sm:text-sm">
              {SAMPLE_FULL}
            </pre>
          </div>
        </div>
      </div>
    </section>
  );
}
