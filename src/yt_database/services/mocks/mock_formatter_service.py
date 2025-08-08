from loguru import logger


class MockFormatterService:
    """
    Mock für FormatterService.

    Simuliert die Formatierung für Tests. Gibt einen festen String zurück.

    Beispiel:
        >>> mock = MockFormatterService()
        >>> mock.format(["foo"], {"id": "bar"})
        'MOCK-HEADER\nMOCK-TRANSKRIPT: [\'foo\']'
    """

    def format(self, transcript, metadata):
        logger.info(f"[MOCK] format aufgerufen für {metadata.get('id', 'unbekannt')}")
        return f"MOCK-HEADER\nMOCK-TRANSKRIPT: {transcript}"

    def parse_json3_transcript(self, file_path: str) -> list[dict[str, str]]:
        """
        Mockt das Parsen einer json3-Transkriptdatei. Gibt eine Dummy-Liste zurück.
        Für Tests: Simuliere das Parsen, indem eine feste Liste zurückgegeben wird.
        """
        logger.info(f"[MOCK] parse_json3_transcript aufgerufen für {file_path}")
        return [{"text": "Testzeile", "start": "0.0", "end": "1.0"}]
