from discord.ext import commands
from minecraftTellrawGenerator import MinecraftTellRawGenerator as tellraw

import config

class BridgeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        if message.author.bot:
            return
                
        if message.channel.id != config.bot["channel_id"]:
            self.bot.echo(f"Received message in incorrect channel.")
            return

        self.bot.echo(f"Received message: [{message.author.display_name}]: {message.content}")
        a = tellraw(
            text = "["
        )
        b = tellraw(
            text="Discord",
            color="blue",
            hover=tellraw(text="This message was sent from Discord!", color="light_purple"),
            bold=True
        )
        c = tellraw(
            text = "] "
        )
        d = None
        if config.webhook["insertion_available"]:
            d = tellraw(
                text=message.author.display_name,
                insertion="<@" + str(message.author.id) + "> ",
                hover=tellraw(text="Click to reply!", color="yellow")
            )
            
        else:
            d = tellraw(
                text=message.author.display_name,
                insertion="<@" + str(message.author.id) + "> ",
                hover=tellraw(text=message.author.mention, color="yellow")
            )
        e = tellraw(
            text=": " + message.content
        )

        combined = tellraw.multiple_tellraw(a, b, c, d, e)
        self.bot.console_pane.send_keys("tellraw @a " + combined)
        self.bot.echo(f"Tellraw sent to server: {combined}")
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author == self.bot.user:
            return
        
        if before.author.bot:
            return
        
        if before.channel.id != config.bot["channel_id"]:
            self.bot.echo(f"Received edit in incorrect channel.")
            return
        
        self.bot.echo(f"Edit detected.")
        self.bot.echo(f"Before: {before.content}")
        self.bot.echo(f"After : {after.content}")

        a = tellraw(
            text="["
        )
        b = tellraw(
            text="Discord",
            color="blue",
            hover=tellraw(text="This message was sent from Discord!", color="light_purple"),
            bold=True
        )
        c = tellraw(
            text="] "
        )
        d = tellraw(
            text="[EDIT - OLD] ",
            color="dark_gray",
            italic=True
        )
        e = tellraw(
            text=before.author.display_name,
            color="dark_gray",
            italic=True
        )
        
        f = tellraw(
            text=": " + before.content,
            hover=tellraw(text="This is an edit of a previous message."),
            color="dark_gray",
            italic=True
        )

        combined = tellraw.multiple_tellraw(a, b, c, d, e, f)
        self.bot.console_pane.send_keys("tellraw @a " + combined)
        self.bot.echo(f"Tellraw sent to server: {combined}")

        a = tellraw(
            text = "["
        )
        b = tellraw(
            text="Discord",
            color="blue",
            hover=tellraw(text="This message was sent from Discord!", color="light_purple"),
            bold=True
        )
        c = tellraw(
            text="] "
        )
        d = tellraw(
            text="[EDIT - NEW] ",
            color="gold"
        )
        e = tellraw(
            text=after.author.display_name,
            color="gold"
        )
        
        f = tellraw(
            text=": ",
            color="gold"
        )

        g = tellraw(
            text=after.content,
            color="gold"
        )

        combined = tellraw.multiple_tellraw(a, b, c, d, e, f, g)
        self.bot.console_pane.send_keys("tellraw @a " + combined)
        self.bot.echo(f"Tellraw sent to server: {combined}")
    
async def setup(bot):
    await bot.add_cog(BridgeCog(bot))