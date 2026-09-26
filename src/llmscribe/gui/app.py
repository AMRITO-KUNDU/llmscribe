"""Modern LLMScribe GUI — platform-native dark design language.

Adapts its palette and typography to the host platform:
  • Windows  -> Fluent-style dark (Segoe UI, light-blue accent)
  • Linux    -> GNOME/Adwaita-style dark (Cantarell/Ubuntu, blue accent)
  • macOS    -> San Francisco type, iOS/macOS-style dark palette
  • other    -> falls back to the Linux/Adwaita palette

Uses ttk (not hand-rolled Canvas widgets) for every interactive control
so that grid alignment, stretching and hover/disabled states are handled
by Tk's own layout engine rather than custom code — this keeps buttons,
entries and scrollbars pixel-aligned with each other at any window size.
"""

from __future__ import annotations

import os
import platform
import queue
import threading
import webbrowser
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class _WorkerResult:
    ok: bool
    message: str
    output_file: Path | None = None
    summary: str | None = None


def pick_folder_gui() -> Path | None:
    """Open a folder-picker dialog and return the selected path."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        folder = filedialog.askdirectory(title="Select Project Folder")
        root.destroy()
        return Path(folder) if folder else None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────
# Platform-aware design tokens
# ─────────────────────────────────────────────────────────

def _first_available_font(candidates: list[str], available: set[str]) -> str:
    for name in candidates:
        if name in available:
            return name
    return "TkDefaultFont"


def _resolve_theme(available_fonts: set[str]) -> dict:
    system = platform.system()  # "Windows" | "Linux" | "Darwin"

    if system == "Windows":
        colors = dict(
            BG="#202020", SURFACE="#2c2c2c", SURFACE2="#383838",
            SURFACE3="#454545", BORDER="#3f3f3f",
            ACCENT="#60cdff", ACCENT_HOV="#7fd8ff", ACCENT_PRESS="#3fb8ee",
            TEXT="#ffffff", SUBTEXT="#c5c5c5", MUTED="#8a8a8a",
            SUCCESS="#6ccb5f", ERROR_C="#ff99a4",
            ON_ACCENT="#000000",
        )
        ui_candidates = ["Segoe UI Variable Text", "Segoe UI", "Segoe UI Semibold"]
        title_candidates = ["Segoe UI Variable Display", "Segoe UI Semibold", "Segoe UI"]
        mono_candidates = ["Cascadia Code", "Cascadia Mono", "Consolas"]
        icon_candidates = ["Segoe UI Symbol", "Segoe UI"]
    elif system == "Darwin":
        colors = dict(
            BG="#1c1c1e", SURFACE="#242426", SURFACE2="#2e2e30",
            SURFACE3="#3a3a3c", BORDER="#3a3a3c",
            ACCENT="#0a84ff", ACCENT_HOV="#3395ff", ACCENT_PRESS="#0069d9",
            TEXT="#f5f5f7", SUBTEXT="#a1a1a6", MUTED="#8e8e93",
            SUCCESS="#32d74b", ERROR_C="#ff453a",
            ON_ACCENT="#ffffff",
        )
        ui_candidates = ["SF Pro Text", "Helvetica Neue", "Helvetica"]
        title_candidates = ["SF Pro Display", "Helvetica Neue"]
        mono_candidates = ["SF Mono", "Menlo", "Monaco"]
        icon_candidates = ["SF Pro Text", "Helvetica Neue"]
    else:  # Linux and everything else -> GNOME / Adwaita-dark
        colors = dict(
            BG="#1e1e1e", SURFACE="#2d2d2d", SURFACE2="#383838",
            SURFACE3="#454545", BORDER="#444444",
            ACCENT="#3584e4", ACCENT_HOV="#4a90e8", ACCENT_PRESS="#2b6dc4",
            TEXT="#eeeeec", SUBTEXT="#b3b3b0", MUTED="#8a8a87",
            SUCCESS="#57e389", ERROR_C="#ff7b63",
            ON_ACCENT="#ffffff",
        )
        ui_candidates = ["Cantarell", "Ubuntu", "Noto Sans", "DejaVu Sans"]
        title_candidates = ["Cantarell", "Ubuntu", "Noto Sans"]
        mono_candidates = ["JetBrains Mono", "Ubuntu Mono", "Noto Sans Mono", "DejaVu Sans Mono"]
        icon_candidates = ["Noto Sans Symbols", "DejaVu Sans"]

    ui_font = _first_available_font(ui_candidates, available_fonts)
    title_font = _first_available_font(title_candidates, available_fonts)
    mono_font = _first_available_font(mono_candidates, available_fonts)
    icon_font = _first_available_font(icon_candidates, available_fonts)

    fonts = dict(
        UI=(ui_font, 10),
        LABEL=(ui_font, 9),
        LABEL_CAPS=(ui_font, 8),
        TITLE=(title_font, 14, "bold"),
        MONO=(mono_font, 10),
        STATUS=(ui_font, 9),
        BTN=(ui_font, 10, "bold" if system != "Darwin" else "normal"),
        ICON=(icon_font, 12),
    )

    return {"system": system, **colors, "fonts": fonts}


class ToggleSwitch:
    """A pill-shaped on/off switch bound to a tk.BooleanVar.

    Both Windows 11 Settings and GNOME Settings use this in place of a
    checkbox for boolean options — it's fixed-size and self-contained,
    so it doesn't interact with (or destabilize) the grid layout the
    way a stretching custom widget would.
    """

    def __init__(self, parent, theme, variable, on_toggle=None, width=42, height=24):
        import tkinter as tk
        self.theme = theme
        self.var = variable
        self.on_toggle = on_toggle
        self.w, self.h = width, height
        self.r = height / 2

        self.canvas = tk.Canvas(
            parent, width=width, height=height, bg=parent.cget("bg"),
            highlightthickness=0, bd=0, cursor="hand2",
        )
        self._draw()
        self.canvas.bind("<Button-1>", self._toggle)

    def _round_pts(self, x1, y1, x2, y2, r):
        return [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]

    def _draw(self):
        t = self.theme
        on = self.var.get()
        track = t["ACCENT"] if on else t["SURFACE3"]
        c = self.canvas
        c.delete("all")
        pts = self._round_pts(0, 0, self.w, self.h, self.r)
        c.create_polygon(pts, fill=track, outline=track, smooth=True)
        knob_x = self.w - self.r if on else self.r
        pad = 3
        c.create_oval(
            knob_x - self.r + pad, pad, knob_x + self.r - pad, self.h - pad,
            fill="#ffffff", outline="",
        )

    def _toggle(self, _event=None):
        self.var.set(not self.var.get())
        self._draw()
        if self.on_toggle:
            self.on_toggle()

    def grid(self, **kw):
        self.canvas.grid(**kw)


# ─────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────

def main() -> None:
    try:
        import tkinter as tk
        from tkinter import filedialog, ttk, font as tkfont
    except ImportError as exc:
        raise SystemExit("Tkinter is required to run the GUI.") from exc

    from llmscribe.core.writer import build_project_summary

    SIDE_PAD = 24  # single inset used by every row so left/right edges line up

    class App(tk.Tk):
        def __init__(self):
            super().__init__()
            self.withdraw()  # hide until themed, to avoid a flash of default styling

            available = set(tkfont.families(self))
            self.theme = _resolve_theme(available)
            T = self.theme

            self.title("LLMScribe")
            self.geometry("1180x720")
            self.minsize(880, 560)
            self.configure(bg=T["BG"])

            self._queue: queue.Queue[_WorkerResult] = queue.Queue()
            self._running = False
            self._last_summary: str = ""
            self._last_output_file: Path | None = None

            self.project_var = tk.StringVar()
            self.output_var = tk.StringVar(value=str(Path.cwd() / "project_overview.txt"))
            self.tree_only_var = tk.BooleanVar(value=False)

            self._apply_ttk_style()
            self._build_ui()
            self.bind("<Return>", lambda _: self._start_generate())
            self.after(100, self._poll_queue)

            self.deiconify()

        # ── ttk styling (buttons + scrollbars) ─────

        def _apply_ttk_style(self) -> None:
            T = self.theme
            style = ttk.Style(self)
            try:
                style.theme_use("clam")  # only clam reliably honors custom colors
            except Exception:
                pass

            # Flat button base: no dotted focus ring, no relief border —
            # just padding + label, so height/width are entirely predictable
            # and match across every button in the sidebar.
            flat_layout = [(
                "Button.padding", {
                    "children": [("Button.label", {"sticky": "nswe"})],
                    "sticky": "nswe",
                }
            )]
            style.layout("Primary.TButton", flat_layout)  # type: ignore[arg-type]
            style.layout("Secondary.TButton", flat_layout)  # type: ignore[arg-type]
            style.layout("Icon.TButton", flat_layout)  # type: ignore[arg-type]

            style.configure(
                "Primary.TButton", background=T["ACCENT"], foreground=T["ON_ACCENT"],
                font=T["fonts"]["BTN"], padding=(16, 11), borderwidth=0, relief="flat",
            )
            style.map(
                "Primary.TButton",
                background=[("disabled", T["SURFACE"]), ("pressed", T["ACCENT_PRESS"]),
                            ("active", T["ACCENT_HOV"])],
                foreground=[("disabled", T["MUTED"])],
            )

            style.configure(
                "Secondary.TButton", background=T["SURFACE2"], foreground=T["SUBTEXT"],
                font=T["fonts"]["UI"], padding=(12, 9), borderwidth=0, relief="flat",
            )
            style.map(
                "Secondary.TButton",
                background=[("disabled", T["SURFACE"]), ("pressed", T["SURFACE2"]),
                            ("active", T["SURFACE3"])],
                foreground=[("disabled", T["MUTED"]), ("active", T["TEXT"])],
            )

            style.configure(
                "Icon.TButton", background=T["SURFACE2"], foreground=T["SUBTEXT"],
                font=T["fonts"]["ICON"], padding=(10, 8), borderwidth=0, relief="flat",
            )
            style.map(
                "Icon.TButton",
                background=[("pressed", T["SURFACE2"]), ("active", T["SURFACE3"])],
                foreground=[("active", T["TEXT"])],
            )

            # Flat, arrow-less scrollbars (the GTK/Fluent "overlay-style" look) —
            # the stock clam scrollbar draws chunky arrow buttons at both ends,
            # which is what read as "odd" in the dark theme.
            style.element_create("Flat.Vertical.Scrollbar.trough", "from", "clam")
            style.element_create("Flat.Vertical.Scrollbar.thumb", "from", "clam")
            style.layout("Modern.Vertical.TScrollbar", [  # type: ignore[arg-type]
                ("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
                    ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"}),
                ]}),
            ])
            style.layout("Modern.Horizontal.TScrollbar", [  # type: ignore[arg-type]
                ("Horizontal.Scrollbar.trough", {"sticky": "ew", "children": [
                    ("Horizontal.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"}),
                ]}),
            ])
            for name in ("Modern.Vertical.TScrollbar", "Modern.Horizontal.TScrollbar"):
                style.configure(
                    name, troughcolor=T["BG"], background=T["SURFACE3"],
                    bordercolor=T["BG"], relief="flat", gripcount=0,
                    arrowsize=0, width=11,
                )
                style.map(name, background=[("active", T["ACCENT"])])

        # ── Widget helpers ──────────────────────────

        def _label(self, parent, text, font=None, color=None, **kw) -> tk.Label:
            T = self.theme
            return tk.Label(
                parent, text=text, font=font or T["fonts"]["LABEL"],
                fg=color or T["SUBTEXT"], bg=parent.cget("bg"), anchor="w", **kw,
            )

        def _entry(self, parent, textvariable, **kw) -> tk.Entry:
            T = self.theme
            return tk.Entry(
                parent, textvariable=textvariable, font=T["fonts"]["UI"],
                bg=T["SURFACE2"], fg=T["TEXT"], insertbackground=T["ACCENT"],
                relief="flat", bd=0, highlightthickness=1,
                highlightbackground=T["BORDER"], highlightcolor=T["ACCENT"],
                **kw,
            )

        def _divider(self, parent, **grid_kw) -> None:
            T = self.theme
            tk.Frame(parent, bg=T["BORDER"], height=1).grid(sticky="ew", **grid_kw)

        # ── Layout ──────────────────────────────────

        def _build_ui(self) -> None:
            self.columnconfigure(0, weight=0, minsize=308)
            self.columnconfigure(1, weight=1)
            self.rowconfigure(0, weight=1)
            self._build_sidebar()
            self._build_preview()

        def _build_sidebar(self) -> None:
            T = self.theme
            sidebar = tk.Frame(self, bg=T["SURFACE"], width=308)
            sidebar.grid(row=0, column=0, sticky="nsew")
            sidebar.grid_propagate(False)
            sidebar.columnconfigure(0, weight=1)

            # Header
            header = tk.Frame(sidebar, bg=T["SURFACE"])
            header.grid(row=0, column=0, sticky="ew", padx=SIDE_PAD, pady=(28, 0))
            tk.Label(header, text="LLMScribe", font=T["fonts"]["TITLE"],
                     fg=T["TEXT"], bg=T["SURFACE"], anchor="w").pack(side="left")
            tk.Label(header, text="  v1", font=T["fonts"]["LABEL"],
                     fg=T["MUTED"], bg=T["SURFACE"], anchor="w").pack(side="left")

            self._divider(sidebar, row=1, column=0, padx=SIDE_PAD, pady=(16, 0))

            # Form — every row below shares one column layout: a stretchy
            # column 0 and, where present, a fixed-width column 1. That is
            # what keeps the entries, icon buttons and toggle lined up on
            # the same right edge regardless of window width.
            form = tk.Frame(sidebar, bg=T["SURFACE"])
            form.grid(row=2, column=0, sticky="ew", padx=SIDE_PAD, pady=(20, 0))
            form.columnconfigure(0, weight=1)

            self._label(form, "PROJECT FOLDER", font=T["fonts"]["LABEL_CAPS"]).grid(
                row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
            row_proj = tk.Frame(form, bg=T["SURFACE"])
            row_proj.grid(row=1, column=0, columnspan=2, sticky="ew")
            row_proj.columnconfigure(0, weight=1)
            entry_proj = self._entry(row_proj, self.project_var)
            entry_proj.grid(row=0, column=0, sticky="ew", ipady=8)
            entry_proj.bind("<FocusOut>", lambda _: self._refresh_output_path())
            ttk.Button(row_proj, text="\U0001F4C2", style="Icon.TButton",
                       command=self._browse_project).grid(row=0, column=1, sticky="ns", padx=(8, 0))

            self._label(form, "OUTPUT FILE", font=T["fonts"]["LABEL_CAPS"]).grid(
                row=2, column=0, columnspan=2, sticky="ew", pady=(20, 6))
            row_out = tk.Frame(form, bg=T["SURFACE"])
            row_out.grid(row=3, column=0, columnspan=2, sticky="ew")
            row_out.columnconfigure(0, weight=1)
            entry_out = self._entry(row_out, self.output_var)
            entry_out.grid(row=0, column=0, sticky="ew", ipady=8)
            ttk.Button(row_out, text="\U0001F4BE", style="Icon.TButton",
                       command=self._browse_output).grid(row=0, column=1, sticky="ns", padx=(8, 0))

            # Tree-only toggle row — same two-column split as the rows above,
            # so the switch's right edge lines up with the icon buttons'.
            row_toggle = tk.Frame(form, bg=T["SURFACE"])
            row_toggle.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(22, 0))
            row_toggle.columnconfigure(0, weight=1)
            self._label(row_toggle, "Tree only (skip file contents)",
                        font=T["fonts"]["UI"], color=T["TEXT"]).grid(row=0, column=0, sticky="w")
            self._tree_toggle = ToggleSwitch(row_toggle, T, self.tree_only_var)
            self._tree_toggle.grid(row=0, column=1, sticky="e")

            # Generate — full width, native ttk stretching (no manual resize code)
            self._generate_btn = ttk.Button(
                form, text="Generate", style="Primary.TButton", command=self._start_generate,
            )
            self._generate_btn.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(24, 0))

            self._divider(sidebar, row=3, column=0, padx=SIDE_PAD, pady=(28, 0))

            # Secondary actions — equal-width columns, both buttons stretch together
            actions = tk.Frame(sidebar, bg=T["SURFACE"])
            actions.grid(row=4, column=0, sticky="ew", padx=SIDE_PAD, pady=(14, 0))
            actions.columnconfigure(0, weight=1, uniform="actions")
            actions.columnconfigure(1, weight=1, uniform="actions")
            self._copy_btn = ttk.Button(actions, text="Copy output", style="Secondary.TButton",
                                         command=self._copy_all)
            self._copy_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
            self._open_btn = ttk.Button(actions, text="Open file", style="Secondary.TButton",
                                         command=self._open_last_output)
            self._open_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

            # Status
            self._status_var = tk.StringVar(value="Ready")
            self._status_lbl = tk.Label(
                sidebar, textvariable=self._status_var, font=T["fonts"]["STATUS"],
                fg=T["SUBTEXT"], bg=T["SURFACE"], anchor="w",
            )
            self._status_lbl.grid(row=5, column=0, sticky="ew", padx=SIDE_PAD, pady=(16, 0))

            tk.Frame(sidebar, bg=T["SURFACE"]).grid(row=6, column=0, sticky="nsew")
            sidebar.rowconfigure(6, weight=1)

            self._divider(sidebar, row=7, column=0, padx=0)
            tk.Label(
                sidebar, text="Scans text files \u00b7 respects .gitignore",
                font=T["fonts"]["LABEL_CAPS"], fg=T["MUTED"], bg=T["SURFACE"], anchor="w",
            ).grid(row=8, column=0, sticky="ew", padx=SIDE_PAD, pady=(10, 18))

        def _build_preview(self) -> None:
            T = self.theme
            pane = tk.Frame(self, bg=T["BG"])
            pane.grid(row=0, column=1, sticky="nsew")
            pane.columnconfigure(0, weight=1)
            pane.rowconfigure(1, weight=1)

            bar = tk.Frame(pane, bg=T["SURFACE"])
            bar.grid(row=0, column=0, sticky="ew")
            bar.columnconfigure(1, weight=1)
            tk.Frame(bar, bg=T["BORDER"], width=1).grid(row=0, column=0, sticky="ns")
            tk.Label(bar, text="Preview", font=T["fonts"]["LABEL"], fg=T["SUBTEXT"],
                     bg=T["SURFACE"], anchor="w", padx=18, pady=11).grid(row=0, column=1, sticky="w")
            self._line_var = tk.StringVar(value="")
            tk.Label(bar, textvariable=self._line_var, font=T["fonts"]["LABEL"],
                     fg=T["MUTED"], bg=T["SURFACE"], anchor="e", padx=18).grid(row=0, column=2, sticky="e")

            text_frame = tk.Frame(pane, bg=T["BG"])
            text_frame.grid(row=1, column=0, sticky="nsew")
            text_frame.columnconfigure(1, weight=1)
            text_frame.rowconfigure(0, weight=1)
            tk.Frame(text_frame, bg=T["BORDER"], width=1).grid(row=0, column=0, sticky="ns")

            self.preview = tk.Text(
                text_frame, wrap="none", bg=T["BG"], fg=T["TEXT"], relief="flat", bd=0,
                font=T["fonts"]["MONO"], padx=22, pady=20, insertbackground=T["ACCENT"],
                selectbackground=T["SURFACE2"], selectforeground=T["TEXT"],
                highlightthickness=0, state="disabled", cursor="arrow",
            )
            self.preview.grid(row=0, column=1, sticky="nsew")

            scrollbar_v = ttk.Scrollbar(text_frame, orient="vertical", command=self.preview.yview,
                                        style="Modern.Vertical.TScrollbar")
            scrollbar_v.grid(row=0, column=2, sticky="ns")
            scrollbar_h = ttk.Scrollbar(text_frame, orient="horizontal", command=self.preview.xview,
                                        style="Modern.Horizontal.TScrollbar")
            scrollbar_h.grid(row=1, column=1, sticky="ew")
            self.preview.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

            self._set_preview_text(
                "Select a project folder and press Generate.\n\nThe output will appear here."
            )

        # ── Actions ──────────────────────────────

        def _browse_project(self) -> None:
            folder = filedialog.askdirectory(title="Select Project Folder")
            if not folder:
                return
            self.project_var.set(folder)
            self._refresh_output_path()

        def _browse_output(self) -> None:
            initial = Path(self.output_var.get() or "project_overview.txt")
            path = filedialog.asksaveasfilename(
                title="Save Output As", defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialdir=str(initial.parent) if initial.parent.exists() else None,
                initialfile=initial.name,
            )
            if path:
                self.output_var.set(path)

        def _refresh_output_path(self) -> None:
            text = self.project_var.get().strip()
            if not text:
                return
            project_path = Path(text).expanduser()
            self.output_var.set(str(project_path / "project_overview.txt"))

        def _set_status(self, msg: str, color: str | None = None) -> None:
            self._status_var.set(msg)
            self._status_lbl.configure(fg=color or self.theme["SUBTEXT"])

        def _set_running(self, running: bool) -> None:
            self._running = running
            if running:
                self._generate_btn.configure(text="Generating\u2026", state="disabled")
            else:
                self._generate_btn.configure(text="Generate", state="normal")

        def _start_generate(self) -> None:
            if self._running:
                return

            project_text = self.project_var.get().strip()
            output_text = self.output_var.get().strip()
            tree_only = self.tree_only_var.get()

            if not project_text:
                self._set_status("\u26a0  Choose a project folder first.", self.theme["ERROR_C"])
                return

            project_path = Path(project_text).expanduser()
            if not project_path.exists() or not project_path.is_dir():
                self._set_status("\u26a0  Project folder path is invalid.", self.theme["ERROR_C"])
                return

            output_file = Path(output_text or "project_overview.txt").expanduser()

            self._set_preview_text("Scanning\u2026")
            self._set_status("Scanning project (tree only)\u2026" if tree_only else "Scanning project\u2026")
            self._line_var.set("")
            self._set_running(True)

            def worker() -> None:
                try:
                    summary = build_project_summary(project_path.resolve(), tree_only=tree_only)
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text(summary, encoding="utf-8")
                except Exception as exc:
                    self._queue.put(_WorkerResult(False, f"Failed: {exc}"))
                    return
                self._queue.put(_WorkerResult(True, "Done.", output_file=output_file, summary=summary))

            threading.Thread(target=worker, daemon=True).start()

        def _poll_queue(self) -> None:
            try:
                result = self._queue.get_nowait()
            except queue.Empty:
                self.after(100, self._poll_queue)
                return

            self._set_running(False)

            if result.ok and result.output_file and result.summary:
                self._last_output_file = result.output_file
                self._last_summary = result.summary
                self._set_preview_text(result.summary)
                lines = result.summary.count("\n")
                self._line_var.set(f"{lines:,} lines")
                self._set_status(f"\u2713  Saved to {result.output_file.name}", self.theme["SUCCESS"])
            else:
                self._set_status(result.message, self.theme["ERROR_C"])

            self.after(100, self._poll_queue)

        def _set_preview_text(self, text: str) -> None:
            self.preview.configure(state="normal")
            self.preview.delete("1.0", "end")
            self.preview.insert("end", text)
            self.preview.configure(state="disabled")

        def _copy_all(self) -> None:
            if not self._last_summary:
                return
            self.clipboard_clear()
            self.clipboard_append(self._last_summary)
            self.update_idletasks()
            self._set_status("Copied to clipboard.", self.theme["SUCCESS"])

        def _open_last_output(self) -> None:
            if self._last_output_file is None:
                return
            self._open_path(self._last_output_file)

        def _open_path(self, path: Path) -> None:
            try:
                os.startfile(path)  # type: ignore[attr-defined]
                return
            except Exception:
                pass
            try:
                webbrowser.open(path.resolve().as_uri())
            except Exception:
                return

    App().mainloop()


if __name__ == "__main__":
    main()