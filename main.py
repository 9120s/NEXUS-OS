import os
import threading
from flask import Flask
import discord
from discord.ext import commands
from discord import app_commands

# 1. خادم Web لضمان بقاء البوت شغالاً 24/7 عبر UptimeRobot
app = Flask(__name__)

@app.route('/')
def home():
    return "NEXUS-OS Engine Status: ONLINE (24/7)"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# 2. إعداد البوت
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- 3. نظام التذاكر المتقدم (Interactive Ticket System) ---

class TicketModal(discord.ui.Modal):
    def __init__(self, category_name: str):
        super().__init__(title=f"تذكرة جديدة | {category_name}")
        self.category_name = category_name

        self.ticket_reason = discord.ui.TextInput(
            label="تفاصيل الطلب / المشكلة",
            style=discord.TextStyle.paragraph,
            placeholder="اكتب شرحاً متكاملاً لمساعدتك بأسرع وقت...",
            required=True,
            max_length=1000
        )
        self.add_item(self.ticket_reason)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        # إنشاء القناة وتحديد الصلاحيات
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            overwrites=overwrites
        )

        embed = discord.Embed(
            title=f"🌐 NEXUS-OS | تذكرة {self.category_name}",
            description=f"**صاحب التذكرة:** {user.mention}\n\n**السبب / التفاصيل:**\n```{self.ticket_reason.value}```",
            color=0x5865F2
        )
        embed.set_footer(text="NEXUS-OS Security & Support Engine")

        view = TicketManageButtons()
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ تم إنشاء تذكرتك بنجاح: {channel.mention}", ephemeral=True)

class TicketManageButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="إغلاق التذكرة", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="nexus_close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 جاري إغلاق التذكرة وأرشفة المحادثة...")
        await interaction.channel.delete()

class TicketSelectMenu(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="الدعم الفني والتقني", value="الدعم الفني", emoji="🛠️", description="حل المشاكل الفنية والاستفسارات العامة"),
            discord.SelectOption(label="التقديم للإدارة", value="تقديم إدارة", emoji="📋", description="إرسال طلب انضمام لطاقم الإدارة"),
            discord.SelectOption(label="البلاغات والشكاوى", value="بلاغ", emoji="⚠️", description="الإبلاغ عن مخالفة للقوانين"),
            discord.SelectOption(label="المتجر والاشتراكات", value="المتجر", emoji="💎", description="الاستفسار عن الرتب والميزات الخاصة"),
        ]
        super().__init__(placeholder="⚡ اختر قسم التذكرة للبدء...", min_values=1, max_values=1, options=options, custom_id="nexus_ticket_select")

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        await interaction.response.send_modal(TicketModal(selected))

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelectMenu())

# --- 4. أحداث البوت والأوامر ---

@bot.event
async def on_ready():
    print(f"==========================================")
    print(f" NEXUS-OS Engine Active: {bot.user.name}")
    print(f"==========================================")
    try:
        synced = await bot.tree.sync()
        print(f" [✓] تم مزامنة {len(synced)} أمر سلاش احترافي.")
    except Exception as e:
        print(f" [X] خطأ في المزامنة: {e}")

@bot.tree.command(name="nexus_tickets", description="نشر بنل الدعم والتذاكر التفاعلي لـ NEXUS-OS")
@app_commands.checks.has_permissions(administrator=True)
async def nexus_tickets(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌐 NEXUS-OS | مركز الدعم والخدمات",
        description="مرحباً بك في مركز الدعم التفاعلي.\nاختر القسم المناسب لمشكلتك من القائمة المنسدلة أسفله، وسيتم فتح تذكرة خاصة بك فوراً.",
        color=0x2b2d31
    )
    embed.set_image(url="https://i.imgur.com/v8t48vU.png")  # يمكن استبدال الصورة برابط شعار سيرفرك
    embed.set_footer(text="NEXUS-OS • Automated Support System")
    
    await interaction.channel.send(embed=embed, view=TicketPanelView())
    await interaction.response.send_message("تم نشر لوحة التذاكر التفاعلية بنجاح!", ephemeral=True)

# 5. التشغيل
if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("خطأ: لم يتم العثور على DISCORD_TOKEN في Environment Variables!")
