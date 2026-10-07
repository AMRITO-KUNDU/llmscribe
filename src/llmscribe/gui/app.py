"""LLMScribe GUI — sage-on-charcoal design with a unified top bar.

Layout: one full-width top bar spans sidebar + preview so the two panes read
as a single surface, with a monospace UI and a serif wordmark.

Requires:  pip install customtkinter pillow
"""

from __future__ import annotations

import os
import queue
import threading
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import customtkinter as ctk
from llmscribe import __version__

APP_VERSION = f"v{__version__}"

# ── Palette ──────────────────────────────────────────────
BG = "#0f110f"
TOPBAR = "#151915"
SIDEBAR = "#131713"
PANE = "#0f110f"
FIELD = "#1b201b"
FIELD_HOV = "#242a24"
BORDER = "#252b26"
BORDER_STRONG = "#353c36"
TEXT = "#d8dcd3"
SUBTEXT = "#9aa195"
MUTED = "#6f766c"
SAGE = "#b9c4ad"
SAGE_HOV = "#c9d3be"
SAGE_DIM = "#5b6455"
ON_SAGE = "#131810"
ERROR_C = "#e58f84"

SIDEBAR_W = 264
PAD = 18


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


# ── Icons (drawn with PIL, supersampled so edges are smooth) ──

def _make_icon(kind: str, color: str, px: int = 18):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None

    S, N = 8, 24
    big = px * S
    k = big / N
    w = max(1, round(1.7 * k))
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def P(x, y):
        return (x * k, y * k)

    if kind == "folder":
        d.rounded_rectangle([3 * k, 8 * k, 21 * k, 19 * k], radius=2 * k, outline=color, width=w)
        d.line([P(3, 9), P(3, 6.5), P(4.5, 5), P(9, 5), P(11, 8)], fill=color, width=w, joint="curve")
    elif kind == "save":
        d.rounded_rectangle([4 * k, 4 * k, 20 * k, 20 * k], radius=2 * k, outline=color, width=w)
        d.rectangle([8 * k, 4 * k, 16 * k, 9 * k], outline=color, width=w)
        d.rounded_rectangle([7 * k, 13 * k, 17 * k, 20 * k], radius=1 * k, outline=color, width=w)
    elif kind == "copy":
        d.rounded_rectangle([9 * k, 9 * k, 20 * k, 20 * k], radius=2 * k, outline=color, width=w)
        d.line([P(9, 15), P(6, 15), P(4, 13), P(4, 6), P(6, 4), P(13, 4), P(15, 6), P(15, 9)],
               fill=color, width=w, joint="curve")

    resample = getattr(Image, "Resampling", None)
    if resample is not None:
        img = img.resize((px * 2, px * 2), resample.LANCZOS)
    try:
        img = img.resize((px * 2, px * 2), Image.Resampling.LANCZOS)
    except AttributeError:
        img = img.resize((px * 2, px * 2), getattr(Image, "LANCZOS", 3))
    return ctk.CTkImage(light_image=img, dark_image=img, size=(px, px))


def _first(candidates: list[str], available: set[str], fallback: str) -> str:
    for name in candidates:
        if name in available:
            return name
    return fallback


