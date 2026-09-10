"use client";

import { CopyButton } from "@/components/site/copy-button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const CLI = `llmscribe --path /path/to/your/project

# Save to a specific place
llmscribe --path ~/Documents/my-app --output ~/Desktop/my-app.txt

# Only the folder tree (no file contents)
llmscribe --path ~/Documents/my-app --tree-only

# Open the graphical folder picker
llmscribe --gui`;

const CUI = `LLMScribe CUI
1) Enter project folder path
2) Open GUI folder picker
3) Quit
Choose an option [1-3]:`;

export function Interfaces() {
  return (
    <section id="interfaces" className="scroll-mt-20 border-t border-border">
      <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">
          Three interfaces
        </p>
        <h2 className="display mt-3 max-w-2xl text-3xl sm:text-4xl">
          A desktop window, a terminal menu, and a scriptable CLI.
        </h2>
        <p className="mt-4 max-w-xl text-muted">
          Install once. Use whichever fits the moment — recommended GUI for most people, CLI when
          you already know the path, CUI if you prefer a numbered menu.
        </p>

        <Tabs defaultValue="gui" className="mt-10">
          <TabsList className="w-full max-w-md sm:w-auto">
            <TabsTrigger value="gui" className="flex-1 sm:flex-none">
              GUI
            </TabsTrigger>
            <TabsTrigger value="cli" className="flex-1 sm:flex-none">
              CLI
            </TabsTrigger>
            <TabsTrigger value="cui" className="flex-1 sm:flex-none">
              CUI
            </TabsTrigger>
          </TabsList>

          <TabsContent value="gui">
            <InterfaceCard
              title="llmscribe-gui"
              blurb="A window appears. Choose a folder, optionally rename the output, tick Tree only if you only want structure, then Generate. When it finishes you can Copy the text or Open the saved file."
              command="llmscribe-gui"
              extra="Also: llmscribe --gui  ·  python -m llmscribe.gui"
            />
          </TabsContent>

          <TabsContent value="cli">
            <InterfaceCard
              title="llmscribe"
              blurb="Fastest once you know the path. Default output is project_overview.txt in the folder where you ran the command."
              command={CLI}
              extra="Requires Python 3.10 or newer. Tkinter is not needed for CLI mode."
            />
          </TabsContent>

          <TabsContent value="cui">
            <InterfaceCard
              title="llmscribe-cui"
              blurb="A simple numbered menu in the terminal. Type 1 and paste a path, or type 2 to open the same graphical folder picker used by the desktop app."
              command={CUI}
            />
          </TabsContent>
        </Tabs>
      </div>
    </section>
  );
}

function InterfaceCard({
  title,
  blurb,
  command,
  extra,
}: {
  title: string;
  blurb: string;
  command: string;
  extra?: string;
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-border bg-surface">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border px-5 py-4">
        <div>
          <p className="font-mono text-sm text-primary">{title}</p>
          <p className="mt-1 max-w-2xl text-sm text-muted">{blurb}</p>
          {extra ? <p className="mt-2 font-mono text-xs text-subtle">{extra}</p> : null}
        </div>
        <CopyButton text={command} />
      </div>
      <pre className="overflow-x-auto p-5 font-mono text-sm leading-relaxed text-fg/90">
        {command}
      </pre>
    </div>
  );
}
