"use client";

import { CopyButton } from "@/components/site/copy-button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const MCP_CONFIG = `{
  "mcpServers": {
    "llmscribe": {
      "command": "llmscribe-mcp"
    }
  }
}`;

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

const EXE_BUILD = `# Build standalone LLMScribe-GUI.exe from source using PyInstaller:
pip install pyinstaller
python build_exe.py

# Output binary placed at dist/LLMScribe-GUI.exe`;

export function Interfaces() {
  return (
    <section id="interfaces" className="scroll-mt-20 border-t border-border">
      <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">
          Four interfaces
        </p>
        <h2 className="display mt-3 max-w-2xl text-3xl sm:text-4xl">
          An MCP server for agents, a standalone EXE, a desktop GUI, and a CLI.
        </h2>
        <p className="mt-4 max-w-xl text-muted">
          Install once. Use whichever fits the situation — MCP server for AI agents, standalone EXE for non-tech users, recommended Python GUI for desktop users, CLI for terminal power users.
        </p>

        <Tabs defaultValue="mcp" className="mt-10">
          <TabsList className="w-full max-w-2xl sm:w-auto grid grid-cols-2 sm:grid-cols-4">
            <TabsTrigger value="mcp">MCP Server</TabsTrigger>
            <TabsTrigger value="exe">Standalone EXE</TabsTrigger>
            <TabsTrigger value="gui">Desktop GUI</TabsTrigger>

            <TabsTrigger value="cli">CLI / CUI</TabsTrigger>
          </TabsList>

          <TabsContent value="mcp">
            <InterfaceCard
              title="llmscribe-mcp (For AI Agents)"
              blurb="Model Context Protocol (MCP) server providing 7 tools for AI coding tools (Cursor, Claude Desktop, Windsurf, Roo Code, Goose)."
              command={MCP_CONFIG}
              extra="Provides project_overview, project_map, project_search, project_list_files, project_get_file, project_get_files, and project_diff."
            />
          </TabsContent>

          <TabsContent value="exe">
            <InterfaceCard
              title="LLMScribe-GUI.exe (No Python Required)"
              blurb="Single-file standalone Windows executable for non-technical users. Download from GitHub Releases and double-click to launch immediately."
              command={EXE_BUILD}
              extra="Bundles Python, CustomTkinter, and dependencies into a self-contained ~29 MB binary."
            />
          </TabsContent>

          <TabsContent value="gui">
            <InterfaceCard
              title="llmscribe-gui"
              blurb="Modern CustomTkinter desktop window. Choose a folder, toggle Tree only, and click Generate to preview, copy, or open saved files."
              command="llmscribe-gui"
              extra="Also: llmscribe --gui  ·  python -m llmscribe.gui"
            />
          </TabsContent>

          <TabsContent value="cli">
            <InterfaceCard
              title="llmscribe & llmscribe-cui"
              blurb="CLI for fast scriptable export, and CUI for interactive numbered menu choice in the terminal."
              command={CLI}
              extra="Interactive CUI available via llmscribe-cui"
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
