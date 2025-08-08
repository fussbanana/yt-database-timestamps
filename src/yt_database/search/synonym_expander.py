"""
Synonym-Expansion System für erweiterte Suchfunktionalität.

Ermöglicht es, Suchbegriffe automatisch um verwandte Begriffe zu erweitern,
um mehr relevante Ergebnisse zu finden.
"""

from typing import Dict, List
from dataclasses import dataclass

from yt_database.models.search_strategy import SearchStrategy


@dataclass
class SynonymGroup:
    """Eine Gruppe von verwandten Begriffen."""

    primary: str  # Hauptbegriff
    synonyms: List[str]  # Verwandte Begriffe
    weight: float = 1.0  # Gewichtung (für spätere Relevanz-Berechnung)


class SynonymExpander:
    """
    Erweitert Suchbegriffe um Synonyme und verwandte Begriffe.

    Unterstützt bidirektionale Synonym-Zuordnung und intelligente Expansion
    basierend auf der gewählten Suchstrategie.
    """

    def __init__(self):
        """Initialisiert den Expander mit vordefinierten Synonym-Gruppen."""
        self._synonym_groups = self._load_default_synonyms()
        self._term_to_group = self._build_lookup_map()

    def _load_default_synonyms(self) -> List[SynonymGroup]:
        """Lädt die Standard-Synonym-Definitionen."""
        return [
            # Politik & Gesellschaft
            SynonymGroup(
                "politik",
                [
                    "politisch",
                    "regierung",
                    "staat",
                    "parteien",
                    "government",
                    "politiker",
                    "politikerin",
                    "demokratie",
                    "wahlen",
                ],
            ),
            SynonymGroup(
                "kritik",
                [
                    "kritisch",
                    "analyse",
                    "bewertung",
                    "meinung",
                    "kommentar",
                    "rezension",
                    "beurteilung",
                    "einschätzung",
                    "kritisiert",
                ],
            ),
            # Technologie & KI
            SynonymGroup(
                "ai",
                [
                    "ki",
                    "künstliche intelligenz",
                    "artificial intelligence",
                    "machine learning",
                    "deep learning",
                    "neural",
                    "algorithmus",
                    "automation",
                    "roboter",
                    "chatgpt",
                    "llm",
                ],
            ),
            SynonymGroup(
                "technologie",
                [
                    "tech",
                    "digital",
                    "digitalisierung",
                    "innovation",
                    "software",
                    "computer",
                    "internet",
                    "online",
                    "cyber",
                ],
            ),
            # Umwelt & Klima
            SynonymGroup(
                "klima",
                [
                    "klimawandel",
                    "climate",
                    "umwelt",
                    "wetter",
                    "temperatur",
                    "co2",
                    "emission",
                    "nachhaltigkeit",
                    "ökologie",
                    "green",
                ],
            ),
            SynonymGroup(
                "energie",
                [
                    "strom",
                    "power",
                    "solar",
                    "wind",
                    "atom",
                    "nuklear",
                    "fossil",
                    "erneuerbar",
                    "energiewende",
                    "batterie",
                ],
            ),
            # Wirtschaft & Finanzen
            SynonymGroup(
                "wirtschaft",
                [
                    "ökonomie",
                    "economy",
                    "markt",
                    "business",
                    "unternehmen",
                    "firma",
                    "konzern",
                    "industrie",
                    "handel",
                    "kommerz",
                ],
            ),
            SynonymGroup(
                "geld",
                [
                    "money",
                    "finanzen",
                    "euro",
                    "dollar",
                    "währung",
                    "investment",
                    "aktien",
                    "börse",
                    "krypto",
                    "bitcoin",
                    "inflation",
                ],
            ),
            # Geografie & Länder
            SynonymGroup("deutschland", ["german", "deutsch", "bundesrepublik", "brd", "germany"]),
            SynonymGroup(
                "usa", ["america", "amerika", "american", "united states", "us", "vereinigte staaten", "amerikanisch"]
            ),
            SynonymGroup("europa", ["eu", "european", "europäisch", "europäische union"]),
            # Konflikt & Krieg
            SynonymGroup(
                "krieg",
                ["war", "konflikt", "kämpfe", "militär", "soldaten", "waffen", "verteidigung", "angriff", "invasion"],
            ),
            SynonymGroup(
                "israel",
                ["israelisch", "israeli", "zionismus", "zionist", "jerusalem", "tel aviv", "palästina", "gaza"],
            ),
            # Medien & Kommunikation
            SynonymGroup(
                "media",
                [
                    "medien",
                    "presse",
                    "journalismus",
                    "news",
                    "nachrichten",
                    "zeitung",
                    "tv",
                    "fernsehen",
                    "radio",
                    "podcast",
                ],
            ),
            SynonymGroup(
                "social media",
                ["soziale medien", "facebook", "twitter", "instagram", "youtube", "tiktok", "linkedin", "whatsapp"],
            ),
            # Wissenschaft & Forschung
            SynonymGroup(
                "wissenschaft",
                [
                    "science",
                    "forschung",
                    "studie",
                    "research",
                    "experiment",
                    "analyse",
                    "theorie",
                    "hypothesis",
                    "evidenz",
                ],
            ),
            SynonymGroup(
                "medizin",
                [
                    "medicine",
                    "gesundheit",
                    "health",
                    "arzt",
                    "doctor",
                    "krankenhaus",
                    "therapie",
                    "behandlung",
                    "pharma",
                ],
            ),
        ]

    def _build_lookup_map(self) -> Dict[str, SynonymGroup]:
        """Erstellt eine Lookup-Map von Begriff zu Synonym-Gruppe."""
        lookup = {}
        for group in self._synonym_groups:
            # Hauptbegriff
            lookup[group.primary.lower()] = group
            # Alle Synonyme
            for synonym in group.synonyms:
                lookup[synonym.lower()] = group
        return lookup

    def expand_terms(self, terms: List[str], strategy: SearchStrategy, max_expansions: int = 3) -> List[str]:
        """
        Erweitert eine Liste von Begriffen um Synonyme.

        Args:
            terms: Liste der ursprünglichen Suchbegriffe
            strategy: Gewählte Suchstrategie
            max_expansions: Maximale Anzahl von Synonymen pro Begriff

        Returns:
            Erweiterte Liste mit ursprünglichen Begriffen und Synonymen
        """
        if strategy == SearchStrategy.EXACT_PHRASE:
            # Bei exakter Phrasensuche keine Expansion
            return terms

        expanded = set(terms)  # Originalbegriffe behalten

        for term in terms:
            term_lower = term.lower()
            if term_lower in self._term_to_group:
                group = self._term_to_group[term_lower]

                # Intelligente Synonym-Auswahl basierend auf Strategie
                if strategy == SearchStrategy.FUZZY:
                    # Bei Fuzzy-Suche: mehr Synonyme
                    synonyms_to_add = group.synonyms[: max_expansions * 2]
                elif strategy == SearchStrategy.ANY_WORD:
                    # Bei OR-Suche: moderate Expansion
                    synonyms_to_add = group.synonyms[:max_expansions]
                else:
                    # Bei AND/AUTO: konservative Expansion (nur die besten)
                    synonyms_to_add = group.synonyms[: max_expansions // 2 + 1]

                for synonym in synonyms_to_add:
                    expanded.add(synonym)

        return list(expanded)

    def get_synonyms_for_term(self, term: str) -> List[str]:
        """Gibt alle Synonyme für einen bestimmten Begriff zurück."""
        term_lower = term.lower()
        if term_lower in self._term_to_group:
            group = self._term_to_group[term_lower]
            return [group.primary] + group.synonyms
        return [term]

    def add_synonym_group(self, group: SynonymGroup):
        """Fügt eine neue Synonym-Gruppe hinzu."""
        self._synonym_groups.append(group)
        # Lookup-Map aktualisieren
        self._term_to_group[group.primary.lower()] = group
        for synonym in group.synonyms:
            self._term_to_group[synonym.lower()] = group

    def get_all_groups(self) -> List[SynonymGroup]:
        """Gibt alle verfügbaren Synonym-Gruppen zurück."""
        return self._synonym_groups.copy()

    def build_expanded_fts_query(self, original_terms: List[str], strategy: SearchStrategy) -> str:
        """
        Erstellt eine FTS5-Query mit Synonym-Expansion.

        Args:
            original_terms: Ursprüngliche Suchbegriffe
            strategy: Gewählte Suchstrategie

        Returns:
            FTS5-kompatible Query-String mit Synonymen
        """
        expanded_terms = self.expand_terms(original_terms, strategy)

        if strategy == SearchStrategy.EXACT_PHRASE:
            # Keine Expansion bei exakter Phrase
            return f'"{" ".join(original_terms)}"'

        elif strategy == SearchStrategy.ALL_WORDS:
            # Alle Begriffe müssen vorkommen, aber Synonyme sind OR-verknüpft
            term_groups = []
            for term in original_terms:
                synonyms = self.get_synonyms_for_term(term)
                if len(synonyms) > 1:
                    # Gruppe mit Synonymen: (term1 OR synonym1 OR synonym2)
                    synonym_query = " OR ".join(f"{s}*" for s in synonyms)
                    term_groups.append(f"({synonym_query})")
                else:
                    # Kein Synonym gefunden
                    term_groups.append(f"{term}*")

            return " AND ".join(term_groups)

        elif strategy == SearchStrategy.ANY_WORD:
            # Beliebiger Begriff (einschließlich Synonyme) reicht
            all_terms = [f"{term}*" for term in expanded_terms]
            return " OR ".join(all_terms)

        elif strategy == SearchStrategy.FUZZY:
            # Ähnlich zu ANY_WORD, aber mit mehr Synonymen
            all_terms = [f"{term}*" for term in expanded_terms]
            return " OR ".join(all_terms)

        elif strategy == SearchStrategy.AUTO:
            # Intelligente Kombination: erst original, dann mit Synonymen
            original_query = " AND ".join(f"{term}*" for term in original_terms)

            if len(expanded_terms) > len(original_terms):
                # Synonyme gefunden: Alternative OR-Suche hinzufügen
                synonym_query = " OR ".join(f"{term}*" for term in expanded_terms)
                return f"({original_query}) OR ({synonym_query})"
            else:
                # Keine Synonyme: Standard-Query
                return original_query

        # Fallback
        return " OR ".join(f"{term}*" for term in expanded_terms)
