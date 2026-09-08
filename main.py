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

# 2. إعداد البوت مع كامل الصلاحيات
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
        desc = f"**صاحب التذكرة:** {user.mention}\n\n**التفاصيل:**\n```{details_text}```"
        
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
            
            log_ch = get_log_channel(guild, "log-ticket")
            if log_ch:
                log_embed = discord.Embed(
                    title="📝 تم إغلاق تذكرة",
                    description=(
                        f"**اسم القناة:** `{ch.name}`\n"
                        f"**أُغلقت بواسطة:** {inter.user.mention}\n"
                        f"**صاحب التذكرة الأصلي:** {user.mention}"
                    ),
                    color=0xED4245
                )
                await log_ch.send(embed=log_embed)
                
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

# --- 4. نظام السجلات الشامل (Logs) والترحيب ---

@bot.event
async def on_ready():
    print("==========================================")
    print(f" AURA Systems Active | Logged in as {bot.user.name}")
    print("==========================================")

# سجل الترحب والرتبة التلقائية
@bot.event
async def on_member_join(member: discord.Member):
    role = discord.utils.get(member.guild.roles, name="Member")
    if role:
        try:
            await member.add_roles(role)
        except Exception:
            pass

    welcome_ch = get_log_channel(member.guild, "welcome")
    if welcome_ch:
        embed = discord.Embed(
            title=f"👋 أهلاً بك في {member.guild.name}!",
            description=f"مرحباً بك {member.mention}، نورت السيرفر!",
            color=0x57F287
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"العضو رقم {member.guild.member_count}")
        await welcome_ch.send(embed=embed)

    log_ch = get_log_channel(member.guild, "log-join")
    if log_ch:
        embed = discord.Embed(title="📥 دخول عضو جديد", description=f"{member.mention} ({member.name})", color=0x57F287)
        await log_ch.send(embed=embed)

# سجل المغادرة
@bot.event
async def on_member_remove(member: discord.Member):
    log_ch = get_log_channel(member.guild, "log-leave")
    if log_ch:
        embed = discord.Embed(title="📤 مغادرة عضو", description=f"{member.mention} ({member.name})", color=0xED4245)
        await log_ch.send(embed=embed)

# سجل حذف الرسائل
@bot.event
async def on_raw_message_delete(payload: discord.RawMessageDeleteEvent):
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    log_ch = get_log_channel(guild, "log-message")
    if not log_ch:
        return

    if payload.cached_message:
        msg = payload.cached_message
        if msg.author and msg.author.bot:
            return
        author = msg.author.mention if msg.author else "غير معروف"
        content = msg.content if msg.content else "محتوى غير نصي"
        ch_mention = msg.channel.mention
    else:
        author = "غير معروف (رسالة قديمة)"
        content = "تم حذف الرسالة (غير مخزنة)"
        ch = guild.get_channel(payload.channel_id)
        ch_mention = ch.mention if ch else "قناة غير معروفة"

    desc = f"**المرسل:** {author}\n**القناة:** {ch_mention}\n\n**المحتوى:**\n```{content}```"
    embed = discord.Embed(title="🗑️ تم حذف رسالة", description=desc, color=0xFEE75C)
    await log_ch.send(embed=embed)

# سجل تعديل الرسائل
@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.author.bot or before.content == after.content:
        return
    log_ch = get_log_channel(before.guild, "log-message")
    if log_ch:
        desc = (
            f"**المرسل:** {before.author.mention}\n"
            f"**القناة:** {before.channel.mention}\n\n"
            f"**قبل:**\n```{before.content}```\n"
            f"**بعد:**\n```{after.content}```"
        )
        embed = discord.Embed(title="✏️ تم تعديل رسالة", description=desc, color=0x5865F2)
        await log_ch.send(embed=embed)

# سجل إنشاء وحذف الرومات
@bot.event
async def on_guild_channel_create(channel: discord.abc.GuildChannel):
    log_ch = get_log_channel(channel.guild, "log-rom")
    if log_ch:
        embed = discord.Embed(title="📁 تم إنشاء قناة", description=f"**الاسم:** {channel.name}", color=0x57F287)
        await log_ch.send(embed=embed)

@bot.event
async def on_guild_channel_delete(channel: discord.abc.GuildChannel):
    log_ch = get_log_channel(channel.guild, "log-rom")
    if log_ch:
        embed = discord.Embed(title="🗑️ تم حذف قناة", description=f"**الاسم:** {channel.name}", color=0xED4245)
        await log_ch.send(embed=embed)

# --- 5. أوامر Slash الإدارية والشاملة ---

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

@bot.slash_command(name="kick", description="طرد عضو من السيرفر")
@commands.has_permissions(kick_members=True)
async def kick(ctx: discord.ApplicationContext, member: discord.Member, reason: str = "لم يتم تحديد سبب"):
    await member.kick(reason=reason)
    await ctx.respond(f"✅ تم طرد {member.mention} | السبب: {reason}", ephemeral=True)

@bot.slash_command(name="ban", description="حظر عضو من السيرفر")
@commands.has_permissions(ban_members=True)
async def ban(ctx: discord.ApplicationContext, member: discord.Member, reason: str = "لم يتم تحديد سبب"):
    await member.ban(reason=reason)
    await ctx.respond(f"⛔ تم حظر {member.mention} | السبب: {reason}", ephemeral=True)

@bot.slash_command(name="lock", description="قفل القناة الحالية")
@commands.has_permissions(manage_channels=True)
async def lock(ctx: discord.ApplicationContext):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.respond("🔒 تم قفل القناة بنجاح.")

@bot.slash_command(name="unlock", description="فتح القناة الحالية")
@commands.has_permissions(manage_channels=True)
async def unlock(ctx: discord.ApplicationContext):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.respond("🔓 تم فتح القناة بنجاح.")

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
