import json
import os
from BeFake import BeFake

import click
import httpx


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


@cli.command(help="Refresh token")
def refresh():
    bf = BeFake()
    try:
        bf.load("token.txt")
    except:
        raise Exception("No token found, are you logged in?")
    bf.refresh_token()
    bf.save("token.txt")
    print("Token refreshed.")


def download_media(client: httpx.Client, item):
    return [
        client.get(item["photoURL"]).content,
        client.get(item["secondaryPhotoURL"]).content,
    ]


@cli.command(help="Download a feed")
@click.argument("feed_id", type=click.Choice(["friends", "memories"]))
def feed(feed_id):
    bf = BeFake()
    try:
        bf.load("token.txt")
    except:
        raise Exception("No token found, are you logged in?")
    if feed_id == "friends":
        feed = bf.get_friends_feed()
        try:
            os.mkdir("feeds")
        except:
            pass
        try:
            os.mkdir("feeds/friends")
        except:
            pass
        try:
            with open("feeds/friends.json", "r") as f:
                old_feed = json.loads(f.read())
        except:
            old_feed = []

        with open("feeds/friends.json", "w") as f:
            f.write(json.dumps(old_feed + feed))
        for item in feed:
            try:
                os.mkdir("feeds/friends/" + item["user"]["username"])
            except:
                pass

            try:
                os.mkdir("feeds/friends/" + item["user"]["username"] + "/" + item["id"])
            except:
                pass

            with open(
                "feeds/friends/"
                + item["user"]["username"]
                + "/"
                + item["id"]
                + "/info.json",
                "w",
            ) as f:
                f.write(json.dumps(item))

            primary, secondary = download_media(bf.client, item)
            with open(
                "feeds/friends/"
                + item["user"]["username"]
                + "/"
                + item["id"]
                + "/primary.jpg",
                "wb",
            ) as f:
                f.write(primary)
            with open(
                "feeds/friends/"
                + item["user"]["username"]
                + "/"
                + item["id"]
                + "/secondary.jpg",
                "wb",
            ) as f:
                f.write(secondary)

    elif feed_id == "memories":
        raise Exception("TODO")
        feed = bf.get_memories_feed()


if __name__ == "__main__":
    cli()
