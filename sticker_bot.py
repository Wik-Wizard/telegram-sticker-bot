import io
import os
import requests
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Get your token from environment variable
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me an image and I’ll add a sticker to the left bottom corner!")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = file.file_path

    # Download the user’s image
    response = requests.get(file_path)
    img = Image.open(io.BytesIO(response.content)).convert("RGBA")

    # Open your sticker (ensure it's in the same folder)
    sticker = Image.open("sticker.png").convert("RGBA")

    # Resize the sticker if needed (you can adjust size here)
    sticker_size = int(min(img.width, img.height) * 0.25)
    sticker = sticker.resize((sticker_size, sticker_size))

    # Calculate position: left bottom corner
    x = 0  # 0 px from left
    y = img.height - sticker.height - 0  # 0 px from bottom

    # Paste the sticker (using alpha mask for transparency)
    img.paste(sticker, (x, y), sticker)

    # Save image to memory
    bio = io.BytesIO()
    bio.name = "output.png"
    img.save(bio, "PNG")
    bio.seek(0)

    # Send back the new image
    await update.message.reply_photo(photo=bio, caption="✨ Here’s your image with a sticker in the left bottom corner!")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()


