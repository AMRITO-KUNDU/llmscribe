"""Modern LLMScribe GUI — built on customtkinter for real anti-aliased widgets.

Why customtkinter instead of plain Tkinter/ttk:
  Plain Tk/ttk has no anti-aliasing and no image-based rendering, so any
  rounded corner or pill shape has to be hand-drawn on a Canvas and comes
  out visibly jagged. customtkinter renders every control (buttons,
  switches, entries, scrollbars) as anti-aliased images and redraws them
  automatically on resize, so corners are actually smooth and the toggle
  switch/scrollbar look like real, finished controls rather than an
  approximation.

Platform-aware accent color (kept from the previous version): the shapes
now come from customtkinter itself, but the palette still leans toward a
Windows-Fluent-ish light blue on Windows and a GNOME/Adwaita-ish blue on
Linux, so the app doesn't look identical everywhere.
"""

from __future__ import annotations

import os
import platform
import queue
import threading
import webbrowser
from dataclasses import dataclass
from pathlib import Path

import customtkinter as ctk


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
            BG="#202020", SURFACE="#2b2b2b", SURFACE2="#353535",
            SURFACE3="#454545", BORDER="#3f3f3f",
            ACCENT="#60cdff", ACCENT_HOV="#7fd8ff",
            TEXT="#ffffff", SUBTEXT="#c5c5c5", MUTED="#8a8a8a",
            SUCCESS="#6ccb5f", ERROR_C="#ff99a4", ON_ACCENT="#000000",
        )
        ui_candidates = ["Segoe UI Variable Text", "Segoe UI"]
        title_candidates = ["Segoe UI Variable Display", "Segoe UI Semibold", "Segoe UI"]
        mono_candidates = ["Cascadia Code", "Cascadia Mono", "Consolas"]
    elif system == "Darwin":
        colors = dict(
            BG="#1c1c1e", SURFACE="#242426", SURFACE2="#2e2e30",
            SURFACE3="#3a3a3c", BORDER="#3a3a3c",
            ACCENT="#0a84ff", ACCENT_HOV="#3395ff",
            TEXT="#f5f5f7", SUBTEXT="#a1a1a6", MUTED="#8e8e93",
            SUCCESS="#32d74b", ERROR_C="#ff453a", ON_ACCENT="#ffffff",
        )
        ui_candidates = ["SF Pro Text", "Helvetica Neue", "Helvetica"]
        title_candidates = ["SF Pro Display", "Helvetica Neue"]
        mono_candidates = ["SF Mono", "Menlo", "Monaco"]
    else:  # Linux and everything else -> GNOME / Adwaita-dark
        colors = dict(
            BG="#1e1e1e", SURFACE="#282828", SURFACE2="#333333",
            SURFACE3="#3f3f3f", BORDER="#444444",
            ACCENT="#3584e4", ACCENT_HOV="#4a90e8",
            TEXT="#eeeeec", SUBTEXT="#b3b3b0", MUTED="#8a8a87",
            SUCCESS="#57e389", ERROR_C="#ff7b63", ON_ACCENT="#ffffff",
        )
        ui_candidates = ["Cantarell", "Ubuntu", "Noto Sans", "DejaVu Sans"]
        title_candidates = ["Cantarell", "Ubuntu", "Noto Sans"]
        mono_candidates = ["JetBrains Mono", "Ubuntu Mono", "Noto Sans Mono", "DejaVu Sans Mono"]

    ui_font = _first_available_font(ui_candidates, available_fonts)
    title_font = _first_available_font(title_candidates, available_fonts)
    mono_font = _first_available_font(mono_candidates, available_fonts)

    return {"system": system, "font_ui": ui_font, "font_title": title_font,
            "font_mono": mono_font, **colors}


# ─────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────

