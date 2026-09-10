import { i as __toESM } from "../_runtime.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { a as Trigger2, i as Root2, m as Slot, n as Header$1, r as Item, t as Content2, v as require_jsx_runtime } from "../_libs/@radix-ui/react-accordion+[...].mjs";
import { a as Package, c as FolderX, d as Earth, f as Copy, g as AppWindow, h as ArrowDown, i as Save, l as FolderOpen, m as Check, o as Menu, p as ChevronDown, r as SquareTerminal, s as Github, t as X, u as FileCode2 } from "../_libs/lucide-react.mjs";
import { t as cva } from "../_libs/class-variance-authority+clsx.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { n as cn } from "./router-CEjpqOTO.mjs";
import { i as Trigger, n as List, r as Root2$1, t as Content } from "../_libs/radix-ui__react-tabs.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/routes-DyhfDUwL.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var buttonVariants = cva("inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-[color,background-color,border-color,opacity,transform] duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/70 focus-visible:ring-offset-2 focus-visible:ring-offset-bg disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 active:not-disabled:scale-[0.96]", {
	variants: {
		variant: {
			default: "bg-primary text-primary-foreground hover:bg-primary/90",
			outline: "border border-border bg-transparent text-fg hover:bg-elevated",
			ghost: "text-fg hover:bg-elevated",
			secondary: "bg-elevated text-fg hover:bg-elevated/80 border border-border",
			link: "text-primary underline-offset-4 hover:underline"
		},
		size: {
			default: "h-11 px-4",
			sm: "h-9 rounded-md px-3 text-sm",
			lg: "h-12 rounded-lg px-6",
			icon: "size-11"
		}
	},
	defaultVariants: {
		variant: "default",
		size: "default"
	}
});
var Button = import_react.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(asChild ? Slot : "button", {
		className: cn(buttonVariants({
			variant,
			size,
			className
		})),
		ref,
		...props
	});
});
Button.displayName = "Button";
function CopyButton({ text, label = "Copy", copiedLabel = "Copied", className, variant = "outline", size = "sm", onCopied, ...props }) {
	const [copied, setCopied] = (0, import_react.useState)(false);
	async function handleCopy() {
		try {
			await navigator.clipboard.writeText(text);
			setCopied(true);
			toast.success("Copied to clipboard");
			onCopied?.();
			window.setTimeout(() => setCopied(false), 1600);
		} catch {
			toast.error("Could not copy");
		}
	}
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
		type: "button",
		variant,
		size,
		onClick: handleCopy,
		className: cn(className),
		...props,
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
			className: "relative size-4",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Copy, { className: cn("absolute inset-0 size-4 transition-[opacity,transform,filter] duration-200", copied ? "scale-[0.25] opacity-0 blur-[4px]" : "scale-100 opacity-100 blur-none") }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Check, { className: cn("absolute inset-0 size-4 transition-[opacity,transform,filter] duration-200", copied ? "scale-100 opacity-100 blur-none" : "scale-[0.25] opacity-0 blur-[4px]") })]
		}), copied ? copiedLabel : label]
	});
}
var SITE = {
	name: "LLMScribe",
	version: "1.0.0",
	tagline: "Turn any project folder into one clean text file that AI tools can read.",
	description: "LLMScribe walks a project, builds a directory tree, and dumps the full contents of every source file into a single .txt file. Perfect for pasting into ChatGPT, Claude, Grok, Cursor, or any other AI coding assistant.",
	author: "Amrito Kundu",
	github: "https://github.com/AMRITO-KUNDU/LLMScribe",
	pypi: "https://pypi.org/project/llmscribe/",
	issues: "https://github.com/AMRITO-KUNDU/LLMScribe/issues",
	licenseUrl: "https://github.com/AMRITO-KUNDU/LLMScribe/blob/main/LICENSE",
	license: "Apache License 2.0",
	python: "3.10+",
	install: "pip install llmscribe"
};
var NAV = [
	{
		href: "#how",
		label: "How it works"
	},
	{
		href: "#interfaces",
		label: "Interfaces"
	},
	{
		href: "#output",
		label: "Output"
	},
	{
		href: "#install",
		label: "Install"
	},
	{
		href: "#faq",
		label: "FAQ"
	}
];
var EXTENSIONS = [
	".py",
	".js",
	".ts",
	".jsx",
	".tsx",
	".java",
	".go",
	".rs",
	".md",
	".json",
	".yaml",
	".toml",
	".html",
	".css",
	".sh"
];
var IGNORED = [
	".git",
	"node_modules",
	"venv",
	"__pycache__",
	"dist",
	"build",
	".idea",
	".vscode",
	".DS_Store",
	"Thumbs.db",
	".gitignore rules"
];
var SAMPLE_TREE = `Selected Files Directory Structure:

my-project/
├── src/
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_main.py
├── pyproject.toml
└── README.md`;
var SAMPLE_FULL = `${SAMPLE_TREE}

File Contents:

--- src/main.py ---
def hello():
    print("Hello world")

--- src/utils.py ---
def add(a: int, b: int) -> int:
    return a + b

--- tests/test_main.py ---
from src.main import hello

def test_hello():
    hello()

--- pyproject.toml ---
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.10"

--- README.md ---
# my-project

A tiny sample app used in the LLMScribe walkthrough.
`;
var PYTHON_API = `from pathlib import Path
from llmscribe.core.writer import run, build_project_summary

# Write a file
run(
    project_path=Path("/path/to/project"),
    output_file=Path("summary.txt"),
    tree_only=False,
)

# Or just get the text
text = build_project_summary(Path("/path/to/project"))`;
function Api() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("section", {
		id: "api",
		className: "scroll-mt-20 border-t border-border",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid gap-10 lg:grid-cols-2 lg:items-start",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "font-mono text-xs tracking-widest text-primary uppercase",
						children: "Python API"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
						className: "display mt-3 text-3xl sm:text-4xl",
						children: "Use the core from your own code."
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "mt-4 text-muted",
						children: "The same writer the CLI uses is importable. Write a file, or keep the summary as a string and send it wherever you need context."
					})
				] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "overflow-hidden rounded-xl border border-border bg-surface",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex items-center justify-between border-b border-border px-5 py-3",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "font-mono text-xs text-muted",
							children: "llmscribe.core.writer"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyButton, { text: PYTHON_API })]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("pre", {
						className: "overflow-x-auto p-5 font-mono text-sm leading-relaxed text-fg/90",
						children: PYTHON_API
					})]
				})]
			})
		})
	});
}
var Accordion = Root2;
var AccordionItem = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Item, {
	ref,
	className: cn("border-b border-border", className),
	...props
}));
AccordionItem.displayName = "AccordionItem";
var AccordionTrigger = import_react.forwardRef(({ className, children, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Header$1, {
	className: "flex",
	children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Trigger2, {
		ref,
		className: cn("flex flex-1 items-center justify-between gap-4 py-5 text-left text-base font-medium transition-colors hover:text-primary [&[data-state=open]>svg]:rotate-180", className),
		...props,
		children: [children, /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ChevronDown, { className: "size-4 shrink-0 text-muted transition-transform duration-200" })]
	})
}));
AccordionTrigger.displayName = Trigger2.displayName;
var AccordionContent = import_react.forwardRef(({ className, children, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Content2, {
	ref,
	className: "overflow-hidden text-sm data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down",
	...props,
	children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: cn("pb-5 text-muted leading-relaxed", className),
		children
	})
}));
AccordionContent.displayName = Content2.displayName;
var ITEMS = [
	{
		q: "I don’t have a terminal. How do I open one?",
		a: "Windows: Win + R, type cmd or powershell, press Enter. macOS: Cmd + Space, type Terminal, press Enter. Linux: Ctrl + Alt + T on most distributions. Then run llmscribe-gui for the desktop window."
	},
	{
		q: "The GUI doesn’t open / complains about Tkinter.",
		a: "On some Linux systems you need the system package first: python3-tk on Ubuntu/Debian, python3-tkinter on Fedora, tk on Arch. Command-line mode (llmscribe --path …) works without Tkinter."
	},
	{
		q: "Where does the file get saved?",
		a: "By default it is saved as project_overview.txt in the folder where you ran the command. Use --output to put it anywhere you like. In the GUI you can change the output path before generating."
	},
	{
		q: "Which files are included?",
		a: "Any file with a common source or text extension — .py, .js, .ts, .jsx, .tsx, .java, .go, .rs, .md, .json, .yaml, .toml, .html, .css, .sh, and many more. Binary assets and dependency trees are skipped."
	},
	{
		q: "Does it respect .gitignore?",
		a: "Yes. Anything listed in the project’s own .gitignore is ignored, along with .git, node_modules, venv, __pycache__, dist, build, .idea, .vscode, .DS_Store, and Thumbs.db."
	},
	{
		q: "Can I export only the folder tree?",
		a: "Yes. Pass --tree-only on the CLI, or tick Tree only in the GUI. You get the directory structure without file contents — useful when the model only needs layout."
	}
];
function Faq() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("section", {
		id: "faq",
		className: "scroll-mt-20 border-t border-border",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mx-auto max-w-3xl px-5 py-20 sm:px-8 sm:py-24",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-xs tracking-widest text-primary uppercase",
					children: "FAQ"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
					className: "display mt-3 text-3xl sm:text-4xl",
					children: "Common questions"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Accordion, {
					type: "single",
					collapsible: true,
					className: "mt-8",
					children: ITEMS.map((item, i) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AccordionItem, {
						value: `item-${i}`,
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(AccordionTrigger, { children: item.q }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(AccordionContent, { children: item.a })]
					}, item.q))
				})
			]
		})
	});
}
var FEATURES = [
	{
		icon: AppWindow,
		title: "Three ways in",
		body: "A desktop GUI for people who would rather click, a numbered CUI for the terminal, and a full CLI for scripts and muscle memory."
	},
	{
		icon: FolderX,
		title: "Smart ignore",
		body: "Drops .git, node_modules, venv, caches, IDE folders, OS junk, and anything already listed in the project's own .gitignore."
	},
	{
		icon: FileCode2,
		title: "Source, not noise",
		body: "Includes common source and text extensions — Python, JavaScript, TypeScript, Go, Rust, Java, Markdown, JSON, YAML, HTML, CSS, shell, and more."
	},
	{
		icon: SquareTerminal,
		title: "Tree-only mode",
		body: "Need structure without the files? Pass --tree-only, or tick the box in the GUI, and you get the directory tree alone."
	},
	{
		icon: Package,
		title: "Embeddable core",
		body: "Import llmscribe.core from Python. run() writes a file; build_project_summary() returns the text so you can pipe it elsewhere."
	},
	{
		icon: Earth,
		title: "Anywhere Python runs",
		body: "Windows, macOS, and Linux. Python 3.10 or newer. The CLI works even if Tkinter is missing; the GUI needs it on some Linux setups."
	}
];
function Features() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("section", {
		id: "features",
		className: "scroll-mt-20 border-t border-border",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-xs tracking-widest text-primary uppercase",
					children: "Capabilities"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
					className: "display mt-3 max-w-xl text-3xl sm:text-4xl",
					children: "Built to stay out of the way."
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "mt-12 grid gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-2 lg:grid-cols-3",
					children: FEATURES.map((f) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("article", {
						className: "bg-bg p-6 sm:p-7",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(f.icon, {
								className: "size-5 text-primary",
								strokeWidth: 1.6
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
								className: "mt-4 text-base font-medium",
								children: f.title
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "mt-2 text-sm leading-relaxed text-muted",
								children: f.body
							})
						]
					}, f.title))
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mt-12 grid gap-6 lg:grid-cols-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "rounded-xl border border-border bg-surface p-6 sm:p-8",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
								className: "text-base font-medium",
								children: "Included"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "mt-1 text-sm text-muted",
								children: "Common source and text extensions. Many more than the chips below."
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("ul", {
								className: "mt-5 flex flex-wrap gap-2",
								children: [EXTENSIONS.map((ext) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", {
									className: "rounded-full border border-border bg-bg px-3 py-1 font-mono text-xs text-fg",
									children: ext
								}, ext)), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", {
									className: "rounded-full border border-border px-3 py-1 font-mono text-xs text-muted",
									children: "+ more"
								})]
							})
						]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "rounded-xl border border-border bg-surface p-6 sm:p-8",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
								className: "text-base font-medium",
								children: "Ignored automatically"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "mt-1 text-sm text-muted",
								children: "Dependency trees, caches, IDE folders, OS junk, and your .gitignore."
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("ul", {
								className: "mt-5 flex flex-wrap gap-2",
								children: IGNORED.map((item) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", {
									className: "rounded-full border border-border bg-bg px-3 py-1 font-mono text-xs text-muted",
									children: item
								}, item))
							})
						]
					})]
				})
			]
		})
	});
}
function LogoMark({ className }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("svg", {
		viewBox: "0 0 32 32",
		className: cn("size-8", className),
		"aria-hidden": "true",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("rect", {
				width: "32",
				height: "32",
				rx: "7",
				className: "fill-bg"
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("rect", {
				x: "1",
				y: "1",
				width: "30",
				height: "30",
				rx: "6",
				fill: "none",
				className: "stroke-primary",
				strokeWidth: "1.5"
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("path", {
				d: "M12 8.5 L22.5 16 L12 23.5",
				fill: "none",
				className: "stroke-primary",
				strokeWidth: "3",
				strokeLinecap: "butt",
				strokeLinejoin: "miter"
			})
		]
	});
}
function Wordmark({ className }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
		className: cn("flex items-center gap-2.5", className),
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LogoMark, { className: "size-7" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
			className: "display text-xl leading-none tracking-tight",
			children: "LLMScribe"
		})]
	});
}
function FinalCta() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("section", {
		className: "border-t border-border",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mx-auto max-w-6xl px-5 py-20 text-center sm:px-8 sm:py-24",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
					className: "display mx-auto max-w-2xl text-3xl sm:text-5xl",
					children: "Stop copying files one at a time."
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "mx-auto mt-4 max-w-lg text-muted",
					children: "Install LLMScribe, point it at a project, paste the result into the model you already use."
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mx-auto mt-8 flex max-w-md items-center gap-2 rounded-lg border border-border bg-surface p-1.5 pl-4 text-left",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("code", {
						className: "min-w-0 flex-1 truncate font-mono text-sm text-primary",
						children: SITE.install
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyButton, { text: SITE.install })]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mt-5 flex flex-wrap items-center justify-center gap-3",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						asChild: true,
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
							href: SITE.pypi,
							target: "_blank",
							rel: "noreferrer",
							children: "Open on PyPI"
						})
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						variant: "outline",
						asChild: true,
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
							href: SITE.github,
							target: "_blank",
							rel: "noreferrer",
							children: "GitHub"
						})
					})]
				})
			]
		})
	});
}
function Footer() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("footer", {
		className: "border-t border-border",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mx-auto flex max-w-6xl flex-col gap-8 px-5 py-10 sm:px-8 md:flex-row md:items-start md:justify-between",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Wordmark, {}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "mt-3 max-w-xs text-sm text-muted",
				children: SITE.tagline
			})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid grid-cols-2 gap-10 text-sm sm:grid-cols-3",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "font-medium text-fg",
						children: "Product"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("ul", {
						className: "mt-3 space-y-2 text-muted",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
								className: "hover:text-fg",
								href: "#how",
								children: "How it works"
							}) }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
								className: "hover:text-fg",
								href: "#install",
								children: "Install"
							}) }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
								className: "hover:text-fg",
								href: "#api",
								children: "Python API"
							}) }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
								className: "hover:text-fg",
								href: "#faq",
								children: "FAQ"
							}) })
						]
					})] }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "font-medium text-fg",
						children: "Links"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("ul", {
						className: "mt-3 space-y-2 text-muted",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
								className: "hover:text-fg",
								href: SITE.github,
								target: "_blank",
								rel: "noreferrer",
								children: "GitHub"
							}) }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
								className: "hover:text-fg",
								href: SITE.pypi,
								target: "_blank",
								rel: "noreferrer",
								children: "PyPI"
							}) }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
								className: "hover:text-fg",
								href: SITE.issues,
								target: "_blank",
								rel: "noreferrer",
								children: "Issues"
							}) }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
								className: "hover:text-fg",
								href: SITE.licenseUrl,
								target: "_blank",
								rel: "noreferrer",
								children: "License"
							}) })
						]
					})] }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "col-span-2 sm:col-span-1",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "font-medium text-fg",
							children: "Credits"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "mt-3 text-muted",
							children: [
								"Made by ",
								SITE.author,
								".",
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("br", {}),
								SITE.license,
								"."
							]
						})]
					})
				]
			})]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "border-t border-border",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
				className: "mx-auto max-w-6xl px-5 py-5 font-mono text-xs text-subtle sm:px-8",
				children: [
					"© ",
					(/* @__PURE__ */ new Date()).getFullYear(),
					" ",
					SITE.author,
					". LLMScribe ",
					SITE.version,
					"."
				]
			})
		})]
	});
}
function Header() {
	const [scrolled, setScrolled] = (0, import_react.useState)(false);
	const [open, setOpen] = (0, import_react.useState)(false);
	(0, import_react.useEffect)(() => {
		const onScroll = () => setScrolled(window.scrollY > 8);
		onScroll();
		window.addEventListener("scroll", onScroll, { passive: true });
		return () => window.removeEventListener("scroll", onScroll);
	}, []);
	(0, import_react.useEffect)(() => {
		document.body.style.overflow = open ? "hidden" : "";
		return () => {
			document.body.style.overflow = "";
		};
	}, [open]);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("header", {
		className: cn("sticky top-0 z-40 transition-[background-color,border-color] duration-200", scrolled || open ? "border-b border-border bg-bg/90 backdrop-blur-md" : "border-b border-transparent bg-transparent"),
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-5 sm:px-8",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
					href: "#top",
					className: "shrink-0 text-fg",
					"aria-label": "LLMScribe home",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Wordmark, {})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("nav", {
					className: "hidden items-center gap-7 md:flex",
					"aria-label": "Primary",
					children: NAV.map((item) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
						href: item.href,
						className: "text-sm text-muted transition-colors hover:text-fg",
						children: item.label
					}, item.href))
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "hidden items-center gap-2 md:flex",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						variant: "ghost",
						size: "sm",
						asChild: true,
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("a", {
							href: SITE.github,
							target: "_blank",
							rel: "noreferrer",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Github, {}), "GitHub"]
						})
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						size: "sm",
						asChild: true,
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
							href: "#install",
							children: "Install"
						})
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "outline",
					size: "icon",
					className: "shrink-0 md:hidden",
					"aria-expanded": open,
					"aria-controls": "mobile-nav",
					"aria-label": open ? "Close menu" : "Open menu",
					onClick: () => setOpen((v) => !v),
					children: open ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(X, {}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Menu, {})
				})
			]
		}), open ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			id: "mobile-nav",
			className: "border-t border-border bg-bg px-5 py-4 md:hidden",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("nav", {
				className: "flex flex-col gap-1",
				"aria-label": "Mobile",
				children: [
					NAV.map((item) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
						href: item.href,
						onClick: () => setOpen(false),
						className: "flex min-h-11 items-center rounded-md px-2 text-base text-fg",
						children: item.label
					}, item.href)),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
						href: SITE.github,
						target: "_blank",
						rel: "noreferrer",
						className: "flex min-h-11 items-center rounded-md px-2 text-base text-fg",
						children: "GitHub"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						className: "mt-2 w-full",
						asChild: true,
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
							href: "#install",
							onClick: () => setOpen(false),
							children: "Install"
						})
					})
				]
			})
		}) : null]
	});
}
function downloadText(filename, text) {
	const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
	const url = URL.createObjectURL(blob);
	const a = document.createElement("a");
	a.href = url;
	a.download = filename;
	a.click();
	URL.revokeObjectURL(url);
}
function GuiMock() {
	const [treeOnly, setTreeOnly] = (0, import_react.useState)(false);
	const [status, setStatus] = (0, import_react.useState)("idle");
	const [copied, setCopied] = (0, import_react.useState)(false);
	const timer = (0, import_react.useRef)(null);
	const output = treeOnly ? SAMPLE_TREE : SAMPLE_FULL;
	const lines = output.trimEnd().split("\n").length;
	(0, import_react.useEffect)(() => {
		return () => {
			if (timer.current) window.clearTimeout(timer.current);
		};
	}, []);
	function generate() {
		if (timer.current) window.clearTimeout(timer.current);
		setStatus("scanning");
		const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
		timer.current = window.setTimeout(() => {
			setStatus("done");
		}, reduced ? 0 : 720);
	}
	async function copyOutput() {
		if (status !== "done") return;
		try {
			await navigator.clipboard.writeText(output);
			setCopied(true);
			toast.success("Output copied");
			window.setTimeout(() => setCopied(false), 1600);
		} catch {
			toast.error("Could not copy");
		}
	}
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "overflow-hidden rounded-xl border border-border bg-surface shadow-panel",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "flex h-10 items-center gap-2 border-b border-border bg-elevated px-3",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
					className: "flex gap-1.5",
					"aria-hidden": "true",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "size-2.5 rounded-full bg-border" }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "size-2.5 rounded-full bg-border" }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "size-2.5 rounded-full bg-border" })
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "flex-1 text-center font-mono text-xs text-muted",
					children: "LLMScribe"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "font-mono text-xs text-subtle",
					children: "v1.0.0"
				})
			]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "grid md:grid-cols-[220px_minmax(0,1fr)] lg:grid-cols-[240px_minmax(0,1fr)]",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("aside", {
				className: "flex flex-col gap-4 border-b border-border p-4 md:border-r md:border-b-0",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "display text-lg leading-none",
						children: "LLMScribe"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "mt-1 font-mono text-xs text-subtle",
						children: "v1.0.0"
					})] }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", {
						className: "block",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "mb-1.5 block font-mono text-xs tracking-wider text-subtle uppercase",
							children: "Project folder"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "flex h-10 items-center gap-2 rounded-md border border-border bg-input px-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "min-w-0 flex-1 truncate font-mono text-xs text-fg",
								children: "~/Documents/my-project"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(FolderOpen, { className: "size-3.5 shrink-0 text-muted" })]
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", {
						className: "block",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "mb-1.5 block font-mono text-xs tracking-wider text-subtle uppercase",
							children: "Output file"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "flex h-10 items-center gap-2 rounded-md border border-border bg-input px-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "min-w-0 flex-1 truncate font-mono text-xs text-fg",
								children: "project_overview.txt"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Save, { className: "size-3.5 shrink-0 text-muted" })]
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", {
						className: "flex min-h-11 items-center gap-2 text-sm text-muted",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
							type: "checkbox",
							checked: treeOnly,
							onChange: (e) => {
								setTreeOnly(e.target.checked);
								if (status === "done") setStatus("idle");
							},
							className: "size-4 rounded border-border accent-primary"
						}), "Tree only"]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						type: "button",
						onClick: generate,
						className: "flex h-11 w-full items-center justify-center rounded-md bg-primary text-sm font-medium text-primary-foreground transition-[opacity,transform] duration-150 hover:opacity-90 active:scale-[0.96]",
						children: status === "scanning" ? "Scanning…" : "Generate"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid grid-cols-2 gap-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
							type: "button",
							onClick: copyOutput,
							disabled: status !== "done",
							className: "flex h-11 items-center justify-center gap-1.5 rounded-md border border-border text-xs font-medium text-fg disabled:opacity-40",
							children: [copied ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Check, { className: "size-3.5" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Copy, { className: "size-3.5" }), copied ? "Copied" : "Copy"]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
							type: "button",
							onClick: () => downloadText("project_overview.txt", output),
							disabled: status !== "done",
							className: "flex h-11 items-center justify-center rounded-md border border-border text-xs font-medium text-fg disabled:opacity-40",
							children: "Open file"
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
						className: cn("font-mono text-xs", status === "done" ? "text-primary" : "text-subtle"),
						children: [
							status === "idle" && "Ready",
							status === "scanning" && "Walking project…",
							status === "done" && "Saved to project_overview.txt"
						]
					})
				]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex min-h-72 flex-col bg-bg",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center justify-between border-b border-border px-4 py-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "text-xs text-muted",
						children: "Preview"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "font-mono text-xs tabular-nums text-subtle",
						children: status === "done" ? `${lines} lines` : "—"
					})]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "min-h-64 flex-1 overflow-auto p-4 sm:p-6",
					children: [
						status === "idle" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "max-w-xs text-sm leading-relaxed text-muted",
							children: "Select a project folder and press Generate. The output will appear here."
						}) : null,
						status === "scanning" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "font-mono text-sm text-muted",
							children: "Scanning text files · respecting .gitignore"
						}) : null,
						status === "done" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("pre", {
							className: "font-mono text-xs leading-relaxed text-fg/90 sm:text-sm",
							children: output
						}) : null
					]
				})]
			})]
		})]
	});
}
var badgeVariants = cva("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium tracking-wide", {
	variants: { variant: {
		default: "border-transparent bg-primary/15 text-primary",
		outline: "border-border text-muted",
		solid: "border-transparent bg-elevated text-fg"
	} },
	defaultVariants: { variant: "default" }
});
function Badge({ className, variant, ...props }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: cn(badgeVariants({ variant }), className),
		...props
	});
}
function Hero() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("section", {
		className: "paper-wash relative overflow-hidden",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mx-auto grid max-w-6xl gap-12 px-5 py-16 sm:px-8 sm:py-20 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)] lg:items-center lg:gap-10 lg:py-24",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex flex-wrap items-center gap-2",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Badge, { children: [
							"v",
							SITE.version,
							" on PyPI"
						] }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Badge, {
							variant: "outline",
							children: ["Python ", SITE.python]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
							variant: "outline",
							children: "Apache 2.0"
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h1", {
					className: "display mt-6 max-w-xl text-4xl text-fg sm:text-5xl lg:text-6xl",
					children: "Give any project to an AI in one file."
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
					className: "mt-5 max-w-md text-base leading-relaxed text-muted sm:text-lg",
					children: [SITE.tagline, " No configuration. Windows, macOS, and Linux."]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mt-8 flex max-w-md items-center gap-2 rounded-lg border border-border bg-surface p-1.5 pl-4",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("code", {
						className: "min-w-0 flex-1 truncate font-mono text-sm text-primary",
						children: SITE.install
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyButton, {
						text: SITE.install,
						label: "Copy"
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mt-5 flex flex-wrap items-center gap-3",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						size: "lg",
						asChild: true,
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
							href: "#install",
							children: "Get started"
						})
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						size: "lg",
						variant: "outline",
						asChild: true,
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("a", {
							href: SITE.github,
							target: "_blank",
							rel: "noreferrer",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Github, {}), "View source"]
						})
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
					className: "mt-6 text-sm text-subtle",
					children: [
						"Three commands:",
						" ",
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("code", {
							className: "font-mono text-muted",
							children: "llmscribe"
						}),
						",",
						" ",
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("code", {
							className: "font-mono text-muted",
							children: "llmscribe-gui"
						}),
						",",
						" ",
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("code", {
							className: "font-mono text-muted",
							children: "llmscribe-cui"
						})
					]
				})
			] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(GuiMock, {}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
				className: "mt-3 flex items-center gap-2 text-xs text-subtle",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ArrowDown, { className: "size-3.5" }), "Interactive demo — Generate, copy, or download a sample export."]
			})] })]
		})
	});
}
var STEPS = [
	{
		n: "01",
		title: "Point it at a folder",
		body: "Pass a path on the command line, pick a folder in the desktop window, or type it into the terminal menu. That is the only input."
	},
	{
		n: "02",
		title: "It walks, filters, and writes",
		body: "LLMScribe builds a directory tree, skips junk and .gitignore matches, and concatenates every supported source file into one document."
	},
	{
		n: "03",
		title: "Paste it into an AI chat",
		body: "The .txt is ready for ChatGPT, Claude, Grok, Cursor, or anything else that can read a project as text. Copy, open, or save it wherever you like."
	}
];
function HowItWorks() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("section", {
		id: "how",
		className: "scroll-mt-20 border-t border-border",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-xs tracking-widest text-primary uppercase",
					children: "How it works"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
					className: "display mt-3 max-w-xl text-3xl sm:text-4xl",
					children: "One walk through the tree. One file out."
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("ol", {
					className: "mt-12 grid gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-3",
					children: STEPS.map((step) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", {
						className: "bg-bg p-6 sm:p-8",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "font-mono text-xs text-primary",
								children: step.n
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
								className: "mt-4 text-lg font-medium",
								children: step.title
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "mt-2 text-sm leading-relaxed text-muted",
								children: step.body
							})
						]
					}, step.n))
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("blockquote", {
					className: "mt-14 max-w-2xl",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "display text-2xl italic text-fg sm:text-3xl",
						children: "Made for people who just want to give their whole project to an AI without fighting with copy-paste."
					})
				})
			]
		})
	});
}
var SOURCE = `git clone https://github.com/AMRITO-KUNDU/LLMScribe.git
cd LLMScribe
pip install -e .`;
var LINUX_TK = `# Ubuntu / Debian
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk`;
function Install() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("section", {
		id: "install",
		className: "scroll-mt-20 border-t border-border",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-xs tracking-widest text-primary uppercase",
					children: "Install"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
					className: "display mt-3 text-3xl sm:text-4xl",
					children: "On PyPI. One command."
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
					className: "mt-4 max-w-xl text-muted",
					children: [
						"Requires Python ",
						SITE.python,
						". After install, three commands are on your PATH."
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mt-10 overflow-hidden rounded-xl border border-border bg-surface",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-3",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "font-mono text-xs text-muted",
							children: "From PyPI"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyButton, { text: SITE.install })]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("pre", {
						className: "overflow-x-auto p-5 font-mono text-lg text-primary sm:text-xl",
						children: SITE.install
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mt-6 grid gap-6 lg:grid-cols-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CodePanel, {
						title: "From source",
						code: SOURCE
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CodePanel, {
						title: "Linux GUI (Tkinter)",
						code: LINUX_TK,
						note: "Only needed if the desktop window fails to open. The CLI always works without it."
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("dl", {
					className: "mt-10 grid gap-6 sm:grid-cols-3",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Fact, {
							term: "llmscribe",
							def: "Command-line tool. Fastest once you know the path."
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Fact, {
							term: "llmscribe-gui",
							def: "Desktop window. Recommended for most people."
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Fact, {
							term: "llmscribe-cui",
							def: "Numbered menu in the terminal."
						})
					]
				})
			]
		})
	});
}
function CodePanel({ title, code, note }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "overflow-hidden rounded-xl border border-border bg-surface",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between gap-3 border-b border-border px-5 py-3",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "font-mono text-xs text-muted",
					children: title
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyButton, { text: code })]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("pre", {
				className: "overflow-x-auto p-5 font-mono text-sm leading-relaxed text-fg/90",
				children: code
			}),
			note ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "border-t border-border px-5 py-3 text-xs text-subtle",
				children: note
			}) : null
		]
	});
}
function Fact({ term, def }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "rounded-xl border border-border bg-bg p-5",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("dt", {
			className: "font-mono text-sm text-primary",
			children: term
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("dd", {
			className: "mt-2 text-sm text-muted",
			children: def
		})]
	});
}
var Tabs = Root2$1;
var TabsList = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(List, {
	ref,
	className: cn("inline-flex h-11 items-center justify-center rounded-lg border border-border bg-surface p-1 text-muted", className),
	...props
}));
TabsList.displayName = List.displayName;
var TabsTrigger = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Trigger, {
	ref,
	className: cn("inline-flex h-9 items-center justify-center rounded-md px-4 text-sm font-medium whitespace-nowrap transition-colors", "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/70", "disabled:pointer-events-none disabled:opacity-50", "data-[state=active]:bg-elevated data-[state=active]:text-fg", className),
	...props
}));
TabsTrigger.displayName = Trigger.displayName;
var TabsContent = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Content, {
	ref,
	className: cn("mt-6 focus-visible:outline-none", className),
	...props
}));
TabsContent.displayName = Content.displayName;
var CLI = `llmscribe --path /path/to/your/project

# Save to a specific place
llmscribe --path ~/Documents/my-app --output ~/Desktop/my-app.txt

# Only the folder tree (no file contents)
llmscribe --path ~/Documents/my-app --tree-only

# Open the graphical folder picker
llmscribe --gui`;
var CUI = `LLMScribe CUI
1) Enter project folder path
2) Open GUI folder picker
3) Quit
Choose an option [1-3]:`;
function Interfaces() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("section", {
		id: "interfaces",
		className: "scroll-mt-20 border-t border-border",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-xs tracking-widest text-primary uppercase",
					children: "Three interfaces"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
					className: "display mt-3 max-w-2xl text-3xl sm:text-4xl",
					children: "A desktop window, a terminal menu, and a scriptable CLI."
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "mt-4 max-w-xl text-muted",
					children: "Install once. Use whichever fits the moment — recommended GUI for most people, CLI when you already know the path, CUI if you prefer a numbered menu."
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tabs, {
					defaultValue: "gui",
					className: "mt-10",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsList, {
							className: "w-full max-w-md sm:w-auto",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
									value: "gui",
									className: "flex-1 sm:flex-none",
									children: "GUI"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
									value: "cli",
									className: "flex-1 sm:flex-none",
									children: "CLI"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
									value: "cui",
									className: "flex-1 sm:flex-none",
									children: "CUI"
								})
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
							value: "gui",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(InterfaceCard, {
								title: "llmscribe-gui",
								blurb: "A window appears. Choose a folder, optionally rename the output, tick Tree only if you only want structure, then Generate. When it finishes you can Copy the text or Open the saved file.",
								command: "llmscribe-gui",
								extra: "Also: llmscribe --gui  ·  python -m llmscribe.gui"
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
							value: "cli",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(InterfaceCard, {
								title: "llmscribe",
								blurb: "Fastest once you know the path. Default output is project_overview.txt in the folder where you ran the command.",
								command: CLI,
								extra: "Requires Python 3.10 or newer. Tkinter is not needed for CLI mode."
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
							value: "cui",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(InterfaceCard, {
								title: "llmscribe-cui",
								blurb: "A simple numbered menu in the terminal. Type 1 and paste a path, or type 2 to open the same graphical folder picker used by the desktop app.",
								command: CUI
							})
						})
					]
				})
			]
		})
	});
}
function InterfaceCard({ title, blurb, command, extra }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "overflow-hidden rounded-xl border border-border bg-surface",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "flex flex-wrap items-start justify-between gap-3 border-b border-border px-5 py-4",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-sm text-primary",
					children: title
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "mt-1 max-w-2xl text-sm text-muted",
					children: blurb
				}),
				extra ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "mt-2 font-mono text-xs text-subtle",
					children: extra
				}) : null
			] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyButton, { text: command })]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("pre", {
			className: "overflow-x-auto p-5 font-mono text-sm leading-relaxed text-fg/90",
			children: command
		})]
	});
}
function Output() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("section", {
		id: "output",
		className: "scroll-mt-20 border-t border-border",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-24",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid gap-10 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:items-start",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "font-mono text-xs tracking-widest text-primary uppercase",
						children: "The output"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
						className: "display mt-3 text-3xl sm:text-4xl",
						children: "A directory tree, then every file, in one document."
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "mt-4 text-muted",
						children: "The export is plain text. No wrappers, no JSON schema, no extra markup — so you can paste the whole file straight into an AI chat."
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("ul", {
						className: "mt-6 space-y-3 text-sm text-muted",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", {
								className: "flex gap-3",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" }), "Tree first, so the model sees structure before contents."]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", {
								className: "flex gap-3",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" }), "Each file headed with its path, then the full source."]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", {
								className: "flex gap-3",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" }),
									"Default filename:",
									" ",
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("code", {
										className: "font-mono text-fg",
										children: "project_overview.txt"
									})
								]
							})
						]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "mt-6",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CopyButton, {
							text: SAMPLE_FULL,
							label: "Copy sample",
							size: "default"
						})
					})
				] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "overflow-hidden rounded-xl border border-border bg-surface",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex items-center justify-between border-b border-border px-4 py-2.5",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "font-mono text-xs text-muted",
							children: "project_overview.txt"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "font-mono text-xs text-subtle",
							children: "sample"
						})]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("pre", {
						className: "max-h-[28rem] overflow-auto p-5 font-mono text-xs leading-relaxed text-fg/90 sm:text-sm",
						children: SAMPLE_FULL
					})]
				})]
			})
		})
	});
}
function Home() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		id: "top",
		className: "min-h-dvh",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
				href: "#main",
				className: "sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-foreground",
				children: "Skip to content"
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Header, {}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("main", {
				id: "main",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Hero, {}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(HowItWorks, {}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Interfaces, {}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Output, {}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Features, {}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Install, {}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Api, {}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Faq, {}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(FinalCta, {})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Footer, {})
		]
	});
}
//#endregion
export { Home as component };
