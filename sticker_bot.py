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

# States for conversation
WAITING_FOR_TITLE = 1

# Store user photo temporarily
user_photos = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me a photo and I’ll let you add a sticker or a title!"
    )

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = file.file_path

    response = requests.get(file_path)
    img = Image.open(io.BytesIO(response.content)).convert("RGBA")

    # Save the image temporarily in memory
    user_photos[update.message.from_user.id] = img

    # Show inline buttons
    keyboard = [
        [
            InlineKeyboardButton("Add the Tagline", callback_data="sticker"),
            InlineKeyboardButton("Add Title for the Image", callback_data="title")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an action:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in user_photos:
        await query.edit_message_text("Please send a photo first!")
        return

    img = user_photos[user_id]

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
        # Remove temp image
        user_photos.pop(user_id, None)

    elif query.data == "title":
        await query.edit_message_text("✏️ Enter your title here:")
        return WAITING_FOR_TITLE

async def add_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_photos:
        await update.message.reply_text("Please send a photo first!")
        return ConversationHandler.END

    img = user_photos[user_id]
    text = update.message.text

    draw = ImageDraw.Draw(img)
    width, height = img.size

    # Determine max font size to occupy 1/5 of image height
    max_text_height = height / 5
    font_size = int(max_text_height)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # system font path
    font = ImageFont.truetype(font_path, font_size)

    # Reduce font size if text too wide
    text_width, text_height = draw.textsize(text, font=font)
    while text_width > width * 0.9:
        font_size -= 2
        font = ImageFont.truetype(font_path, font_size)
        text_width, text_height = draw.textsize(text, font=font)

    # Create blurred rectangle background
    padding = 20
    box = [
        (width - text_width) // 2 - padding,
        (height - text_height) // 2 - padding,
        (width + text_width) // 2 + padding,
        (height + text_height) // 2 + padding
    ]
    # Crop region, blur, then paste with alpha
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
    user_photos.pop(user_id, None)
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.PHOTO, handle_image)],
        states={
            WAITING_FOR_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_title)]
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
