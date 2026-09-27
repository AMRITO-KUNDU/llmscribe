import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const ITEMS = [
  {
    q: "How do I connect LLMScribe to Cursor or Claude Desktop?",
    a: "Add LLMScribe to your MCP client config (mcpServers block in Cursor or Claude Desktop) using command 'llmscribe-mcp'. Your AI agent will automatically gain access to all 7 project tools.",
  },
  {
    q: "Can non-technical users run the GUI without installing Python?",
    a: "Yes. Download LLMScribe-GUI.exe from the latest GitHub Release. It is a self-contained ~29 MB binary that runs directly on Windows without requiring Python or pip.",
  },
  {
    q: "What tools are included in the MCP server?",
    a: "7 tools: project_overview, project_map, project_search, project_list_files, project_get_file, project_get_files (batch file fetch with 50-file limit), and project_diff (git status & diffs).",
  },
  {
    q: "Does it support both Markdown and JSON output formats?",
    a: "Yes. All MCP tools support format='markdown' (default) and format='json'. In JSON mode, responses return structured tree/files arrays and metadata (file_count, character_count, match_count, etc.).",
  },
  {
    q: "Does it respect .gitignore?",
    a: "Yes. Anything listed in the project's own .gitignore is ignored automatically, along with .git, node_modules, venv, __pycache__, dist, build, .idea, .vscode, .DS_Store, and Thumbs.db.",
  },
  {
    q: "Can I export only the folder tree structure?",
    a: "Yes. Pass --tree-only on the CLI, tick Tree only in the GUI, or call project_map() via MCP to get the directory layout without file contents.",
  },
];

export function Faq() {
  return (
    <section id="faq" className="scroll-mt-20 border-t border-border">
      <div className="mx-auto max-w-3xl px-5 py-20 sm:px-8 sm:py-24">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">FAQ</p>
        <h2 className="display mt-3 text-3xl sm:text-4xl">Common questions</h2>
        <Accordion type="single" collapsible className="mt-8">
          {ITEMS.map((item, i) => (
            <AccordionItem key={item.q} value={`item-${i}`}>
              <AccordionTrigger>{item.q}</AccordionTrigger>
              <AccordionContent>{item.a}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
