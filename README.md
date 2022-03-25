# Destiny Fate Finder

*by nwL ([https://nwL.ms](https://nwl.ms))*

When did you meet your Destiny 2 clan? Find out here.

## How to use

1. Run the program with `python main.py` to generate a config file.
2. Configure the program in the newly created `config.py`.
3. Run the program once again with `python main.py`.

## Troubleshooting

**My requests suddenly don't work anymore.**  
You might have been blocked by Bungie. Try setting
`Settings.Advanced_AsyncThreadAmount` to a lower value to appease the Bungie overlords. If that doesn't work, turn
on `Settings.Advanced_CurlVerbose` and take notes.

**Part [x] of your code does not work in Python 2.**  
Correct.

## Known issues

* The `"activities"` filter does not work right now. You can safely use it, it's just a no-op.
* The requests might hang indefinitely after a few minutes. Unfortunately, I don't yet have the resources to monitor
  around ~7000 requests to find out what the issue is.