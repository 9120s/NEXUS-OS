import os
import threading
from flask import Flask
import discord
from discord.ext import commands

# 1. إعداد خادم Web لاستجابة UptimeRobot
app = Flask(__name__)

@app.route('/')
def home():
    return "NEXUS-OS is Running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# 2. إعداد البوت
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# 3. تصميم القائمة المنسدلة للوحة NEXUS-OS
class NexusControlMenu(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="مركز التذاكر والدعم", value="tickets", emoji="🎫", description="نشر بنل التذاكر التفاعلي"),
            discord.SelectOption(label="نظام Party Up للألعاب", value="party", emoji="🎮", description="نشر لوحة الغرف الصوتية"),
            discord.SelectOption(label="إحصائيات السيرفر", value="stats", emoji="📊", description="عرض تقرير متكامل عن السيرفر"),
        ]
        super().__init__(placeholder="⚡ اختر النظام المراد إدارته...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "stats":
            guild = interaction.guild
            embed = discord.Embed(title=f"📊 إحصائيات {guild.name}", color=0x2b2d31)
            embed.add_field(name="👥 الأعضاء", value=f"`{guild.member_count}`", inline=True)
            embed.add_field(name="💬 القنوات", value=f"`{len(guild.channels)}`", inline=True)
            embed.add_field(name="🚀 التعزيزات", value=f"`{guild.premium_subscription_count}`", inline=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"تم اختيار نظام `{self.values[0]}` بنجاح.", ephemeral=True)

class NexusDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(NexusControlMenu())

# 4. أحداث البوت والأوامر
@bot.event
async def on_ready():
    print(f"==========================================")
    print(f" تم تسجيل الدخول بنجاح باسم: {bot.user.name}")
    print(f"==========================================")
    try:
        synced = await bot.tree.sync()
        print(f"تم مزامنة {len(synced)} أمر بنجاح.")
    except Exception as e:
        print(f"فشلت المزامنة: {e}")

@bot.tree.command(name="nexus", description="فتح لوحة تحكم NEXUS-OS الرئيسية")
async def nexus(interaction: discord.Interaction):
    embed = discord.Embed(
        title="✨ NEXUS-OS | Control Center",
        description="مرحباً بك في لوحة الإدارة السريعة. حدد الخيار المطلوب من القائمة أدناه لتفعيل وإدارة الأنظمة.",
        color=0x5865F2
    )
    embed.set_footer(text="NEXUS-OS • System v2.0")
    await interaction.response.send_message(embed=embed, view=NexusDashboardView(), ephemeral=True)

@bot.tree.command(name="ping", description="فحص سرعة استجابة البوت")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! السرعة: {round(bot.latency * 1000)}ms")

# 5. تشغيل البوت
if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("خطأ: لم يتم العثور على DISCORD_TOKEN في Environment Variables!")
