"""
Tests für die SearchStrategy-Funktionalität.
"""

import pytest
from yt_database.models.search_strategy import SearchStrategy, SEARCH_STRATEGIES


def test_search_strategy_enum():
    """Test dass alle SearchStrategy-Werte korrekt definiert sind."""
    assert SearchStrategy.AUTO.value == "auto"
    assert SearchStrategy.EXACT_PHRASE.value == "exact"
    assert SearchStrategy.ALL_WORDS.value == "all"
    assert SearchStrategy.ANY_WORD.value == "any"
    assert SearchStrategy.FUZZY.value == "fuzzy"


def test_search_strategies_info():
    """Test dass SEARCH_STRATEGIES die korrekten Metadaten enthält."""
    assert len(SEARCH_STRATEGIES) == 5

    # Finde Auto-Strategie
    auto_info = next(s for s in SEARCH_STRATEGIES if s.strategy == SearchStrategy.AUTO)
    assert "Auto" in auto_info.display_name
    assert "Intelligent" in auto_info.display_name
    assert auto_info.description is not None
    assert auto_info.example is not None


def test_all_strategies_have_info():
    """Test dass jede SearchStrategy in SEARCH_STRATEGIES vertreten ist."""
    strategy_values = {info.strategy for info in SEARCH_STRATEGIES}
    enum_values = set(SearchStrategy)

    assert strategy_values == enum_values, "SEARCH_STRATEGIES muss alle Enum-Werte enthalten"


class TestQueryBuilder:
    """Tests für die FTS5-Query-Builder-Logik."""

    def setup_method(self):
        """Mock ProjectManagerService für Tests."""
        from yt_database.services.project_manager_service import ProjectManagerService
        self.service = ProjectManagerService.__new__(ProjectManagerService)

    def test_exact_phrase_strategy(self):
        """Test der EXACT_PHRASE-Strategie."""
        result = self.service._build_fts_query("israel politik", SearchStrategy.EXACT_PHRASE)
        assert result == '"israel politik"'

    def test_all_words_strategy(self):
        """Test der ALL_WORDS-Strategie."""
        result = self.service._build_fts_query("israel politik", SearchStrategy.ALL_WORDS)
        assert result == "israel* AND politik*"

        # Einzelwort sollte unverändert bleiben
        result_single = self.service._build_fts_query("israel", SearchStrategy.ALL_WORDS)
        assert result_single == "israel"

    def test_any_word_strategy(self):
        """Test der ANY_WORD-Strategie."""
        result = self.service._build_fts_query("israel politik", SearchStrategy.ANY_WORD)
        assert result == "israel* OR politik*"

    def test_fuzzy_strategy(self):
        """Test der FUZZY-Strategie."""
        result = self.service._build_fts_query("israel politik", SearchStrategy.FUZZY)
        assert result == "israel* OR politik*"

        # Kurze Wörter sollten ohne Wildcard bleiben
        result_short = self.service._build_fts_query("ab cd", SearchStrategy.FUZZY)
        assert result_short == "ab OR cd"

    def test_auto_strategy_single_word(self):
        """Test der AUTO-Strategie mit Einzelwort."""
        result = self.service._build_fts_query("israel", SearchStrategy.AUTO)
        assert result == "israel*"

    def test_auto_strategy_two_words(self):
        """Test der AUTO-Strategie mit zwei Wörtern."""
        result = self.service._build_fts_query("israel politik", SearchStrategy.AUTO)
        # Sollte sowohl exakte Phrase als auch AND-Verknüpfung probieren
        assert '"israel politik"' in result
        assert "israel* AND politik*" in result
        assert " OR " in result

    def test_empty_query(self):
        """Test mit leerer Query."""
        for strategy in SearchStrategy:
            result = self.service._build_fts_query("", strategy)
            assert result == ""

    def test_whitespace_cleanup(self):
        """Test dass überflüssige Leerzeichen entfernt werden."""
        result = self.service._build_fts_query("  israel   politik  ", SearchStrategy.EXACT_PHRASE)
        assert result == '"israel politik"'