def main() -> None:
    from llmscribe.core.writer import build_project_summary

    ctk.set_appearance_mode("dark")

    SIDE_PAD = 24
    RADIUS = 8

    class App(ctk.CTk):
        def __init__(self):
            super().__init__()

            import tkinter.font as tkfont
            available = set(tkfont.families())
            self.theme = _resolve_theme(available)
            T = self.theme

            self.fonts = {
                "title": ctk.CTkFont(family=T["font_title"], size=17, weight="bold"),
                "ui": ctk.CTkFont(family=T["font_ui"], size=13),
                "ui_bold": ctk.CTkFont(family=T["font_ui"], size=13, weight="bold"),
                "label": ctk.CTkFont(family=T["font_ui"], size=11),
                "caps": ctk.CTkFont(family=T["font_ui"], size=10),
                "mono": ctk.CTkFont(family=T["font_mono"], size=13),
                "status": ctk.CTkFont(family=T["font_ui"], size=11),
            }

            self.title("LLMScribe")
            self.geometry("1180x720")
            self.minsize(880, 560)
            self.configure(fg_color=T["BG"])

            self._queue: queue.Queue[_WorkerResult] = queue.Queue()
            self._running = False
            self._last_summary: str = ""
            self._last_output_file: Path | None = None

            self.project_var = ctk.StringVar()
            self.output_var = ctk.StringVar(value=str(Path.cwd() / "project_overview.txt"))
            self.tree_only_var = ctk.BooleanVar(value=False)

            self._build_ui()
            self.bind("<Return>", lambda _: self._start_generate())
            self.after(100, self._poll_queue)

        # ── Layout ──────────────────────────────────

        def _build_ui(self) -> None:
            self.grid_columnconfigure(0, weight=0, minsize=308)
            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(0, weight=1)
            self._build_sidebar()
            self._build_preview()

        def _build_sidebar(self) -> None:
            T, F = self.theme, self.fonts
            sidebar = ctk.CTkFrame(self, width=308, corner_radius=0, fg_color=T["SURFACE"])
            sidebar.grid(row=0, column=0, sticky="nsew")
            sidebar.grid_propagate(False)
            sidebar.grid_columnconfigure(0, weight=1)

            # Header
            header = ctk.CTkFrame(sidebar, fg_color="transparent")
            header.grid(row=0, column=0, sticky="ew", padx=SIDE_PAD, pady=(28, 0))
            ctk.CTkLabel(header, text="LLMScribe", font=F["title"], text_color=T["TEXT"],
                         anchor="w").pack(side="left")
            ctk.CTkLabel(header, text="  v1", font=F["label"], text_color=T["MUTED"],
                         anchor="w").pack(side="left")

            ctk.CTkFrame(sidebar, fg_color=T["BORDER"], height=1, corner_radius=0).grid(
                row=1, column=0, sticky="ew", padx=SIDE_PAD, pady=(16, 0))

            # Form
            form = ctk.CTkFrame(sidebar, fg_color="transparent")
            form.grid(row=2, column=0, sticky="ew", padx=SIDE_PAD, pady=(20, 0))
            form.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(form, text="PROJECT FOLDER", font=F["caps"], text_color=T["SUBTEXT"],
                        anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
            row_proj = ctk.CTkFrame(form, fg_color="transparent")
            row_proj.grid(row=1, column=0, columnspan=2, sticky="ew")
            row_proj.grid_columnconfigure(0, weight=1)
            entry_proj = ctk.CTkEntry(
                row_proj, textvariable=self.project_var, font=F["ui"], height=38,
                corner_radius=RADIUS, fg_color=T["SURFACE2"], border_color=T["BORDER"],
                border_width=1, text_color=T["TEXT"],
            )
            entry_proj.grid(row=0, column=0, sticky="ew")
            entry_proj.bind("<FocusOut>", lambda _: self._refresh_output_path())
            ctk.CTkButton(
                row_proj, text="\U0001F4C2", width=38, height=38, corner_radius=RADIUS,
                fg_color=T["SURFACE2"], hover_color=T["SURFACE3"], text_color=T["SUBTEXT"],
                font=F["ui"], command=self._browse_project,
            ).grid(row=0, column=1, sticky="ns", padx=(8, 0))

            ctk.CTkLabel(form, text="OUTPUT FILE", font=F["caps"], text_color=T["SUBTEXT"],
                        anchor="w").grid(row=2, column=0, columnspan=2, sticky="ew", pady=(20, 6))
            row_out = ctk.CTkFrame(form, fg_color="transparent")
            row_out.grid(row=3, column=0, columnspan=2, sticky="ew")
            row_out.grid_columnconfigure(0, weight=1)
            entry_out = ctk.CTkEntry(
                row_out, textvariable=self.output_var, font=F["ui"], height=38,
                corner_radius=RADIUS, fg_color=T["SURFACE2"], border_color=T["BORDER"],
                border_width=1, text_color=T["TEXT"],
            )
            entry_out.grid(row=0, column=0, sticky="ew")
            ctk.CTkButton(
                row_out, text="\U0001F4BE", width=38, height=38, corner_radius=RADIUS,
                fg_color=T["SURFACE2"], hover_color=T["SURFACE3"], text_color=T["SUBTEXT"],
                font=F["ui"], command=self._browse_output,
            ).grid(row=0, column=1, sticky="ns", padx=(8, 0))

            # Tree-only toggle — a real CTkSwitch: anti-aliased pill + knob
            row_toggle = ctk.CTkFrame(form, fg_color="transparent")
            row_toggle.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(22, 0))
            row_toggle.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row_toggle, text="Tree only (skip file contents)", font=F["ui"],
                        text_color=T["TEXT"], anchor="w").grid(row=0, column=0, sticky="w")
            ctk.CTkSwitch(
                row_toggle, text="", variable=self.tree_only_var, onvalue=True, offvalue=False,
                width=42, height=22, switch_width=42, switch_height=22,
                progress_color=T["ACCENT"], button_color="#ffffff", button_hover_color="#ffffff",
                fg_color=T["SURFACE3"],
            ).grid(row=0, column=1, sticky="e")

            # Generate — full width, genuinely stretches via CTk's own resize handling
            self._generate_btn = ctk.CTkButton(
                form, text="Generate", font=F["ui_bold"], height=44, corner_radius=RADIUS,
                fg_color=T["ACCENT"], hover_color=T["ACCENT_HOV"], text_color=T["ON_ACCENT"],
                command=self._start_generate,
            )
            self._generate_btn.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(24, 0))

            ctk.CTkFrame(sidebar, fg_color=T["BORDER"], height=1, corner_radius=0).grid(
                row=3, column=0, sticky="ew", padx=SIDE_PAD, pady=(28, 0))

            # Secondary actions
            actions = ctk.CTkFrame(sidebar, fg_color="transparent")
            actions.grid(row=4, column=0, sticky="ew", padx=SIDE_PAD, pady=(14, 0))
            actions.grid_columnconfigure(0, weight=1, uniform="actions")
            actions.grid_columnconfigure(1, weight=1, uniform="actions")
            self._copy_btn = ctk.CTkButton(
                actions, text="Copy output", font=F["ui"], height=34, corner_radius=RADIUS,
                fg_color=T["SURFACE2"], hover_color=T["SURFACE3"], text_color=T["SUBTEXT"],
                command=self._copy_all,
            )
            self._copy_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
            self._open_btn = ctk.CTkButton(
                actions, text="Open file", font=F["ui"], height=34, corner_radius=RADIUS,
                fg_color=T["SURFACE2"], hover_color=T["SURFACE3"], text_color=T["SUBTEXT"],
                command=self._open_last_output,
            )
            self._open_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

            # Status
            self._status_lbl = ctk.CTkLabel(
                sidebar, text="Ready", font=F["status"], text_color=T["SUBTEXT"], anchor="w",
            )
            self._status_lbl.grid(row=5, column=0, sticky="ew", padx=SIDE_PAD, pady=(16, 0))

            sidebar.grid_rowconfigure(6, weight=1)
            ctk.CTkFrame(sidebar, fg_color="transparent").grid(row=6, column=0, sticky="nsew")

            ctk.CTkFrame(sidebar, fg_color=T["BORDER"], height=1, corner_radius=0).grid(
                row=7, column=0, sticky="ew")
            ctk.CTkLabel(
                sidebar, text="Scans text files \u00b7 respects .gitignore", font=F["caps"],
                text_color=T["MUTED"], anchor="w",
            ).grid(row=8, column=0, sticky="ew", padx=SIDE_PAD, pady=(10, 18))

        def _build_preview(self) -> None:
            T, F = self.theme, self.fonts
            pane = ctk.CTkFrame(self, fg_color=T["BG"], corner_radius=0)
            pane.grid(row=0, column=1, sticky="nsew")
            pane.grid_columnconfigure(0, weight=1)
            pane.grid_rowconfigure(1, weight=1)

            bar = ctk.CTkFrame(pane, fg_color=T["SURFACE"], corner_radius=0, height=40)
            bar.grid(row=0, column=0, sticky="ew")
            bar.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(bar, text="Preview", font=F["label"], text_color=T["SUBTEXT"],
                        anchor="w").grid(row=0, column=0, sticky="w", padx=18, pady=10)
            self._line_lbl = ctk.CTkLabel(bar, text="", font=F["label"], text_color=T["MUTED"],
                                          anchor="e")
            self._line_lbl.grid(row=0, column=1, sticky="e", padx=18, pady=10)

            # CTkTextbox ships its own anti-aliased x/y scrollbars that only
            # appear when content actually overflows — no manual wiring needed.
            self.preview = ctk.CTkTextbox(
                pane, wrap="none", corner_radius=0, fg_color=T["BG"], text_color=T["TEXT"],
                font=F["mono"], border_width=0, border_spacing=20,
                scrollbar_button_color=T["SURFACE3"], scrollbar_button_hover_color=T["ACCENT"],
                activate_scrollbars=True,
            )
            self.preview.grid(row=1, column=0, sticky="nsew")
            self.preview.configure(state="disabled")

            self._set_preview_text(
                "Select a project folder and press Generate.\n\nThe output will appear here."
            )

        # ── Actions ──────────────────────────────

        def _browse_project(self) -> None:
            from tkinter import filedialog
            folder = filedialog.askdirectory(title="Select Project Folder")
            if not folder:
                return
            self.project_var.set(folder)
            self._refresh_output_path()

        def _browse_output(self) -> None:
            from tkinter import filedialog
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
            self._status_lbl.configure(text=msg, text_color=color or self.theme["SUBTEXT"])

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
            self._line_lbl.configure(text="")
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
                self._line_lbl.configure(text=f"{lines:,} lines")
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