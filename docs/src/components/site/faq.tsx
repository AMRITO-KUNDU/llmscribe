import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { SITE } from "@/lib/site";

const ITEMS = [
  {
    q: "How do I connect LLMScribe to Cursor, Claude, or another MCP client?",
    a: (
      <>
        Run the server locally with <code>llmscribe-mcp</code> and add it to your client's config —
        for example <code>mcpServers</code> in Cursor or Claude Desktop, <code>servers</code> in VS
        Code, or <code>context_servers</code> in Zed. Or point any remote-capable client at the
        hosted endpoint <code>https://llmscribe.onrender.com/mcp</code>. Step-by-step setup for 13
        popular clients is in the{" "}
        <a
          className="text-primary underline underline-offset-4 hover:no-underline"
          href="#connect"
        >
          Connect section
        </a>{" "}
        above. Your agent then gains access to all 7 project tools.
      </>
    ),
  },
  {
    q: "Can non-technical users run the GUI without installing Python?",
    a: (
      <>
        Yes. Download LLMScribe-GUI.exe from the{" "}
        <a
          className="text-primary underline underline-offset-4 hover:no-underline"
          href={SITE.releases}
          target="_blank"
          rel="noreferrer"
        >
          latest GitHub Release
        </a>
        . It is a self-contained ~29 MB binary that runs directly on Windows without requiring Python
        or pip.
      </>
    ),
  },
  {
    q: "What tools are included in the MCP server?",
    a: "7 tools: project_map, project_overview, search, read, read_many (batch read, 50-file limit), project_dependencies, and project_diff (git status & diffs).",
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
