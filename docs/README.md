# LLMScribe site

Marketing and documentation site for LLMScribe — a local-only Python CLI, MCP server and
desktop GUI that turns a project directory into clean, structured context for AI
coding agents.

## Scripts

```bash
npm install
npm run dev        # dev server
npm run build      # production build (Vercel output)
npm run preview    # serve the built output
npm run typecheck
npm run lint
npm run format
```

## Structure

```
public/                  static assets
src/
  components/
    site/                 page sections (hero, features, FAQ, etc.)
    ui/                   base UI primitives
  lib/                    site content/config and utilities
  routes/                 file-based routes (/)
  router.tsx
  styles.css
```
