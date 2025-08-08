"""
Phase 5: Semantische Suche mit AI-Embeddings (Vereinfachte Version)

Dieses Modul implementiert bedeutungsbasierte Suche mit Vektor-Embeddings.
Verwendet SQLite BLOB-Speicherung + In-Memory Similarity Search für Einfachheit.
"""

import logging
import sqlite3
from typing import List, Optional, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

from yt_database.models.search_models import SearchResult

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """
    Semantische Suche mit AI-Embeddings für bedeutungsbasierte Suchergebnisse.

    Vereinfachte Version ohne sqlite-vss - verwendet Standard SQLite + NumPy für Similarity.

    Funktionsweise:
    1. Texte werden in 384-dimensionale Vektoren umgewandelt (Embeddings)
    2. Ähnlichkeit zwischen Query und Dokumenten über Cosine-Similarity
    3. Findet semantisch ähnliche Inhalte, auch ohne exakte Keyword-Matches

    Beispiel:
    - Query: "python tutorial"
    - Findet auch: "Programmier-Einführung", "Coding-Grundlagen", "Script-Anleitung"
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self._model: Optional[SentenceTransformer] = None
        self._db_connection: Optional[sqlite3.Connection] = None

        logger.info(f"SemanticSearchService initialisiert für DB: {db_path}")
        logger.info(f"Embedding-Model: {self.model_name}")

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-Loading des Embedding-Models (150MB Download beim ersten Mal)."""
        if self._model is None:
            logger.info("Lade Embedding-Model... (kann beim ersten Mal etwas dauern)")
            # Forciere CPU-Verwendung für Kompatibilität
            self._model = SentenceTransformer(self.model_name, device="cpu")
            logger.info(f"Model geladen: {self.model_name} (CPU)")
        return self._model

    @property
    def db_connection(self) -> sqlite3.Connection:
        """Lazy-Loading der Datenbankverbindung."""
        if self._db_connection is None:
            self._db_connection = sqlite3.connect(self.db_path)
            logger.debug("SQLite Datenbankverbindung hergestellt")
        return self._db_connection

    def initialize_vector_database(self) -> None:
        """
        Erstellt die Vector Database Tabellen falls sie nicht existieren.

        Erstellt:
        - chapter_embeddings: Speichert die 384-dim Vektor-Embeddings
        """
        conn = self.db_connection
        cursor = conn.cursor()

        # Erstelle Embeddings-Tabelle
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chapter_embeddings (
                chapter_id INTEGER PRIMARY KEY,
                embedding_vector BLOB NOT NULL,
                text_content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chapter_id) REFERENCES chapters(id)
            )
        """
        )

        # Index für bessere Performance
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chapter_embeddings_id
            ON chapter_embeddings(chapter_id)
        """
        )

        conn.commit()
        logger.info("Vector Database Tabellen erstellt/überprüft")

    def create_embedding(self, text: str) -> np.ndarray:
        """
        Wandelt Text in 384-dimensionalen Vektor um.

        Args:
            text: Der zu konvertierende Text

        Returns:
            NumPy Array mit 384 Dimensionen, repräsentiert die Bedeutung des Textes
        """
        if not text.strip():
            # Leerer Text -> Null-Vektor
            return np.zeros(384)

        # Model erstellt Embedding (Bedeutungs-Vektor)
        embedding = self.model.encode(text, normalize_embeddings=True)

        # Konvertiere zu NumPy Array falls nötig
        if hasattr(embedding, "numpy"):
            embedding = embedding.numpy()
        elif not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding)

        logger.debug(f"Embedding erstellt für Text-Length: {len(text)} -> Vector-Shape: {embedding.shape}")
        return embedding

    def store_chapter_embedding(self, chapter_id: int, text: str) -> None:
        """
        Erstellt und speichert Embedding für ein Kapitel.

        Args:
            chapter_id: ID des Kapitels
            text: Volltext des Kapitels (title + content)
        """
        embedding = self.create_embedding(text)

        conn = self.db_connection
        cursor = conn.cursor()

        # Speichere Embedding als BLOB (Binary Large Object)
        embedding_blob = embedding.tobytes()

        cursor.execute(
            """
            INSERT OR REPLACE INTO chapter_embeddings
            (chapter_id, embedding_vector, text_content)
            VALUES (?, ?, ?)
        """,
            (chapter_id, embedding_blob, text),
        )

        conn.commit()
        logger.debug(f"Embedding gespeichert für Kapitel {chapter_id}")

    def batch_create_embeddings(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Erstellt Embeddings für alle Kapitel ohne bestehende Embeddings.

        Args:
            limit: Optional - Begrenze Anzahl für Testing

        Returns:
            Statistiken über den Batch-Prozess
        """
        logger.info("Starte Batch-Embedding-Erstellung...")

        # Erst Vector Database initialisieren
        self.initialize_vector_database()

        conn = self.db_connection
        cursor = conn.cursor()

        # Finde Kapitel ohne Embeddings
        sql = """
            SELECT c.id, c.title, c.text_content
            FROM chapters c
            LEFT JOIN chapter_embeddings ce ON c.id = ce.chapter_id
            WHERE ce.chapter_id IS NULL
        """

        if limit:
            sql += f" LIMIT {limit}"

        cursor.execute(sql)
        chapters_to_process = cursor.fetchall()

        total_chapters = len(chapters_to_process)
        logger.info(f"Verarbeite {total_chapters} Kapitel für Embeddings...")

        processed = 0
        errors = 0

        for chapter_id, title, content in chapters_to_process:
            try:
                # Kombiniere Title + Content für bessere semantische Repräsentation
                full_text = f"{title}\n\n{content}" if content else title

                self.store_chapter_embedding(chapter_id, full_text)
                processed += 1

                if processed % 5 == 0:
                    logger.info(f"Fortschritt: {processed}/{total_chapters} Kapitel verarbeitet")

            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten von Kapitel {chapter_id}: {e}")
                errors += 1

        stats = {
            "total_chapters": total_chapters,
            "processed": processed,
            "errors": errors,
            "success_rate": processed / total_chapters if total_chapters > 0 else 0,
        }

        logger.info(f"Batch-Embedding abgeschlossen: {stats}")
        return stats

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Berechnet Cosine-Similarity zwischen zwei Vektoren."""
        # Normalisiere Vektoren falls nötig
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-10)
        vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-10)

        # Cosine-Similarity = Dot-Product von normalisierten Vektoren
        return float(np.dot(vec1_norm, vec2_norm))

    def semantic_search(self, query: str, limit: int = 20, similarity_threshold: float = 0.3) -> List[SearchResult]:
        """
        Führt semantische Suche basierend auf Bedeutungs-Ähnlichkeit durch.

        Args:
            query: Suchtext
            limit: Maximale Anzahl Ergebnisse
            similarity_threshold: Mindest-Ähnlichkeit (0.0-1.0)

        Returns:
            Liste von SearchResult, sortiert nach Semantic Similarity
        """
        if not query.strip():
            return []

        # Erstelle Embedding für die Query
        query_embedding = self.create_embedding(query)

        conn = self.db_connection
        cursor = conn.cursor()

        # Hole alle Embeddings mit zugehörigen Kapitel-Daten
        sql = """
            SELECT
                ce.chapter_id,
                ce.embedding_vector,
                c.title as chapter_title,
                c.start_time,
                c.end_time,
                c.video_id,
                t.title as video_title,
                t.channel_id,
                ch.name as channel_name,
                ch.handle as channel_handle,
                ce.text_content
            FROM chapter_embeddings ce
            JOIN chapters c ON ce.chapter_id = c.id
            JOIN transcripts t ON t.video_id = c.video_id
            JOIN channels ch ON ch.id = t.channel_id
        """

        cursor.execute(sql)
        rows = cursor.fetchall()

        # Berechne Similarities für alle Embeddings
        similarities = []
        for row in rows:
            chapter_id = row[0]
            embedding_blob = row[1]

            # Embedding aus BLOB rekonstruieren
            chapter_embedding = np.frombuffer(embedding_blob, dtype=np.float32)

            # Similarity berechnen
            similarity = self.cosine_similarity(query_embedding, chapter_embedding)

            if similarity >= similarity_threshold:
                similarities.append((similarity, row))

        # Sortiere nach Similarity (absteigend)
        similarities.sort(key=lambda x: x[0], reverse=True)

        # Erstelle SearchResult-Objekte
        results = []
        for similarity, row in similarities[:limit]:
            (
                chapter_id,
                _,
                chapter_title,
                start_time,
                end_time,
                video_id,
                video_title,
                channel_id,
                channel_name,
                channel_handle,
                text_content,
            ) = row

            # Timestamp URL erstellen
            timestamp_url = f"https://www.youtube.com/watch?v={video_id}&t={start_time}s"

            # Start-Zeit als String formatieren
            minutes = start_time // 60
            seconds = start_time % 60
            start_time_str = f"{minutes:02d}:{seconds:02d}"

            # Snippet aus dem Text erstellen
            snippet = text_content[:200] + "..." if len(text_content) > 200 else text_content

            result = SearchResult(
                video_title=video_title,
                channel_name=channel_name,
                channel_handle=channel_handle or "",
                chapter_title=chapter_title,
                timestamp_url=timestamp_url,
                start_time_str=start_time_str,
                relevance_score=similarity,  # Semantic Similarity als Relevanz
                highlighted_snippet=snippet,
            )
            results.append(result)

        logger.info(f"Semantische Suche für '{query}': {len(results)} Ergebnisse gefunden")
        return results

    def get_embedding_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken über die Embedding-Datenbank zurück."""
        conn = self.db_connection
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM chapter_embeddings")
            total_embeddings = cursor.fetchone()[0]
        except Exception as e:
            total_embeddings = 0

        try:
            cursor.execute("SELECT COUNT(*) FROM chapters")
            total_chapters = cursor.fetchone()[0]
        except Exception as e:
            total_chapters = 0

        coverage = total_embeddings / total_chapters if total_chapters > 0 else 0

        return {
            "total_embeddings": total_embeddings,
            "total_chapters": total_chapters,
            "coverage_percent": round(coverage * 100, 1),
            "model_name": self.model_name,
        }

    def close(self) -> None:
        """Schließt Datenbankverbindung."""
        if self._db_connection:
            self._db_connection.close()
            self._db_connection = None
            logger.debug("SemanticSearchService Datenbankverbindung geschlossen")
