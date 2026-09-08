import discord
from discord.ext import commands
from datetime import datetime, timezone
import database

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def calculate_trust_score(self, joined_at_str, messages, infractions):
        score = 50
        if joined_at_str:
            joined_at = datetime.fromisoformat(joined_at_str)
            days = (datetime.now(timezone.utc) - joined_at).days
            score += min(25, days // 10)
        score += min(25, messages // 100)
        score -= (infractions * 20)
        return max(0, min(100, score))

    def build_progress_bar(self, percentage):
        filled = int(percentage // 10)
        empty = 10 - filled
        return "🟦" * filled + "⬛" * empty

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        joined_str = message.author.joined_at.isoformat() if message.author.joined_at else datetime.now(timezone.utc).isoformat()
        await database.get_or_create_user(message.author.id, joined_str)
        await database.add_message(message.author.id)

    @commands.slash_command(name="profile", description="عرض بطاقة البروفايل ونسبة الثقة المتقدمة")
    async def profile(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        joined_str = member.joined_at.isoformat() if member.joined_at else datetime.now(timezone.utc).isoformat()
        await database.get_or_create_user(member.id, joined_str)
        data = await database.get_user_data(member.id)
        
        days = (datetime.now(timezone.utc) - member.joined_at).days if member.joined_at else 0
        trust_score = self.calculate_trust_score(data["joined_at"], data["message_count"], data["infractions"])
        progress_bar = self.build_progress_bar(trust_score)

        embed = discord.Embed(
            title=f"💳 ملف العضو • {member.display_name}",
            color=0x2b2d31,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👤 العضو", value=member.mention, inline=True)
        embed.add_field(name="📅 تاريخ الانضمام", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
        embed.add_field(name="💬 مجموع الرسائل", value=f"`{data['message_count']:,}`", inline=True)
        
        embed.add_field(
            name=f"🛡️ مؤشر الثقة والسمعة ({trust_score}%)",
            value=f"{progress_bar}\n*يعتمد المؤشر على الأقدمية، النشاط، ونظافة السجل من المخالفات.*",
            inline=False
        )

        embed.add_field(name="🎫 التذاكر المفتوحة", value=f"`{data['tickets_opened']}`", inline=True)
        embed.add_field(name="⚠️ المخالفات والتحذيرات", value=f"`{data['infractions']}`", inline=True)
        embed.add_field(name="🏆 الإنجازات", value=f"`{data['achievements_count']}`", inline=True)

        embed.set_footer(text="NEXUS OS • Smart Server Management")
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(ProfileCog(bot))