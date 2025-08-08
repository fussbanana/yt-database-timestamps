"""
Suggestion-Provider für intelligente Suchvorschläge.

Nutzt das FTS5-Vokabular und Synonym-System um relevante Suchvorschläge
basierend auf Häufigkeit und Relevanz zu generieren.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
import sqlite3
from loguru import logger

from yt_database.search.synonym_expander import SynonymExpander


@dataclass
class SearchSuggestion:
    """Ein Suchvorschlag mit Metadaten."""

    term: str
    frequency: int  # Häufigkeit in der Datenbank
    category: str  # Art des Vorschlags: "exact", "synonym", "related"
    confidence: float  # Confidence-Score (0.0-1.0)


class SearchSuggestionProvider:
    """
    Generiert intelligente Suchvorschläge basierend auf:
    - FTS5-Vokabular (tatsächlich vorhandene Begriffe)
    - Synonym-System (verwandte Begriffe)
    - Häufigkeitsanalyse (populäre Begriffe bevorzugen)
    - Prefix-Matching (während dem Tippen)
    """

    def __init__(self, db_path: str):
        """
        Initialisiert den Suggestion-Provider.

        Args:
            db_path: Pfad zur SQLite-Datenbank
        """
        self.db_path = db_path
        self.synonym_expander = SynonymExpander()
        self._vocab_cache: Optional[List[Tuple[str, int]]] = None
        self._last_cache_update = 0

    def get_suggestions(self, partial_query: str, limit: int = 10) -> List[SearchSuggestion]:
        """
        Generiert Suchvorschläge für eine partielle Eingabe.

        Args:
            partial_query: Teilweise eingegebener Suchbegriff
            limit: Maximale Anzahl von Vorschlägen

        Returns:
            Liste von SearchSuggestion-Objekten, sortiert nach Relevanz
        """
        if not partial_query or len(partial_query) < 2:
            return []

        partial_lower = partial_query.lower().strip()
        suggestions = []

        # 1. Direkte Prefix-Matches aus FTS5-Vokabular
        direct_matches = self._get_direct_matches(partial_lower, limit)
        for term, freq in direct_matches:
            suggestions.append(SearchSuggestion(term=term, frequency=freq, category="exact", confidence=1.0))

        # 2. Synonym-basierte Vorschläge
        if len(suggestions) < limit:
            synonym_matches = self._get_synonym_matches(partial_lower, limit - len(suggestions))
            suggestions.extend(synonym_matches)

        # 3. Fuzzy/ähnliche Begriffe (falls noch Platz)
        if len(suggestions) < limit:
            fuzzy_matches = self._get_fuzzy_matches(partial_lower, limit - len(suggestions))
            suggestions.extend(fuzzy_matches)

        # Nach Confidence und Häufigkeit sortieren
        suggestions.sort(key=lambda s: (s.confidence, s.frequency), reverse=True)

        return suggestions[:limit]

    def _get_direct_matches(self, partial: str, limit: int) -> List[Tuple[str, int]]:
        """Sucht direkte Prefix-Matches im FTS5-Vokabular."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Prüfe erst, ob das FTS5-Vokabular-Table existiert
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chapter_fts_vocab'")
                if not cursor.fetchone():
                    # Fallback: Suche direkt in den Kapitel-Titeln
                    sql = """
                    SELECT DISTINCT
                        LOWER(substr(title, 1, ?)) as term,
                        COUNT(*) as cnt
                    FROM chapter
                    WHERE LOWER(title) LIKE ?
                    GROUP BY term
                    HAVING cnt >= 1
                    ORDER BY cnt DESC
                    LIMIT ?
                    """
                    cursor.execute(sql, (len(partial) + 5, f"%{partial}%", limit))
                    return cursor.fetchall()

                # Original FTS5-Vokabular-Suche
                sql = """
                SELECT term, cnt
                FROM chapter_fts_vocab
                WHERE term LIKE ?
                  AND LENGTH(term) >= 3
                  AND cnt >= 2
                ORDER BY cnt DESC, LENGTH(term) ASC
                LIMIT ?
                """

                cursor.execute(sql, (f"{partial}%", limit))
                return cursor.fetchall()

        except sqlite3.Error as e:
            logger.warning(f"Fehler beim Abrufen direkter Matches: {e}")
            return []

    def _get_synonym_matches(self, partial: str, limit: int) -> List[SearchSuggestion]:
        """Findet Vorschläge basierend auf Synonym-Gruppen."""
        suggestions = []

        # Prüfe, ob der partielle Begriff zu einer Synonym-Gruppe gehört
        for group in self.synonym_expander.get_all_groups():
            # Prüfe Hauptbegriff
            if group.primary.lower().startswith(partial):
                freq = self._get_term_frequency(group.primary)
                if freq > 0:
                    suggestions.append(
                        SearchSuggestion(term=group.primary, frequency=freq, category="synonym", confidence=0.9)
                    )

            # Prüfe Synonyme
            for synonym in group.synonyms:
                if synonym.lower().startswith(partial):
                    freq = self._get_term_frequency(synonym)
                    if freq > 0:
                        suggestions.append(
                            SearchSuggestion(term=synonym, frequency=freq, category="synonym", confidence=0.8)
                        )

        # Nach Frequenz sortieren und limitieren
        suggestions.sort(key=lambda s: s.frequency, reverse=True)
        return suggestions[:limit]

    def _get_fuzzy_matches(self, partial: str, limit: int) -> List[SearchSuggestion]:
        """Findet ähnliche Begriffe mit Fuzzy-Matching."""
        suggestions = []

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Prüfe, ob FTS5-Vokabular verfügbar ist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chapter_fts_vocab'")
                if not cursor.fetchone():
                    # Fallback: Direkte Suche in Kapitel-Titeln
                    sql = """
                    SELECT title, 1 as cnt
                    FROM chapter
                    WHERE LOWER(title) LIKE ?
                      AND LENGTH(title) >= 3
                    LIMIT ?
                    """
                    cursor.execute(sql, (f"%{partial}%", limit))
                    results = cursor.fetchall()

                    # Extrahiere Wörter aus Titeln
                    word_counts = {}
                    for title, _ in results:
                        words = title.lower().split()
                        for word in words:
                            if len(word) >= 3 and partial in word:
                                word_counts[word] = word_counts.get(word, 0) + 1

                    # Konvertiere zu Tupeln
                    results = [(word, count) for word, count in word_counts.items()]
                else:
                    # Original FTS5-Vokabular-Suche
                    sql = """
                    SELECT term, cnt
                    FROM chapter_fts_vocab
                    WHERE term LIKE ?
                      AND LENGTH(term) >= 3
                      AND cnt >= 1
                      AND term NOT LIKE ?
                    ORDER BY cnt DESC
                    LIMIT ?
                    """
                    cursor.execute(sql, (f"%{partial}%", f"{partial}%", limit))
                    results = cursor.fetchall()

                for term, freq in results:
                    confidence = self._calculate_fuzzy_confidence(partial, term)
                    if confidence > 0.3:  # Mindest-Confidence
                        suggestions.append(
                            SearchSuggestion(term=term, frequency=freq, category="related", confidence=confidence)
                        )

        except sqlite3.Error as e:
            logger.warning(f"Fehler beim Fuzzy-Matching: {e}")

        return suggestions[:limit]

    def _get_term_frequency(self, term: str) -> int:
        """Gibt die Häufigkeit eines Begriffs im FTS5-Vokabular zurück."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT cnt FROM chapter_fts_vocab WHERE term = ?", (term,))
                result = cursor.fetchone()
                return result[0] if result else 0
        except sqlite3.Error:
            return 0

    def _calculate_fuzzy_confidence(self, partial: str, full_term: str) -> float:
        """Berechnet einen Confidence-Score für Fuzzy-Matches."""
        if not partial or not full_term:
            return 0.0

        # Einfache Ähnlichkeitsmetriken
        partial_lower = partial.lower()
        term_lower = full_term.lower()

        # Prefix-Bonus
        if term_lower.startswith(partial_lower):
            return 0.9

        # Substring-Match
        if partial_lower in term_lower:
            # Je näher am Anfang, desto höher der Score
            pos = term_lower.index(partial_lower)
            return max(0.7 - (pos * 0.1), 0.3)

        # Levenshtein-ähnliche einfache Metrik
        common_chars = sum(c1 == c2 for c1, c2 in zip(partial_lower, term_lower))
        similarity = common_chars / max(len(partial_lower), len(term_lower))

        return similarity * 0.6

    def get_popular_terms(self, limit: int = 20) -> List[SearchSuggestion]:
        """Gibt die populärsten Suchbegriffe zurück (für Leer-Suche o.ä.)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                sql = """
                SELECT term, cnt
                FROM chapter_fts_vocab
                WHERE LENGTH(term) >= 4
                  AND cnt >= 5
                  AND term NOT IN ('the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'man', 'men', 'put', 'say', 'she', 'too', 'use')
                ORDER BY cnt DESC
                LIMIT ?
                """

                cursor.execute(sql, (limit,))
                results = cursor.fetchall()

                return [
                    SearchSuggestion(term=term, frequency=freq, category="popular", confidence=1.0)
                    for term, freq in results
                ]

        except sqlite3.Error as e:
            logger.warning(f"Fehler beim Abrufen populärer Begriffe: {e}")
            return []

    def get_suggestions_for_strategy(self, partial_query: str, strategy, limit: int = 10) -> List[str]:
        """
        Vereinfachte API für GUI-Integration.

        Args:
            partial_query: Partielle Sucheingabe
            strategy: Nicht verwendet, für Kompatibilität
            limit: Maximale Anzahl Vorschläge

        Returns:
            Liste von Suggestion-Strings (für QCompleter)
        """
        suggestions = self.get_suggestions(partial_query, limit)

        # Formatiere für Anzeige: "begriff (123 Kapitel)"
        formatted = []
        for suggestion in suggestions:
            if suggestion.category == "exact":
                formatted.append(f"{suggestion.term} ({suggestion.frequency})")
            elif suggestion.category == "synonym":
                formatted.append(f"{suggestion.term} ({suggestion.frequency}) ~")
            else:
                formatted.append(f"{suggestion.term} ({suggestion.frequency}) ?")

        return formatted

    def refresh_cache(self):
        """Erneuert den internen Cache (falls nötig)."""
        # Für zukünftige Optimierungen
        pass
