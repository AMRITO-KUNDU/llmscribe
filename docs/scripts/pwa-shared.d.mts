export declare const DEFAULT_APP_NAME = "LLMScribe";
export declare const OG_SITE_REL_PATH = "src/lib/og/site.json";

export declare function acceptsHtml(accept?: string | null): boolean;
export declare function appNameFromHost(hostHeader?: string | null): string;

export declare function createHeadInjector(ctx?: {
  host?: string;
  cwd?: string;
  site?: Record<string, unknown>;
  appName?: string;
}): {
  push(chunk: Uint8Array | string): Buffer[];
  flush(): Buffer[];
};

export declare function isDocumentPath(pathname?: string | null): boolean;
export declare function isInstallQuery(url?: string | null): boolean;
export declare function renderInstallPageHtml(
  template: string,
  opts?: { host?: string; url?: string },
): string;
export declare function renderWebManifest(hostHeader?: string | null): string;
export declare function snapshotOgIdentity(cwd?: string): { site: Record<string, unknown> };
