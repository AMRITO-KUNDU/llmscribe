import { createRootRoute, HeadContent, Outlet, Scripts } from "@tanstack/react-router";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "sonner";
import appCss from "../styles.css?url";

const APP_NAME = "LLMScribe";
const DESCRIPTION =
  "Turn local projects and public GitHub repositories into clean, deterministic, structured context. Open-source Python CLI, MCP server, and GUI — published on PyPI.";
const SITE_URL = "https://llmscribe.vercel.app";
const OG_IMAGE = `${SITE_URL}/og.png`;
const TAGLINE = `${APP_NAME} — one file, the whole project`;

const structuredData = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: APP_NAME,
  description: DESCRIPTION,
  url: SITE_URL,
  applicationCategory: "DeveloperApplication",
  operatingSystem: "Windows, macOS, Linux",
  softwareVersion: "1.2.2",
  license: "https://www.apache.org/licenses/LICENSE-2.0",
  downloadUrl: "https://pypi.org/project/llmscribe/",
  author: {
    "@type": "Person",
    name: "Amrito Kundu",
    url: "https://github.com/AMRITO-KUNDU",
  },
  offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
  sameAs: [
    "https://github.com/AMRITO-KUNDU/llmscribe",
    "https://pypi.org/project/llmscribe/",
  ],
};

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: TAGLINE },
      { name: "description", content: DESCRIPTION },
      { name: "theme-color", content: "#0b0c0b" },
      { name: "author", content: "Amrito Kundu" },
      { name: "robots", content: "index, follow" },
      { property: "og:type", content: "website" },
      { property: "og:site_name", content: APP_NAME },
      { property: "og:title", content: TAGLINE },
      { property: "og:description", content: DESCRIPTION },
      { property: "og:url", content: SITE_URL },
      { property: "og:image", content: OG_IMAGE },
      { property: "og:image:width", content: "1200" },
      { property: "og:image:height", content: "630" },
      {
        property: "og:image:alt",
        content: `${APP_NAME} — turn any repository into structured, LLM-ready context`,
      },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:title", content: TAGLINE },
      { name: "twitter:description", content: DESCRIPTION },
      { name: "twitter:image", content: OG_IMAGE },
    ],
    links: [
      { rel: "canonical", href: SITE_URL },
      { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" },
      { rel: "stylesheet", href: appCss },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=Instrument+Serif:ital@0;1&display=swap",
      },
    ],
    scripts: [
      {
        type: "application/ld+json",
        children: JSON.stringify(structuredData),
      },
    ],
  }),
  component: () => (
    <html lang="en" className="antialiased" suppressHydrationWarning>
      <head>
        <HeadContent />
      </head>
      <body className="min-h-dvh bg-bg text-fg">
        <TooltipProvider delayDuration={200}>
          <Outlet />
          <Toaster
            theme="dark"
            position="bottom-right"
            toastOptions={{
              className: "!bg-elevated !text-fg !border-border !font-sans !shadow-panel",
            }}
          />
        </TooltipProvider>
        <Scripts />
      </body>
    </html>
  ),
});
