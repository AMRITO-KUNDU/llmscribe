import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const ITEMS = [
  {
    q: "I don’t have a terminal. How do I open one?",
    a: "Windows: Win + R, type cmd or powershell, press Enter. macOS: Cmd + Space, type Terminal, press Enter. Linux: Ctrl + Alt + T on most distributions. Then run llmscribe-gui for the desktop window.",
  },
  {
    q: "The GUI doesn’t open / complains about Tkinter.",
    a: "On some Linux systems you need the system package first: python3-tk on Ubuntu/Debian, python3-tkinter on Fedora, tk on Arch. Command-line mode (llmscribe --path …) works without Tkinter.",
  },
  {
    q: "Where does the file get saved?",
    a: "By default it is saved as project_overview.txt in the folder where you ran the command. Use --output to put it anywhere you like. In the GUI you can change the output path before generating.",
  },
  {
    q: "Which files are included?",
    a: "Any file with a common source or text extension — .py, .js, .ts, .jsx, .tsx, .java, .go, .rs, .md, .json, .yaml, .toml, .html, .css, .sh, and many more. Binary assets and dependency trees are skipped.",
  },
  {
    q: "Does it respect .gitignore?",
    a: "Yes. Anything listed in the project’s own .gitignore is ignored, along with .git, node_modules, venv, __pycache__, dist, build, .idea, .vscode, .DS_Store, and Thumbs.db.",
  },
  {
    q: "Can I export only the folder tree?",
    a: "Yes. Pass --tree-only on the CLI, or tick Tree only in the GUI. You get the directory structure without file contents — useful when the model only needs layout.",
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
