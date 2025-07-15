import os

# ✅ Step 3: Create Your Bot on Discord
# Go to https://discord.com/developers/applications ➜ Create a new application
# Go to the Bot tab ➜ "Add Bot"
# Under Privileged Gateway Intents ➜ enable: Message Content Intent
# Copy the bot token and paste it in your script ➜ bot.run(...)
# Go to OAuth2 → URL Generaton ➜ Scopes: bot /  Bot Permissions: Read Messages, Manage Messages, Read Message History
# Copy and visit the generated URL to invite the bot to your server


THIS_BOT_HAS_AN_OFFICIAL_TOKEN     = os.environ.get("discord_bot_token_ClaireCJS_bot")          # registered token for the bot
TOKEN_WYVERN                       = os.environ.get("discord_bot_token_CarolynCASL_bot")        # registered token for the bot
THIS_CHANNEL_REQUIRES_SPOILER_TAGS = 1378792331154559086                                        # channel to enforce
WAIT_SECONDS_AFTER_DELETION_MSG    = 30                                                         # time for enforcement messages to remain on screen

import discord
from   discord.ext import commands

intents                 = discord.Intents.default()
intents.message_content = True
intents.messages        = True
bot                     = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready(): print(f"Logged in as {bot.user} (ID: {bot.user.id})")

#meets_text_requirements = True                                                                                                                                                                            # If we wanted to enforce text-level spoilering, we would do this: meets_text_requirements = "||" in message.contene ... But because we don’t, juset set the text as good/True:

#OLD @bot.event
#OLD async def on_message(message):
#OLD     if message.author.bot:                                          return
#OLD     if message.channel.id != THIS_CHANNEL_REQUIRES_SPOILER_TAGS:    return
#OLD     attachments_ok = all(a.is_spoiler() for a in message.attachments)                                                                                                                                         # Check if all attachments are spoilered
#OLD     if not attachments_ok:                                                                                                                                                                                    # if not meets_text_requirements and message.attachments and not attachments_ok:    #if not meets_text_requirements and not message.attachments: await message.delete(); await message.channel.send(f"{message.author.mention}, please use spoiler tags like `||this||` in this channel.",delete_after=5)
#OLD         await message.delete()
#OLD         await message.channel.send(f"{message.author.mention}, please mark image " +
#OLD             + "uploads as spoilers using the eye icon or rename the file with `SPOILER_`."
#OLD             ,delete_after=WAIT_SECONDS_AFTER_DELETION_MSG)

@bot.event
async def on_message(message):
    if message.author.bot:                                       return
    if message.channel.id != THIS_CHANNEL_REQUIRES_SPOILER_TAGS: return

    attachments_ok = all(a.is_spoiler() for a in message.attachments)

    if not attachments_ok:
        try:
            await message.delete()
        except Exception as e:
            print(f"⚠️ Failed to delete message: {e}")

        try:
            await message.channel.send(
                f"{message.author.mention}, please mark image uploads as spoilers using the eye icon (on mobile, touch the picture after you’ve attached it to your message, and there is an eyeball you can click), or rename the file with `SPOILER_` at the beginning of the filename",
                delete_after=WAIT_SECONDS_AFTER_DELETION_MSG
            )
        except Exception as e:
            print(f"⚠️ Failed to send explanation message: {e}")


if os.environ.get("MACHINENAME").upper() == "WYVERN":
    print("it’s wyvern!")
    bot.run(TOKEN_WYVERN)
else:
    bot.run(THIS_BOT_HAS_AN_OFFICIAL_TOKEN)


