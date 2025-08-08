"""
Search strategy definitions for enhanced multi-word search functionality.

Defines different approaches for interpreting and executing search queries.
"""

from enum import Enum
from typing import NamedTuple


class SearchStrategy(Enum):
    """Verschiedene Strategien für die Interpretation von Suchbegriffen."""

    AUTO = "auto"  # Intelligente Auswahl basierend auf Query-Struktur
    EXACT_PHRASE = "exact"  # Gesamte Eingabe als exakte Phrase behandeln
    ALL_WORDS = "all"  # Alle Wörter müssen vorkommen (AND-Verknüpfung)
    ANY_WORD = "any"  # Mindestens ein Wort muss vorkommen (OR-Verknüpfung)
    FUZZY = "fuzzy"  # Unscharfe Suche mit Wildcards und Prefix-Matching
    SEMANTIC = "semantic"  # Bedeutungsbasierte Suche mit AI-Embeddings
    HYBRID = "hybrid"  # Kombiniert semantische + keyword-basierte Suche


class SearchStrategyInfo(NamedTuple):
    """Metadaten für eine Suchstrategie zur GUI-Anzeige."""

    strategy: SearchStrategy
    display_name: str
    description: str
    example: str


# Verfügbare Strategien mit Anzeigeinformationen
SEARCH_STRATEGIES = [
    SearchStrategyInfo(
        strategy=SearchStrategy.AUTO,
        display_name="Auto (Intelligent)",
        description="Wählt automatisch die beste Strategie basierend auf der Eingabe",
        example='israel politik → versucht erst "israel politik", dann israel AND politik',
    ),
    SearchStrategyInfo(
        strategy=SearchStrategy.EXACT_PHRASE,
        display_name="Exakte Phrase",
        description="Behandelt die gesamte Eingabe als zusammenhängende Phrase",
        example='israel politik → nur Kapitel mit genau "israel politik"',
    ),
    SearchStrategyInfo(
        strategy=SearchStrategy.ALL_WORDS,
        display_name="Alle Wörter",
        description="Alle eingegebenen Wörter müssen im Kapitel vorkommen",
        example="israel politik → israel AND politik (beide Begriffe erforderlich)",
    ),
    SearchStrategyInfo(
        strategy=SearchStrategy.ANY_WORD,
        display_name="Beliebiges Wort",
        description="Mindestens eines der eingegebenen Wörter muss vorkommen",
        example="israel politik → israel OR politik (eines der Wörter reicht)",
    ),
    SearchStrategyInfo(
        strategy=SearchStrategy.FUZZY,
        display_name="Unscharf",
        description="Erweiterte Suche mit Wildcards und ähnlichen Begriffen",
        example="israel* politi* → findet auch 'israelisch', 'politisch', etc.",
    ),
    SearchStrategyInfo(
        strategy=SearchStrategy.SEMANTIC,
        display_name="Semantisch (AI)",
        description="Bedeutungsbasierte Suche mit künstlicher Intelligenz",
        example="python tutorial → findet auch 'Programmier-Einführung', 'Coding-Grundlagen'",
    ),
    SearchStrategyInfo(
        strategy=SearchStrategy.HYBRID,
        display_name="Hybrid (AI + Keywords)",
        description="Kombiniert semantische und keyword-basierte Suche für beste Ergebnisse",
        example="machine learning → AI-Bedeutung + exakte Keywords, gewichtet kombiniert",
    ),
]
