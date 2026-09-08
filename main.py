import os
import threading
from flask import Flask
import discord
from discord.ext import commands

# 1. خادم Web لضمان استمرار التشغيل 24/7
app = Flask(__name__)

@app.route('/')
def home():
    return "NEXUS-OS: ONLINE"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# 2. إعداد البوت
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- 3. نظام التذاكر المتقدم ---

class TicketModal(discord.ui.Modal):
    def __init__(self, category: str):
        super().__init__(title=f"تذكرة: {category}")
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
        
        embed = discord.Embed(
            title=f"🌐 NEXUS-OS | تذكرة جديدة",
            description=f"**صاحب التذكرة:** {user.mention}\n\n**التفاصيل:**\n```{self.children[0].value}```",
            color=0x5865F2
        )
        embed.set_footer(text="NEXUS-OS Support Engine")

        view = discord.ui.View(timeout=None)
        close_btn = discord.ui.Button(label="إغلاق التذكرة", style=discord.ButtonStyle.danger, emoji="🔒")
        
        async def close_callback(inter: discord.Interaction):
            await inter.response.send_message("🔒 جاري إغلاق التذكرة...")
            await inter.channel.delete()
            
        close_btn.callback = close_callback
        view.add_item(close_btn)

        await ch.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ تم إنشاء التذكرة بنجاح: {ch.mention}", ephemeral=True)

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

# --- 4. الأوامر الواضحة والمباشرة ---

@bot.event
async def on_ready():
    print(f"==========================================")
    print(f" NEXUS-OS Ready: {bot.user.name}")
    print(f"==========================================")

# /tickets - إرسال بنل التذاكر
@bot.slash_command(name="tickets", description="نشر بنل التذاكر التفاعلي")
@commands.has_permissions(administrator=True)
async def tickets(ctx: discord.ApplicationContext):
    view = discord.ui.View(timeout=None)
    view.add_item(TicketSelect())
    embed = discord.Embed(
        title="🌐 NEXUS-OS | مركز الدعم والخدمات",
        description="مرحباً بك. اختر القسم المناسب لمشكلتك من القائمة المنسدلة أسفله لفتح تذكرة مباشرة.",
        color=0x2b2d31
    )
    embed.set_footer(text="NEXUS-OS • Automated Support")
    await ctx.channel.send(embed=embed, view=view)
    await ctx.respond("تم نشر لوحة التذاكر بنجاح.", ephemeral=True)

# /clear - مسح الرسائل
@bot.slash_command(name="clear", description="مسح عدد محدد من الرسائل")
@commands.has_permissions(manage_messages=True)
async def clear(ctx: discord.ApplicationContext, amount: int = 10):
    deleted = await ctx.channel.purge(limit=amount)
    await ctx.respond(f"تم مسح {len(deleted)} رسالة بنجاح.", ephemeral=True)

# /stats - إحصائيات السيرفر
@bot.slash_command(name="stats", description="عرض إحصائيات السيرفر الحالية")
async def stats(ctx: discord.ApplicationContext):
    g = ctx.guild
    embed = discord.Embed(title=f"📊 إحصائيات {g.name}", color=0x2b2d31)
    embed.add_field(name="👥 الأعضاء", value=f"`{g.member_count}`", inline=True)
    embed.add_field(name="💬 القنوات", value=f"`{len(g.channels)}`", inline=True)
    embed.add_field(name="🚀 التعزيزات", value=f"`{g.premium_subscription_count}`", inline=True)
    await ctx.respond(embed=embed, ephemeral=True)

# /ping - فحص الاستجابة
@bot.slash_command(name="ping", description="فحص سرعة استجابة البوت")
async def ping(ctx: discord.ApplicationContext):
    await ctx.respond(f"🏓 Pong! السرعة: {round(bot.latency * 1000)}ms", ephemeral=True)

if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("خطأ: لم يتم العثور على DISCORD_TOKEN في Environment Variables!")
