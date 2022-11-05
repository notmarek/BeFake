# Save location customization with flags

You can customize where BeFake saves data using flags

## Feed - Memories

```bash
befake feed memories --save-location "data/feeds/memories/{date}"
```

### Keys
The following keys are supported (they will be replaced with their value):

 - **{date}:** The day the memory was created


## Feed - Friends and Discovery

```bash
befake feed \ 
  --save-location "data/feeds/friends/{user}/{post_id}" \ 
  --realmoji-location "data/feeds/friends/{post_user}/{post_id}/{user}" \
  <friends|discovery>
```

- `--save-location`: specifies the path of the post (`primary.jpg` and `secondary.jpg`) and it's metadata (`info.json`)
- `--realmoji-location`: specifies the download of the realmojis on a post
  - You can save disk space by not downloading a users realmoji on every post they have reacted to
- `--instant-realmoji-location`: specifies the download path of the instant realmojis on a post
  - Uses the value from `--realmoji-location` if not set

## Keys

### Post path (`--save-location`)
The following keys are supported (they will be replaced with their value):

 - **{date}:** The time the post was created
 - **{user}:** The poster's username
 - **{post_id}:** The unique ID of the post

### Realmoji (`--realmoji-location` and `--instant-realmoji-location`)
The following keys are supported (they will be replaced with their value):

 - **{date}:** The time the post was created
 - **{post_id}:** The unique ID of the post
 - **{user}:** The username of the realmoji's poster
 - **{post_user}:** The username of the poster
 - **{type}:** The type of the realmoji (ex. `up` or `surprised`)
 - **{post_date}:** The date and time the post was created
 - **{date}:** The date and time the realmoji was posted


## Parse-Friends

```bash
befake parse-friends --save-location "data/friends/{user}/"
```

### Saving directory (`--save-location`)

Specifies the **directory** where the profiles are saved.

#### Keys
The following keys are supported (they will be replaced with their value):

 - **{user}:** The username of the friend