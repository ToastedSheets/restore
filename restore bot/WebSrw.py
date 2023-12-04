from flask import Flask, request, redirect, render_template
from threading import Thread
import requests, json, sqlite3

#Local
import Settings

app = Flask("")

@app.route("/discord/")
def login_redirect():
    if not request.args.get("code"):
        return redirect(Settings.DISCORD_REDIRECT_URL)
    code = request.args.get("code")
    resp = exchange_code(code)
    if resp == "Missing scopes":
        return render_template("error.html")
        return("There are some missing scopes. please try again using the provided url.", 405)
    elif resp == "Redirect":
        return redirect(Settings.DISCORD_REDIRECT_URL)
    return render_template("verified.html")

def exchange_code(code):
    data = {
        'client_id': Settings.CLIENT_ID,
        'client_secret': Settings.CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': Settings.REDIRECT_URI,
        'scope': 'identify email guilds.join'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers)
    cred = r.json()
    print(cred)
    if not cred:
        return "Redirect"
    if cred.get("error"):
        return "Redirect"
    rscopes = ["identify", "email", "guilds.join"]
    scopes = cred["scope"]
    for scope in rscopes:
        if scope not in scopes:
            return "Missing scopes"
    print("Ok we pull up!")
    userreq = requests.get('https://discord.com/api/v9/users/@me', headers={
        "Authorization": "Bearer %s" % cred['access_token']
    })
    user = userreq.json()
    data = {"access_token": cred['access_token']}
    headers = {"Authorization": "Bot %s" % Settings.TOKEN, "Content-Type": "application/json"}
    #joinguild = requests.put(f"https://discord.com/api/v9/guilds/{Settings.SERVER_ID}/members/{user['id']}", json=data, headers=headers)
    giverole = requests.put(f"https://discord.com/api/v9/guilds/{Settings.SERVER_ID}/members/{user['id']}/roles/{Settings.VERIFY_ROLE_ID}", headers={
        "Authorization": "Bot %s" % Settings.TOKEN})
    add_to_db(user["id"], cred["access_token"], cred["refresh_token"])
    return user['username']

def add_to_db(id, access_token, refresh_token):
    db = sqlite3.connect("database.db")
    cursor = db.cursor()
    sql = (f"INSERT INTO oauth (id, access_token, refresh_token)" f"VALUES(?, ?, ?)")
    val = (id, access_token, refresh_token)
    cursor.execute(sql, val)
    db.commit()
    db.close()


def run():
    app.run(host="0.0.0.0", port=2036)


def Verify():
    server = Thread(target=run)
    server.start()