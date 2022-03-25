from src.functions import run
from src.Settings import Settings

if Settings.try_load():
    run()
else:
    path = Settings.create_stub()
    print('Created stub config in ' + path)
    print('Fill it out and re-run this file.')
