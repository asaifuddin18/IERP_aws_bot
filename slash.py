'''
Main IERP script
Attributes
----------
client: discord.Client
    client object from discord.py
slash: discord_slash.SlashCommand
    slash object used for discord slash commands
point_d: defaultdict
    Default dictionary with default value 0 mapping discord id (int) to points
used: defaultdict
    Default dictioanry with default value empty set mapping code/message id to a set of users
uses_per_day: dictionary
    Dictionary mapping date (str) to frequency (int)
unique_users_per_day: dictionary
    Dictionary mapping date (str) to number of users (int)
unique_codes_per_day: dictionary
    Dictionary mapping date (str) to number of codes (int)
points_in_circulation: dictionary
    Dictionary mapping date (str) to number of points (int)
'''
from constants import ADMIN_CHANNEL, ANNOUNCEMENT_CHANNEL, INTEGER, PATH_TO_CIRCULATION, PATH_TO_POINTS, PATH_TO_POINT_VALUES, PATH_TO_SECRETS, PATH_TO_SERVERS_AND_ROLES, PATH_TO_SHOP, PATH_TO_UNIQUE_CODES, PATH_TO_UNIQUE_USERS, PATH_TO_USED, PATH_TO_WEEKLY_RESET, ROLE, STRING, WEBSITE_URL, IE_GUILD_ID, SPECIAL_ROLE_ID
import interactions
from interactions import ActionRow, Button
import typing
import time
import string
import random
from datetime import date
from datetime import datetime
import asyncio
import json
from pytz import timezone
import math
import pickle
import os
from os import path
from collections import defaultdict

PATH_TO_ID_TO_NAME = "config/id_to_name.pickle"
PATH_TO_LOG = "config/log.pickle"

with open(PATH_TO_SECRETS) as f:
    secrets = json.load(f)
TOKEN = secrets['token']
bot_client = interactions.Client(TOKEN)
def default_point():
    return 0
point_d = defaultdict(default_point)
if path.exists(PATH_TO_POINTS) and os.path.getsize(PATH_TO_POINTS) > 0:
    with open(PATH_TO_POINTS, "rb") as f:
        point_d = pickle.load(f)
used = defaultdict(set)

id_to_name = {} #id to tag
if path.exists(PATH_TO_ID_TO_NAME) and os.path.getsize(PATH_TO_ID_TO_NAME) > 0:
    with open(PATH_TO_ID_TO_NAME, "rb") as f:
        id_to_name = pickle.load(f)

log = []
if path.exists(PATH_TO_LOG) and os.path.getsize(PATH_TO_LOG) > 0:
    with open(PATH_TO_LOG, "rb") as f:
        log = pickle.load(f)

active_codes = {} #Code: points, start_time, duration
giveaways = {} #Code: points, start_time, duration, entries, num_winners
adminChannelID = ADMIN_CHANNEL
announcement_channel = ANNOUNCEMENT_CHANNEL
guilds_and_admin_roles = {}
top_5 = []
with open(PATH_TO_SERVERS_AND_ROLES) as f:
    servers_and_roles = json.load(f)

#for server in servers_and_roles['servers']:
#    guilds_and_admin_roles[server['id']] = [create_permission(x['id'], SlashCommandPermissionType.ROLE, True) for x in server['roles']]

with open(PATH_TO_SHOP) as f:
    shop_info = json.load(f)
'''
Prints Ready! when Discord client is connected
'''
"""@client.event
async def on_ready():
    print("Ready!")"""


@bot_client.command(
    default_member_permissions= interactions.Permissions.MANAGE_ROLES
)
async def admin(ctx):
    pass

'''
Discord client event called when a message gets a reaction added to it. (This only applies to messages sent after the start of the bot)
This specific function is designed to award 10 points to a reaction in the announcement channel
Parameters
----------
reaction: discord.Reaction
    https://discordpy.readthedocs.io/en/stable/api.html#reaction
user: discord.User
    https://discordpy.readthedocs.io/en/stable/api.html#id7
'''
"""@client.event
async def on_reaction_add(reaction, user):
    global num_redeemed
    msg = reaction.message
    if msg.channel.id == announcement_channel and (msg.mention_everyone or 'Student' in [r.name for r in msg.role_mentions]):
        if user.id not in used[msg.id]: #make sure code has not already been redeemed!
            point_d[user.id] += 5
            used[msg.id].add(user.id)
            num_redeemed += 1"""

@admin.subcommand(
    name="remove_points",
    description="Manually removes points from a user.",
    options=[interactions.Option(
        name = "user_id",
        description = "User ID (not tag) of the user getting points",
        type = interactions.OptionType.STRING,
        required = True
    ),
    interactions.Option(
        name = "points",
        description = "Amount of points to remove.",
        type = interactions.OptionType.INTEGER,
        required = True
    )]
)
async def remove_points(ctx, user_id: str, points: int):
    try:
        temp = int(user_id)
    except(ValueError):
        await ctx.send('Thats not a valid user_id (User ID is a number)', ephemeral=True)
        return
    point_d[user_id] -= points
    point_d[user_id] = max(point_d[user_id], 0)
    try:
        guild = await get_guild()
        member = await guild.get_member(user_id)
        id_to_name[user_id] = member.user.username + "#" + member.user.discriminator
    except:
        del point_d[user_id]
        await ctx.send('That person is not in the discord', ephemeral=True)
        return
    log.append(str(ctx.author.id) + " removed " + str(points) + " from " + id_to_name[user_id])
    await ctx.send("Points removed successfully", ephemeral=True)



