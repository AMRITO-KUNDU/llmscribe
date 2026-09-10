import { ArrowDown, Github } from "lucide-react";
import { CopyButton } from "@/components/site/copy-button";
import { GuiMock } from "@/components/site/gui-mock";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SITE } from "@/lib/site";

export function Hero() {
  return (
    <section className="paper-wash relative overflow-hidden">
      <div className="mx-auto grid max-w-6xl gap-12 px-5 py-16 sm:px-8 sm:py-20 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)] lg:items-center lg:gap-10 lg:py-24">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge>v{SITE.version} on PyPI</Badge>
            <Badge variant="outline">Python {SITE.python}</Badge>
            <Badge variant="outline">Apache 2.0</Badge>
          </div>

          <h1 className="display mt-6 max-w-xl text-4xl text-fg sm:text-5xl lg:text-6xl">
            Give any project to an AI in one file.
          </h1>

          <p className="mt-5 max-w-md text-base leading-relaxed text-muted sm:text-lg">
            {SITE.tagline} No configuration. Windows, macOS, and Linux.
          </p>

          <div className="mt-8 flex max-w-md items-center gap-2 rounded-lg border border-border bg-surface p-1.5 pl-4">
            <code className="min-w-0 flex-1 truncate font-mono text-sm text-primary">
              {SITE.install}
            </code>
            <CopyButton text={SITE.install} label="Copy" />
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Button size="lg" asChild>
              <a href="#install">Get started</a>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <a href={SITE.github} target="_blank" rel="noreferrer">
                <Github />
                View source
              </a>
            </Button>
          </div>

          <p className="mt-6 text-sm text-subtle">
            Three commands:{" "}
            <code className="font-mono text-muted">llmscribe</code>,{" "}
            <code className="font-mono text-muted">llmscribe-gui</code>,{" "}
            <code className="font-mono text-muted">llmscribe-cui</code>
          </p>
        </div>

        <div>
          <GuiMock />
          <p className="mt-3 flex items-center gap-2 text-xs text-subtle">
            <ArrowDown className="size-3.5" />
            Interactive demo — Generate, copy, or download a sample export.
          </p>
        </div>
      </div>
    </section>
  );
}
