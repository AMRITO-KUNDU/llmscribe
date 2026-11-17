"""The Windows EXE must carry the brand icon — on the file and in the window.

Two separate things used to be wrong: ``docs/public/favicon.ico`` held a single 32px
image, and the GUI looked for the icon at a repo-relative path that does not exist
inside a PyInstaller one-file bundle.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICO = ROOT / "docs" / "public" / "favicon.ico"


def ico_sizes(path: Path) -> list[tuple[int, int]]:
    """Read the ICO directory without Pillow (it is not a test dependency).

    Header is 6 bytes, then 16 bytes per image; a width/height byte of 0 means 256.
    """
    data = path.read_bytes()
    count = int.from_bytes(data[4:6], "little")
    sizes = []
    for i in range(count):
        entry = 6 + i * 16
        sizes.append((data[entry] or 256, data[entry + 1] or 256))
    return sizes


def test_icon_is_multi_resolution():
    sizes = ico_sizes(ICO)
    widths = {w for w, _ in sizes}

    # Windows picks from these: 16 title bar, 32 taskbar, 48 explorer, 256 large view.
    assert {16, 32, 48, 256} <= widths, f"missing standard sizes, has {sorted(widths)}"
    assert len(sizes) >= 6, f"only {len(sizes)} image(s) embedded"


def test_build_command_embeds_and_bundles_the_icon():
    import build_exe

    cmd = build_exe.build_command()

    assert "--icon" in cmd, "the .exe file would get PyInstaller's default icon"
    assert cmd[cmd.index("--icon") + 1] == str(build_exe.ICON_PATH)

    # Without --add-data the icon is not inside the bundle, so the running window
    # cannot set it and silently falls back to the Tk feather.
    assert "--add-data" in cmd, "the icon is not bundled for the window icon"
    source, destination = cmd[cmd.index("--add-data") + 1].split(build_exe.os.pathsep)
    assert source == str(build_exe.ICON_PATH)
    assert destination.replace(build_exe.os.sep, "/") == "docs/public"

    assert cmd[-1].endswith("app.py"), "the entry point must come last"


def test_icon_path_resolves_in_a_source_checkout():
    from llmscribe.gui import app

    resolved = app._icon_path()
    assert resolved is not None and resolved.is_file()
    assert resolved.name == "favicon.ico"


def test_icon_path_uses_meipass_when_frozen(tmp_path, monkeypatch):
    """In a one-file build __file__ is inside the temp dir; sys._MEIPASS is the root."""
    from llmscribe.gui import app

    (tmp_path / "docs" / "public").mkdir(parents=True)
    bundled = tmp_path / "docs" / "public" / "favicon.ico"
    bundled.write_bytes(ICO.read_bytes())

    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert app._icon_path() == bundled


def test_icon_path_returns_none_when_absent(tmp_path, monkeypatch):
    from llmscribe.gui import app

    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert app._icon_path() is None