@admin.subcommand(
    name="give_points",
    description="Manually give points to a user. Only do this in the case of a single user or some error happened.",
    options=[interactions.Option(
        name = "user_id",
        description = "User ID (not tag) of the user getting points",
        type = interactions.OptionType.STRING,
        required = True
    ),
    interactions.Option(
        name = "points",
        description = "Amount of points to give",
        type = interactions.OptionType.INTEGER,
        required = True
    )]
)
async def give_points(ctx, user_id: str, points: int):
    try:
        temp = int(user_id)
    except(ValueError):
        await ctx.send('Thats not a valid user_id (User ID is a number)', ephemeral=True)
        return
    point_d[user_id] += points
    try:
        guild = await get_guild()
        member = await guild.get_member(user_id)
        id_to_name[user_id] = member.user.username + "#" + member.user.discriminator
    except:
        del point_d[user_id]
        await ctx.send('That person is not in the discord', ephemeral=True)
        return
    log.append(str(ctx.author.id) + " gave " + str(points) + " to " + id_to_name[user_id])
    await ctx.send("Points successfully awarded!", ephemeral=True)


async def get_guild():
    guild = None
    for g in bot_client.guilds:
        if str(g.id) == str(IE_GUILD_ID):
            guild = g
            break
    return guild


'''
Command that displays the number of points a user has
'''
@bot_client.command(
  name="points",
  description="Returns the user's points"
)
async def points(ctx):
    points = point_d[str(ctx.author.id)]
    if points == 0:
        await ctx.send("You have <:OMEGALUL:417825307605860353> points!", ephemeral=True) 
    else:
        await ctx.send(f'You have {points} points!', ephemeral=True)

'''
Command that creates a redeemable code with a custom duration and point reward. This is used in the case of random events that are not PUGS
Parameters
----------
length: int
    The duration of the code in minutes (0 is infinite)
amount: int
    The amount of points the code is worth
name: str [OPTIONAL]
    The name of the code
'''
@admin.subcommand(
    name="generate_code",
    description="This generates a reward code. No name inputted will generate a random name",
    options=[interactions.Option(
        name = "length",
        description= "Length of the code in minutes",
        type = interactions.OptionType.INTEGER,
        required = True
    ),
    interactions.Option(
        name = "amount",
        description = "Amount of points this code is worth",
        type = interactions.OptionType.INTEGER,
        required = True
    ),
    interactions.Option(
        name = "name",
        description = "The custom name for the code",
        type = interactions.OptionType.STRING,
        required = False
    )]
)
async def generate_code(ctx, length: int, amount: int, name: typing.Optional[str] = ""):
    seconds = length*60
    code = name
    if code == "":
        letters = string.ascii_letters
        code = ''.join(random.choice(letters) for i in range(8))
    
    if code not in active_codes.keys():
        active_codes[code] = (amount, time.time(), seconds)
        log.append(str(ctx.author.id) + " generated " + code + " for " + str(amount) + " minutes")
        await ctx.send(f'{code} of value {amount} generated for {length} minutes', ephemeral=True)
    else:
        await ctx.send("Could not generate code. Code with same name has already been generated!", ephemeral=True)

'''
Command to redeem a custom generated code
Parameters
----------
code: str
    A unique code generated previously via customGenerateCode
'''
@bot_client.command(
    name="redeem_code",
    description="Got a IERP code? Redeem it here!",
    options=[interactions.Option(
        name = "code",
        description = "The name of the code",
        type = interactions.OptionType.STRING,
        required = True
    )]
)
async def redeem_code(ctx, code: str):
    auth_id = str(ctx.author.id)
    if code in active_codes.keys() and auth_id not in used[code]: #valid key & user has not already redeemed
        point_d[auth_id] += active_codes[code][0]
        used[code].add(auth_id)
        try:
            id_to_name[auth_id] = ctx.author.user.username + "#" + ctx.author.user.discriminator
        except:
            del point_d[auth_id]
            await ctx.send("Cannot locate you, something went wrong", ephemeral=True)
            return
        
        log.append(id_to_name[auth_id] + " redeemed " + code + " for " + str(active_codes[code][0]) + " points")
        await ctx.send(f'Code redeemed, you now have {point_d[auth_id]} points!', ephemeral=True)
    elif str(auth_id) not in used[code]: #was a valid user
        await ctx.send("Invalid or expired code!", ephemeral=True)
    else:
        await ctx.send("Code already redeemed!", ephemeral=True)


