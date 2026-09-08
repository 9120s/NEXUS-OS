import os
import threading
import discord
from flask import Flask
import database

# 1. إعداد خادم ويب خفيف لإرضاء Render
app = Flask(__name__)

@app.route('/')
def home():
    return "NEXUS-OS Bot is Online!"

def run_web_service():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. إعدادات بوت ديسكورد
bot = discord.Bot(intents=discord.Intents.default())

@bot.event
async def on_ready():
    await database.init_db()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Database initialized successfully!")

# 3. تشغيل الويب سيرفر والبوت معاً
if __name__ == "__main__":
    # تشغيل سيرفر Flask في Thread منفصل
    threading.Thread(target=run_web_service, daemon=True).start()
    
    # الحصول على التوكن وتشغيل البوت
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("ERROR: DISCORD_TOKEN environment variable not set!")
