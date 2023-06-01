import re
import discord
import emoji
from discord.ext import commands
from minecraftTellrawGenerator import MinecraftTellRawGenerator as tellraw

import config

emoji_match = "<a?(:.*?:)\d*?>"
def parse_emoji(content):
    return emoji.demojize(re.sub(emoji_match, "\1", content))

class BridgeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            # Parse message embed for server restart notifications.
            # This is obviously the best way to do this.

            if len(message.embeds) > 0:
                embed_0 = message.embeds[0]
                match = re.match("^:warning: (Automatic server restart in .+\.)$", embed_0.description)
                if match:
                    combined = tellraw.multiple_tellraw(
                        tellraw(text="["),
                        tellraw(text="Server",color="red"),
                        tellraw(text="] "),
                        tellraw(text=match.group(1),color="yellow")
                    )
                    self.bot.console_pane.send_keys("tellraw @a " + combined)
            return
        
        if message.author.bot:
            return
                
        if message.channel.id != config.bot["channel_id"]:
            return

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
            text=": " + parse_emoji(message.content)
        )

        combined = None

        if len(message.attachments) > 0:
            attachment_list = []

            i = 0
            for attachment in message.attachments:
                i += 1
                attachment_list.append(tellraw(
                    text=" ["
                ))
                attachment_list.append(tellraw(
                    text=f"attachment {i}",
                    url=attachment.url,
                    color="aqua",
                    hover=attachment.url
                ))
                attachment_list.append(tellraw(
                    text="]"
                ))

            combined = tellraw.multiple_tellraw(a, b, c, d, e, *attachment_list)
        else:
            combined = tellraw.multiple_tellraw(a, b, c, d, e)
        
        self.bot.console_pane.send_keys("tellraw @a " + combined)
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author == self.bot.user:
            return
        
        if before.author.bot:
            return
        
        if before.channel.id != config.bot["channel_id"]:
            return
    
        if before.content == after.content: # Catch embed "edits"
            return

        combined = tellraw.multiple_tellraw(
            # Line 1: old message
            tellraw(
                text="["
            ),
            tellraw(
                text="Discord",
                color="blue",
                hover=tellraw(text="This message was sent from Discord!", color="light_purple"),
                bold=True
            ),
            tellraw(
                text="] "
            ),
            tellraw(
                text="[EDIT - OLD] ",
                color="dark_gray",
                italic=True
            ),
            tellraw(
                text=before.author.display_name,
                color="dark_gray",
                italic=True
            ),
            tellraw(
                text=": " + parse_emoji(before.content) + "\n",
                color="dark_gray",
                hover=tellraw(text="This is the old message."),
                italic=True
            ),

            # Line 2: new message
            tellraw(
                text="["
            ),
            tellraw(
                text="Discord",
                color="blue",
                hover=tellraw(text="This message was sent from Discord!", color="light_purple"),
                bold=True
            ),
            tellraw(
                text="] "
            ),
            tellraw(
                text="[EDIT - NEW] ",
                color="gold"
            ),
            tellraw(
                text=after.author.display_name,
                color="gold"
            ),
            tellraw(
                text=": ",
                color="gold"
            ),
            tellraw(
                text=parse_emoji(after.content),
                hover=tellraw(text="This is the new message."),
                color="gold"
            )
        )
        self.bot.console_pane.send_keys("tellraw @a " + combined)
    
async def setup(bot):
    await bot.add_cog(BridgeCog(bot))