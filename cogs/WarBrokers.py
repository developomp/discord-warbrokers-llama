import wbscraper.player

import discord
from discord.ext import commands


# todo: add change/remove uid feature
class WarBrokers(commands.Cog):
	def __init__(self, bot):
		self.help_msg = "<#475048014604402708> and <#693401827710074931> automatically updates when the contents of the database is changed."
		self.bot = bot

	async def update_player(self, user_id):
		player = self.bot.llama_firebase.read("players", user_id)

		stat_page = wbscraper.URL.join(wbscraper.URL.stat_root, "players/i", player["uid"])
		player_wb = wbscraper.player.get_player(stat_page)

		user = self.bot.LP_SERVER.get_member(user_id)
		role = "Error"
		if self.bot.PYJAMAS in user.roles:
			role = "Pyjama"
		if self.bot.THE_LLAMA in user.roles:
			role = "The Llama"

		player_description = f"Discord: {user.mention}\n"
		player_description += f"Role: {role}\n"

		try:
			player_description += "Preferred Weapon: %s\n" % player["weapon"]
		except KeyError:
			player_description += "Preferred Weapon: %s\n" % "No Data"

		player_description += "K/D: %.4s\n" % player_wb.kdr

		try:
			player_description += "Time Zone: %s\n" % player["time"]
		except KeyError:
			player_description += "Time Zone: %s\n" % "No Data"

		player_description += f"Stats page: {stat_page}\n"

		embed = discord.Embed(
			title=player_wb.nick,
			description=player_description
		)

		# update if stat message is in the database, add to the database otherwise.
		lp_info_channel = self.bot.get_channel(int(self.bot.VARS["channels"]["LLAMAS_AND_PYJAMAS_INFO"]))
		try:
			stat_msg = await lp_info_channel.fetch_message(player["message_id"])
			await stat_msg.edit(embed=embed)
		except (KeyError, discord.NotFound):
			info_message = await lp_info_channel.send(embed=embed)
			self.bot.llama_firebase.write("players", user_id, "message_id", info_message.id)

	async def update_active(self):
		players = self.bot.llama_firebase.read_collection("players")

		description = ""
		for game_server in self.bot.WB_GAME_SERVERS:
			description += f"{game_server}:\n"
			region_is_empty = True
			for player in players:
				try:
					if game_server in players[player]["server"]:
						description += f"<@{player}>\n"
						region_is_empty = False
				except KeyError:
					pass
			if region_is_empty:
				description += "-- Empty --\n"
			description += "\n"

		emoji = discord.utils.get(self.bot.LP_SERVER.emojis, name="blobsalute")
		embed = discord.Embed(
			title=f"{emoji} LLAMA’S PYJAMAS ACTIVE ROSTER {emoji}",
			description=description
		)

		active_roster_channel = self.bot.get_channel(int(self.bot.VARS["channels"]["ACTIVE"]))
		try:
			active_msg = await active_roster_channel.fetch_message(int(self.bot.VARS["messages"]["ACTIVE"]))
			await active_msg.edit(embed=embed)
		except (KeyError, discord.NotFound):
			active_msg = await active_roster_channel.send(embed=embed)
			self.bot.llama_firebase.write("vars", "messages", "ACTIVE", active_msg.id)

	@commands.command(
		help="Sets/updates data in the database.",
		usage="""`{prefix}set <uid | weapon | time | server>`
`{prefix}set <uid>` (ex: `{prefix}set 5d2ead35d142affb05757778`)
**Must run this before running other stat commands**
Correlates WB uid with your discord ID. Must be a valid WB uid.

`{prefix}set weapon <weapon>` (ex: `{prefix}set weapon Sniper & AR`)
Sets your preferred weapon. No input specifications.

`{prefix}set time <time>` (ex: `{prefix}set time UTC+8`)
Sets your time zone. No input specifications.

`{prefix}set server <server1> <server2> ...` (ex: `{prefix}set server ASIA USA`)
Sets the servers you usually play on. Use `{prefix}set server help` to get more info.
"""
	)
	async def set(self, ctx, a1, *args):
		if not any(role in self.bot.LLAMA_PERMS for role in ctx.message.author.roles):
			await ctx.send(embed=discord.Embed(description="LMAO You're not even in LP! Access denied!"))
			return

		# if the message is sent in the right channel
		if ctx.message.channel.id not in self.bot.BOT_WORK:
			await ctx.send(embed=discord.Embed(description=f"Bruh what do you think <#{self.bot.VARS['channels']['LLAMA_BOT']}> is for?"))
			return

		user_exists_in_firestore = self.bot.llama_firebase.exists("players", ctx.message.author.id)

		# -set <uid>
		if int(len(a1)) == 24:
			if user_exists_in_firestore:
				await ctx.send(embed=discord.Embed(description="You're already in the database. ask <@501277805540147220> to change it."))
				return

			original_content = "checking uid validity..."
			msg = await ctx.send(embed=discord.Embed(description=original_content))
			try:
				wbscraper.player.get_player(a1)
			except Exception:
				await msg.edit(embed=discord.Embed(description=f"{original_content}\nuid not valid. Aborting."))
				return

			original_content = f"{original_content}\nuid is valid. Adding user to database..."
			await msg.edit(embed=discord.Embed(description=original_content))
			self.bot.llama_firebase.create("players", ctx.message.author.id, "uid", a1)
			await msg.edit(embed=discord.Embed(description=f"{original_content}\nnew player registered!"))
			return
		else:
			a1 = a1.lower()
			if not args:
				raise discord.ext.commands.errors.MissingRequiredArgument

		if user_exists_in_firestore:
			if a1 in ["weapon", "time"]:
				try:
					self.bot.llama_firebase.write("players", ctx.message.author.id, a1, " ".join(args))
					await self.bot.update_player(ctx.message.author.id)
				except Exception:
					await ctx.send("<@501277805540147220> bruh fix this", embed=discord.Embed(description="operation failed :("))
					return
			elif a1 == "server":
				if all(i in self.bot.WB_GAME_SERVERS for i in args):
					try:
						self.bot.llama_firebase.write("players", ctx.message.author.id, "server", ",".join(list(dict.fromkeys(args))))  # remove duplicate
						await self.bot.update_active()
					except Exception:
						await ctx.send("<@501277805540147220> bruh fix this", embed=discord.Embed(description="operation failed :("))
						return
				else:
					await ctx.send(embed=discord.Embed(description=f"""
1 - List of available servers: {', '.join("`{0}`".format(w) for w in self.bot.WB_GAME_SERVERS)} (case sensitive)
2 - servers should be separated with spaces (not commas)
3 - you can choose multiple servers

ex: `-set server ASIA USA`"""))
					return

			await ctx.send(
				embed=discord.Embed(
					description=f"updated <#{self.bot.VARS['channels']['ACTIVE']}> and/or <#{self.bot.VARS['channels']['LLAMAS_AND_PYJAMAS_INFO']}>!"
				)
			)
		else:
			await ctx.send(embed=discord.Embed(description=f"You'll have to register first. Try using `{self.bot.command_prefix}help set`"))

	@commands.command(
		help="Removes a data from the database.",
		usage="""`{prefix}rm <arg1> <arg2> ...` (choose from: `weapon`, `time`, `server`)
ex:
`{prefix}rm time server`
"""
	)
	async def rm(self, ctx, a1):
		a1 = str(a1).lower()
		if not any(i in self.bot.LLAMA_PERMS for i in ctx.message.author.roles):
			await ctx.send(embed=discord.Embed(description=f"Ew! non LP peasant! *spits at {ctx.message.author.mention}*"))
			return

		if ctx.message.channel.id not in self.bot.BOT_WORK:
			await ctx.send(embed=discord.Embed(description=f"You're not in the right channel. Do it in <#{self.bot.VARS['channels']['LLAMA_BOT']}>"))
			return

		if not self.bot.llama_firebase.exists("players", ctx.message.author.id):
			await ctx.send(embed=discord.Embed(description="You're not even in my database. At least register."))
			await ctx.send(embed=discord.Embed(description=self.bot.HELP_STAT))
			return

		if a1 in ["weapon", "time", "server"]:
			try:
				self.bot.llama_firebase.read("players", ctx.message.author.id)[a1]
			except KeyError:
				await ctx.send(embed=discord.Embed(description=f"field {a1} is not set or already deleted"))
				return

			self.bot.llama_firebase.delete("players", ctx.message.author.id, a1)
			await ctx.send(embed=discord.Embed(description=f"field `{a1}` removed from `{ctx.message.author.name}`"))
		else:
			await ctx.send(embed=discord.Embed(description=f"field {a1} does not exist"))
			return


def setup(bot):
	bot.add_cog(WarBrokers(bot))
