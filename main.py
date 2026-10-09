
import os
import json
import asyncio
from pathlib import Path

from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION = os.environ["TG_SESSION"]
SOURCE = os.environ["SOURCE_CHANNEL"]
DESTINATION = os.environ["DEST_CHANNEL"]

STATE_FILE = Path("last_id.json")


def save_last_id(message_id):
    STATE_FILE.write_text(
        json.dumps({"last_id": message_id}),
        encoding="utf-8"
    )


async def main():
    client = TelegramClient(
        StringSession(SESSION),
        API_ID,
        API_HASH
    )

    await client.start()

    try:
        source = await client.get_entity(SOURCE)
        destination = await client.get_entity(DESTINATION)

        if not STATE_FILE.exists():
            latest = await client.get_messages(source, limit=1)
            last_id = latest[0].id if latest else 0
            save_last_id(last_id)
            print(f"Initial checkpoint: {last_id}")
            return

        state = json.loads(
            STATE_FILE.read_text(encoding="utf-8")
        )
        last_id = int(state.get("last_id", 0))

        async for message in client.iter_messages(
            source, min_id=last_id, reverse=True
        ):
            try:
                if message.media:
                    media_bytes = await message.download_media(file=bytes)

                    if media_bytes is None:
                        raise RuntimeError("Media download failed")

                    await client.send_file(
                        destination,
                        media_bytes,
                        caption=message.message or ""
                    )

                elif message.message:
                    await client.send_message(
                        destination,
                        message.message,
                        link_preview=True
                    )

                save_last_id(message.id)
                print(f"Processed message {message.id}")

            except Exception as error:
                print(f"Failed at message {message.id}: {error}")
                raise

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
