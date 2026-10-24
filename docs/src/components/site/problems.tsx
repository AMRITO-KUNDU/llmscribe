const QUOTES = [
  {
    quote: "Every time it explores like 200 files for a small change.",
    who: "Google Antigravity user",
  },
  {
    quote: "Nine searches and fourteen files for one variable — the search itself isn't ranked.",
    who: "Cursor user",
  },
  {
    quote: "I asked it what it was doing. It said it was looking at unnecessary files.",
    who: "Cursor user",
  },
  {
    quote: "It randomly proceeds to re-read the same files over and over again.",
    who: "Google Antigravity user",
  },
  {
    quote:
      "Stale fixtures, mock data, outdated comments — it wastes tokens and makes me argue with my agent non stop.",
    who: "Claude Code user",
  },
  {
    quote: "Search reports no matches, then a plain grep finds the content immediately.",
    who: "Claude Code Grep bug report",
  },
];

const ANSWERS = [
  {
    problem: "Reads 200 files to change one line",
    answer: "project_map returns the whole tree with contents excluded, before a single file is read.",
  },
  {
    problem: "Re-reads the same files in a loop",
    answer: "Output is deterministic. Same input, same bytes, every run.",
  },
  {
    problem: "Misses the file that actually mattered",
    answer:
      "project_dependencies resolves local, stdlib, external and unresolved imports — plus reverse dependencies.",
  },
  {
    problem: "Search returns nothing when the text exists",
    answer:
      "search returns path, line, matched text and match type, or a stable error code. Never a silent empty.",
  },
  {
    problem: "Stale fixtures read as current truth",
    answer: "Nothing is inferred, embedded or ranked. You get the files as they are, plus a Git diff.",
  },
  {
    problem: "Build output and binaries fill the context",
    answer: "Real .gitignore semantics. Binaries and oversized files are skipped, not summarised.",
  },
  {
    problem: "Context gets silently truncated",
    answer: "Every cut is reported: truncated, truncation_note, omitted_files.",
  },
];

export function Problems() {
  return (
    <section id="problem" className="scroll-mt-20 border-t border-border">
      <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">The problem</p>
        <h2 className="display mt-3 max-w-2xl text-3xl sm:text-4xl">
          Your agent does not have an intelligence problem.
        </h2>
        <p className="mt-5 max-w-2xl leading-relaxed text-muted">
          It has a retrieval problem. On a 1.4-million-line codebase, one benchmark agent burned
          6,000 seconds and produced nothing; the same model with structured code search finished the
          same task in 89 seconds. Across another benchmark, Codex CLI never reached the file that
          would have solved the task in <span className="text-fg">27–29% of runs</span> — and once it
          had the right context, its score nearly doubled. The bottleneck is what goes into the
          window, not how clever the model is.
        </p>

        <div className="mt-12 grid gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-2 lg:grid-cols-3">
          {QUOTES.map((item) => (
            <figure key={item.quote} className="bg-bg p-6">
              <blockquote className="text-sm leading-relaxed text-fg">“{item.quote}”</blockquote>
              <figcaption className="mt-3 font-mono text-xs text-subtle">{item.who}</figcaption>
            </figure>
          ))}
        </div>

        <h3 className="display mt-16 max-w-xl text-2xl sm:text-3xl">
          What LLMScribe does about it
        </h3>
        <div className="mt-8 overflow-hidden rounded-xl border border-border">
          {ANSWERS.map((row, i) => (
            <div
              key={row.problem}
              className={
                "grid gap-2 p-5 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)] sm:gap-8 " +
                (i % 2 === 1 ? "bg-surface" : "bg-bg")
              }
            >
              <p className="text-sm font-medium text-fg">{row.problem}</p>
              <p className="text-sm leading-relaxed text-muted">{row.answer}</p>
            </div>
          ))}
        </div>

        <p className="mt-8 max-w-2xl text-sm leading-relaxed text-muted">
          The file an agent needs next is usually the one structurally related to the file it is
          already looking at — a dependent, a sibling module, a test fixture. That is a graph
          question, not a similarity question, which is why LLMScribe ships dependency analysis and
          a real tree instead of embeddings.
        </p>
      </div>
    </section>
  );
}
