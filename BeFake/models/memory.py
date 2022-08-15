from .picture import Picture


class Memory(object):
    def __init__(self, data_dict, befake) -> None:
        self.bf = befake
        self.id = data_dict.get("id", None)
        self.thumbnail = Picture(data_dict.get("thumbnail", {}))
        self.primary_photo = Picture(data_dict.get("primary", {}))
        self.secondary_photo = Picture(data_dict.get("secondary", {}))
        self.is_late = data_dict.get("isLate", None)
        self.memory_day = data_dict.get("memoryDay", None)

    def __repr__(self) -> str:
        return f"<Memory {self.id}>"
