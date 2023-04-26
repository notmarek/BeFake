<picture width="512" align="right">
 <source media="(prefers-color-scheme: dark)" srcset="./assets/befake-white.png">
 <img src="./assets/befake-black.png">
</picture>

A cool tool for collecting all your friends photos from BeReal (including RealMojis) without taking any screenshots, opening the app, annoying analytics and much much more!

A near total coverage of BeReals mobile API is planned and nearly done, except a few things.

## API Update
Due to recent changes in both BeFake and BeReal API, running ```befake legacy-token``` or a relogin is required.

## Install
```bash
pip install git+https://github.com/notmarek/BeFake
```

## Usage
```bash
befake [OPTIONS] COMMAND [ARGS]...
```


## Docker
```bash
docker run -v "{HOST_DATA_DIRECTORY}:/data" -v "{TOKEN}:/data/token.txt" notmarek/BeFake {command}
```

## Projects using this library
* [BeFake Dashboard](https://github.com/ArtrenH/BeFake-Dashboard) visualize your bereal antics in a nice way using Flask!

## Related projects
* [TooFake](https://github.com/s-alad/toofake) BeReal experience in your browser!


## Developement


```bash
  python -m venv .venv // create a venv (optional)
  source .venv/bin/activate

  pip install -r requirements.txt
  python befake.py
```

have fun

