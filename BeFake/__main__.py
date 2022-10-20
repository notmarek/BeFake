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
        print(feed)
        for elem in feed:
            print(elem.username, elem.location)

    elif feed_id == "discovery":
        feed = bf.get_discovery_feed()

    os.makedirs(f"feeds/{feed_id}", exist_ok=True)
    for item in feed:
        os.makedirs(f"feeds/{feed_id}/{item.user.username}/{item.id}", exist_ok=True)

        with open(
            f"feeds/{feed_id}/{item.user.username}/{item.id}/info.json",
            "w+",
        ) as f:
            f.write(json.dumps(item.toJSON(), indent=4))

        with open(
            f"feeds/{feed_id}/{item.user.username}/{item.id}/primary.jpg",
            "wb",
        ) as f:
            f.write(item.primary_photo.download())
        with open(
            f"feeds/{feed_id}/{item.user.username}/{item.id}/secondary.jpg",
            "wb",
        ) as f:
            f.write(item.secondary_photo.download())
        for emoji in item.realmojis:
            os.makedirs(
                f"feeds/{feed_id}/{item.user.username}/{item.id}/reactions/{emoji.type}",
                exist_ok=True,
            )

            with open(
                f"feeds/{feed_id}/{item.user.username}/{item.id}/reactions/{emoji.type}/{emoji.username}.jpg",
                "wb",
            ) as f:
                f.write(emoji.photo.download())


if __name__ == "__main__":
    cli()
