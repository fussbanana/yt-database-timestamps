"""Query-Parser für benutzerfreundliche FTS5-Suchen.

Dieses Modul wandelt eine rohe Suchzeichenfolge in eine strukturierte Darstellung
(`SearchQuery`) sowie in einen für SQLite FTS5 kompatiblen MATCH-Ausdruck um.

Unterstützte Syntaxmerkmale:
- Phrasen: "genaue phrase" (bleiben als Anführungszeichen erhalten)
- Muss-Begriffe: +token (werden mit AND verknüpft)
- Ausgeschlossene Begriffe: -token (werden als AND NOT verknüpft)
- Neutrale Begriffe: token (werden AND-verknüpft)
- Prefix-Match: Einzelwörter erhalten ein Suffix "*" (für FTS5-Präfixsuche)

Verwendung:
    >>> q = parse_search_query('"klima wandel" +politik -meinung daten')
    >>> q.fts5_match
    '("klima wandel" AND +politik* AND daten* AND NOT meinung*)'

Die Funktion `tokens_for_highlighting` liefert eine konsolidierte Liste an
Begriffen (ohne ausgeschlossene), die sich gut für UI-Hervorhebung eignen.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from loguru import logger


@dataclass(frozen=True)
class SearchQuery:
    """Strukturierte Repräsentation einer Sucheingabe.

    Attributes:
        raw: Originale Nutzereingabe (unverändert, getrimmt).
        phrases: Liste exakter Phrasen (innerhalb von ").
        required: Muss-Begriffe (mit führendem '+').
        excluded: Ausgeschlossene Begriffe (mit führendem '-').
        terms: Neutrale Einzelbegriffe.
        fts5_match: Generierter FTS5-MATCH-Ausdruck.
    """

    raw: str
    phrases: List[str]
    required: List[str]
    excluded: List[str]
    terms: List[str]
    fts5_match: str


_RE_PHRASE = re.compile(r'"([^"]+)"')
"""Regex zum Extrahieren von Phrasen in doppelten Anführungszeichen."""


def _normalize_token(token: str) -> str:
    """Normalisiert ein Einzelwort-Token für die Suche.

    - Whitespacebeschnitt und Kleinschreibung
    - Entfernt gängige Satzzeichen an den Rändern

    Args:
        token: Ursprüngliches Token (ein Wort).

    Returns:
        str: Normalisiertes Token (kann leer sein).
    """
    # Beginn der Normalisierung – wir loggen, um Eingaben überblicken zu können
    logger.debug(f"Normalisiere Token: '{token}'")
    # Leerraum entfernen und kleinschreiben
    token = token.strip().lower()
    # Satzzeichen am Rand entfernen (Innenleben bleibt erhalten)
    normalized = token.strip(".,:;!?")
    logger.debug(f"Normalisiertes Token: '{normalized}'")
    return normalized


def _prefixify(token: str) -> str:
    """Fügt, falls sinnvoll, ein Präfix-Wildcard an ein Token an.

    Args:
        token: Ein bereits normalisiertes Token.

    Returns:
        str: Unverändertes Token oder Token mit '*' für FTS5-Präfixsuche.
    """
    logger.debug(f"Prefixify für Token: '{token}'")
    # Leere Tokens bleiben unverändert
    if not token:
        return token
    # Bereits vorhandenes Wildcard nicht doppelt hinzufügen
    if token.endswith("*"):
        return token
    with_star = f"{token}*"
    logger.debug(f"Mit Präfix-Wildcard: '{with_star}'")
    return with_star


def parse_search_query(raw: str) -> SearchQuery:
    """Parst eine Roh-Query in eine `SearchQuery` für FTS5.

    Unterstützte Syntax:
    - "phrase mit leerzeichen" → exakte Phrase
    - +muss → Muss-Token
    - -nicht → Ausschluss-Token
    - wort → neutrales Token

    Args:
        raw: Unverarbeitete Nutzereingabe.

    Returns:
        SearchQuery: Strukturierte Query inklusive FTS5-MATCH-Ausdruck.
    """
    logger.debug(f"parse_search_query(raw={raw!r})")
    # Robuste Vorverarbeitung: None → "" und Trim
    raw = (raw or "").strip()
    if not raw:
        logger.debug("Leere Query – gebe leere SearchQuery zurück")
        return SearchQuery(raw="", phrases=[], required=[], excluded=[], terms=[], fts5_match="")

    # Phrasen extrahieren und für die Tokenisierung temporär durch Leerzeichen ersetzen
    phrases = [m.group(1).strip() for m in _RE_PHRASE.finditer(raw) if m.group(1).strip()]
    logger.debug(f"Gefundene Phrasen: {phrases}")
    tmp = _RE_PHRASE.sub(" ", raw)

    # Sammel-Container für die verschiedenen Token-Klassen
    required: List[str] = []
    excluded: List[str] = []
    terms: List[str] = []

    # Tokenisierung der nicht-phrase Teile
    for part in tmp.split():
        # Überspringe leere Split-Resultate
        if not part:
            continue
        # Prüfe auf führendes '+' oder '-' für Muss/Ausschluss
        sign = part[0]
        body = part[1:] if sign in {"+", "-"} else part
        tok = _normalize_token(body)
        if not tok:
            continue
        if sign == "+":
            required.append(tok)
        elif sign == "-":
            excluded.append(tok)
        else:
            terms.append(tok)

    logger.debug(f"Tokens – required={required}, excluded={excluded}, terms={terms}")

    # MATCH-Ausdruck zusammensetzen
    match_parts: List[str] = []
    # Phrasen unverändert (ohne Wildcard) und in Anführungszeichen
    for ph in phrases:
        match_parts.append(f'"{ph}"')

    # Muss-Token mit '+' und Präfix-Wildcard
    for t in required:
        match_parts.append(f"+{_prefixify(t)}")

    # Neutrale Token mit Präfix-Wildcard
    for t in terms:
        match_parts.append(_prefixify(t))

    # Ausgeschlossene Token mit NOT und Präfix-Wildcard
    for t in excluded:
        match_parts.append(f"NOT {_prefixify(t)}")

    # Für Determinismus explizit mit AND verbinden und einklammern
    fts5_match = " AND ".join(match_parts) if match_parts else ""
    if match_parts and not (fts5_match.startswith("(") and fts5_match.endswith(")")):
        fts5_match = f"({fts5_match})"
    logger.debug(f"Erzeugter MATCH-Ausdruck: {fts5_match!r}")

    return SearchQuery(
        raw=raw,
        phrases=phrases,
        required=required,
        excluded=excluded,
        terms=terms,
        fts5_match=fts5_match,
    )


def tokens_for_highlighting(query: SearchQuery) -> List[str]:
    """Erzeugt eine deduplizierte Liste von Begriffen für UI-Hervorhebung.

    Phrasen und alle positiven/neutralen Tokens werden aufgenommen, ausgeschlossene
    Begriffe nicht. Die Deduplizierung erfolgt case-insensitiv.

    Args:
        query: Das Ergebnis von `parse_search_query`.

    Returns:
        List[str]: Liste von zu markierenden Begriffen.
    """
    logger.debug(
        "tokens_for_highlighting: phrases=%s, required=%s, terms=%s",
        query.phrases,
        query.required,
        query.terms,
    )
    # Deduplizierung über Kleinbuchstaben-Repräsentation
    seen = set()
    result: List[str] = []

    def _add(x: str) -> None:
        # Case-insensitive Deduplizierung
        key = x.lower()
        if key and key not in seen:
            seen.add(key)
            result.append(x)

    # Phrasen zuerst (werden in der UI oft wichtig hervorgehoben)
    for p in query.phrases:
        _add(p)
    # Danach Required + neutrale Begriffe
    for t in query.required + query.terms:
        _add(t)

    logger.debug(f"Highlighting-Begriffe: {result}")
    return result
