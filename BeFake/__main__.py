import json
import os
from BeFake import BeFake
from models.realmoji_picture import RealmojiPicture
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
@click.argument("feed_id", type=click.Choice(["friends", "discovery", "memories"]))
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

    elif feed_id == "memories":
        feed = bf.get_memories_feed()

    os.makedirs(f"{DATA_DIR}/feeds/{feed_id}", exist_ok=True)
    for item in feed:
        if feed_id == "memories":
            print("saving memory", f"{DATA_DIR}/feeds/memories/{item.memory_day}")
            os.makedirs(f"{DATA_DIR}/feeds/memories/{item.memory_day}", exist_ok=True)
            with open(f"{DATA_DIR}/feeds/memories/{item.memory_day}/primary.jpg", "wb") as f:
                f.write(item.primary_photo.download())
            with open(f"{DATA_DIR}/feeds/memories/{item.memory_day}/secondary.jpg", "wb") as f:
                f.write(item.secondary_photo.download())
            with open(f"{DATA_DIR}/feeds/memories/{item.memory_day}/info.json", "w+") as f:
                json.dump(item.data_dict, f, indent=4)
            continue
        print(f"saving post by {item.user.username}".ljust(50, " "),f"{item.id}")
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
@click.argument('primary_path', required=False, type=click.STRING)
@click.argument('secondary_path', required=False, type=click.STRING)
def post(primary_path, secondary_path):
    primary_path = "data/photos/primary.jpg" if not primary_path else primary_path
    secondary_path = "data/photos/secondary.jpg" if not secondary_path else secondary_path
    bf = BeFake()
    try:
        bf.load("token.txt")
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    with open("data/photos/primary.png", "rb") as f:
        primary_bytes = f.read()
    with open("data/photos/secondary.png", "rb") as f:
        secondary_bytes = f.read()
    r = bf.create_post(
        primary=primary_bytes, secondary=secondary_bytes,
        is_late=False, is_public=False, caption="Insert your caption here", location={"latitude": "0", "longitude": "0"}, retakes=0)
    print(r)

@cli.command(help="Upload random photoes to BeReal Servers")
@click.argument("filename", type=click.STRING)
def upload(filename):
    bf = BeFake()
    try:
        bf.load("token.txt")
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    with open(f"data/photos/{filename}", "rb") as f:
        data = f.read()
    r = bf.upload(data)
    print(f"Your file is now uploaded to:\n\t{r}")

@cli.command(help="Add a comment to a post")
@click.argument("post_id", type=click.STRING)
@click.argument("content", type=click.STRING)
def comment(post_id, content):
    bf = BeFake()
    try:
        bf.load("token.txt")
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    r = bf.add_comment(post_id, content)
    print(r)

@cli.command(help="Pretend to screenshot a post")
@click.argument("post_id", type=click.STRING)
def screenshot(post_id):
    bf = BeFake()
    try:
        bf.load("token.txt")
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    r = bf.take_screenshot(post_id)
    print(r)

if __name__ == "__main__":
    cli()
    #bf = BeFake()
    #try:
    #    bf.load("token.txt")
    #except Exception as ex:
    #    raise Exception("No token found, are you logged in?")

    #with open("data/photos/cat.png", "rb") as f:
    #    picture_bytes = f.read()

    # Instant Reaction
    #print(bf.post_instant_realmoji(picture_bytes, "J-NIa7WAaSOuVs536atLw"))

    # Realmoji Upload + Post
    #name = bf.upload_realmoji(picture_bytes, "up")
    #print(bf.post_realmoji("J-NIa7WAaSOuVs536atLw", "up", "👍", name))