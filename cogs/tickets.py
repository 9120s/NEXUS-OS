import discord
from discord.ext import commands
import datetime

class TicketModal(discord.ui.Modal):
    def __init__(self, category_type: str):
        super().__init__(title=f"استمارة: {category_type}")
        self.category_type = category_type

        self.subject = discord.ui.TextInput(
            label="عنوان المشكلة / الطلب",
            placeholder="اكتب عنواناً مختصراً للطلب...",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.add_item(self.subject)

        self.details = discord.ui.TextInput(
            label="الشرح بالتفصيل",
            placeholder="يرجى كتابة التفاصيل الكاملة هنا ليتم العمل عليها بسرعة...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.details)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        channel_name = f"ticket-{user.name}".lower().replace(" ", "-")
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        
        if existing_channel:
            await interaction.response.send_message(f"⚠️ لديك تذكرة نشطة بالفعل في {existing_channel.mention}", ephemeral=True)
            return

        category_name = "📂 التذاكر والدعم"
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        embed = discord.Embed(
            title=f"🎫 NEXUS OS • تذكرة جديدة ({self.category_type})",
            color=0x2b2d31,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="👤 العضو", value=user.mention, inline=True)
        embed.add_field(name="📌 القسم", value=self.category_type, inline=True)
        embed.add_field(name="📝 العنوان", value=f"```\n{self.subject.value}\n```", inline=False)
        embed.add_field(name="💬 التفاصيل", value=f"```\n{self.details.value}\n```", inline=False)
        embed.set_footer(text="NEXUS OS • اختر إجراءً من الأزرار أدناه")

        await channel.send(content=f"{user.mention} | أهلاً بك، يرجى انتظار رد الإدارة.", embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ تم إنشاء التذكرة بنجاح: {channel.mention}", ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="إغلاق التذكرة", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("🔒 جارٍ إغلاق التذكرة وحذف القناة خلال 5 ثوانٍ...")
        await discord.utils.sleep_until(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=5))
        await interaction.channel.delete()

    @discord.ui.button(label="استلام التذكرة", style=discord.ButtonStyle.success, emoji="👤", custom_id="claim_ticket")
    async def claim_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ هذا الخيار مخصص للإدارة فقط.", ephemeral=True)
            return

        embed = discord.Embed(
            description=f"✅ تم استلام هذه التذكرة بواسطة: {interaction.user.mention}",
            color=discord.Color.green()
        )
        button.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message(embed=embed)

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="الدعم التقني والحلول", value="الدعم التقني", description="حل الأعطال الفنية والتقنية", emoji="🛠️"),
            discord.SelectOption(label="الاستفسارات والاقتراحات", value="استفسار", description="تقديم أسئلة أو اقتراحات لتطوير السيرفر", emoji="💡"),
            discord.SelectOption(label="طلبات الشراكة والإعلانات", value="الشراكات", description="التواصل بشأن الشراكات والمحتوى", emoji="🤝"),
            discord.SelectOption(label="البلاغات ضد المخالفين", value="بلاغ", description="الإبلاغ عن سلوك مخالف من عضو أو إداري", emoji="🚨"),
            discord.SelectOption(label="التقديم على الطاقم الإداري", value="تقديم إدارة", description="الانضمام للفريق الإداري", emoji="👑"),
        ]
        super().__init__(placeholder="🔽 اختر قسم التذكرة المناسب لطلبك...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketModal(category_type=self.values[0]))

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class TicketsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="setup_tickets", description="إرسال لوحة التذاكر الاحترافية")
    @commands.has_permissions(administrator=True)
    async def setup_tickets(self, ctx):
        embed = discord.Embed(
            title="🎫 NEXUS OS • مركز الدعم والخدمات",
            description=(
                "أهلاً بك في نظام التذاكر الموحد.\n\n"
                "**خطوات فتح تذكرة:**\n"
                "1️⃣ اختر القسم المناسب لطلبك من القائمة أدناه.\n"
                "2️⃣ املأ بيانات الاستمارة بالتفاصيل الدقيقة.\n"
                "3️⃣ سيتم فتح غرفة خاصة بك لمتابعة الطلب مع الفريق المختص."
            ),
            color=0x2b2d31
        )
        embed.set_footer(text="NEXUS OS • Your Server. One Brain.")
        await ctx.respond(embed=embed, view=TicketView())

def setup(bot):
    bot.add_cog(TicketsCog(bot))