import json
import os
from .BeFake import BeFake
from .models.post import Post
import click

DATA_DIR = "data"

@click.group()
@click.pass_context
def cli(ctx):
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)


@cli.command(help="Login to BeReal")
@click.argument("phone_number", type=str)
def login(phone_number):
    bf = BeFake()
    bf.send_otp(phone_number)
    otp = input("Enter otp: ")
    bf.verify_otp(otp)
    bf.save()
    print("Login successful.")
    print("You can now try to use the other commands ;)")


@cli.command(help="Get info about your account")
def me():
    bf = BeFake()
    bf.load()
    user = bf.get_user_info()
    print(user)
    print(user.__dict__)


@cli.command(help="Refresh token")
def refresh():
    bf = BeFake()
    try:
        bf.load()
    except:
        raise Exception("No token found, are you logged in?")
    bf.refresh_tokens()
    print(bf.token, end='', flush=True)
    bf.save()


@cli.command(help="Download a feed")
@click.argument("feed_id", type=click.Choice(["friends", "discovery", "memories"]))
@click.option("--save-location", help="The paths where the posts should be downloaded")
@click.option("--realmoji-location", help="The paths where the (non-instant) realmojis should be downloaded")
@click.option("--instant-realmoji-location", help="The paths where the instant realmojis should be downloaded")
def feed(feed_id, save_location, realmoji_location, instant_realmoji_location):
    date_format = 'YYYY-MM-DD_HH-mm-ss'

    bf = BeFake()
    try:
        bf.load()
    except:
        raise Exception("No token found, are you logged in?")
    if feed_id == "friends":
        feed = bf.get_friends_feed()

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
            print("saving memory", item.memory_day)
            _save_location = save_location.format(date=item.memory_day)
        else:
            print(f"saving post by {item.user.username}".ljust(50, " "),f"{item.id}")
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
def parse_friends(save_location):
    date_format = 'YYYY-MM-DD_HH-mm-ss'

    bf = BeFake()
    try:
        bf.load()
    except:
        raise Exception("No token found, are you logged in?")
    friends = bf.get_friends()

    if save_location is None:
        save_location = f"{DATA_DIR}" + "/friends/{user}"

    for friend in friends:
        _save_location = save_location.format(user=friend.username)
        os.makedirs(f"{_save_location}", exist_ok=True)
        with open(f"{_save_location}/info.json", "w+") as f:
            json.dump(friend.data_dict, f, indent=4)

        if friend.profile_picture.exists():
            creation_date = friend.profile_picture.get_date().format(date_format)
            friend.profile_picture.download(f"{_save_location}/{creation_date}_profile_picture")

@cli.command(help="Post the photos under /data/photos to your feed")
@click.argument('primary_path', required=False, type=click.STRING)
@click.argument('secondary_path', required=False, type=click.STRING)
def post(primary_path, secondary_path):
    primary_path = "data/photos/primary.jpg" if not primary_path else primary_path
    secondary_path = "data/photos/secondary.jpg" if not secondary_path else secondary_path
    bf = BeFake()
    try:
        bf.load()
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    with open("data/photos/primary.png", "rb") as f:
        primary_bytes = f.read()
    with open("data/photos/secondary.png", "rb") as f:
        secondary_bytes = f.read()
    r = Post.create_post(
        primary=primary_bytes, secondary=secondary_bytes,
        is_late=False, is_public=False, caption="Insert your caption here", location={"latitude": "0", "longitude": "0"}, retakes=0)
    print(r)

@cli.command(help="Upload random photoes to BeReal Servers")
@click.argument("filename", type=click.STRING)
def upload(filename):
    bf = BeFake()
    try:
        bf.load()
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
        bf.load()
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    r = bf.add_comment(post_id, content)
    print(r)

@cli.command(help="Pretend to screenshot a post")
@click.argument("post_id", type=click.STRING)
def screenshot(post_id):
    bf = BeFake()
    try:
        bf.load()
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    r = bf.take_screenshot(post_id)
    print(r)

@cli.command(help="Delete your post")
def delete_post():
    bf = BeFake()
    try:
        bf.load()
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    r = bf.delete_post()
    print(r)

@cli.command(help="Change the caption of your post")
@click.argument("caption", type=click.STRING)
def change_caption(caption):
    bf = BeFake()
    try:
        bf.load()
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    r = bf.change_caption(caption)
    print(r)

@cli.command(help="Gets information about a user profile")
@click.argument("user_id", type=click.STRING)
def get_user_profile(user_id):
    bf = BeFake()
    try:
        bf.load()
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    r = bf.get_user_profile(user_id)
    print(r)

@cli.command(help="Sends a notification to your friends, saying you're taking a bereal")
@click.argument("user_id", type=click.STRING, required=False)
@click.argument("username", type=click.STRING, required=False)
def send_push_notification(user_id, username):
    bf = BeFake()
    try:
        bf.load()
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    r = bf.send_capture_in_progress_push(topic=user_id if user_id else None, username=username if username else None)
    print(r)

@cli.command(help="post an instant realmoji")
@click.argument("post_id", type=click.STRING)
@click.argument("filename", required=False, type=click.STRING)
def instant_realmoji(post_id, filename):
    bf = BeFake()
    try:
        bf.load()
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    if not filename:
        filename = "primary.jpg"
    with open(f"data/photos/{filename}", "rb") as f:
        data = f.read()
    r = bf.post_instant_realmoji(post_id, data)
    print(r)

@cli.command(help="Upload an emoji-specific realmoji")
@click.argument("type", type=click.Choice(["up", "happy", "surprised", "laughing", "heartEyes"]))
@click.argument("filename", required=False, type=click.STRING)
def upload_realmoji(type, filename):
    bf = BeFake()
    try:
        bf.load()
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    if not filename:
        filename = f"{type}.jpg"
    with open(f"data/photos/{filename}", "rb") as f:
        data = f.read()
    r = bf.upload_realmoji(data, emoji_type=type)
    print(r)

# currently broken, gives internal server error
@cli.command(help="Add realmoji to post")
@click.argument("post_id", type=click.STRING)
@click.argument("type", type=click.Choice(["up", "happy", "surprised", "laughing", "heartEyes"]))
@click.argument("filename", required=False, type=click.STRING)
def emoji_realmoji(post_id, type, filename):
    type = str(type)
    bf = BeFake()
    try:
        bf.load()
    except Exception as ex:
        raise Exception("No token found, are you logged in?")
    if not filename:
        filename = f"{type}.jpg"
    with open(f"data/photos/{filename}", "rb") as f:
        data = f.read()
    # we don't have any method to know which realmojis (mapped to a type) the user already uploaded, we think, the client just stores the urls to uploaded realmojis and sends them...
    r1 = bf.upload_realmoji(data, emoji_type=type)
    r2 = bf.post_realmoji(post_id, emoji_type=type, name=r1)
    print(r2)


if __name__ == "__main__":
    cli(obj={})
