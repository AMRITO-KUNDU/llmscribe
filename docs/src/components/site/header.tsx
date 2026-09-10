"use client";

import { useEffect, useState } from "react";
import { Github, Menu, X } from "lucide-react";
import { Wordmark } from "@/components/site/logo";
import { Button } from "@/components/ui/button";
import { NAV, SITE } from "@/lib/site";
import { cn } from "@/lib/utils";

export function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header
      className={cn(
        "sticky top-0 z-40 transition-[background-color,border-color] duration-200",
        scrolled || open
          ? "border-b border-border bg-bg/90 backdrop-blur-md"
          : "border-b border-transparent bg-transparent",
      )}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-5 sm:px-8">
        <a href="#top" className="shrink-0 text-fg" aria-label="LLMScribe home">
          <Wordmark />
        </a>

        <nav className="hidden items-center gap-7 md:flex" aria-label="Primary">
          {NAV.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="text-sm text-muted transition-colors hover:text-fg"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <Button variant="ghost" size="sm" asChild>
            <a href={SITE.github} target="_blank" rel="noreferrer">
              <Github />
              GitHub
            </a>
          </Button>
          <Button size="sm" asChild>
            <a href="#install">Install</a>
          </Button>
        </div>

        <Button
          variant="outline"
          size="icon"
          className="shrink-0 md:hidden"
          aria-expanded={open}
          aria-controls="mobile-nav"
          aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => setOpen((v) => !v)}
        >
          {open ? <X /> : <Menu />}
        </Button>
      </div>

      {open ? (
        <div
          id="mobile-nav"
          className="border-t border-border bg-bg px-5 py-4 md:hidden"
        >
          <nav className="flex flex-col gap-1" aria-label="Mobile">
            {NAV.map((item) => (
              <a
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className="flex min-h-11 items-center rounded-md px-2 text-base text-fg"
              >
                {item.label}
              </a>
            ))}
            <a
              href={SITE.github}
              target="_blank"
              rel="noreferrer"
              className="flex min-h-11 items-center rounded-md px-2 text-base text-fg"
            >
              GitHub
            </a>
            <Button className="mt-2 w-full" asChild>
              <a href="#install" onClick={() => setOpen(false)}>
                Install
              </a>
            </Button>
          </nav>
        </div>
      ) : null}
    </header>
  );
}
