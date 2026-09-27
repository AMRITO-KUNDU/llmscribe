/**
 * Single source of truth for app head chrome (PWA, manifest, OG tags),
 * shared by the Vite plugin and Nitro middleware.
 */
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

export const DEFAULT_APP_NAME = "LLMScribe";
export const OG_SITE_REL_PATH = "src/lib/og/site.json";

const SHARE_META_KEYS = new Set([
  "og:title",
  "og:description",
  "og:image",
  "og:image:width",
  "og:image:height",
  "og:type",
  "og:url",
  "og:site_name",
  "twitter:card",
  "twitter:title",
  "twitter:image",
  "twitter:description",
]);

export function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function unescapeHtml(value) {
  return String(value)
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">")
    .replaceAll("&quot;", '"')
    .replaceAll("&#39;", "'")
    .replaceAll("&amp;", "&");
}

export function appNameFromHost() {
  return DEFAULT_APP_NAME;
}

export function publicAppHost(hostHeader) {
  const host = String(hostHeader ?? "")
    .split(",")[0]
    .trim()
    .split(":")[0]
    .toLowerCase();
  if (!host || !/^[a-z0-9.-]+$/.test(host) || !host.includes(".")) return "";
  if (/^\d{1,3}(?:\.\d{1,3}){3}$/.test(host)) return "";
  return host;
}

export function resolvePublicHost(hostHeader) {
  return publicAppHost(process.env?.VITE_PUBLIC_HOSTNAME) || publicAppHost(hostHeader);
}

export function isInstallQuery(url) {
  const query = String(url ?? "").split("?", 2)[1] ?? "";
  const params = new URLSearchParams(query);
  const install = params.get("install");
  const platform = (params.get("platform") ?? "").toLowerCase();
  return (install === "1" || install === "true") && platform === "ios";
}

export function isDocumentPath(pathname) {
  const path = String(pathname ?? "");
  return (
    !path.startsWith("/api/") &&
    !path.startsWith("/@") &&
    !path.startsWith("/node_modules") &&
    !/\.[a-z0-9]+$/i.test(path)
  );
}

export function acceptsHtml(accept) {
  const value = String(accept ?? "");
  return value === "" || value.includes("text/html") || value.includes("*/*");
}

export function stripInstallParams(url) {
  const [path = "/", query = ""] = String(url ?? "/").split("?", 2);
  const params = new URLSearchParams(query);
  params.delete("install");
  params.delete("platform");
  const rest = params.toString();
  return rest ? `${path}?${rest}` : path;
}

export function renderInstallPageHtml(template, { host, url } = {}) {
  return String(template)
    .replaceAll("{{APP_NAME}}", escapeHtml(DEFAULT_APP_NAME))
    .replaceAll("{{APP_URL}}", escapeHtml(stripInstallParams(url)));
}

export function renderWebManifest() {
  return JSON.stringify(
    {
      name: DEFAULT_APP_NAME,
      short_name: DEFAULT_APP_NAME,
      id: "/",
      start_url: "/",
      scope: "/",
      display: "standalone",
      background_color: "#0f172a",
      theme_color: "#0f172a",
      icons: [
        {
          src: "/favicon.svg",
          sizes: "any",
          type: "image/svg+xml",
        },
      ],
    },
    null,
    2,
  );
}

export function appPwaHeadTags(appName = DEFAULT_APP_NAME) {
  return [
    ["manifest", '<link rel="manifest" href="/manifest.webmanifest">'],
    ["icon", '<link rel="icon" href="/favicon.svg" type="image/svg+xml">'],
    [
      "apple-mobile-web-app-title",
      `<meta name="apple-mobile-web-app-title" content="${escapeHtml(appName)}">`,
    ],
    ["theme-color", '<meta name="theme-color" content="#0f172a">'],
  ];
}