async def update_top_5_role():
    guild = await get_guild()
    special_role = await guild.get_role(SPECIAL_ROLE_ID)
    for id in top_5:
        member = await guild.get_member(id)
        await member.remove_role(special_role)
    top_5.clear()
    sorted_ids = sorted(point_d, key=point_d.get, reverse=True)
    for i in range(5):
        if i >= len(sorted_ids):
            break
        try:
            temp_member = await guild.get_member(sorted_ids[i])
        except:
            del point_d[sorted_ids[i]]
            i -= 1
            continue
        top_5.append(sorted_ids[i])
        await temp_member.add_role(special_role, IE_GUILD_ID)

'''
Command to view points of all users participating in the rewards program
Parameters
----------
page: int
    The page of the leaderboard to display. Page 1 displays the top 10 users, while the last page displays the bottom 10 users. Any page number beyond the maximum will display the last page.
'''
@bot_client.command(
    name="leaderboard",
    description="Displays the top point earners",
    options=[interactions.Option(
        name = "page",
        description = "Page number of the leaderboard",
        type = interactions.OptionType.INTEGER,
        required = False
    )]
)
async def leaderboard(ctx, page: typing.Optional[int] = 1):
    if len(point_d) == 0:
        await ctx.send("Nobody is on the leaderboard yet!")
        return
    em = await create_leaderboard_embed(page)
    buttons = [Button(style=interactions.ButtonStyle.DANGER, label="Previous page", custom_id = 'previous_page'), Button(style=interactions.ButtonStyle.SUCCESS, label="Next page", custom_id = 'next_page')]
    await ctx.send(embeds = em, components=ActionRow(components=buttons))

async def create_leaderboard_embed(page: int):
    total_pages = math.ceil(len(point_d)/10)
    if page < 1:
        page = 1
    em = interactions.Embed(title = f'Top members by points in Illini Esports', description = 'The highest point members in the server')
    if page > total_pages:
        page = total_pages
    
    sorted_ids = sorted(point_d, key=point_d.get, reverse=True)
    embed_str = ""
    for i in range(10*(page - 1), min(len(point_d), 10*page)):
        if i < 0:
            break
        if sorted_ids[i] not in id_to_name:
            guild = await get_guild()
            member = await guild.get_member(sorted_ids[i])
            id_to_name[(sorted_ids[i])] = member.user.username + "#" + member.user.discriminator
        temp = f'{id_to_name[sorted_ids[i]]}: **{point_d[sorted_ids[i]]}'
        if i == 0:
            embed_str += f'🥇: {temp} points**\n'
        elif i == 1:
            embed_str += f'🥈: {temp} points**\n'
        elif i == 2:
            embed_str += f'🥉: {temp} points**\n'
        elif i == len(point_d) - 1:
            embed_str += f'<:KEKW:637019720721104896>: {temp} points**'
        else:
            embed_str += f'{i+1}: {temp} points**\n'
    em.add_field(name='\u200b', value=embed_str, inline = False)
    em.set_footer(text=f'Page {page}/{total_pages}')
    em.timestamp = datetime.today()
    em.set_thumbnail(url="https://pbs.twimg.com/profile_images/1378045236845412355/TjjZcbbu_400x400.jpg")
    em.set_author(name="IERP", icon_url="https://pbs.twimg.com/profile_images/1378045236845412355/TjjZcbbu_400x400.jpg")
    return em

@bot_client.component("previous_page")
async def previous_page(ctx):
    try:
        footer = str(ctx.message.embeds[0].footer.text)
    except:
        embed = await create_leaderboard_embed(1)
        await ctx.edit(embeds = embed)
        return
    page = int(footer[5:footer.index('/')])
    em = await create_leaderboard_embed(page - 1)
    await ctx.edit(embeds = em)

@bot_client.component("next_page")
async def next_page(ctx):
    try:
        footer = str(ctx.message.embeds[0].footer.text)
    except:
        embed = await create_leaderboard_embed(1)
        await ctx.edit(embeds = embed)
        return
    page = int(footer[5:footer.index('/')])
    em = await create_leaderboard_embed(page + 1)
    await ctx.edit(embeds = em)

'''
Runner function to check for active PUGS, active raffles, active codes, save global variables to files, and ping the server. This occurs once every 30 seconds
'''
async def expired():
    while True:
        await asyncio.sleep(30)
        for code in active_codes.keys():
            if active_codes[code][1] + active_codes[code][2] < time.time() and active_codes[code][2] != 0:
                points = active_codes[code]
                del active_codes[code]
                del used[code]
                log.append(code + " worth" + str(points) + " expired")
                break

        await update_top_5_role()
        
        with open(PATH_TO_POINTS, "wb") as f:
            pickle.dump(point_d, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open(PATH_TO_ID_TO_NAME, "wb") as f:
            pickle.dump(id_to_name, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open(PATH_TO_LOG, "wb") as f:
            pickle.dump(log, f, protocol=pickle.HIGHEST_PROTOCOL)

with open(PATH_TO_SECRETS) as f:
    secrets = json.load(f)
TOKEN = secrets['token']
loop = asyncio.get_event_loop()
asyncio.ensure_future(expired())
asyncio.ensure_future(bot_client.start())
loop.run_forever()