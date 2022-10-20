from BeFake import BeFake
import pendulum

bf = BeFake()
bf.load("token.txt")

primary = None
secondary = None
with open("BeFake/pictures/back_camera.png", "rb") as f:
    primary = f.read()
with open("BeFake/pictures/front_camera.png", "rb") as f:
    secondary = f.read()

now = pendulum.now()
taken_at = f"{now.to_date_string()}T{now.to_time_string()}Z"
print(bf.create_post(primary, secondary, False, False, "Greetings from Downtown Manhatten", {"latitude": "40.741895", "longitude": "-73.989308"}, 0, taken_at=taken_at))