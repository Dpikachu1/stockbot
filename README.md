# Intro - what is StockBot?
StockBot is a service that tracks the stock level of products on supported websites. Users can interact with the bot through Discord and track any given product on Newegg, BestBuy, CanadaComputers, MemoryExpress and Amazon.


Please note that this bot does NOT attempt to purchase merchandise, it only acts a method for potential buyers to get notified when a product they are looking to buy becomes available.

# Using StockBot
#### This guide assumes some technical knowledge of Discord applications and Linux servers/AWS (if the bot is being used as a cloud service)

What you need:
- Any linux server of your choice (preferably Ubuntu/Fedora) -> *Note: if using AWS, this guide will explain the basics of setting up an EC2 instance*
- PuTTY -> *(or any SSL of your choice)*
- FileZilla -> *(or any FTP software of your choice)*
- Python 3.8.x
- A Discord Server

# Discord Setup
1. Log into https://discord.com/developers/applications
2. If “StockBot” is not a creation of yours, select “New Application”
3. Name and give full permissions to the bot
4. Under OAuth2, scroll down to “Scopes” and select “bot” -> *This will open another list of permissions and be sure to check “Administrator”*
5. Ensure both Presence intent and Server Member Intent are turned on
5. There will be a link between the two lists, copy and paste that into your browser -> *This will allow you to add the bot to your server (guild) of choice*
6. Save everything!
- That's it for the Discord end of things, be sure to keep the bot page open however, as we will need the auth token in a bit.


# AWS
*If not using AWS, please create a linux-based server of your choice*
1. Using AWS, launch an EC2 instance for ubuntu 20.04 LTS -> *(leave all settings as default except encrypt the volume, make sure to also have a key created!)*
2. Use PuTTY to access the console, use port 22 and the public IPv4 DNS address that AWS gives you upon starting the instance -> *(username is ubuntu)*
#### Install Firefox
3. In the console type: sudo apt-get firefox
#### Install Python3.8
4. Type in console: sudo apt update and sudo apt -y upgrade
5. Now, we need to install pip, use the command in console: sudo apt install -y python3-pip
#### Install selenium for python and web driver
6. Type in console: pip3 install selenium and pip3 install webdriver_manager then sudo apt install firefox-geckodriver
- We are going to use a virtual environment to run the bot from, to do this, we need python venv
7. Use the command in console: sudo apt install python3-venv
#### Install Bot Dependencies
- We need to use pip to install the redis, beautifulSoup and discord.py modules in python
8. Now, we need to install redis-server, use the command in console: sudo apt install redis-server
9. To install redis, type in console this command: pip3 install redis To install beautifulSoup: pip3 install bs4 Discord: pip3 install discord
#### Folders and Virtual Environment
- Now let’s setup the folders and the virtual environment
10. Make a “discordBot” directory by typing in console: mkdir discordBot Then move to that directory by typing: cd discordBot
- Now let’s make the virtual environment
11. Type in console: python3 -m venv env
12. Start by moving to the newly created env directory by typing in console: cd env Then finally, activate it with this command in console: source bin/activate -> *You should now see an (env) in front of the command prompt*
13. Make a new directory called “bot” using the command: mkdir bot and move to it using in console: cd bot
#### Storing the Bot Token
14. In console, Navigate back to the discordBot directory by typing the following set of commands: cd and cd discordBot
15. To start redis, use this commandredis-server -> *NOTE, this may produce an error saying “Address already in use”. This is good, it means redis is already running! If no errors occur, then redis just started and you are also good to move onto the next step!*
16. Now let’s get into the redis client, type this into the console: redis-cli -> *An ip should now become your command prompt*
17. Now, let’s add our bots auth token! To get the token, revisit the applications developer portal website. You can find the token under the “Bot” tab right beside the bots profile picture. Simply select “Copy”.
18. Now in the console type: set ‘AUTH_TOKEN’ ‘TOKEN HERE WITH SINGLE QUOTES SURROUNDING’ -> *The console should send back OK. To exit redis, use CTRL+D in console*
Great! Now the bot is ready to be activated!
#### Uploading Bot Files
19. Open FileZilla and use Site Manager to connect to the AWS instance. Once connected, navigate to the bot directory and upload all bot python files
# Activating Bot
1. To activate the bot, move back to the console in PuTTY and navigate to the bot directory. Then, type the following command: python3.8 bot.py

























