import os
import threading
from flask import Flask
import discord
from discord.ext import commands

# 1. خادم Web لضمان استمرار التشغيل 24/7 على Render
app = Flask(__name__)

@app.route('/')
def home():
    return "AURA Core Engine: ONLINE"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# 2. إعداد البوت مع كامل الصلاحيات (Intents)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# دالة مساعدة للبحث عن القنوات بغض النظر عن الإيموجيات
def get_log_channel(guild, keyword):
    return discord.utils.find(lambda c: keyword in c.name, guild.text_channels)

# --- 3. نظام التذاكر التفاعلي ---

class TicketModal(discord.ui.Modal):
    def __init__(self, category: str):
        super().__init__(title=f"تذكرة: {category}")
        self.category = category
        self.add_item(discord.ui.InputText(
            label="تفاصيل المشكلة / الطلب",
            style=discord.InputTextStyle.long,
            placeholder="اكتب شرحاً متكاملاً لمساعدتك بأسرع وقت..."
        ))

    async def callback(self, interaction: discord.Interaction):
        guild, user = interaction.guild, interaction.user
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        ch = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites)
        
        details_text = self.children[0].value
        desc = f"**صاحب التذكرة:** {user.mention}\n\n**التفاصيل:**\n```{details_text}
