# LLMScribe site

Marketing/docs site for LLMScribe, a Python CLI/GUI/CUI tool that turns a project folder into one clean text file for AI tools to read.

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
