import discord
from discord.ext import commands, tasks
import datetime

class DashboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dashboard_message = None

    @commands.slash_command(name="setup_dashboard", description="إنشاء لوحة التحكم المباشرة للسيرفر")
    @commands.has_permissions(administrator=True)
    async def setup_dashboard(self, ctx):
        embed = self.generate_dashboard_embed(ctx.guild)
        message = await ctx.send(embed=embed)
        self.dashboard_message = message
        if not self.update_dashboard.is_running():
            self.update_dashboard.start(ctx.guild)
        await ctx.respond("✅ تم إنشاء لوحة التحكم وتفعيل التحديث التلقائي كل 5 دقائق.", ephemeral=True)

    def generate_dashboard_embed(self, guild):
        total_members = guild.member_count
        bot_count = sum(1 for m in guild.members if m.bot)
        human_count = total_members - bot_count

        embed = discord.Embed(
            title=f"📊 NEXUS OS • لوحة تحكم السيرفر الحية",
            description=f"إحصائيات متجددة تلقائياً لـ **{guild.name}**",
            color=0x2b2d31,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="👥 إجمالي الأعضاء", value=f"`{human_count:,}`", inline=True)
        embed.add_field(name="🤖 البوتات", value=f"`{bot_count}`", inline=True)
        embed.add_field(name="📁 القنوات", value=f"`{len(guild.channels)}`", inline=True)
        embed.add_field(name="🚀 عدد التبوستات (Boosts)", value=f"`{guild.premium_subscription_count}` (المستوى {guild.premium_tier})", inline=False)
        embed.set_footer(text="NEXUS OS • تحديث تلقائي مستمر")
        return embed

    @tasks.loop(minutes=5)
    async def update_dashboard(self, guild):
        if self.dashboard_message:
            try:
                embed = self.generate_dashboard_embed(guild)
                await self.dashboard_message.edit(embed=embed)
            except Exception:
                pass

def setup(bot):
    bot.add_cog(DashboardCog(bot))