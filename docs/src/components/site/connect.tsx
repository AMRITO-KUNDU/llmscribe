import { CopyButton } from "@/components/site/copy-button";
import { CONNECT } from "@/lib/site";

const LOCAL = `{
  "mcpServers": {
    "llmscribe": {
      "command": "llmscribe-mcp"
    }
  }
}`;

export function Connect() {
  return (
    <section id="connect" className="scroll-mt-20 border-t border-border">
      <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">Connect</p>
        <h2 className="display mt-3 max-w-2xl text-3xl sm:text-4xl">
          Add LLMScribe to the app you already use.
        </h2>
        <p className="mt-4 max-w-2xl text-muted">
          LLMScribe is a standard MCP server that runs locally over{" "}
          <span className="text-fg">stdio</span> — no cloud, no network. Install it once with pip,
          then point your client at the command below.
        </p>

        <div className="mt-10 max-w-2xl overflow-hidden rounded-xl border border-border bg-surface">
          <div className="flex items-start justify-between gap-3 border-b border-border px-5 py-4">
            <div>
              <p className="font-mono text-xs tracking-widest text-primary uppercase">Local</p>
              <p className="mt-1 text-sm text-fg">stdio — runs on your machine</p>
              <p className="mt-2 max-w-md text-sm text-muted">
                Everything stays local. Your code is never uploaded and no network access is used.
              </p>
            </div>
            <CopyButton text={LOCAL} />
          </div>
          <pre className="overflow-x-auto px-5 py-4 font-mono text-sm leading-relaxed text-fg/90">
            {LOCAL}
          </pre>
          <p className="border-t border-border px-5 py-3 font-mono text-xs text-subtle">
            pip install llmscribe
          </p>
        </div>

        <div className="mt-16">
          <h3 className="text-lg font-medium">Per-app setup</h3>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Each client reads a different configuration file. Copy the block for your tool. Verified
            against each tool's official documentation.
          </p>

          <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {CONNECT.map((item) => (
              <div
                key={item.app}
                className="flex flex-col overflow-hidden rounded-xl border border-border bg-surface"
              >
                <div className="flex items-start justify-between gap-3 border-b border-border px-4 py-3">
                  <div className="min-w-0">
                    <p className="font-mono text-sm text-primary">{item.app}</p>
                    <p className="mt-1 text-xs text-subtle">{item.where}</p>
                  </div>
                  <CopyButton text={item.config} />
                </div>
                <pre className="overflow-x-auto px-4 py-3 font-mono text-xs leading-relaxed text-fg/90">
                  {item.config}
                </pre>
                {item.note ? (
                  <p className="mt-auto border-t border-border px-4 py-3 text-xs text-muted">
                    {item.note}
                  </p>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
