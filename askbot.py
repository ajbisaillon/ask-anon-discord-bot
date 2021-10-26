import discord
import os
import re
from dotenv import load_dotenv

client = discord.Client() 

anonymous_questions_cat_name = "anonymous-questions"
questions_channel_name = "ask"
anon_questions_channel_name = "anon-questions"

channel_mention_re = r"<#(\d+)>"

@client.event 
async def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------------------")

@client.event
async def on_guild_join(guild):
    anonymous_questions_cat = discord.utils.get(guild.channels, name=anonymous_questions_cat_name)
    if (anonymous_questions_cat == None):
        # create category
        anonymous_questions_cat = await guild.create_category(anonymous_questions_cat_name)
    if (discord.utils.get(guild.text_channels, name=questions_channel_name) == None): 
        # create channel
        await anonymous_questions_cat.create_text_channel(questions_channel_name)
    if (discord.utils.get(guild.text_channels, name=anon_questions_channel_name) == None):
        # set permissions
        owner = await guild.fetch_member(guild.owner_id)
        bot = await guild.fetch_member(client.user.id)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            owner: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True),
            bot: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
        }
        # create channel
        await anonymous_questions_cat.create_text_channel(anon_questions_channel_name, overwrites=overwrites)

@client.event
async def on_message(message):
    # the bot should not reply to itself
    if message.author.id == client.user.id:
        return

    # ONLY want to delete messages sent in the "questions" text channel
    questions_channel = discord.utils.get(message.guild.text_channels, name=questions_channel_name)
    if (message.channel == questions_channel):
        anon_questions_channel = discord.utils.get(message.guild.text_channels, name=anon_questions_channel_name)
        question = message.content
        await message.delete()
        await anon_questions_channel.send(question)

    if message.content.startswith("!help"):
        await message.reply("Use `!summary` for information about what this bot does or `!commands` for how to use it.")

    if message.content.startswith("!summary"):
        await message.reply("**Summary:**\n"
        "On joining a server, the bot will create the `ANONYMOUS-QUESTIONS` channel category.\n"
        "Any user can send messages in the `ask` channel.\n" 
        "The bot will repost the message content in the `anon-questions` channel, which is viewable only by the server owner.\n"
        "The server owner can choose which questions are published.\n")

    if message.content.startswith("!commands"):
        await message.reply("**Usage:**\n"
        "Use command `!move <message_id> <#channel_name>` to move the specified message to a specific channel (hold shift and hover over a message to get the id).\n")

    if message.content.startswith("!move"):
        # check if server owner
        if message.author.id != message.guild.owner_id:
            await message.reply("You are not authorized to use this command.", mention_author=False)
            return

        # parse the message for <message_id> and <#channel_name>
        command = message.content.split()
        if len(command) != 3:
            await message.reply("Usage is: `!move <message_id> <#channel_name>`", mention_author=False)
            return
        p = re.compile(channel_mention_re)
        m = p.match(command[2])
        target_channel_id = int(m.group(1))
        if m == None:
            await message.reply("Enter a valid channel in the format: `<#channel_name>`", mention_author=False)
            return
        try:
            question = await message.channel.fetch_message(command[1].split("-")[1])
        except discord.errors.NotFound:
            await message.reply("Enter a valid message id.", mention_author=False)
            return
        target_channel = discord.utils.get(message.guild.channels, id=target_channel_id)
        await target_channel.send(question.content)
        await question.delete()
        await message.delete()

load_dotenv()
client.run(os.environ["token_id"])