def main() -> None:
    import tkinter.font as tkfont
    from tkinter import filedialog

    from llmscribe.core.writer import build_project_summary

    ctk.set_appearance_mode("dark")

    class App(ctk.CTk):
        def __init__(self):
            super().__init__()

            fams = set(tkfont.families())
            mono = _first(
                ["IBM Plex Mono", "JetBrains Mono", "SF Mono", "Cascadia Mono", "Cascadia Code",
                 "Menlo", "Consolas", "DejaVu Sans Mono", "Liberation Mono"],
                fams, "Courier",
            )
            serif = _first(
                ["Iowan Old Style", "Georgia", "Cambria", "Noto Serif", "DejaVu Serif",
                 "Liberation Serif", "Times New Roman"],
                fams, "Times",
            )
            self.F = {
                "brand": ctk.CTkFont(family=serif, size=22),
                "mono": ctk.CTkFont(family=mono, size=13),
                "mono_s": ctk.CTkFont(family=mono, size=12),
                "mono_b": ctk.CTkFont(family=mono, size=12, weight="bold"),
                "caps": ctk.CTkFont(family=mono, size=11),
                "gen": ctk.CTkFont(family=mono, size=13, weight="bold"),
                "preview": ctk.CTkFont(family=mono, size=14),
            }

            self.title("LLMScribe")
            self.geometry("1180x760")
            self.minsize(880, 560)
            self.configure(fg_color=BG)
            
            # Set window icon
            try:
                icon_path = Path(__file__).parent.parent.parent.parent / "docs" / "public" / "favicon.ico"
                if icon_path.exists():
                    self.iconbitmap(str(icon_path))
            except Exception:
                pass  # Icon is optional, don't fail if it doesn't work

            self._queue: queue.Queue[_WorkerResult] = queue.Queue()
            self._running = False
            self._last_summary = ""
            self._last_output_file: Path | None = None

            self.project_var = ctk.StringVar()
            self.output_var = ctk.StringVar(value="project_overview.txt")
            self.tree_only_var = ctk.BooleanVar(value=False)

            self.icons = {
                "folder": _make_icon("folder", SUBTEXT),
                "save": _make_icon("save", SUBTEXT),
                "copy": _make_icon("copy", TEXT, 16),
            }

            self._build_ui()
            self.bind("<Return>", lambda _: self._start_generate())
            self.after(100, self._poll_queue)

        # ── helpers ─────────────────────────────────

        def _hline(self, parent, **grid):
            ctk.CTkFrame(parent, fg_color=BORDER, height=1, corner_radius=0).grid(sticky="ew", **grid)

        def _field(self, parent, var, icon_key, command, placeholder=""):
            """Rounded field with the action icon sitting inside it."""
            box = ctk.CTkFrame(parent, fg_color=FIELD, corner_radius=12, height=44,
                               border_width=1, border_color=FIELD)
            box.grid_propagate(False)
            box.grid_columnconfigure(0, weight=1)
            entry = ctk.CTkEntry(box, textvariable=var, font=self.F["mono_s"], text_color=TEXT,
                                 placeholder_text=placeholder, placeholder_text_color=MUTED,
                                 fg_color="transparent", border_width=0, height=30)
            entry.grid(row=0, column=0, sticky="ew", padx=(6, 0), pady=6)
            icon = self.icons.get(icon_key)
            btn = ctk.CTkButton(box, text="" if icon else "…", image=icon, width=30, height=30,
                                corner_radius=8, fg_color="transparent", hover_color=FIELD_HOV,
                                text_color=SUBTEXT, command=command)
            btn.grid(row=0, column=1, padx=(2, 7), pady=6)
            entry.bind("<FocusIn>", lambda _: box.configure(border_color=SAGE_DIM))
            entry.bind("<FocusOut>", lambda _: box.configure(border_color=FIELD))
            return box, entry

        # ── layout ──────────────────────────────────

        def _build_ui(self) -> None:
            self.grid_columnconfigure(0, weight=0)
            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(0, weight=0)
            self.grid_rowconfigure(1, weight=1)
            self._build_topbar()
            self._build_sidebar()
            self._build_preview()

        def _build_topbar(self) -> None:
            bar = ctk.CTkFrame(self, fg_color=TOPBAR, corner_radius=0, height=42)
            bar.grid(row=0, column=0, columnspan=2, sticky="ew")
            bar.grid_propagate(False)
            bar.grid_columnconfigure((0, 2), weight=1, uniform="tb")
            bar.grid_columnconfigure(1, weight=0)
            bar.grid_rowconfigure(0, weight=1)
            ctk.CTkLabel(bar, text="LLMScribe", font=self.F["mono_s"], text_color=SUBTEXT
                         ).grid(row=0, column=1)
            ctk.CTkLabel(bar, text=APP_VERSION, font=self.F["mono_s"], text_color=MUTED,
                         anchor="e").grid(row=0, column=2, sticky="e", padx=16)
            # bottom border of the bar (overlaid on its last pixel row)
            sep = ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0)
            sep.grid(row=0, column=0, columnspan=2, sticky="sew")

        def _build_sidebar(self) -> None:
            side = ctk.CTkFrame(self, fg_color=SIDEBAR, corner_radius=0, width=SIDEBAR_W)
            side.grid(row=1, column=0, sticky="nsew")
            side.grid_propagate(False)
            side.grid_columnconfigure(0, weight=1)
            side.grid_columnconfigure(1, weight=0)
            side.grid_rowconfigure(0, weight=1)
            ctk.CTkFrame(side, fg_color=BORDER, width=1, corner_radius=0).grid(
                row=0, column=1, sticky="ns")

            body = ctk.CTkFrame(side, fg_color="transparent")
            body.grid(row=0, column=0, sticky="nsew", padx=PAD, pady=(20, 0))
            body.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(body, text="LLMScribe", font=self.F["brand"], text_color=TEXT,
                         anchor="w").grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(body, text=APP_VERSION, font=self.F["mono_s"], text_color=MUTED,
                         anchor="w").grid(row=1, column=0, sticky="w", pady=(0, 20))

            ctk.CTkLabel(body, text="PROJECT FOLDER", font=self.F["caps"], text_color=SUBTEXT,
                         anchor="w").grid(row=2, column=0, sticky="w", pady=(0, 8))
            box, entry = self._field(body, self.project_var, "folder", self._browse_project,
                                     "Select a folder…")
            box.grid(row=3, column=0, sticky="ew")
            entry.bind("<FocusOut>", lambda _: self._refresh_output_path())

            ctk.CTkLabel(body, text="OUTPUT FILE", font=self.F["caps"], text_color=SUBTEXT,
                         anchor="w").grid(row=4, column=0, sticky="w", pady=(20, 8))
            box2, _ = self._field(body, self.output_var, "save", self._browse_output)
            box2.grid(row=5, column=0, sticky="ew")

            ctk.CTkCheckBox(
                body, text="Tree only", variable=self.tree_only_var, onvalue=True, offvalue=False,
                font=self.F["mono_s"], text_color=SUBTEXT, checkbox_width=18, checkbox_height=18,
                corner_radius=5, border_width=1, border_color=BORDER_STRONG, fg_color=SAGE,
                hover_color=SAGE_HOV, checkmark_color=ON_SAGE,
            ).grid(row=6, column=0, sticky="w", pady=(24, 0))

            self._generate_btn = ctk.CTkButton(
                body, text="Generate", font=self.F["gen"], height=48, corner_radius=14,
                fg_color=SAGE, hover_color=SAGE_HOV, text_color=ON_SAGE,
                text_color_disabled=ON_SAGE, command=self._start_generate,
            )
            self._generate_btn.grid(row=7, column=0, sticky="ew", pady=(22, 0))

            actions = ctk.CTkFrame(body, fg_color="transparent")
            actions.grid(row=8, column=0, sticky="ew", pady=(12, 0))
            actions.grid_columnconfigure((0, 1), weight=1, uniform="act")
            outline: dict[str, Any] = dict(height=44, corner_radius=12, fg_color="transparent",
                           border_width=1, border_color=BORDER_STRONG, hover_color=FIELD,
                           text_color=TEXT, font=self.F["mono_b"])
            ctk.CTkButton(actions, text=" Copy", image=self.icons.get("copy"), compound="left",
                          command=self._copy_all, **outline
                          ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
            ctk.CTkButton(actions, text="Open file", command=self._open_last_output, **outline
                          ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

            self._status_lbl = ctk.CTkLabel(
                body, text="", font=self.F["mono_s"], text_color=SUBTEXT, anchor="w",
                justify="left", wraplength=SIDEBAR_W - 2 * PAD - 4)
            self._status_lbl.grid(row=9, column=0, sticky="w", pady=(18, 0))

        def _build_preview(self) -> None:
            pane = ctk.CTkFrame(self, fg_color=PANE, corner_radius=0)
            pane.grid(row=1, column=1, sticky="nsew")
            pane.grid_columnconfigure(0, weight=1)
            pane.grid_rowconfigure(2, weight=1)

            head = ctk.CTkFrame(pane, fg_color="transparent", height=36)
            head.grid(row=0, column=0, sticky="ew")
            head.grid_propagate(False)
            head.grid_columnconfigure(0, weight=1)
            head.grid_rowconfigure(0, weight=1)
            ctk.CTkLabel(head, text="Preview", font=self.F["mono_s"], text_color=SUBTEXT,
                         anchor="w").grid(row=0, column=0, sticky="w", padx=18)
            self._line_lbl = ctk.CTkLabel(head, text="", font=self.F["mono_s"], text_color=MUTED,
                                          anchor="e")
            self._line_lbl.grid(row=0, column=1, sticky="e", padx=18)
            self._hline(pane, row=1, column=0)

            self.preview = ctk.CTkTextbox(
                pane, wrap="none", corner_radius=0, fg_color=PANE, text_color=TEXT,
                font=self.F["preview"], border_width=0, border_spacing=14,
                scrollbar_button_color=BORDER_STRONG, scrollbar_button_hover_color=SAGE_DIM,
            )
            self.preview.grid(row=2, column=0, sticky="nsew")
            try:
                self.preview._textbox.configure(
                    selectbackground=BORDER_STRONG, selectforeground=TEXT, padx=10, pady=6,
                    spacing1=2, spacing3=2)
            except Exception:
                pass
            self._set_preview_text(
                "Select a project folder and press Generate.\n\nThe output will appear here.")

        # ── actions ─────────────────────────────────

        def _browse_project(self) -> None:
            folder = filedialog.askdirectory(title="Select Project Folder")
            if folder:
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
            if text:
                self.output_var.set(str(Path(text).expanduser() / "project_overview.txt"))

        def _set_status(self, msg: str, color: str = SUBTEXT) -> None:
            self._status_lbl.configure(text=msg, text_color=color)

        def _set_running(self, running: bool) -> None:
            self._running = running
            if running:
                self._generate_btn.configure(text="Generating…", state="disabled", fg_color=SAGE_DIM)
            else:
                self._generate_btn.configure(text="Generate", state="normal", fg_color=SAGE)

        def _start_generate(self) -> None:
            if self._running:
                return
            project_text = self.project_var.get().strip()
            output_text = self.output_var.get().strip()
            tree_only = self.tree_only_var.get()

            if not project_text:
                self._set_status("Choose a project folder first.", ERROR_C)
                return
            project_path = Path(project_text).expanduser()
            if not project_path.is_dir():
                self._set_status("Project folder path is invalid.", ERROR_C)
                return
            output_file = Path(output_text or "project_overview.txt").expanduser()

            self._set_preview_text("Scanning…")
            self._set_status("Scanning project (tree only)…" if tree_only else "Scanning project…")
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
                self._line_lbl.configure(text=f"{result.summary.count(chr(10)) + 1:,} lines")
                self._set_status(f"Saved to\n{result.output_file.name}", TEXT)
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
            self._set_status("Copied to clipboard.", TEXT)

        def _open_last_output(self) -> None:
            if self._last_output_file is not None:
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
