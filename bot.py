# Made by @ANONYMOUS_AMIT
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ConversationHandler
)
import os
import requests

# Define states
QUESTION = 1

# List of questions to ask user
questions = [
    '🖥️ 1. Laptop/PC Model?', '⚙️ 2. Processor (CPU)?', '🎮 3. GPU (Integrated/Dedicated & model)?',
    '💾 4. RAM Size (GB)?', '🗂️ 5. Storage Type (SSD or HDD)?', '🪟 6. Windows Version?',
    '🔒 7. Is Virtualization enabled in BIOS (Yes/No)?', '🧰 8. Is Hyper-V Enabled? (Yes/No)',
    '🛡️ 9. Is Core Isolation Enabled? (Yes/No)', '🔌 10. Power Plan (Balanced/High Perf)?',
    '🌡️ 11. Fan Profile (Silent/Balanced/Turbo)?', '📱 12. Emulator Name + Version?',
    '🤖 13. Android Version in Emulator?', '🧠 14. CPU Cores allocated?', '📊 15. RAM allocated to Emulator?',
    '🎨 16. Graphics Mode (OpenGL/Vulkan/DirectX)?', '🎯 17. FPS Cap in Emulator?',
    '🖼️ 18. Resolution in Emulator?', '📏 19. DPI Setting?', '🔓 20. Root Mode? (Yes/No)',
    '🎞️ 21. Frame Interpolation or V-Sync? (Yes/No)', '🕹️ 22. Game Name + Version?',
    '🎮 23. In-Game Graphics Setting?', '⏱️ 24. FPS Setting in Game?', '🧭 25. Gyroscope Used (Yes/No)?',
    '🎛️ 26. Game Control Mode?', '🔥 27. Avg FPS on BGMI Events (Hot Drop)?',
    '⚔️ 28. Avg FPS in Normal Fight?', '🧮 29. Avg CPU Usage during gameplay?',
    '📈 30. GPU Usage %?', '💽 31. RAM Usage in Task Manager?', '🥶 32. FPS Drops or Freezes (when)?',
    '🌐 33. Ping Consistency?', '📦 34. Apps Running in Background?', '👓 35. Any Overlay Software?',
    '📹 36. Screen Recording/Streaming ON?', '💿 37. Emulator Installed on SSD/HDD?',
    '🎯 38. Main Goal: Smooth gameplay / Graphics / Streaming?', '🔋 39. Battery or Plugged-in?',
    '🛠️ 40. Any custom Windows or emulator tweaks?',
    '🚨 41. Describe your exact problem in gameplay or emulator (e.g., low FPS, lag, stutter, crash)?'
]

# User data store
user_data_store = {}

# Load Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Prompt generator
def generate_prompt(answers):
    prompt = "You are an emulator optimization expert. Based on the following user data, analyze and give best emulator settings for smooth 60 FPS performance in BGMI.\n\n"
    for q, a in zip(questions, answers):
        prompt += f"{q}\nUser: {a}\n"
    prompt += ("\nRespond with:\n"
               "1. Best emulator config (CPU cores, RAM, graphics mode, FPS, DPI)\n"
               "2. Best in-game graphics + FPS config\n"
               "3. Required Windows/BIOS tweaks\n"
               "4. What to disable (Hyper-V, Core Isolation, overlays, etc)\n"
               "5. Suggest a better emulator if current one is poor\n"
               "6. Step-by-step guide to apply all fixes\n"
               "7. Explain what might be causing the user's specific problems described in last question\n")
    return prompt

# Gemini API call
def call_gemini_api(prompt):
    if not GEMINI_API_KEY:
        return "❌ Gemini API key is not configured. Please set the GEMINI_API_KEY environment variable."

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"❌ Gemini API error: {str(e)}"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id] = {'answers': [], 'q_index': 0}
    await update.message.reply_text(
        "👋 Welcome to the Emulator Optimizer Bot!\n"
        "⚙️ I will ask you a series of questions to help you get the best settings for smooth gaming performance.\n\n"
        "✨ Made by @ANONYMOUS_AMIT\n\n" + questions[0]
    )
    return QUESTION

# Handle answers
async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_data_store.get(user_id)

    if not state:
        await update.message.reply_text("❌ Something went wrong. Please type /start again.")
        return ConversationHandler.END

    state['answers'].append(update.message.text)
    state['q_index'] += 1

    if state['q_index'] < len(questions):
        await update.message.reply_text(questions[state['q_index']])
        return QUESTION
    else:
        prompt = generate_prompt(state['answers'])
        context.user_data['prompt'] = prompt

        keyboard = [[InlineKeyboardButton("⚡ Generate with Gemini", callback_data="generate_gemini")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("✅ All done! Paste the below prompt into ChatGPT or Gemini to get your best settings:\n")
        await update.message.reply_text(f"```\n{prompt}\n```", parse_mode=ParseMode.MARKDOWN)
        await update.message.reply_text("Or click below to generate automatically:", reply_markup=reply_markup)
        return ConversationHandler.END

# /cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Process cancelled.")
    return ConversationHandler.END

# Handle Gemini button press
async def gemini_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    prompt = context.user_data.get('prompt')
    if not prompt:
        await query.edit_message_text("❌ No prompt found. Please start again with /start.")
        return

    await query.edit_message_text("⚙️ Generating response using Gemini... Please wait.")
    reply = call_gemini_api(prompt)

    # Split reply if too long for Telegram (4096 char limit)
    max_len = 4096
    for i in range(0, len(reply), max_len):
        await query.message.reply_text(reply[i:i+max_len])

# Main function
def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("❌ Error: BOT_TOKEN not set in environment variables.")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    # Conversation handler for collecting answers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(gemini_callback, pattern="^generate_gemini$"))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()

