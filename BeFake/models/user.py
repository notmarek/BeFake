import pendulum


class User(object):
    """BeReal user object"""

    def __init__(self, data_dict, befake):
        self.bf = befake
        self.id = data_dict.get("id", None)
        self.username = data_dict.get("username", None)
        self.new_username = data_dict.get("newUsername", None)
        self.birth_date = data_dict.get("birthdate", None)
        if self.birth_date is not None:
            self.birth_date = pendulum.parse(self.birth_date)
        self.full_name = data_dict.get("fullname", None)
        self.realmojis = data_dict.get(
            "realmojis", None
        )  # TODO: implement realmoji object
        self.terms = data_dict.get("terms", None)
        self.devices = data_dict.get("devices", None)  # TODO: implement device object
        self.stats = data_dict.get("stats", None)  # TODO: implement stats object
        self.can_delete_post = data_dict.get("canDeletePost", None)
        self.can_update_region = data_dict.get("canUpdateRegion", None)
        self.phone_number = data_dict.get("phoneNumber", None)
        self.biography = data_dict.get("biography", None)
        self.location = data_dict.get("location", None)
        self.country_code = data_dict.get("countryCode", None)
        self.region = data_dict.get("region", None)
        self.created_at = data_dict.get("createdAt", None)
        self.profile_picture = data_dict.get(
            "profilePicture", None
        )  # TODO: implement picture object
        self.friend_ship_status = data_dict.get("status", None)
        if self.created_at is not None:
            self.created_at = pendulum.parse(self.created_at)

    def __repr__(self) -> str:
        return f"<User {self.id}>"
