import io
import os
import requests
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Get your token securely from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me an image and I’ll add a sticker tightly to the bottom-left corner!")


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = file.file_path

    # Download the user's image
    response = requests.get(file_path)
    img = Image.open(io.BytesIO(response.content)).convert("RGBA")

    # Open your sticker (make sure 'sticker.png' is in the same folder)
    sticker = Image.open("sticker.png").convert("RGBA")

    # Keep your original sticker sizing logic
    sticker_size = int(min(img.width, img.height) * 0.25)
    sticker = sticker.resize((sticker_size, sticker_size))

    # 🧩 Updated position — exactly bottom-left corner (no gap)
    x = 0  # touches left edge
    y = img.height - sticker.height  # touches bottom edge

    # Paste sticker with transparency
    img.paste(sticker, (x, y), sticker)

    # Save edited image to memory
    bio = io.BytesIO()
    bio.name = "output.png"
    img.save(bio, "PNG")
    bio.seek(0)

    # Send back modified image
    await update.message.reply_photo(photo=bio, caption="✨ Sticker added snugly to the bottom-left corner!")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    print("✅ Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
