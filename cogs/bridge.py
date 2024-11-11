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
        if self.bot.block_chat:
            return # Security feature: Do not allow chat until the server is confirmed online, otherwise tellraw messages will be sent to the shell.

        if message.author == self.bot.user:
            # Parse message embed for server restart notifications.
            # This is obviously the best way to do this.
            # TODO: Make this part less good. (sarcasm)

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
                    await self.bot.send_server_command("tellraw @a " + combined)
                    return
            if message.content == "Server restart will be cancelled.":
                combined = tellraw.multiple_tellraw(
                    tellraw(text="["),
                    tellraw(text="Server",color="red"),
                    tellraw(text="] "),
                    tellraw(text="Server restart will be cancelled.",color="orange")
                )
                await self.bot.send_server_command("tellraw @a " + combined)
                return
            return
        
        if message.author.bot:
            return
                
        if message.channel.id != config.bot["channel_id"]:
            return
        
        pre = None
        if message.reference:
            message_author = None
            message_content = None
            if message.reference.cached_message:
                message_author = message.reference.cached_message.author
                message_content = message.reference.cached_message.content
            else:
                message_data = await self.bot.bridge_channel.fetch_message(message.reference.message_id)
                message_author = message_data.author
                message_content = message_data.content

            pre = tellraw.multiple_tellraw(
                tellraw(
                    text="[REPLY] ",
                    color="gray",
                    italic=True
                ),
                tellraw(
                    text=message_author.display_name,
                    color="gray",
                    italic=True
                ),
                tellraw(
                    text=": " + parse_emoji(message_content) + "\n",
                    color="gray",
                    hover=tellraw(text="This is the message being replied to."),
                    italic=True
                )
            )
        else:
            pre = tellraw(text="")

        a = tellraw(
            text= "╚> [" if message.reference else "["
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
                insertion=f"reply:{str(message.id)}:pingoff ",
                hover=tellraw(text="Shift+click to reply to this message!", color="yellow")
            )
            e = tellraw(
                text=": " + parse_emoji(message.content),
                insertion=f"reply:{str(message.id)}:pingoff ",
                hover=tellraw(text="Shift+click to reply to this message!", color="yellow")
            )
            
        else:
            d = tellraw(
                text=message.author.display_name,
                insertion=f"reply:{str(message.id)}:pingoff ",
                hover=tellraw(text=message.author.mention, color="yellow")
            )
            e = tellraw(
                text=": " + parse_emoji(message.content),
                insertion=f"reply:{str(message.id)}:pingoff ",
                hover=tellraw(text=message.author.mention, color="yellow")
            )
        

        combined = None

        if len(message.attachments) > 0:
            attachment_list = []

            i = 0
            for attachment in message.attachments:
                i += 1
                attachment_list.append(tellraw(
                    text="[" if message.content == "" and i == 1 else " ["
                ))
                attachment_list.append(tellraw(
                    text=f"attachment {i}",
                    url=attachment.url,
                    color="aqua",
                    hover=tellraw.multiple_tellraw(
                        tellraw(
                            text="Click to open "
                        ),
                        tellraw(
                            text=attachment.url,
                            color="aqua"
                        ),
                        tellraw(
                            text="."
                        )
                    )
                ))
                attachment_list.append(tellraw(
                    text="]"
                ))

            combined = tellraw.multiple_tellraw(pre, a, b, c, d, e, *attachment_list)
        else:
            combined = tellraw.multiple_tellraw(pre, a, b, c, d, e)
        
        await self.bot.send_server_command("tellraw @a " + combined)
    
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
        await self.bot.send_server_command("tellraw @a " + combined)
    
async def setup(bot):
    await bot.add_cog(BridgeCog(bot))