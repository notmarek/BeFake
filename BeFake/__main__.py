import json
import os

from functools import wraps

import string
import random

from .BeFake import BeFake
from .models.post import Post, Location

import click

DATA_DIR = "data"


def load_bf(func):
    """
    Loads the BeFake object and passes it as the first argument to the function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        bf = BeFake()
        try:
            bf.load()
        except:
            raise Exception("No token found, are you logged in?")
        return func(bf, *args, **kwargs)

    return wrapper


@click.group()
@click.pass_context
def cli(ctx):
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)


@cli.command(help="Login to BeReal")
@click.argument("phone_number", type=str)
@click.argument("deviceid", type=str, default=''.join(random.choices(string.ascii_lowercase + string.digits, k=16)))
@click.option("backend", "--backend", "-b", type=click.Choice(["vonage", "firebase", "recaptcha"]), default="vonage",
              show_default=True)
def login(phone_number, deviceid, backend):
    bf = BeFake(deviceId=deviceid)
    if backend == "vonage":
        bf.send_otp_vonage(phone_number)
        otp = input("Enter otp: ")
        bf.verify_otp_vonage(otp)
        bf.save()
        click.echo("Vonage login successful.")
    elif backend == "firebase":
        bf.send_otp_firebase(phone_number)
        otp = input("Enter otp: ")
        bf.verify_otp_firebase(otp)
        bf.save()
        click.echo("Firebase login successful.")
    elif backend == "recaptcha":
        click.echo("Follow the instructions at https://github.com/notmarek/BeFake/wiki/reCAPTCHA for your operating system.")
        click.echo("\n\nOpen the following URL:")
        click.echo(bf.get_recaptcha_url())
        click.echo()
        recaptcha_token = input("Enter reCAPTCHA token: ")
        bf.send_otp_recaptcha(recaptcha_token, phone_number)
        otp = input("Enter otp: ")
        bf.verify_otp_firebase(otp)
        bf.save()
        click.echo("Firebase reCAPTCHA login successful.")

    click.echo("You can now try to use the other commands ;)")


@cli.command(help="Get a new access_token from your old token.txt config file")
def legacy_token():
    bf = BeFake()
    bf.legacy_load()
    bf.save()
    click.echo("Successful token import, you can now use the other commands!")

@cli.command(help="Get info about your account")
@load_bf
def me(bf):
    user = bf.get_user_info()
    click.echo(user)
    click.echo(user.__dict__)


@cli.command(help="Refresh token")
@load_bf
def refresh(bf):
    bf.refresh_tokens()
    click.echo(bf.token, nl=False)
    bf.save()


@cli.command(help="Download a feed")
@click.argument("feed_id", type=click.Choice(["friends", "friends-of-friends", "discovery", "memories"]))
@click.option("--save-location", help="The paths where the posts should be downloaded")
@click.option("--realmoji-location", help="The paths where the (non-instant) realmojis should be downloaded")
@click.option("--instant-realmoji-location", help="The paths where the instant realmojis should be downloaded")
@load_bf
def feed(bf, feed_id, save_location, realmoji_location, instant_realmoji_location):
    date_format = 'YYYY-MM-DD_HH-mm-ss'

    if feed_id == "friends":
        feed = bf.get_friends_feed()
    elif feed_id == "friends-of-friends":
        feed = bf.get_fof_feed()
    elif feed_id == "discovery":
        feed = bf.get_discovery_feed()
    elif feed_id == "memories":
        feed = bf.get_memories_feed()

    # Add fallback location for save_location and realmoji_location parameters if they were not specified by the user.
    # These strings will get formatted later, that's why the "f" is missing before the strings.
    if save_location is None:
        if feed_id == "memories":
            save_location = f"{DATA_DIR}" + "/feeds/memories/{date}"
        else:
            save_location = f"{DATA_DIR}" + "/feeds/{feed_id}/{user}/{post_id}"

    if realmoji_location is None:
        realmoji_location = \
            f"{DATA_DIR}" + \
            "/feeds/{feed_id}/{post_user}/{post_id}/reactions/{type}/{user}"

    instant_realmoji_location = realmoji_location if instant_realmoji_location is None else instant_realmoji_location

    for item in feed:
        if feed_id == "memories":
            click.echo("saving memory {}".format(item.memory_day))
            _save_location = save_location.format(date=item.memory_day)
        else:
            click.echo(f"saving post by {item.user.username}".ljust(50, " ") + item.id)
            post_date = item.creation_date.format(date_format)
            _save_location = save_location.format(user=item.user.username, date=post_date, feed_id=feed_id,
                                                  post_id=item.id)

        os.makedirs(f"{_save_location}", exist_ok=True)

        with open(f"{_save_location}/info.json", "w+") as f:
            f.write(json.dumps(item.data_dict, indent=4))
        item.primary_photo.download(f"{_save_location}/primary")
        item.secondary_photo.download(f"{_save_location}/secondary")

        if feed_id == "memories":
            continue
        for emoji in item.realmojis:
            # Differenciate between instant and non-instant realomji locations
            _realmoji_location = instant_realmoji_location if emoji.type == 'instant' else realmoji_location

            # Format realmoji location
            _realmoji_location = _realmoji_location.format(user=emoji.username, type=emoji.type, feed_id=feed_id,
                                                           post_date=post_date, post_user=item.username,
                                                           post_id=item.id, date='{date}')

            # Getting the realmoji creation date sends an extra request
            # Only use that if it's actually needed
            if '{date}' in _realmoji_location:
                _realmoji_location = _realmoji_location.format(date=emoji.get_creation_date().format(date_format))

            os.makedirs(os.path.dirname(_realmoji_location), exist_ok=True)
            emoji.photo.download(f"{_realmoji_location}")


@cli.command(help="Download friends information")
@click.option("--save-location", help="The directory where the data should be downloaded")
@load_bf
def parse_friends(bf, save_location):
    date_format = 'YYYY-MM-DD_HH-mm-ss'

    friends = bf.get_friends()
    if save_location is None:
        save_location = f"{DATA_DIR}" + "/friends/{user}"

    for friend in friends:
        _save_location = save_location.format(user=friend.username)
        os.makedirs(f"{_save_location}", exist_ok=True)
        with open(f"{_save_location}/info.json", "w+") as f:
            json.dump(friend.data_dict, f, indent=4)

        if friend.profile_picture:
            creation_date = friend.profile_picture.get_date().format(date_format)
            friend.profile_picture.download(f"{_save_location}/{creation_date}_profile_picture")


@cli.command(help="Post the photos under /data/photos to your feed")
@click.option('visibility', '--visibility', "-v", type=click.Choice(['friends', 'friends-of-friends', 'public']),
              default='friends', show_default=True, help="Set post visibility")
@click.option('caption', '--caption', "-c", type=click.STRING, default='', show_default=False, help="Post caption")
@click.option('location', '--location', "-l", type=float, nargs=2, default=[None, None],
              help="Post location, in latitude, longitude format.")
@click.option('retakes', '--retakes', "-r", type=int, default=0, show_default=True, help="Retake counter")
@click.option('resize', '--no-resize', "-R", default=True, show_default=True,
              help="Do not resize image to upload spec (1500, 2000), upload as is.")
@click.argument('primary_path', required=False, type=click.STRING)
@click.argument('secondary_path', required=False, type=click.STRING)
@load_bf
def post(bf, visibility, caption, location, retakes, primary_path, secondary_path, resize):
    if location != [None, None]:
        loc = Location(location[0], location[1])
    primary_path = "data/photos/primary.jpg" if not primary_path else primary_path
    secondary_path = "data/photos/secondary.jpg" if not secondary_path else secondary_path
    with open("data/photos/primary.jpg", "rb") as f:
        primary_bytes = f.read()
    with open("data/photos/secondary.jpg", "rb") as f:
        secondary_bytes = f.read()
    r = Post.create_post(bf, primary=primary_bytes, secondary=secondary_bytes, is_late=False, visibility=visibility,
                         caption=caption, location=loc, retakes=retakes, resize=resize)
    click.echo(r)


@cli.command(help="View an invidual post")
@click.argument("feed_id", type=click.Choice(["friends", "friends-of-friends", "discovery"]))
@click.argument("post_id", type=click.STRING)
@load_bf
def get_post(bf, feed_id, post_id):
    if feed_id == "friends":
        feed = bf.get_friends_feed()
    elif feed_id == "friends-of-friends":
        feed = bf.get_fof_feed()
    elif feed_id == "discovery":
        feed = bf.get_discovery_feed()

    for post in feed:
        if post.id == post_id:
            click.echo(post.__dict__)


@cli.command(help="Upload random photoes to BeReal Servers")
@click.argument("filename", type=click.STRING)
@load_bf
def upload(bf, filename):
    with open(f"data/photos/{filename}", "rb") as f:
        data = f.read()
    r = bf.upload(data)
    click.echo(f"Your file is now uploaded to:\n\t{r}")


@cli.command(help="Add a comment to a post")
@click.argument("post_id", type=click.STRING)
@click.argument("content", type=click.STRING)
@load_bf
def comment(bf, post_id, content):
    r = bf.add_comment(post_id, content)
    click.echo(r)


@cli.command(help="Delete a given comment")
@click.argument("post_id", type=click.STRING)
@click.argument("comment_id", type=click.STRING)
@load_bf
def remove_comment(bf, post_id, comment_id):
    r = bf.delete_comment(post_id, comment_id)
    click.echo(r)


@cli.command(help="Pretend to screenshot a post")
@click.argument("post_id", type=click.STRING)
@load_bf
def screenshot(bf, post_id):
    r = bf.take_screenshot(post_id)
    click.echo(r)


@cli.command(help="Delete your post")
@load_bf
def delete_post(bf):
    r = bf.delete_post()
    click.echo(r)


@cli.command(help="Change the caption of your post")
@click.argument("caption", type=click.STRING)
@load_bf
def change_caption(bf, caption):
    r = bf.change_caption(caption)
    click.echo(r)


@cli.command(help="Gets information about a user profile")
@click.argument("user_id", type=click.STRING)
@load_bf
def get_user_profile(bf, user_id):
    r = bf.get_user_profile(user_id)
    click.echo(r)
    click.echo(r.__dict__)


@cli.command(help="Sends a notification to your friends, saying you're taking a bereal")
@click.argument("user_id", type=click.STRING, required=False)
@click.argument("username", type=click.STRING, required=False)
@load_bf
def send_push_notification(bf, user_id, username):
    r = bf.send_capture_in_progress_push(topic=user_id if user_id else None, username=username if username else None)
    click.echo(r)


@cli.command(help="post an instant realmoji")
@click.argument("post_id", type=click.STRING)
@click.argument("user_id", type=click.STRING, required=False)
@click.argument("filename", required=False, type=click.STRING)
@load_bf
def instant_realmoji(bf, post_id, user_id, filename):
    if not filename:
        filename = "primary.jpg"
    with open(f"data/photos/{filename}", "rb") as f:
        data = f.read()
    r = bf.post_instant_realmoji(post_id, user_id, data)
    click.echo(r)


@cli.command(help="Upload an emoji-specific realmoji")
@click.argument("type", type=click.Choice(["up", "happy", "surprised", "laughing", "heartEyes"]))
@click.argument("filename", required=False, type=click.STRING)
@load_bf
def upload_realmoji(bf, type, filename):
    if not filename:
        filename = f"{type}.jpg"
    with open(f"data/photos/{filename}", "rb") as f:
        data = f.read()
    r = bf.upload_realmoji(data, emoji_type=type)
    click.echo(r)


# currently broken, gives internal server error
@cli.command(help="Add realmoji to post")
@click.argument("post_id", type=click.STRING)
@click.argument("user_id", type=click.STRING, required=False)
@click.argument("type", type=click.Choice(["up", "happy", "surprised", "laughing", "heartEyes"]))
@load_bf
def emoji_realmoji(bf, post_id, user_id, type):
    type = str(type)
    # we don't have any method to know which realmojis (mapped to a type) the user already uploaded, we think, the client just stores the urls to uploaded realmojis and sends them...
    r2 = bf.post_realmoji(post_id, user_id, emoji_type=type)
    click.echo(r2)


@cli.command(help="Search for a given username.")
@click.argument("username", type=click.STRING)
@load_bf
def search_user(bf, username):
    r = bf.search_username(username)
    click.echo(r)


# TODO: there's probably a better way of doing this, for instance having friend-request <add|view|cancel>.
@cli.command(help="Get friend requests")
@click.argument("operation", type=click.Choice(["sent", "received"]))
@load_bf
def friend_requests(bf, operation):
    r = bf.get_friend_requests(operation)
    click.echo(r)


@cli.command(help="Send friend request")
@click.argument("user_id", type=click.STRING)
@click.option("-s", "--source", "source", type=click.Choice(["search", "contacts", "suggestion"]), default="search",
              show_default=True, help="Where you first found about the user")
@load_bf
def new_friend_request(bf, user_id, source):
    r = bf.add_friend(user_id, source)
    click.echo(r)


@cli.command(help="Cancel friend request")
@click.argument("user_id", type=click.STRING)
@load_bf
def cancel_friend_request(bf, user_id):
    r = bf.remove_friend_request(user_id)
    click.echo(r)


@cli.command(help="get settings")
@load_bf
def settings(bf):
    r = bf.get_settings()
    click.echo(r)


if __name__ == "__main__":
    cli(obj={})
