import config
import dynamo
import discord
import moderation
import miscellaneous as misc
import reddit

TOKEN = config.botToken
roleEmojis = {}
customRoleEmojis = {}
roles_msgs = []
welcomeChat = 334014732572950528
announcementsChat = 349679027126272011
suggestions_chat = 480459932164947969
roles_chat = 365624761398591489
rules_chat = 458786996022673408
bot_log = 245252349587619840
bot_spam = 463874995169394698

modCommands = ["$uncone ", "$cone ", "$coned", "$mute ", "$unmute ", "$clear ", "$custom ", "$servermute ",
               "$serverunmute ", "$help", "$mutechannel", "$unmutechannel", "$suggestions ", "$suggestion ", "$reddit ",
               "$getallcustom", "$phrase ", "$question"]

client = discord.Client()
dynamo.init()


@client.event
async def on_message(message):
    if message.guild is None and message.content.lower().startswith('suggestion: '):
        await misc.new_suggestion(message, client, suggestions_chat)
        return

    if moderation.is_coned(message.author.id):
        await moderation.cone_message(message)

    if not has_power(message):
        await message.channel.send("YOU DON'T GOT THE POWER!")
        return

    if message.content.startswith('$uncone '):
        await moderation.uncone(message)
        return
    if message.content.startswith('$cone '):
        await moderation.cone(message)
        return
    if message.content.startswith('$coned'):
        await moderation.get_coned(message)
        return
    if message.content.startswith('$mute '):
        await moderation.mute(message)
        return
    if message.content.startswith('$unmute '):
        await moderation.unmute(message)
        return
    if message.content.startswith('$servermute '):
        await moderation.server_mute(message)
        return
    if message.content.startswith('$serverunmute '):
        await moderation.server_unmute(message)
        return
    if message.content.startswith('$clear '):
        await moderation.clear(message)
        return
    if message.content.startswith('$invitelink'):
        await misc.invite_link(message, client, welcomeChat)
        return
    if message.content.startswith('$custom '):
        await misc.custom(message)
        return
    if message.content.startswith('$question'):
        await misc.get_question(message)
        return
    if message.content.startswith('$answer '):
        await misc.answer_question(message)
        return
    if message.content.startswith('$score'):
        await misc.get_score(message)
        return
    if message.content.startswith('$fightme '):
        await misc.fight(message)
        return
    if message.content.startswith('$phrase '):
        await misc.new_phrase(message)
        return
    if message.content.startswith('$bansuggestions '):
        await misc.ban_suggestions(message)
        return
    if message.content.startswith('$unbansuggestions '):
        await misc.unban_suggestions(message)
        return
    if message.content.startswith('$'):
        response = dynamo.get_custom_command(message.content[1:])
        if response is not None:
            await message.channel.send(response)
    if message.content == "$getallcustom":
        response = dynamo.get_all_custom()
        for msg in response:
            await message.channel.send(msg)
    if message.content == '$help':
        await misc.help(message)
        return
    if message.content == '$mutechannel':
        await moderation.mute_channel(message)
        return
    if message.content == '$unmutechannel':
        await moderation.unmute_channel(message)
        return
    if message.content.startswith('$suggestions '):
        await misc.get_suggestions(message, client, bot_log)
        return
    if message.content.startswith('$suggestion '):
        await misc.get_suggestion(message, client, bot_log)
        return
    if message.content.startswith('$reddit '):
        await reddit.get_top_post(message)
        return
    if message.content.startswith('$startgiveaway '):
        await misc.start_giveaway(message)
        return
    if message.content.startswith('$endgiveaway '):
        await misc.end_giveaway(client, message)
        return
    # handle phrase
    val = dynamo.get_phrase(message.content)
    if val is not None and message.author.id != client.user.id:
        await message.channel.send(val)
        return


@client.event
async def on_member_join(member):
    msg = "Assalamualaikum " + member.mention + "! Welcome to **Muslim Gamers**! Please take a moment to introduce "
    msg += "yourself! You may only chat here for the time being until you reach lvl 1.\n\n"
    msg += "**You gain lvls by chatting!** After reaching lvl 1 you will gain access to the rest of the chats.\n\n"
    msg += "**Checkout the roles we have over at " + client.get_channel(roles_chat).mention + " and react "
    msg += "to the messages to give yourself the ones you like.**\n\n"
    msg += "Feel free to read " + client.get_channel(rules_chat).mention + " and follow them accordingly.\n"
    msg += "Also check out " + client.get_channel(announcementsChat).mention
    msg += " for the latest things happening in the server.\n"
    await client.get_channel(welcomeChat).send(msg)


@client.event
async def on_member_remove(member):
    msg = member.name + " just left **Muslim Gamers**. Bye bye " + member.mention + "..."
    await client.get_channel(bot_spam).send(msg)


