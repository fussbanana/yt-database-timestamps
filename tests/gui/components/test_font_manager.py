"""
Test für FontManager

Testet die Instanziierung und die Methoden für Font-Varianten.
"""

import pytest
from src.yt_database.gui.components.font_manager import FontManager
from PySide6.QtGui import QFont

class DummyWidget:
    def __init__(self):
        self.font = None
    def setFont(self, font):
        self.font = font

def test_font_manager_instantiation():
    manager = FontManager()
    assert manager.font_family is None
    assert isinstance(manager.font_variants, dict)

def test_get_font_returns_qfont():
    manager = FontManager()
    manager.font_variants = {"ui_default": QFont()}
    font = manager.get_font("ui_default")
    assert isinstance(font, QFont)

def test_apply_font_to_widget():
    manager = FontManager()
    manager.font_variants = {"ui_default": QFont()}
    widget = DummyWidget()
    manager.apply_font_to_widget(widget, "ui_default")
    assert isinstance(widget.font, QFont)

def test_get_available_variants():
    manager = FontManager()
    manager.font_variants = {"ui_default": QFont(), "ui_code": QFont()}
    variants = manager.get_available_variants()
    assert set(variants) == {"ui_default", "ui_code"}

def test_is_inter_loaded_false_initial():
    manager = FontManager()
    assert not manager.is_inter_loaded()
    manager.font_family = "Inter"
    manager.font_variants = {"ui_default": QFont()}
    assert manager.is_inter_loaded()
