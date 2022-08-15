import pendulum
from .picture import Picture


class User(object):
    """BeReal user object"""

    def __init__(self, data_dict, befake) -> None:
        self.bf = befake
        self.id = data_dict.get("id", None)
        self.is_self = self.bf.user_id == self.id
        self.mutual_friends = data_dict.get("mutualFriends", None)
        self.hashed_phone_number = data_dict.get("hashedPhoneNumber", None)
        self.username = data_dict.get("username", None)
        self.new_username = data_dict.get("newUsername", None)
        self.birth_date = data_dict.get("birthdate", None)
        if self.birth_date is not None:
            self.birth_date = pendulum.parse(self.birth_date)
        self.full_name = data_dict.get("fullname", None)
        from .realmoji import RealMoji
        self.realmojis = [RealMoji(rm, befake) for rm in data_dict.get("realmojis", [])]
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
        self.profile_picture = Picture(data_dict.get("profilePicture", {}))
        self.friend_ship_status = data_dict.get("status", None)
        if self.created_at is not None:
            self.created_at = pendulum.parse(self.created_at)
        self.updated_at = data_dict.get("updatedAt", None)
        if self.updated_at is not None:
            self.updated_at = pendulum.parse(self.updated_at)

    def __repr__(self) -> str:
        return f"<User {self.id}>"

    def send_friend_request(self):
        """Send a friend request to this user"""
        if self.is_self:
            raise ValueError("Cannot send friend request to self")
        return self.bf.add_friend(self.id)
