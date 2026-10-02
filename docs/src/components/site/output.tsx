"use client";

import { useState } from "react";
import { CopyButton } from "@/components/site/copy-button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { SAMPLE_FULL, SAMPLE_JSON } from "@/lib/site";

export function Output() {
  const [activeTab, setActiveTab] = useState<"markdown" | "json">("markdown");
  const content = activeTab === "markdown" ? SAMPLE_FULL : SAMPLE_JSON;

  return (
    <section id="output" className="scroll-mt-20 border-t border-border">
      <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="font-mono text-xs tracking-widest text-primary uppercase">
              Output formats
            </p>
            <h2 className="display mt-3 text-3xl sm:text-4xl">
              Clean Markdown for humans, structured JSON for agents.
            </h2>
            <p className="mt-3 max-w-xl text-muted">
              Choose Markdown mode for pasting into chat prompts, or JSON mode for programmatic
              agent parsing with metadata.
            </p>
          </div>

          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "markdown" | "json")}>
            <TabsList>
              <TabsTrigger value="markdown">Markdown Export</TabsTrigger>
              <TabsTrigger value="json">Structured JSON Envelope</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <div className="mt-8 overflow-hidden rounded-xl border border-border bg-surface">
          <div className="flex items-center justify-between border-b border-border px-5 py-3">
            <span className="font-mono text-xs text-muted">
              {activeTab === "markdown" ? "project_overview.txt" : "project_overview (format=json)"}
            </span>
            <CopyButton text={content} />
          </div>
          <pre className="max-h-[480px] overflow-auto p-5 font-mono text-xs leading-relaxed text-fg/90 sm:text-sm">
            {content}
          </pre>
        </div>
      </div>
    </section>
  );
}
