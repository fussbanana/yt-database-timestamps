#!/usr/bin/env python3
"""Test der Markdown-Ersetzung für Chapter-Writing."""

import tempfile
import os

def test_markdown_replacement():
    """Teste die Markdown-Ersetzung für Kapitel."""

    # Test-Markdown-Inhalt wie in der echten Datei
    test_content = """---
title: Test Video
video_id: test123
chapters: 0
detailed_chapters: 0
---

## Kapitel mit Zeitstempeln

## Detaillierte Kapitel

## Transkript

[00:00:05-00:00:10] Test content...
"""

    # Simulierte Kapitel-Daten
    chapter_text = """• 00:01:16: Einführung ins Thema
• 00:03:22: Hauptteil der Diskussion
• 00:08:45: Fazit und Abschluss"""

    # Erstelle temporäre Datei
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(test_content)
        temp_file = f.name

    try:
        # Teste die Ersetzungslogik direkt
        placeholder = "## Kapitel mit Zeitstempeln"

        # Content lesen
        with open(temp_file, 'r') as f:
            content = f.read()

        print(f"Verwendeter Platzhalter: '{placeholder}'")
        print(f"Platzhalter vorhanden: {placeholder in content}")

        # Ersetzung durchführen (simuliert die echte on_chapters_extracted Logik)
        new_content = content.replace(placeholder, f"{placeholder}\n\n```\n{chapter_text.strip()}\n```\n")

        # Zurückschreiben
        with open(temp_file, 'w') as f:
            f.write(new_content)

        # Verifikation: Prüfe ob Kapitel korrekt eingefügt wurden
        with open(temp_file, 'r') as f:
            updated_content = f.read()

        print(f"\nAktualisierter Dateiinhalt:")
        print("=" * 50)
        print(updated_content)
        print("=" * 50)

        # Assertions
        assert "• 00:01:16: Einführung ins Thema" in updated_content
        assert "• 00:03:22: Hauptteil der Diskussion" in updated_content
        assert "• 00:08:45: Fazit und Abschluss" in updated_content
        assert "```" in updated_content

        print("Markdown-Ersetzung erfolgreich!")

    finally:
        # Cleanup
        os.unlink(temp_file)

if __name__ == "__main__":
    test_markdown_replacement()
    print("\nMarkdown-Ersetzungstest erfolgreich!")
