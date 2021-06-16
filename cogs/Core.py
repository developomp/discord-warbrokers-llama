import sys
from time import time
from datetime import timedelta, datetime

import discord
from discord.ext import commands


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # remove any potential existing help command to prevent collision
        self.bot.remove_command("help")

    @commands.command(
        help="Shows very basic information about the bot.",
    )
    async def about(self, ctx):
        uptime = str(timedelta(seconds=int(round(time() - self.bot.start_time))))
        bot_created_time = datetime.utcfromtimestamp(
            ((int(self.bot.user.id) >> 22) + 1420070400000) / 1000
        )
        bot_created_delta = datetime.now() - bot_created_time

        await ctx.send(
            embed=discord.Embed(title="About llama bot")
            .set_thumbnail(url=self.bot.user.avatar_url)
            .add_field(
                name="Python version",
                value=sys.version.split()[0],
            )
            .add_field(
                name="Discord.py version",
                value=discord.__version__,
            )
            .add_field(name="Bot ID", value=f"{self.bot.user.id}")
            .add_field(
                name="Created in (UTC)",
                value=f"{bot_created_time.strftime('%Y-%m-%d %H:%M:%S')} ({bot_created_delta.days} days ago)",
            )
            .add_field(name="Uptime", value=uptime, inline=False)
            .add_field(
                name="Source Code",
                value="https://github.com/developomp/llama-bot",
                inline=False,
            )
        )

    @commands.command(
        aliases=[
            "h",
        ],
        help="Shows list of helpful information about a command or a cog.",
        usage="""> {prefix}{command} <cog | command | None>
ex:
List cogs:
> {prefix}{command}

List commands in the `core` cog:
> {prefix}{command} core

Shows info about `ping` command:
> {prefix}{command} ping""",
    )
    async def help(self, ctx, cog_str=None):
        cogs = list(self.bot.cogs.keys())

        if not cog_str:
            help_embed = discord.Embed(
                title="Help",
                description=f"Use `{self.bot.command_prefix}help <cog>` command to get more information on a cog. (not case sensitive)",
            )

            # Show command to get help for a cog
            for cog in cogs:
                help_embed.add_field(
                    name=cog, value=f"`{self.bot.command_prefix}help {cog.lower()}`"
                )

            # fields that will be shown in main help embed
            for cog_name in self.bot.cogs:
                try:
                    for field in self.bot.get_cog(cog_name).main_help_fields:
                        help_embed.add_field(
                            name=field[0], value=field[1], inline=False
                        )
                except AttributeError:
                    # cog doesn't have main_help_fields
                    pass
        else:
            lower_cogs = [c.lower() for c in cogs]

            if cog_str.lower() in lower_cogs:
                cog = self.bot.get_cog(cogs[lower_cogs.index(cog_str.lower())])

                cog_help = ""
                try:
                    cog_help = cog.help_msg + ("\n\n" if cog.help_msg else "")
                except AttributeError:
                    pass

                help_embed = discord.Embed(
                    title=f'"{cog_str.lower()}" commands',
                    description=f"Use `{self.bot.command_prefix}help <command>` to get more information about a command. (case sensitive)\n\n"
                    + cog_help
                    + f"**Commands:**\n `{'`, `'.join([_.name for _ in cog.get_commands()])}`",
                )
            else:
                comm: discord.ext.commands.Command = discord.utils.get(
                    self.bot.commands, name=cog_str
                )
                if comm:
                    # default usage
                    if not comm.usage:
                        comm.usage = "> {prefix}{command}"
                    await ctx.send(
                        embed=discord.Embed(
                            title=f"{self.bot.command_prefix}{comm.name}",
                            description=(
                                f"**Aliases:** `{'`, `'.join(comm.aliases)}`"
                                if comm.aliases
                                else ""
                            )
                            + "\n\n**Description:**\n"
                            + (comm.help if comm.help else "Under construction...")
                            + "\n\n**Usage:**\n"
                            + comm.usage.format(
                                prefix=self.bot.command_prefix, command=comm.name
                            )
                            if comm.usage
                            else "Under construction...",
                        )
                    )
                    return

                await ctx.send(
                    embed=discord.Embed(
                        description=f"Cannot find cog/command **{cog_str}**.\nUse `{self.bot.command_prefix}help` command to list all cogs."
                    )
                )
                return

        await ctx.send(embed=help_embed)


def setup(bot):
    bot.add_cog(Core(bot))
