import json
import os
from BeFake import BeFake
from utils import *

import click
import httpx

import pendulum

DATA_DIR = "data"

@click.group()
def cli():
    pass


@cli.command(help="Login to BeReal")
@click.argument("phone_number", type=str)
def login(phone_number):
    bf = BeFake()
    bf.send_otp(phone_number)
    otp = input("Enter otp: ")
    bf.verify_otp(otp)
    bf.save("token.txt")
    print("Login successful.")
    print("You can now try to use the other commands ;)")


@cli.command(help="Get info about your account")
def me():
    bf = BeFake()
    bf.load("token.txt")
    user = bf.get_user_info()
    print(user)
    print(user.__dict__)


@cli.command(help="Refresh token")
def refresh():
    bf = BeFake()
    try:
        bf.load("token.txt")
    except:
        raise Exception("No token found, are you logged in?")
    bf.refresh_tokens()
    print("New token: ", bf.token)
    bf.save("token.txt")
    print("Token refreshed.")


def download_media(client: httpx.Client, item):
    return [
        client.get(item["photoURL"]).content,
        client.get(item["secondaryPhotoURL"]).content,
    ]


@cli.command(help="Download a feed")
@click.argument("feed_id", type=click.Choice(["friends", "discovery"]))
def feed(feed_id):
    bf = BeFake()
    try:
        bf.load("token.txt")
    except:
        raise Exception("No token found, are you logged in?")
    if feed_id == "friends":
        feed = bf.get_friends_feed()

    elif feed_id == "discovery":
        feed = bf.get_discovery_feed()

    os.makedirs(f"{DATA_DIR}/feeds/{feed_id}", exist_ok=True)
    for item in feed:
        os.makedirs(f"{DATA_DIR}/feeds/{feed_id}/{item.user.username}/{item.id}", exist_ok=True)

        with open(
            f"{DATA_DIR}/feeds/{feed_id}/{item.user.username}/{item.id}/info.json",
            "w+",
        ) as f:
            f.write(json.dumps(item.data_dict, indent=4))

        with open(
            f"{DATA_DIR}/feeds/{feed_id}/{item.user.username}/{item.id}/primary.jpg",
            "wb",
        ) as f:
            f.write(item.primary_photo.download())
        with open(
            f"{DATA_DIR}/feeds/{feed_id}/{item.user.username}/{item.id}/secondary.jpg",
            "wb",
        ) as f:
            f.write(item.secondary_photo.download())
        for emoji in item.realmojis:
            os.makedirs(
                f"{DATA_DIR}/feeds/{feed_id}/{item.user.username}/{item.id}/reactions/{emoji.type}",
                exist_ok=True,
            )

            with open(
                f"{DATA_DIR}/feeds/{feed_id}/{item.user.username}/{item.id}/reactions/{emoji.type}/{emoji.username}.jpg",
                "wb",
            ) as f:
                f.write(emoji.photo.download())

@cli.command(help="Download friends information")
def parse_friends():
    bf = BeFake()
    try:
        bf.load("token.txt")
    except:
        raise Exception("No token found, are you logged in?")
    friends = bf.get_friends()
    os.makedirs(f"{DATA_DIR}/friends", exist_ok=True)
    for friend in friends:
        os.makedirs(f"{DATA_DIR}/friends/{friend.username}", exist_ok=True)
        os.makedirs(f"{DATA_DIR}/friends/{friend.username}/info", exist_ok=True)
        os.makedirs(f"{DATA_DIR}/friends/{friend.username}/profile_pictures", exist_ok=True)
        with open(f"{DATA_DIR}/friends/{friend.username}/info/info{unix_timestamp()}.json", "w+") as f:
            json.dump(friend.data_dict, f, indent=4)

        if friend.profile_picture.exists():
            with open(f"{DATA_DIR}/friends/{friend.username}/profile_pictures/{unix_timestamp()}.jpg", "wb") as f:
                f.write(friend.profile_picture.download())

@cli.command(help="Post the photos under /data/photos to your feed")
def post():
    bf = BeFake()
    try:
        bf.load("token.txt")
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    with open("data/photos/primary.png", "rb") as f:
        primary_bytes = f.read()
    with open("data/photos/secondary.png", "rb") as f:
        secondary_bytes = f.read()
    now = pendulum.now()
    taken_at = f"{now.to_date_string()}T{now.to_time_string()}Z"
    r = bf.create_post(
        primary=primary_bytes, secondary=secondary_bytes,
        is_late=False, is_public=False, caption="", location={"latitude": "40.741895", "longitude": "-73.989308"})
    print(r)

@cli.command(help="Upload random files to BeReal Servers leeel")
def upload():
    bf = BeFake()
    try:
        bf.load("token.txt")
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    with open("data/photos/jeuusd992wd41.jpg", "rb") as f:
        data = f.read()
    
    r = bf.upload(data)
    print(r)

if __name__ == "__main__":
    cli()
    bf = BeFake()
    try:
        bf.load("token.txt")
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    
    
    r = bf.get_friend_suggestions()
    for elem in r:
        print(elem.username)
    print(r)