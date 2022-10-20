from BeFake import BeFake
import os

bf = BeFake()
bf.load("token.txt")

for memory in bf.get_memories_feed():
    os.makedirs(f"feeds/memory/{memory.memory_day}", exist_ok=True)
    with open(f"feeds/memory/{memory.memory_day}/primary.jpg", "wb") as f:
        f.write(memory.primary_photo.download())
    with open(f"feeds/memory/{memory.memory_day}/secondary.jpg", "wb") as f:
        f.write(memory.secondary_photo.download())