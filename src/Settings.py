import os
import sys

from src.ActivityFilterList import ActivityFilterList


class Settings:
    __root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    ApiKey: str = None
    BungieName: str = None
    ClanId: str = None

    RequeryClanmates: bool = None
    RequeryActivityBatches: bool = None
    RequeryActivityDetails: bool = None

    OnlyListFirstN: int = 0

    Filters = ActivityFilterList()

    # ADVANCED

    Advanced_AsyncThreadAmount: int = 10
    Advanced_CurlVerbose: bool = False

    DataFolder: str = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'data')

    @staticmethod
    def validate():
        print('Validating settings...')

        is_valid = True

        if Settings.ApiKey is None:
            sys.stderr.write("API Key was not set." + "\n")
            is_valid = False

        if Settings.BungieName is None:
            sys.stderr.write("Player Bungie Name was not set." + "\n")
            is_valid = False

        if Settings.ClanId is None:
            sys.stderr.write("Clan ID was not set." + "\n")
            is_valid = False

        if not is_valid:
            print("Validation failed. Exiting.")
            exit(1)

        print("Settings valid.")

    @staticmethod
    def try_load():

        filename = os.path.join(Settings.__root, 'config.py')

        if not os.path.exists(filename):
            return False

        try:
            sys.path.append(Settings.__root)
            from config import init
            init()
            return True
        except ImportError:
            return False

    @staticmethod
    def create_stub(overwrite=False):
        filename = os.path.join(Settings.__root, 'config.py')

        if os.path.exists(filename) and not overwrite:
            return False

        with open(filename, 'w') as f:
            stub = """
import aiobungie

from src.ActivityFilterList import ActivityType
from src.functions import run
from src.Settings import Settings

def init():
    ###################
    ## SETTINGS
    ###################
    
    ## set API key (string)
    # TODO
    Settings.ApiKey = None
    
    ## set search values
    
    ## Bungie Name of player (string)
    # TODO
    Settings.BungieName = None
    
    ## Clan ID (string)
    # TODO
    Settings.ClanId = None
    
    ## requery these things from Bungie?
    ## if no, try to get from cache
    Settings.RequeryClanmates = True
    Settings.RequeryActivityBatches = True
    Settings.RequeryActivityDetails = True  # this is costly!
    
    ## add filtering options
    ## see method docstring for hints
    
    ## filter by date
    # Settings.Filters.addFilter("date", "before", "2020-05-01T00:00:00+00:00")
    
    ## filter by character
    # Settings.Filters.addFilter("character", "is", aiobungie.Class.WARLOCK)
    
    ## filter by activity
    ## currently broken
    # Settings.Filters.addFilter("activity", "is", ActivityType.AllPvE)
    
    ## only list first n matches, 0 to list all
    Settings.OnlyListFirstN = 0
    
    ## sets folder for data
    ## default: ./data
    # Settings.DataFolder = '/home/foo/destiny/data'
    
    #####################
    ## ADVANCED OPTIONS
    #####################
    
    ## This controls the chunk sizes of the async requests.
    ## Larger values are faster, but dangerous and could get you temporarily blocked by the Bungie API.
    ## default = 10
    # Settings.Advanced_AsyncThreadAmount = 10
    
    ## Make curl give verbose output.
    ## this generates a *lot* of text - for an average set of requests, this will generate around 100k lines of output
    ## default = false
    # Settings.Advanced_CurlVerbose = False
    """
            f.write(stub)
            f.close()
            return filename