@client.event
async def on_raw_reaction_add(payload):
    # handle giveaways
    if dynamo.get_giveaway(
            payload.message_id) is not None and payload.emoji.name == "🏆" and payload.user_id != 447970747076575232:
        if dynamo.new_giveaway_entry(payload.user_id, payload.message_id):
            await client.get_channel(payload.channel_id).guild.get_member(payload.user_id).send(
                "You have been entered in the giveaway. Good luck!")
    if payload.message_id in roles_msgs:
        guild = client.get_channel(payload.channel_id).guild
        user = guild.get_member(payload.user_id)
        role_name = roleEmojis.get(payload.emoji.name, None)
        if role_name is not None:
            role = discord.utils.get(guild.roles, name=role_name)
            await user.add_roles(role, atomic=True)


@client.event
async def on_raw_reaction_remove(payload):
    # handle giveaways
    if dynamo.get_giveaway(payload.message_id) is not None and payload.emoji.name == "🏆":
        dynamo.delete_giveaway_entry(payload.user_id, payload.message_id)
        await client.get_channel(payload.channel_id).guild.get_member(payload.user_id).send(
            "Your entry has been removed.")
    if payload.message_id in roles_msgs:
        guild = client.get_channel(payload.channel_id).guild
        user = guild.get_member(payload.user_id)
        role_name = roleEmojis.get(payload.emoji.name, None)
        if role_name is not None:
            role = discord.utils.get(guild.roles, name=role_name)
            try:
                await user.remove_roles(role, atomic=True)
            except Exception as e:
                print("couldn't remove role")


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    setup_emojis()
    await set_up_roles_msg()


async def set_up_roles_msg():
    rules_channel = client.get_channel(roles_chat)
    for emoji in roleEmojis:
        for current_msg in roles_msgs:
            msg = await rules_channel.fetch_message(current_msg)
            try:
                if emoji in customRoleEmojis:
                    await msg.add_reaction(client.get_emoji(customRoleEmojis.get(emoji)))
                else:
                    await msg.add_reaction(emoji)
                break
            except Exception as e:
                print('next msg')


def setup_emojis():
    roleEmojis["🃏"] = "Road Blockers"
    roleEmojis["chickenleg"] = "PUBG Crew"
    roleEmojis["🐉"] = "League of Losers"
    roleEmojis["🏹"] = "Hanzo Mains"
    roleEmojis["🔫"] = "Rush B Watch Cat"
    roleEmojis["💀"] = "Dead by Daylight"
    roleEmojis["⚛"] = "Ancient Defenders"
    roleEmojis["⚽"] = "Learning to Dribble"
    roleEmojis["💠"] = "Guardians"
    roleEmojis["🛠"] = "Master Builders"
    roleEmojis["🐛"] = "Stick Fightin"
    roleEmojis["⛳"] = "Mini Golf Rules"
    roleEmojis["🌈"] = "Fuzing Hostage"
    roleEmojis["🎵"] = "music haramis"
    roleEmojis["runescape"] = "Osbuddies"
    roleEmojis["⚔"] = "Dauntless"
    roleEmojis["💸"] = "Cheap Gamers"
    roleEmojis["🗺"] = "Skribblio"
    roleEmojis["🔷"] = "Paladins"
    roleEmojis["🤺"] = "For Honor"
    roleEmojis["🎣"] = "World of Warcraft"
    roleEmojis["🎇"] = "StarCraft"
    roleEmojis["🕋"] = "Lecture"
    roleEmojis["🤖"] = "TennoFrame"
    roleEmojis["🐊"] = "Monster Hunters"
    roleEmojis["🔄"] = "Nintendo Switch"
    roleEmojis["🤠"] = "The Steves"
    roleEmojis["⛓"] = "Sirat-ul-Exile"
    roleEmojis["🔰"] = "Keyboard Warriors"
    roleEmojis["🐸"] = "Fascist Scum"
    roleEmojis["🏳"] = "Farm Simulator"
    roleEmojis["👊🏾"] = "Button Mashers"
    roleEmojis["🎮"] = "Apex Legends"
    roleEmojis["🇱"] = "League of Losers EU"
    roleEmojis["⚔"] = "Hodor"
    roleEmojis["👷🏾"] = "Rainbow Six Siege"
    roleEmojis["😇"] = "Halo"
    roleEmojis["🌠"] = "Stormtrooper"
    roleEmojis["💳"] = "Tarnoobz"
    roleEmojis["⚠"] = "Going Dark"

    customRoleEmojis["chickenleg"] = 319229845957640192
    customRoleEmojis["runescape"] = 455087244898992129

    roles_msgs.append(398539277035896846)
    roles_msgs.append(458465086693048341)
    roles_msgs.append(460218391781965824)
    roles_msgs.append(633304992719306762)


def has_power(message):
    for command in modCommands:
        if message.content.startswith(
                command) and message.author.top_role.id != 365541261156941829 and message.author.top_role.id != 287369489987928075 and message.author.top_role.id != 192322577207787523 and message.author.top_role.id != 193105896010809344 and message.author.top_role.id != 207996893769236481:
            return False
    return True


client.run(TOKEN)
