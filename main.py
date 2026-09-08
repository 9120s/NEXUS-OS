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
        embed = discord.Embed(
            title=f"🌐 AURA | تذكرة جديدة ({self.category})",
            description=f"**صاحب التذكرة:** {user.mention}\n\n**التفاصيل:**\n```{details_text}```",
            color=0x5865F2
        )
        embed.set_footer(text="AURA Support Engine")

        view = discord.ui.View(timeout=None)
        close_btn = discord.ui.Button(label="إغلاق التذكرة", style=discord.ButtonStyle.danger, emoji="🔒")
        
        async def close_callback(inter: discord.Interaction):
            await inter.response.send_message("🔒 جاري إغلاق التذكرة وحفظ السجل...")
            
            # إرسال سجل التذكرة (Log) إلى قناة log-tickets إن وجدت
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
        embed = discord.Embed(
            title=f"👋 أهلاً بك في {member.guild.name}!",
            description=f"مرحباً بك {member.mention}، نورت السيرفر!\n\nنتمنى لك وقتاً ممتعاً معنا. لا تنسَ الاطلاع على القوانين في `#rules`.",
            color=0x57F287
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"العضو رقم {member.guild.member_count}")
        await welcome_ch.send(embed=embed)

# سجل حذف الرسائل (Message Delete Log)
@bot.event
async def on_message_delete(message: discord.Message):
    if message.author and message.author.bot:
        return
    
    log_ch = discord.utils.get(message.guild.text_channels, name="log-messages")
    if log_ch:
        content = message.content if message.content else "محتوى غير نصي (صورة أو ملف)"
        author = message.author.mention if message.author else "مستخدم غير معروف"
        
        embed = discord.Embed(
            title="🗑️ تم حذف رسالة",
            description=f"**المرسل:** {author}\n**القناة:** {message.channel.mention}\n\n**المحتوى:**\n```{content}```",
            color=0xFEE75C
        )
        await log_ch.send(embed=embed)

# --- 5. أوامر Slash ---

@bot.slash_command(name="tickets", description="نشر بنل التذاكر التفاعلي")
@commands.has_permissions(administrator=True)
async def tickets(ctx: discord.ApplicationContext):
    view = discord.ui.View(timeout=None)
    view.add_item(TicketSelect())
    embed = discord.Embed(
        title="🌐 AURA | مركز الدعم والخدمات",
        description="مرحباً بك. اختر القسم المناسب لمشكلتك من القائمة المنسدلة أسفله لفتح تذكرة مباشرة.",
        color=0x2b2d31
    )
    embed.set_footer(text="AURA • Automated Support Engine")
    await ctx.channel.send(embed=embed, view=view)
    await ctx.respond("تم نشر لوحة التذاكر بنجاح.", ephemeral=True)

@bot.slash_command(name="clear", description="مسح عدد محدد من الرسائل")
@commands.has_permissions(manage_messages=True)
async def clear(ctx: discord.ApplicationContext, amount: int = 10):
    deleted = await ctx.channel.purge(limit=amount)
    await ctx.respond(f"تم مسح {len(deleted)} رسالة بنجاح.", ephemeral=True)

@bot.slash_command(name="stats", description="عرض إحصائيات السيرفر الحالية")
async def stats(ctx: discord.ApplicationContext):
    g = ctx.guild
    embed = discord.Embed(title=f"📊 إحصائيات {g.name}", color=0x2b2d31)
    embed.add_field(name="👥 الأعضاء", value=f"`{g.member_count}`", inline=True)
    embed.add_field(name="💬 القنوات", value=f"`{len(g.channels)}`", inline=True)
    embed.add_field(name="🚀 التعزيزات", value=f"`{g.premium_subscription_count}`", inline=True)
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name="ping", description="فحص سرعة استجابة البوت")
async def ping(ctx: discord.ApplicationContext):
    await ctx.respond(f"🏓 Pong! السرعة: {round(bot.latency * 1000)}ms", ephemeral=True)

if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
