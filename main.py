import os
import discord
from discord.ext import commands
import database

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await database.init_db()
    print(f"🤖 NEXUS OS يعمل بنجاح باسم: {bot.user}")

# تحميل الموديولات الثلاثة
bot.load_extension("cogs.profile")
bot.load_extension("cogs.tickets")
bot.load_extension("cogs.dashboard")

bot.run(os.getenv("DISCORD_TOKEN"))