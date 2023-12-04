import discord
from discord.ext import commands
import requests
import sqlite3

#Local
import Settings
import WebSrw

db = sqlite3.connect("database.db")
cursor = db.cursor()

intents = discord.Intents.all()

Bot = commands.Bot(command_prefix="!", case_insensitive=True, fetch_offline_members=False, allowed_mentions=discord.AllowedMentions(everyone=False, roles=False), intents=intents)

@Bot.event
async def on_ready():
    await Bot.change_presence(status=discord.Status.offline)
    print("Up & Running!")
    Bot.remove_command("help")

@commands.guild_only()
@commands.is_owner()
@Bot.command()
async def pull(ctx):
    role = ctx.guild.get_role(Settings.PULL_ROLE_ID)
    if not role in ctx.author.roles:
        return
    a = await ctx.send("OKAY I PULL UP!\nDon't run any commands while im adding users to the guild")
    refresh_tokens()
    cursor.execute(f"SELECT * FROM oauth")
    result = cursor.fetchall()
    for res in result:
        try:
            data = {"access_token": res[1]}
            headers = {"Authorization": "Bot %s" % Settings.TOKEN, "Content-Type": "application/json"}
            joinguild = requests.put(f"https://discord.com/api/v9/guilds/{Settings.SERVER_ID}/members/{res[0]}", json=data, headers=headers)
            giverole = requests.put(f"https://discord.com/api/v9/guilds/{Settings.SERVER_ID}/members/{res[0]}/roles/{Settings.VERIFY_ROLE_ID}",
                headers={
                    "Authorization": "Bot %s" % Settings.TOKEN
                })
        except Exception as E:
            print(E)
    await a.edit(content="Pulled up!")

def refresh_tokens():
    cursor.execute(f"SELECT * FROM oauth")
    result = cursor.fetchall()
    for res in result:
        data = {
            'client_id': Settings.CLIENT_ID,
            'client_secret': Settings.CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': res[2]
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        r = requests.post('https://discord.com/api/v8/oauth2/token', data=data, headers=headers)
        resp = r.json()

        sql = "UPDATE oauth SET access_token = ?, refresh_token = ? WHERE refresh_token = ?"
        val = (resp["access_token"], resp["refresh_token"], res[2])
        cursor.execute(sql, val)
        db.commit()


WebSrw.Verify()

Bot.run(Settings.TOKEN, reconnect=True)