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

# --- 3. نظام التذاكر وسجلات التذاكر ---

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
        
        # إنشاء القناة الخاصة بالتذكرة
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        ch = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites)
        
        details_text = self.children[0].value
        
        # استخدام Triple Quotes لمنع أي أخطاء في الأسطر النصية
        desc = f"""**صاحب التذكرة:** {user.mention}

**التفاصيل:**
```{details_text}```"""
        
        embed = discord.Embed(
            title=f"🌐 AURA | تذكرة جديدة ({self.category})",
            description=desc,
            color=0x5865F2
        )
        embed.set_footer(text="AURA Support Engine")

        view = discord.ui.View(timeout=None)
        close_btn = discord.ui.Button(label="إغلاق التذكرة", style=discord.ButtonStyle.danger, emoji="🔒")
        
        async def close_callback(inter: discord.Interaction):
            await inter.response.send_message("🔒 جاري إغلاق التذكرة وحفظ السجل...")
            
            log_channel = discord.utils.get(guild.text_channels, name="log-tickets") or discord.utils.get(guild.text_channels, name="logs-ticket")
            if log_channel:
                log_embed = discord.Embed(
                    title="📝 تم إغلاق تذكرة",
                    description=f"**اسم القناة:** `{ch.name}`\n**أُغلقت بواسطة:** {inter.user.mention}\n**صاحب التذكرة الأصلي:** {user.mention}",
                    color=0xED4245
                )
                await log_channel.send(embed=log_embed)
                
            await ch.delete()
            
        close_btn.callback = close_callback
        view.add_item(close_btn)

        await ch.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ تم إنشاء تذكرتك بنجاح: {ch.mention}", ephemeral=True)

class TicketSelect(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="الدعم الفني", emoji="🛠️", description="استفسارات ومشاكل تقنية"),
            discord.SelectOption(label="التقديم للإدارة", emoji="📋", description="طلب انضمام للطاقم"),
            discord.SelectOption(label="البلاغات والشكاوى", emoji="⚠️", description="الإبلاغ عن مخالفة"),
            discord.SelectOption(label="المتجر والاشتراكات", emoji="💎", description="الرتب المخصصة والخدمات"),
        ]
        super().__init__(placeholder="⚡ اختر قسم التذكرة...", options=opts)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketModal(self.values[0]))

# --- 4. الأحداث الشاملة (Welcome, Auto-Role, Message Logs) ---

@bot.event
async def on_ready():
    print("==========================================")
    print(f" AURA Systems Active | Logged in as {bot.user.name}")
    print("==========================================")

# الترحيب بالأعضاء الجدد وإعطائهم الرتبة التلقائية
@bot.event
async def on_member_join(member: discord.Member):
    role = discord.utils.get(member.guild.roles, name="Member")
    if role:
        try:
            await member.add_roles(role)
        except Exception as e:
            print(f"Failed to give role: {e}")

    welcome_ch = discord.utils.get(member.guild.text_channels, name="welcome")
    if welcome_ch:
        welcome_desc = f"""مرحباً بك {member.mention}، نورت السيرفر!

نتمنى لك وقتاً ممتعاً معنا. لا تنسَ الاطلاع على القوانين في `#rules`."""
        embed = discord.Embed(
            title=f"👋 أهلاً بك في {member.guild.name}!",
            description=welcome_desc,
            color=0x57F287
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"العضو رقم {member.guild.member_count}")
        await welcome_ch.send(embed=embed)

# سجل حذف الرسائل الشامل (Raw Message Delete Log)
@bot.event
async def on_raw_message_delete(payload: discord.RawMessageDeleteEvent):
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    log_ch = discord.utils.get(guild.text_channels, name="log-messages")
    if not log_ch:
        return

    if payload.cached_message:
        msg = payload.cached_message
        if msg.author and msg.author.bot:
            return
        author = msg.author.mention if msg.author else "مستخدم غير معروف"
        content = msg.content if msg.content else "محتوى غير نصي (صورة أو ملف)"
        channel_mention = msg.channel.mention
    else:
        author = "مستخدم (خارج الذاكرة)"
        content = "تم حذف الرسالة (غير مخزنة في ذاكرة البوت اللحظية)"
        channel = guild.get_channel(payload.channel_id)
        channel_mention = channel.mention if channel else "قناة غير معروفة"

    log_desc = f"""**المرسل:** {author}
**القناة:** {channel_mention}

**المحتوى:**
```{content}
