# Dokumentation: `Icons`-Klasse

Diese Dokumentation beschreibt die Verwendung der `Icons`-Klasse für ein zentralisiertes und konsistentes Icon-Management in der gesamten Anwendung.

## Zweck

Die `Icons`-Klasse dient als zentrale Anlaufstelle für alle Icons, die aus der kompilierten QRC-Ressourcendatei (`icons_rc.py`) geladen werden. Sie bietet eine saubere, semantische und typsichere Schnittstelle, um Tippfehler zu vermeiden und die Wartbarkeit zu erhöhen.

## Import und Grundverwendung

Um die Klasse zu verwenden, importiere sie einfach in dein Widget oder deine Komponente:

```python
from yt_database.gui.utils.icons import Icons
from PySide6.QtGui import QIcon
```

---

## Drei Verwendungsarten

Es gibt drei empfohlene Wege, um auf Icons zuzugreifen:

### 1. Convenience-Methoden (Empfohlen)

Für häufig verwendete Icons gibt es direkte, statische Methoden, die das `QIcon`-Objekt zurückgeben. Dies ist der sauberste und bevorzugte Weg.

```python
# Direkte Methoden für häufig verwendete Icons
settings_icon = Icons.settings()
book_icon = Icons.book_open()
search_icon = Icons.search()
database_icon = Icons.database()
```

### 2. Über Konstanten

Jedes Icon ist als Klassenkonstante mit seinem QRC-Pfad definiert. Die `get()`-Methode kann verwendet werden, um das `QIcon`-Objekt aus diesem Pfad zu erstellen.

```python
# Zugriff über vordefinierte Konstanten
home_icon = Icons.get(Icons.HOME)
edit_icon = Icons.get(Icons.EDIT)
save_icon = Icons.get(Icons.SAVE)
```

### 3. Direkte QRC-Pfade

In seltenen Fällen kannst du auch direkt den QRC-Pfad verwenden, obwohl dies die Vorteile der zentralen Klasse umgeht.

```python
# Direkter Zugriff auf QRC-Ressourcen
custom_icon = QIcon(":/feather/star.png")
```

---

## Praktische Beispiele

### Toolbar-Buttons

```python
from PySide6.QtGui import QAction

def create_toolbar_action(self):
    # Über Convenience-Methode
    action = QAction(Icons.settings(), "Einstellungen", self)

    # Oder über Konstante
    refresh_action = QAction(Icons.get(Icons.REFRESH), "Aktualisieren", self)
```

### Push-Buttons

```python
from PySide6.QtWidgets import QPushButton

def create_buttons(self):
    # Navigation
    back_btn = QPushButton(Icons.get(Icons.ARROW_LEFT), "Zurück")

    # Aktionen
    play_btn = QPushButton(Icons.get(Icons.PLAY), "Abspielen")
```

### Tree-Widget Icons

```python
from PySide6.QtWidgets import QTreeWidgetItem

def setup_tree_items(self):
    root_item = QTreeWidgetItem()
    root_item.setIcon(0, Icons.get(Icons.FOLDER))
    root_item.setText(0, "Projekte")

    file_item = QTreeWidgetItem(root_item)
    file_item.setIcon(0, Icons.get(Icons.FILE_TEXT))
    file_item.setText(0, "Dokument.txt")
```

---

## Icon-Größen anpassen

Du kannst die Größe der Icons bei Bedarf anpassen.

```python
from PySide6.QtCore import QSize

# Standard-Größe
icon = Icons.settings()

# Spezifische Größe für ein Pixmap
pixmap = icon.pixmap(32, 32)  # 32x32 Pixel

# Für Buttons mit spezifischer Icon-Größe
button = QPushButton(Icons.get(Icons.PLAY))
button.setIconSize(QSize(24, 24))
```

---

## Vorteile der `Icons`-Klasse

1. **Zentralisiert:** Alle Icons werden an einem einzigen Ort verwaltet.
2. **Typsicher:** Die Verwendung von Konstanten verhindert Tippfehler bei den Pfaden.
3. **Semantisch:** Klare und verständliche Namen für Icons (`Icons.SAVE` statt `":/feather/save.png"`).
4. **Einfach:** Convenience-Methoden vereinfachen den Zugriff auf häufig genutzte Icons.
5. **Wartbar:** Änderungen am Icon-Set müssen nur an einer Stelle vorgenommen werden.
6. **Performance:** QRC-Ressourcen sind direkt in die Anwendung einkompiliert und müssen nicht vom Dateisystem geladen werden.
