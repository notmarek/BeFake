from .picture import Picture


class Memory(object):
    def __init__(self, data_dict, befake) -> None:
        self.bf = befake
        if "id" in data_dict:
            # dataDict of old memories
            self.id = data_dict.get("id", None)
        else: 
            # dataDict of new memories
            self.id = data_dict.get("mainPostMemoryId", None)

        if "thumbnail" in data_dict:
            # dataDict of old memories
            self.thumbnail = Picture(data_dict.get("thumbnail", {}))
        else:
            # dataDict of new memories
            self.thumbnail = Picture(data_dict.get("mainPostThumbnail", {}))
        
        if "primary" in data_dict:
            self.primary_photo = Picture(data_dict.get("primary", {}))
        else:
            self.primary_photo = Picture(data_dict.get("mainPostPrimaryMedia", {}))
        
        if "secondary" in data_dict:
            self.secondary_photo = Picture(data_dict.get("secondary", {}))
        else:
            self.secondary_photo = Picture(data_dict.get("mainPostSecondaryMedia", {}))
        
        self.is_late = data_dict.get("isLate", None)
        self.memory_day = data_dict.get("memoryDay", None)
        self.data_dict = data_dict
        
        self.isMain = "True"
        if ("isMain" in data_dict):
            self.isMain = data_dict["isMain"]

    def __repr__(self) -> str:
        return f"<Memory {self.id}>"