export function readOgSite(cwd = process.cwd()) {
  try {
    const raw = readFileSync(join(cwd, OG_SITE_REL_PATH), "utf8");
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

export function ogCardPublicPath(cwd = process.cwd()) {
  if (existsSync(join(cwd, "public/og.jpg"))) return "/og.jpg";
  if (existsSync(join(cwd, "public/og.png"))) return "/og.png";
  return "";
}

export function snapshotOgIdentity(cwd = process.cwd()) {
  const site = { ...readOgSite(cwd) };
  const disk = ogCardPublicPath(cwd);
  if (disk) {
    site.card = "custom";
    site.image = disk;
  }
  return { site };
}

export function titleFromDocument(html) {
  const match = String(html ?? "").match(/<title\b[^>]*>([^<]*)<\/title>/i);
  return match ? unescapeHtml(match[1]).trim() : "";
}

export function resolveOgTitle(site = {}, appName = DEFAULT_APP_NAME, host = "", documentTitle = "") {
  const fromSite = String(site.title ?? "").trim();
  if (fromSite) return fromSite;
  const fromDoc = String(documentTitle ?? "").trim();
  if (fromDoc) return fromDoc;
  return appName || DEFAULT_APP_NAME;
}

export function appOgHeadTags({
  host = "",
  appName = DEFAULT_APP_NAME,
  site = {},
  documentTitle = "",
  cwd = process.cwd(),
} = {}) {
  const title = resolveOgTitle(site, appName, host, documentTitle);
  const publicHost = resolvePublicHost(host);
  const tags = [
    `<meta name="twitter:card" content="summary_large_image">`,
    `<meta property="og:title" content="${escapeHtml(title)}">`,
  ];
  const description = String(site.description ?? "").trim();
  if (description) {
    tags.push(`<meta property="og:description" content="${escapeHtml(description)}">`);
  }
  if (publicHost) {
    const cardPath = ogCardPublicPath(cwd) || "/og.jpg";
    const image = `https://${publicHost}${cardPath}`;
    tags.push(`<meta property="og:image" content="${escapeHtml(image)}">`);
  }
  return tags;
}

export function stripShareMetaTags(html) {
  return String(html).replace(/<meta\b[^>]*>/gi, (tag) => {
    const attrs = [...tag.matchAll(/\b(?:property|name)\s*=\s*["']([^"']+)["']/gi)];
    for (const match of attrs) {
      if (SHARE_META_KEYS.has(String(match[1]).toLowerCase())) return "";
    }
    return tag;
  });
}

function insertAfterHeadOpen(html, snippet) {
  if (/<head\b[^>]*>/i.test(html)) {
    return html.replace(/<head\b[^>]*>/i, (open) => `${open}${snippet}`);
  }
  if (/<html\b[^>]*>/i.test(html)) {
    return html.replace(/<html\b[^>]*>/i, (open) => `${open}<head>${snippet}</head>`);
  }
  return `<!doctype html><html><head>${snippet}</head>${html}`;
}

function insertBeforeHeadClose(html, snippet) {
  if (/<\/head>/i.test(html)) return html.replace(/<\/head>/i, `${snippet}</head>`);
  return insertAfterHeadOpen(html, snippet);
}

export function normalizeHeadContext(ctx = {}) {
  const cwd = ctx.cwd ?? process.cwd();
  const site = ctx.site !== undefined ? ctx.site : snapshotOgIdentity(cwd).site;
  const appName = resolveOgTitle(site, ctx.appName ?? DEFAULT_APP_NAME, ctx.host ?? "");
  return {
    appName,
    host: ctx.host ?? "",
    cwd,
    site,
  };
}

export function injectAppPwaHead(html, ctx = {}) {
  if (typeof html !== "string") return html;
  const { site, host, cwd } = normalizeHeadContext(ctx);
  const documentTitle = titleFromDocument(html);
  const appName = resolveOgTitle(site, ctx.appName ?? DEFAULT_APP_NAME, host, documentTitle);
  let next = stripShareMetaTags(html);

  const missing = appPwaHeadTags(appName)
    .filter(([key]) => {
      if (key === "manifest") return !next.includes('href="/manifest.webmanifest"');
      return !next.includes(`name="${key}"`);
    })
    .map(([, tag]) => tag);

  next = insertAfterHeadOpen(
    next,
    appOgHeadTags({ host, appName, site, documentTitle, cwd }).join(""),
  );

  if (missing.length === 0) return next;
  return insertBeforeHeadClose(next, missing.join(""));
}

export function createHeadInjector(ctx = {}) {
  const normalized = normalizeHeadContext(ctx);
  let pending = [];
  let done = false;

  const apply = (html) =>
    injectAppPwaHead(html, {
      appName: normalized.appName,
      host: normalized.host,
      cwd: normalized.cwd,
      site: normalized.site,
    });

  return {
    push(chunk) {
      const buf = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
      if (done) return [buf];
      pending.push(buf);
      const joined = Buffer.concat(pending);
      const at = joined.toString("latin1").search(/<\/head>/i);
      if (at === -1) return [];
      done = true;
      pending = [];
      const closeLen = 7;
      const head = apply(joined.subarray(0, at + closeLen).toString("utf8"));
      return [Buffer.concat([Buffer.from(head, "utf8"), joined.subarray(at + closeLen)])];
    },
    flush() {
      if (done || pending.length === 0) return [];
      const rest = Buffer.concat(pending);
      pending = [];
      done = true;
      return [Buffer.from(apply(rest.toString("utf8")), "utf8")];
    },
  };
}
