from .picture import Picture


class Memory_v1(object):
    def __init__(self, data_dict, befake) -> None:
        self.bf = befake
        self.main_id = data_dict.get("mainPostMemoryId", None)
        self.id = self.main_id
        self.moment_Id = data_dict.get("momentId", None)
        self.thumbnail = Picture(data_dict.get("mainPostThumbnail", {}))
        self.primary_photo = Picture(data_dict.get("mainPostPrimaryMedia", {}))
        self.secondary_photo = Picture(data_dict.get("mainPostSecondaryMedia", {}))
        self.is_late = data_dict.get("isLate", None)
        self.memory_day = data_dict.get("memoryDay", None)
        self.data_dict = data_dict
        self.main_post_taken_at = data_dict.get("mainPostTakenAt", None)
        self.num_posts_for_moment = data_dict.get("numPostsForMoment", None)

    def __repr__(self) -> str:
        return f"<Memory-v1{self.id}>"
