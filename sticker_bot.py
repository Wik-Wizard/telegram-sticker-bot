import io
import os
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Conversation states
WAITING_FOR_ACTION, WAITING_FOR_TITLE = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Send me a photo and I’ll let you add a sticker or a title."
    )

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    response = requests.get(file.file_path)
    img = Image.open(io.BytesIO(response.download_as_bytearray())).convert("RGBA")

    # Save image in user_data
    context.user_data["photo"] = img

    # Show inline buttons
    keyboard = [
        [
            InlineKeyboardButton("Add the Tagline", callback_data="sticker"),
            InlineKeyboardButton("Add Title for the Image", callback_data="title")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an action:", reply_markup=reply_markup)
    return WAITING_FOR_ACTION

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if "photo" not in context.user_data:
        await query.edit_message_text("Please send a photo first!")
        return ConversationHandler.END

    img = context.user_data["photo"]

    if query.data == "sticker":
        # Sticker overlay process
        sticker = Image.open("sticker.png").convert("RGBA")
        sticker_size = int(min(img.width, img.height) * 0.25)
        sticker = sticker.resize((sticker_size, sticker_size))

        x = -2
        y = img.height - sticker.height + 2
        img.paste(sticker, (x, y), sticker)

        bio = io.BytesIO()
        bio.name = "output.png"
        img.save(bio, "PNG")
        bio.seek(0)

        await query.edit_message_text("✨ Sticker added successfully!")
        await query.message.reply_photo(photo=bio)
        context.user_data.pop("photo", None)
        return ConversationHandler.END

    elif query.data == "title":
        await query.edit_message_text("✏️ Enter your title here:")
        return WAITING_FOR_TITLE

async def add_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "photo" not in context.user_data:
        await update.message.reply_text("Please send a photo first!")
        return ConversationHandler.END

    img = context.user_data["photo"]
    text = update.message.text
    width, height = img.size
    draw = ImageDraw.Draw(img)

    # Max font size = 1/5 of image height
    max_text_height = height / 5
    font_size = int(max_text_height)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # adjust if needed
    font = ImageFont.truetype(font_path, font_size)

    # Reduce font size if text too wide
    text_width, text_height = draw.textsize(text, font=font)
    while text_width > width * 0.9:
        font_size -= 2
        font = ImageFont.truetype(font_path, font_size)
        text_width, text_height = draw.textsize(text, font=font)

    # Glass-like blurred background
    padding = 20
    box = [
        (width - text_width) // 2 - padding,
        (height - text_height) // 2 - padding,
        (width + text_width) // 2 + padding,
        (height + text_height) // 2 + padding
    ]
    region = img.crop(box).filter(ImageFilter.GaussianBlur(10))
    img.paste(region, box)

    # Draw white text
    draw = ImageDraw.Draw(img)
    draw.text(
        ((width - text_width) // 2, (height - text_height) // 2),
        text,
        font=font,
        fill=(255, 255, 255, 255)
    )

    bio = io.BytesIO()
    bio.name = "output.png"
    img.save(bio, "PNG")
    bio.seek(0)

    await update.message.reply_photo(photo=bio, caption="✨ Title added successfully!")
    context.user_data.pop("photo", None)
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.PHOTO, handle_image)],
        states={
            WAITING_FOR_ACTION: [CallbackQueryHandler(button_handler)],
            WAITING_FOR_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_title)]
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
