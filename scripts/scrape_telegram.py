import os
import json
import logging
from datetime import datetime
from pathlib import Path
import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError, RPCError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    filename='logs/scrape_telegram.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram API credentials
api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
phone = os.getenv('TELEGRAM_PHONE')

# List of Telegram channels to scrape
CHANNELS = [
    'Chemed123',
    'lobelia4cosmetics',
    'tikvahpharma',
    'medicalethiopia',
    'Thequorachannel',
    'medinethiopiainsider'
]

async def scrape_channel(client, channel, date_str):
    """Scrape messages and images from a single Telegram channel."""
    try:
        # Get channel entity
        entity = await client.get_entity(channel)
        channel_username = entity.username or channel
        logger.info(f"Starting scrape for channel: {channel_username}")

        # Define directories
        messages_dir = Path(f"data/raw/telegram_messages/{date_str}/{channel_username}")
        images_dir = Path(f"data/raw/telegram_images/{date_str}/{channel_username}")
        messages_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)

        # Scrape messages
        messages = []
        async for message in client.iter_messages(entity, limit=100):  # Adjust limit as needed
            message_data = {
                'id': message.id,
                'date': message.date.isoformat(),
                'text': message.text,
                'media': bool(message.media),
                'sender_id': message.sender_id,
                'views': message.views,
                'forwards': message.forwards
            }
            messages.append(message_data)

            # Download images if present
            if message.photo:
                try:
                    image_path = images_dir / f"{message.id}.jpg"
                    await client.download_media(message.photo, image_path)
                    logger.info(f"Downloaded image: {image_path}")
                    message_data['image_path'] = str(image_path)
                except Exception as e:
                    logger.error(f"Failed to download image for message {message.id} in {channel_username}: {e}")

        # Save messages to JSON
        json_path = messages_dir / 'messages.json'
        with json_path.open('w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(messages)} messages to {json_path}")

    except FloodWaitError as e:
        logger.error(f"Rate limit hit for {channel_username}. Wait for {e.seconds} seconds.")
        await asyncio.sleep(e.seconds)
    except RPCError as e:
        logger.error(f"Telegram API error for {channel_username}: {e}")
    except Exception as e:
        logger.error(f"Error scraping {channel_username}: {e}")

async def main():
    """Main function to scrape all channels."""
    # Initialize Telegram client
    client = TelegramClient('session', api_id, api_hash)
    await client.start(phone=phone)
    
    # Get current date for directory structure
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Scrape each channel
    for channel in CHANNELS:
        await scrape_channel(client, channel, date_str)
    
    await client.disconnect()
    logger.info("Scraping completed.")

if __name__ == '__main__':
    asyncio.run(main())