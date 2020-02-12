# PSChatDisplay
Translucent Chat Display Overlay Window Script for PlexstormBot

This script goes with the Plexstorm Bot, and needs to be installed in a subfolder of the `scripts` folder in order to 
use it. It will auto-load when starting PlexBot, causing a translucent window to appear which will display chat in any 
channels loaded in your bot's `config.ini` file.

#### Python Dependencies:
-  PyQt5
-  playsound

### Using this Script

Ensure you have configured the PlexstormBot from my other repository first, then install in a subfolder of scripts such 
as `scripts/PSChatDisplay` or clone the repository from the scripts folder if you plan to do development work on it.  

`main.py` will be launched automatically when the bot is started, and the window should become visible. For now there is
no configuration without editing the `main.py` script, so you will need to do so in order to alter the size and 
appearance to your liking. `emoji.json` and `emoticons.json` define overrides so that unicode characters and text-based 
smileys will be converted automatically within the displayed chat window. Custom icons are created to show the gender 
assigned to each chatter's account as well. The `sfx` folder contains sound effects that will be played by the bot in 
place of the sound effects you would normally hear from having a browser window opened. These can easily be replaced to 
fit your preference.


### License

Included emoji are modified and optimized for use with the script from the twemoji set, so the twemoji license (CC-BY 
4.0) applies to those. Everything else in the repository, including the icons and sound effects, are under an MIT 
license, so feel free to reuse, redistribute, and modify to your heart's content, as long as the original license 
remains with the modified code. See `LICENSE` for more details.