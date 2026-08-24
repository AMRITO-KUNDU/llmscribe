"""Modern LLMScribe GUI — dark developer-tool aesthetic."""

from __future__ import annotations

import os
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


def main() -> None:
    try:
        import tkinter as tk
        from tkinter import filedialog, ttk
    except ImportError as exc:
        raise SystemExit("Tkinter is required to run the GUI.") from exc

    from llmscribe.core.writer import build_project_summary

    # ─────────────────────────────────────────────
    # Tokens
    # ─────────────────────────────────────────────

    BG          = "#0f1117"   # page background
    SURFACE     = "#1a1d27"   # panel / card surface
    SURFACE2    = "#222638"   # input fields, hover states
    BORDER      = "#2e3147"   # subtle dividers
    ACCENT      = "#6366f1"   # indigo — used sparingly
    ACCENT_HOV  = "#4f52d4"   # accent hover
    TEXT        = "#e8eaf0"   # primary text
    SUBTEXT     = "#8b8fa8"   # labels, captions
    SUCCESS     = "#34d399"   # status ok
    ERROR_C     = "#f87171"   # status error

    FONT_UI     = ("Inter",         10)
    FONT_LABEL  = ("Inter",          9)
    FONT_MONO   = ("JetBrains Mono", 10)
    FONT_TITLE  = ("Inter",         13, "bold")
    FONT_STATUS = ("Inter",          9)

    # ─────────────────────────────────────────────
    # ttk style
    # ─────────────────────────────────────────────

    def apply_styles(root: tk.Tk) -> None:
        style = ttk.Style(root)
        style.theme_use("clam")

        style.configure(
            "Vertical.TScrollbar",
            troughcolor=SURFACE,
            background=SURFACE2,
            bordercolor=SURFACE,
            arrowcolor=SUBTEXT,
            relief="flat",
            width=8,
        )
        style.map(
            "Vertical.TScrollbar",
            background=[("active", ACCENT)],
        )

    # ─────────────────────────────────────────────
    # Widget helpers
    # ─────────────────────────────────────────────

    def make_label(parent, text: str, font=None, color=None, **kw) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            font=font or FONT_LABEL,
            fg=color or SUBTEXT,
            bg=SURFACE,
            anchor="w",
            **kw,
        )

    def make_entry(parent, textvariable, **kw) -> tk.Entry:
        return tk.Entry(
            parent,
            textvariable=textvariable,
            font=FONT_UI,
            bg=SURFACE2,
            fg=TEXT,
            insertbackground=ACCENT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            **kw,
        )

    def make_icon_button(parent, text: str, command, width=3) -> tk.Button:
        """Small square button for browse icons."""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI Symbol", 10),
            bg=SURFACE2,
            fg=SUBTEXT,
            activebackground=SURFACE2,
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            width=width,
            cursor="hand2",
            highlightthickness=0,
        )
        btn.bind("<Enter>", lambda _: btn.config(fg=TEXT))
        btn.bind("<Leave>", lambda _: btn.config(fg=SUBTEXT))
        return btn

    def make_checkbutton(parent, text: str, variable, command=None) -> tk.Checkbutton:
        """Checkbox styled to match the dark sidebar."""
        chk = tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            command=command,
            font=FONT_LABEL,
            fg=TEXT,
            bg=SURFACE,
            activebackground=SURFACE,
            activeforeground=TEXT,
            selectcolor=SURFACE2,
            relief="flat",
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            anchor="w",
            padx=0,
        )
        return chk

    # ─────────────────────────────────────────────
    # App
    # ─────────────────────────────────────────────

    class App(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("LLMScribe")
            self.geometry("1160x720")
            self.minsize(860, 560)
            self.configure(bg=BG)

            self._queue: queue.Queue[_WorkerResult] = queue.Queue()
            self._running = False
            self._last_summary: str = ""
            self._last_output_file: Path | None = None

            self.project_var = tk.StringVar()
            self.output_var  = tk.StringVar(
                value=str(Path.cwd() / "project_overview.txt")
            )
            self.tree_only_var = tk.BooleanVar(value=False)

            apply_styles(self)
            self._build_ui()
            self.bind("<Return>", lambda _: self._start_generate())
            self.after(100, self._poll_queue)

        # ── Layout ────────────────────────────────

        def _build_ui(self) -> None:
            # Root: left panel + right preview
            self.columnconfigure(0, weight=0, minsize=300)
            self.columnconfigure(1, weight=1)
            self.rowconfigure(0, weight=1)

            self._build_sidebar()
            self._build_preview()

        def _build_sidebar(self) -> None:
            sidebar = tk.Frame(self, bg=SURFACE, width=300)
            sidebar.grid(row=0, column=0, sticky="nsew")
            sidebar.grid_propagate(False)
            sidebar.columnconfigure(0, weight=1)

            # ── Header ──
            header = tk.Frame(sidebar, bg=SURFACE, pady=0)
            header.grid(row=0, column=0, sticky="ew", padx=24, pady=(28, 0))

            tk.Label(
                header,
                text="LLMScribe",
                font=FONT_TITLE,
                fg=TEXT,
                bg=SURFACE,
                anchor="w",
            ).pack(side="left")

            tk.Label(
                header,
                text="  v1",
                font=FONT_LABEL,
                fg=SUBTEXT,
                bg=SURFACE,
                anchor="w",
            ).pack(side="left")

            # ── Divider ──
            tk.Frame(sidebar, bg=BORDER, height=1).grid(
                row=1, column=0, sticky="ew", padx=24, pady=(16, 0)
            )

            # ── Form ──
            form = tk.Frame(sidebar, bg=SURFACE)
            form.grid(row=2, column=0, sticky="ew", padx=24, pady=(20, 0))
            form.columnconfigure(0, weight=1)

            # Project folder
            make_label(form, "PROJECT FOLDER").grid(
                row=0, column=0, sticky="ew", pady=(0, 4)
            )
            row_proj = tk.Frame(form, bg=SURFACE)
            row_proj.grid(row=1, column=0, sticky="ew")
            row_proj.columnconfigure(0, weight=1)

            entry_proj = make_entry(row_proj, self.project_var)
            entry_proj.grid(row=0, column=0, sticky="ew", ipady=6)
            entry_proj.bind("<FocusOut>", lambda _: self._refresh_output_path())

            make_icon_button(row_proj, "📂", self._browse_project).grid(
                row=0, column=1, sticky="ew", padx=(6, 0)
            )

            # Output file
            make_label(form, "OUTPUT FILE").grid(
                row=2, column=0, sticky="ew", pady=(18, 4)
            )
            row_out = tk.Frame(form, bg=SURFACE)
            row_out.grid(row=3, column=0, sticky="ew")
            row_out.columnconfigure(0, weight=1)

            entry_out = make_entry(row_out, self.output_var)
            entry_out.grid(row=0, column=0, sticky="ew", ipady=6)

            make_icon_button(row_out, "💾", self._browse_output).grid(
                row=0, column=1, sticky="ew", padx=(6, 0)
            )

            # ── Tree-only checkbox ──
            row_tree_only = tk.Frame(form, bg=SURFACE)
            row_tree_only.grid(row=4, column=0, sticky="ew", pady=(16, 0))

            self._tree_only_chk = make_checkbutton(
                row_tree_only,
                "Tree only (skip file contents)",
                self.tree_only_var,
            )
            self._tree_only_chk.grid(row=0, column=0, sticky="w")

            # ── Generate button ──
            self._generate_btn = tk.Button(
                form,
                text="Generate",
                command=self._start_generate,
                font=("Inter", 10, "bold"),
                bg=ACCENT,
                fg="#ffffff",
                activebackground=ACCENT_HOV,
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                cursor="hand2",
                pady=10,
                highlightthickness=0,
            )
            self._generate_btn.grid(
                row=5, column=0, sticky="ew", pady=(20, 0)
            )
            self._generate_btn.bind(
                "<Enter>", lambda _: self._generate_btn.config(bg=ACCENT_HOV)
            )
            self._generate_btn.bind(
                "<Leave>", lambda _: self._generate_btn.config(bg=ACCENT)
            )

            # ── Divider ──
            tk.Frame(sidebar, bg=BORDER, height=1).grid(
                row=3, column=0, sticky="ew", padx=24, pady=(28, 0)
            )

            # ── Secondary actions ──
            actions = tk.Frame(sidebar, bg=SURFACE)
            actions.grid(row=4, column=0, sticky="ew", padx=24, pady=(12, 0))
            actions.columnconfigure(0, weight=1)
            actions.columnconfigure(1, weight=1)

            self._copy_btn = self._make_secondary_btn(
                actions, "Copy output", self._copy_all
            )
            self._copy_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

            self._open_btn = self._make_secondary_btn(
                actions, "Open file", self._open_last_output
            )
            self._open_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

            # ── Status ──
            self._status_var = tk.StringVar(value="Ready")
            self._status_lbl = tk.Label(
                sidebar,
                textvariable=self._status_var,
                font=FONT_STATUS,
                fg=SUBTEXT,
                bg=SURFACE,
                anchor="w",
            )
            self._status_lbl.grid(
                row=5, column=0, sticky="ew", padx=24, pady=(14, 0)
            )

            # ── Spacer ──
            tk.Frame(sidebar, bg=SURFACE).grid(row=6, column=0, sticky="nsew")
            sidebar.rowconfigure(6, weight=1)

            # ── Footer ──
            tk.Frame(sidebar, bg=BORDER, height=1).grid(
                row=7, column=0, sticky="ew", padx=0
            )
            tk.Label(
                sidebar,
                text="Scans text files · respects .gitignore",
                font=("Inter", 8),
                fg=SUBTEXT,
                bg=SURFACE,
                anchor="w",
            ).grid(row=8, column=0, sticky="ew", padx=24, pady=(10, 16))

        def _make_secondary_btn(self, parent, text: str, command) -> tk.Button:
            btn = tk.Button(
                parent,
                text=text,
                command=command,
                font=FONT_LABEL,
                bg=SURFACE2,
                fg=SUBTEXT,
                activebackground=BORDER,
                activeforeground=TEXT,
                relief="flat",
                bd=0,
                pady=8,
                cursor="hand2",
                highlightthickness=0,
            )
            btn.bind("<Enter>", lambda _: btn.config(fg=TEXT, bg=BORDER))
            btn.bind("<Leave>", lambda _: btn.config(fg=SUBTEXT, bg=SURFACE2))
            return btn

        def _build_preview(self) -> None:
            pane = tk.Frame(self, bg=BG)
            pane.grid(row=0, column=1, sticky="nsew")
            pane.columnconfigure(0, weight=1)
            pane.rowconfigure(1, weight=1)

            # Preview header bar
            bar = tk.Frame(pane, bg=SURFACE, pady=0)
            bar.grid(row=0, column=0, sticky="ew")
            bar.columnconfigure(1, weight=1)

            # Faint left border to separate from sidebar
            tk.Frame(bar, bg=BORDER, width=1).grid(row=0, column=0, sticky="ns")

            tk.Label(
                bar,
                text="Preview",
                font=FONT_LABEL,
                fg=SUBTEXT,
                bg=SURFACE,
                anchor="w",
                padx=18,
                pady=10,
            ).grid(row=0, column=1, sticky="w")

            # Line count label (right side)
            self._line_var = tk.StringVar(value="")
            tk.Label(
                bar,
                textvariable=self._line_var,
                font=FONT_LABEL,
                fg=SUBTEXT,
                bg=SURFACE,
                anchor="e",
                padx=18,
            ).grid(row=0, column=2, sticky="e")

            # Text widget + scrollbar
            text_frame = tk.Frame(pane, bg=BG)
            text_frame.grid(row=1, column=0, sticky="nsew")
            text_frame.columnconfigure(0, weight=1)
            text_frame.rowconfigure(0, weight=1)

            # Thin left border line
            tk.Frame(text_frame, bg=BORDER, width=1).grid(
                row=0, column=0, sticky="ns"
            )

            self.preview = tk.Text(
                text_frame,
                wrap="none",
                bg=BG,
                fg=TEXT,
                relief="flat",
                bd=0,
                font=FONT_MONO,
                padx=20,
                pady=20,
                insertbackground=ACCENT,
                selectbackground=SURFACE2,
                selectforeground=TEXT,
                highlightthickness=0,
                state="disabled",
                cursor="arrow",
            )
            self.preview.grid(row=0, column=1, sticky="nsew")
            text_frame.columnconfigure(1, weight=1)

            scrollbar_v = ttk.Scrollbar(
                text_frame,
                orient="vertical",
                command=self.preview.yview,
            )
            scrollbar_v.grid(row=0, column=2, sticky="ns")

            scrollbar_h = ttk.Scrollbar(
                text_frame,
                orient="horizontal",
                command=self.preview.xview,
            )
            scrollbar_h.grid(row=1, column=1, sticky="ew")

            self.preview.configure(
                yscrollcommand=scrollbar_v.set,
                xscrollcommand=scrollbar_h.set,
            )

            # Placeholder
            self._set_preview_text(
                "Select a project folder and press Generate.\n\n"
                "The output will appear here."
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
                title="Save Output As",
                defaultextension=".txt",
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

        def _set_status(self, msg: str, color: str = SUBTEXT) -> None:
            self._status_var.set(msg)
            self._status_lbl.configure(fg=color)

        def _set_running(self, running: bool) -> None:
            self._running = running
            if running:
                self._generate_btn.configure(
                    text="Generating…", state="disabled", bg=SURFACE2, fg=SUBTEXT
                )
            else:
                self._generate_btn.configure(
                    text="Generate", state="normal", bg=ACCENT, fg="#ffffff"
                )

        def _start_generate(self) -> None:
            if self._running:
                return

            project_text = self.project_var.get().strip()
            output_text  = self.output_var.get().strip()
            tree_only    = self.tree_only_var.get()

            if not project_text:
                self._set_status("⚠  Choose a project folder first.", ERROR_C)
                return

            project_path = Path(project_text).expanduser()
            if not project_path.exists() or not project_path.is_dir():
                self._set_status("⚠  Project folder path is invalid.", ERROR_C)
                return

            output_file = Path(output_text or "project_overview.txt").expanduser()

            self._set_preview_text("Scanning…")
            self._set_status(
                "Scanning project (tree only)…" if tree_only else "Scanning project…",
                SUBTEXT,
            )
            self._line_var.set("")
            self._set_running(True)

            def worker() -> None:
                try:
                    summary = build_project_summary(
                        project_path.resolve(), tree_only=tree_only
                    )
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text(summary, encoding="utf-8")
                except Exception as exc:
                    self._queue.put(_WorkerResult(False, f"Failed: {exc}"))
                    return
                self._queue.put(
                    _WorkerResult(True, "Done.", output_file=output_file, summary=summary)
                )

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
                self._last_summary     = result.summary
                self._set_preview_text(result.summary)
                lines = result.summary.count("\n")
                self._line_var.set(f"{lines:,} lines")
                self._set_status(f"✓  Saved to {result.output_file.name}", SUCCESS)
            else:
                self._set_status(result.message, ERROR_C)

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
            self._set_status("Copied to clipboard.", SUCCESS)

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
