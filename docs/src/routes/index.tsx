import { createFileRoute } from "@tanstack/react-router";
import { Api } from "@/components/site/api";
import { Faq } from "@/components/site/faq";
import { Features } from "@/components/site/features";
import { FinalCta, Footer } from "@/components/site/footer";
import { Header } from "@/components/site/header";
import { Hero } from "@/components/site/hero";
import { HowItWorks } from "@/components/site/how-it-works";
import { Install } from "@/components/site/install";
import { Interfaces } from "@/components/site/interfaces";
import { Output } from "@/components/site/output";

export const Route = createFileRoute("/")({ component: Home });

function Home() {
  return (
    <div id="top" className="min-h-dvh">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-foreground"
      >
        Skip to content
      </a>
      <Header />
      <main id="main">
        <Hero />
        <HowItWorks />
        <Interfaces />
        <Output />
        <Features />
        <Install />
        <Api />
        <Faq />
        <FinalCta />
      </main>
      <Footer />
    </div>
  );
}
