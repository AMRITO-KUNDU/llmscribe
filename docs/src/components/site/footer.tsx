import { CopyButton } from "@/components/site/copy-button";
import { Wordmark } from "@/components/site/logo";
import { Button } from "@/components/ui/button";
import { SITE } from "@/lib/site";

export function FinalCta() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-5 py-20 text-center sm:px-8 sm:py-24">
        <h2 className="display mx-auto max-w-2xl text-3xl sm:text-5xl">
          Stop copying files one at a time.
        </h2>
        <p className="mx-auto mt-4 max-w-lg text-muted">
          Install LLMScribe, point it at a project, paste the result into the model you already
          use.
        </p>
        <div className="mx-auto mt-8 flex max-w-md items-center gap-2 rounded-lg border border-border bg-surface p-1.5 pl-4 text-left">
          <code className="min-w-0 flex-1 truncate font-mono text-sm text-primary">
            {SITE.install}
          </code>
          <CopyButton text={SITE.install} />
        </div>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Button asChild>
            <a href={SITE.pypi} target="_blank" rel="noreferrer">
              Open on PyPI
            </a>
          </Button>
          <Button variant="outline" asChild>
            <a href={SITE.github} target="_blank" rel="noreferrer">
              GitHub
            </a>
          </Button>
        </div>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-5 py-10 sm:px-8 md:flex-row md:items-start md:justify-between">
        <div>
          <Wordmark />
          <p className="mt-3 max-w-xs text-sm text-muted">{SITE.tagline}</p>
        </div>
        <div className="grid grid-cols-2 gap-10 text-sm sm:grid-cols-3">
          <div>
            <p className="font-medium text-fg">Product</p>
            <ul className="mt-3 space-y-2 text-muted">
              <li>
                <a className="hover:text-fg" href="#how">
                  How it works
                </a>
              </li>
              <li>
                <a className="hover:text-fg" href="#install">
                  Install
                </a>
              </li>
              <li>
                <a className="hover:text-fg" href="#api">
                  Python API
                </a>
              </li>
              <li>
                <a className="hover:text-fg" href="#faq">
                  FAQ
                </a>
              </li>
            </ul>
          </div>
          <div>
            <p className="font-medium text-fg">Links</p>
            <ul className="mt-3 space-y-2 text-muted">
              <li>
                <a className="hover:text-fg" href={SITE.github} target="_blank" rel="noreferrer">
                  GitHub
                </a>
              </li>
              <li>
                <a className="hover:text-fg" href={SITE.pypi} target="_blank" rel="noreferrer">
                  PyPI
                </a>
              </li>
              <li>
                <a className="hover:text-fg" href={SITE.issues} target="_blank" rel="noreferrer">
                  Issues
                </a>
              </li>
              <li>
                <a className="hover:text-fg" href={SITE.licenseUrl} target="_blank" rel="noreferrer">
                  License
                </a>
              </li>
            </ul>
          </div>
          <div className="col-span-2 sm:col-span-1">
            <p className="font-medium text-fg">Credits</p>
            <p className="mt-3 text-muted">
              Made by {SITE.author}.
              <br />
              {SITE.license}.
            </p>
          </div>
        </div>
      </div>
      <div className="border-t border-border">
        <p className="mx-auto max-w-6xl px-5 py-5 font-mono text-xs text-subtle sm:px-8">
          © {new Date().getFullYear()} {SITE.author}. LLMScribe {SITE.version}.
        </p>
      </div>
    </footer>
  );
}
