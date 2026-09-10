const STEPS = [
  {
    n: "01",
    title: "Point it at a folder",
    body: "Pass a path on the command line, pick a folder in the desktop window, or type it into the terminal menu. That is the only input.",
  },
  {
    n: "02",
    title: "It walks, filters, and writes",
    body: "LLMScribe builds a directory tree, skips junk and .gitignore matches, and concatenates every supported source file into one document.",
  },
  {
    n: "03",
    title: "Paste it into an AI chat",
    body: "The .txt is ready for ChatGPT, Claude, Grok, Cursor, or anything else that can read a project as text. Copy, open, or save it wherever you like.",
  },
];

export function HowItWorks() {
  return (
    <section id="how" className="scroll-mt-20 border-t border-border">
      <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">How it works</p>
        <h2 className="display mt-3 max-w-xl text-3xl sm:text-4xl">
          One walk through the tree. One file out.
        </h2>

        <ol className="mt-12 grid gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-3">
          {STEPS.map((step) => (
            <li key={step.n} className="bg-bg p-6 sm:p-8">
              <p className="font-mono text-xs text-primary">{step.n}</p>
              <h3 className="mt-4 text-lg font-medium">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{step.body}</p>
            </li>
          ))}
        </ol>

        <blockquote className="mt-14 max-w-2xl">
          <p className="display text-2xl italic text-fg sm:text-3xl">
            Made for people who just want to give their whole project to an AI without fighting
            with copy-paste.
          </p>
        </blockquote>
      </div>
    </section>
  );
}
