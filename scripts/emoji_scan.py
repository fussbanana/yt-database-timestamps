"""
Ein kleines Hilfsskript, das rekursiv alle Projektdateien nach Emoji-Zeichen
durchsucht und Fundstellen mit Datei, Zeile und Spalte ausgibt.

Nutzung:
    poetry run python scripts/emoji_scan.py [--root <pfad>] [--include-hidden]

Google-Style-Dokumentation
--------------------------

Functions:
    main() -> None: Einstiegspunkt für das Skript.

Das Skript versucht, nur echte Emoji-Symbole zu erfassen. Die Unicode-Emoji-
Ranges sind umfangreich; wir verwenden einen konservativen Regex, der die
gängigen Blöcke abdeckt (Emoticons, Misc Symbols, Dingbats, Transport/Map,
Supplemental Symbols & Pictographs, Symbols & Pictographs Extended-A, Flags,
u.a.). Zusätzlich werden Variation Selector-16 (\uFE0F) und Zero-Width-Joiner
(\u200D) berücksichtigt, um zusammengesetzte Emojis nicht zu zerreißen.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import signal
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional, Pattern, Tuple


# Zusammengesetzte Emoji-Sequenzen können ZWJ (\u200D) und VS-16 (\uFE0F) enthalten.
# Wir erfassen Emojis mithilfe eines Regex, der breite Blöcke umfasst. Das ist bewusst
# pragmatisch statt perfekt – Ziel ist, alle sichtbaren Emojis im Code aufzuspüren.

# Grobe Abdeckung verbreiteter Emoji-Blöcke:
# - Emoticons: U+1F600–U+1F64F
# - Misc Symbols: U+2600–U+26FF
# - Dingbats: U+2700–U+27BF
# - Transport & Map: U+1F680–U+1F6FF
# - Misc Symbols & Pictographs: U+1F300–U+1F5FF
# - Supplemental Symbols & Pictographs: U+1F900–U+1F9FF
# - Symbols & Pictographs Extended-A: U+1FA70–U+1FAFF
# - Flags: U+1F1E6–U+1F1FF (Regional Indicator)
# - Weitere Symbole: U+1F700–U+1F77F, U+1F780–U+1F7FF (geometrisch, Pfeile etc.)

_EMOJI_PATTERN: Pattern[str] = re.compile(
    r"(\u0023\uFE0F?\u20E3|\u002A\uFE0F?\u20E3|[\u0030-\u0039]\uFE0F?\u20E3)"  # keycap sequences
    r"|[\u2194-\u21FF]"  # arrows etc.
    r"|[\u2300-\u23FF]"  # misc technical
    r"|[\u2460-\u24FF]"  # enclosed alphanumerics
    r"|[\u25A0-\u25FF]"  # geometric shapes
    r"|[\u2600-\u26FF]"  # misc symbols
    r"|[\u2700-\u27BF]"  # dingbats
    r"|[\U0001F300-\U0001F5FF]"  # misc symbols and pictographs
    r"|[\U0001F600-\U0001F64F]"  # emoticons
    r"|[\U0001F680-\U0001F6FF]"  # transport and map
    r"|[\U0001F700-\U0001F77F]"  # alchemical symbols
    r"|[\U0001F780-\U0001F7FF]"  # geometric shapes extended
    r"|[\U0001F800-\U0001F8FF]"  # supplemental arrows-c
    r"|[\U0001F900-\U0001F9FF]"  # supplemental symbols and pictographs
    r"|[\U0001FA70-\U0001FAFF]"  # symbols & pictographs extended-a
    r"|[\U0001F1E6-\U0001F1FF]"  # flags (regional indicators)
)


@dataclass
class Hit:
    """Repräsentiert eine Emoji-Fundstelle.

    Attributes:
        path: Dateipfad relativ zum Root.
        line: Zeilennummer (1-basiert).
        col: Spaltennummer (1-basiert, Zeichenindex in Python-Logik).
        snippet: Die betroffene Zeile (getrimmt), um Kontext zu geben.
        emoji: Das gefundene Emoji-Zeichen bzw. Sequenz.
    """

    path: str
    line: int
    col: int
    snippet: str
    emoji: str


def iter_files(root: str, include_hidden: bool = False) -> Iterator[str]:
    """Liefert alle regulären Dateien unterhalb von ``root``.

    Args:
        root: Wurzelverzeichnis.
        include_hidden: Ob versteckte Dateien/Ordner (beginnend mit .) einbezogen werden.

    Yields:
        Absolute Dateipfade.
    """

    for dirpath, dirnames, filenames in os.walk(root):
        if not include_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for fname in filenames:
            if not include_hidden and fname.startswith("."):
                continue
            yield os.path.join(dirpath, fname)


def find_emojis_in_text(text: str) -> List[Tuple[int, int, str]]:
    """Findet Emojis im gegebenen Text.

    Args:
        text: Eine einzelne Textzeile.

    Returns:
        Liste von Tupeln (start_index, end_index, match_text).
    """

    hits: List[Tuple[int, int, str]] = []
    for m in _EMOJI_PATTERN.finditer(text):
        hits.append((m.start(), m.end(), m.group(0)))
    return hits


def scan_file(path: str, root: str) -> List[Hit]:
    """Durchsucht eine Datei nach Emojis.

    Args:
        path: Absoluter Dateipfad.
        root: Projekt-Root, um relative Pfade auszugeben.

    Returns:
        Liste der Treffer in dieser Datei.
    """

    rel = os.path.relpath(path, root)
    hits: List[Hit] = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, start=1):
                line_stripped = line.rstrip("\n")
                for start, _end, seq in find_emojis_in_text(line_stripped):
                    # Spaltennummer 1-basiert
                    hits.append(Hit(path=rel, line=i, col=start + 1, snippet=line_stripped, emoji=seq))
    except (UnicodeDecodeError, PermissionError, IsADirectoryError):
        return []
    return hits


def should_skip(path: str) -> bool:
    """Filtert typische Verzeichnisse/Dateien aus, die nicht gescannt werden sollen.

    Dies beschleunigt den Scan und vermeidet Rauschen.
    """

    parts = path.split(os.sep)
    skip_dirs = {
        ".git",
        ".venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "htmlcov",
        "logs",
        "dist",
        "build",
        ".serena",
        ".vscode",
    }
    if any(p in skip_dirs for p in parts):
        return True

    skip_ext = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".pdf",
        ".db",
        ".sqlite",
        ".lock",
        ".so",
        ".dll",
        ".exe",
        ".bin",
        ".ttf",
        ".otf",
        ".woff",
        ".woff2",
        ".eot",
        ".ttc",
        ".zip",
        ".gz",
        ".xz",
        ".bz2",
        ".7z",
        ".tar",
        ".class",
        ".jar",
        ".pyc",
        ".pyo",
        ".pyd",
        ".dylib",
        ".a",
        ".o",
        ".obj",
        ".wasm",
        ".mp4",
        ".webm",
        ".wav",
        ".mp3",
    }
    _, ext = os.path.splitext(path)
    return ext.lower() in skip_ext


def scan(root: str, include_hidden: bool = False) -> List[Hit]:
    """Führt den Emoji-Scan durch.

    Args:
        root: Projektwurzel.
        include_hidden: Versteckte Dateien/Ordner berücksichtigen.

    Returns:
        Alle Treffer im Projekt.
    """

    all_hits: List[Hit] = []
    for apath in iter_files(root, include_hidden=include_hidden):
        if should_skip(apath):
            continue
        hits = scan_file(apath, root)
        if hits:
            all_hits.extend(hits)
    return all_hits


def print_report(hits: List[Hit]) -> None:
    """Gibt eine menschenlesbare Auswertung aus."""
    try:
        if not hits:
            print("Keine Emojis gefunden.")
            return

        total = len(hits)
        print(f"Gefundene Emojis: {total}")
        print()
        for h in hits:
            # Zeilenausschnitt kürzen, um lange Zeilen zu vermeiden
            snippet = h.snippet
            max_len = 120
            if len(snippet) > max_len:
                snippet = snippet[: max_len - 1] + "…"
            print(f"{h.path}:{h.line}:{h.col}: '{h.emoji}' | {snippet}")
    except BrokenPipeError:
        try:
            sys.stdout.flush()
        except Exception:
            pass


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parst CLI-Argumente.

    Args:
        argv: Optionale Argumentliste, standardmäßig sys.argv[1:].

    Returns:
        Namespace mit geparsten Optionen.
    """

    parser = argparse.ArgumentParser(description="Finde Emojis im Projekt.")
    parser.add_argument("--root", default=os.getcwd(), help="Projektwurzel (Default: aktuelles Verzeichnis)")
    parser.add_argument("--include-hidden", action="store_true", help="Auch versteckte Dateien und Ordner scannen")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    """Einstiegspunkt: scannt und druckt den Report."""
    # Robust gegen abgebrochene Pipes (z. B. `| head`)
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (AttributeError, ValueError):
        pass

    args = parse_args(argv)
    hits = scan(args.root, include_hidden=args.include_hidden)
    print_report(hits)


if __name__ == "__main__":
    main()
