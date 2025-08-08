#!/usr/bin/env python3
"""Korrigiere Channel Handles in der Datenbank."""

from yt_database.database import Channel

def update_channel_handles():
    """Aktualisiere die Channel Handles in der Datenbank."""

    print("=== Channel-Daten vor der Korrektur ===")
    for channel in Channel.select():
        print(f"ID: {channel.channel_id}")
        print(f"Name: {channel.name}")
        print(f"Handle: {channel.handle}")
        print(f"URL: {channel.url}")
        print("-" * 40)

    # Korrigiere das Handle für 99 ZU EINS
    try:
        channel = Channel.get(Channel.channel_id == "UCTRjcYzSUGb0UwTP1gNf1uQ")
        old_handle = channel.handle
        channel.handle = "@99ZUEINS"
        channel.save()
        print(f"Channel Handle aktualisiert: '{old_handle}' → '@99ZUEINS'")
    except Exception as e:
        print(f"Fehler beim Aktualisieren des Channel Handles: {e}")

    print("\n=== Channel-Daten nach der Korrektur ===")
    for channel in Channel.select():
        print(f"ID: {channel.channel_id}")
        print(f"Name: {channel.name}")
        print(f"Handle: {channel.handle}")
        print(f"URL: {channel.url}")
        print("-" * 40)

if __name__ == "__main__":
    update_channel_handles()
    print("\nChannel Handle Korrektur abgeschlossen!")
