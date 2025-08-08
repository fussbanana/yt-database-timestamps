"""
Tests für Hilfsfunktionen in utils.
"""

from yt_database.utils.utils import to_snake_case


def test_to_snake_case():
    assert to_snake_case("MeinKanalName") == "mein_kanal_name"
    assert to_snake_case("meinKanalName") == "mein_kanal_name"
    assert to_snake_case("Mein_Kanal-Name!") == "mein_kanal_name"
    assert to_snake_case("") == "unbekannt"
