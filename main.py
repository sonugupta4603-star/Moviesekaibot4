import os
import threading
import base64
from flask import Flask
import telebot
from openai import OpenAI

# Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
MODEL = os.environ.get("MODEL_NAME", "deepseek-ai/DeepSeek-V4.1-Flash:novita")
PORT = int(os.environ.get("PORT", 5000))

# Hugging Face Router & Telegram Bot
client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=HF_TOKEN)
bot = telebot.TeleBot(BOT_TOKEN)

# Flask Web Server (Keep-Alive ke liye sirf 2 letters ka response: "OK")
app = Flask(__name__)

@app.route("/")
def home():
    return "OK", 200

# Telegram Commands
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(message, "Hello! Main aapka AI Chatbot hoon. Koi bhi sawaal ya photo bhejiye!")

# Text Chat
@bot.message_handler(content_types=["text"])
def chat(message):
    try:
        bot.send_chat_action(message.chat.id, "typing")
        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": message.text}]
        )
        reply = res.choices[0].message.content or "Empty response"
        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

# Image Analysis
@bot.message_handler(content_types=["photo"])
def analyze_image(message):
    try:
        bot.send_chat_action(message.chat.id, "typing")
        file_info = bot.get_file(message.photo[-1].file_id)
        img_bytes = bot.download_file(file_info.file_path)
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        
        prompt = message.caption if message.caption else "Describe this image in one sentence."
        res = client.chat.completions.create(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]
            }]
        )
        bot.reply_to(message, res.choices[0].message.content or "Empty response")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

if __name__ == "__main__":
    # Start bot polling in background
    threading.Thread(target=bot.infinity_polling, kwargs={"skip_pending": True}, daemon=True).start()
    # Start web server for Render
    app.run(host="0.0.0.0", port=PORT)
