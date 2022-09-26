# StockBot - Main Script
# This script serves as the "hub" for the entire discord bot and executes other scripts accordingly
# When running the bot, execute this script first
# Designed and Developed by Davis Lenover
# Version 0.93B

# General imports
import logging
import sys
import asyncio
import random

# Functionality scripts
import discord
from discord.ext import tasks
import redis
import shutil
import os
from os import path

# Website Scripts
import newegg
import bestbuy
import canadacomputers
import memoryexpress
import amazon

# Scripts to handle product data
import product_dealer
import stock_tracker

# minWait and maxWait define the time interval between when the bot will check for updates (this is mainly used to prevent ip banning as access to websites looks random)
minWait = 180
maxWait = 300

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Allow all intents
intents = discord.Intents.all() # Intents allow access to all members in guild

# Create access to Redis
redis_server = redis.Redis()

# Start the discord client
client = discord.Client(intents=intents)

# Get working directory of python script
working_directory = os.getcwd()
# Add a directory userData
full_dir = (working_directory + "/userData")

# Directory for where all users are stored
user_storage_path = (full_dir + "/users")

async def handle_new_users(member):

    does_exist = await does_user_exist_in_file(member)

    # Check if the member is not actually new (aka, check if the directory exists already)
    if (not does_exist):

        id_user = str(member.id)
        # If not...
        # Create a new directory for said new member
        os.makedirs(user_storage_path + "/" + id_user)
        # Create the directory where the user will store products to be tracked
        os.makedirs(user_storage_path + "/" + id_user + "/product_data")
        # Create a user data file for the new member
        file_user_data = open(user_storage_path + "/" + id_user + "/user_data.txt", "a+")
        file_user_data.write("USER_ID=" + id_user  + "\n")
        file_user_data.write("CURRENT_NAME=" + str(member) + "\n")
        file_user_data.write("STATUS=MSG_WAIT" + "\n")
        file_user_data.write("CHANNEL_ID=X" + "\n")
        file_user_data.write("WEBSITE_TYPE_TEMP=X" + "\n")
        file_user_data.write("PRODUCT_LINK_TEMP=X" + "\n")
        file_user_data.write("PRODUCT_NAME_TEMP=X" + "\n")
        file_user_data.write("IS_NEW=True" + "\n")
        file_user_data.close()

# Method to check if a user exists in files
async def does_user_exist_in_file(member):

    # For loop through each directory (titled with the users id)
    for user in os.listdir(user_storage_path):

        # Compare the directory name to the id of the requested user
        if user == str(member.id):

            return True

    return False

# Method to store user specific data on the server
async def store_data(data):
    # inside data: member, task, channel_id, status, website_type, product_link, product_name
    # Files are stored as follows:
    # Line 1 - User ID
    # Line 2 - Current Name
    # Line 3 - General Status
    # Line 4 - Channel ID
    # Line 5 - Website Type
    # Line 6 - Product Link
    # Line 7 - Set new user to False

    # Get user data
    member_path = (user_storage_path + "/" + str(data[0].id))
    member_file = open(member_path + "/user_data.txt", "r")
    data_contents = member_file.readlines()
    member_file.close()

    # Preform a current name check (if the name is not already going to be changed)
    if (data[1] != 3):
        member_name = str(data[0])
        if ((data_contents[1][13:-1]) != member_name):
            # If the names do not match, update the file to the current name on discord
            data_contents[1] = ("CURRENT_NAME=" + member_name + "\n")
            member_file = open(member_path + "/user_data.txt", "w")
            member_file.writelines(data_contents)
            member_file.close()
            return member_name

    
    # Store channel id
    if data[1] == 1:
        data_contents[3] = ("CHANNEL_ID=" + str(data[2]) + "\n")
        member_file = open(member_path + "/user_data.txt", "w")
        member_file.writelines(data_contents)
        member_file.close()
        return True

    # Change status
    elif data[1] == 2:
        data_contents[2] = ("STATUS=" + data[3] + "\n")
        member_file = open(member_path + "/user_data.txt", "w")
        member_file.writelines(data_contents)
        member_file.close()
        return True

    # Change current name
    elif data[1] == 3:
        data_contents[1] = ("CURRENT_NAME=" + str(data[0]) + "\n")
        member_file = open(member_path + "/user_data.txt", "w")
        member_file.writelines(data_contents)
        member_file.close()
        return True

    # Change website type
    elif data[1] == 4:
        data_contents[4] = ("WEBSITE_TYPE_TEMP=" + data[4] + "\n")
        member_file = open(member_path + "/user_data.txt", "w")
        member_file.writelines(data_contents)
        member_file.close()
        return True

    # Change product link
    elif data[1] == 5:
        data_contents[5] = ("PRODUCT_LINK_TEMP=" + data[5] + "\n")
        member_file = open(member_path + "/user_data.txt", "w")
        member_file.writelines(data_contents)
        member_file.close()
        return True

    # Change product name
    elif data[1] == 6:
        data_contents[6] = ("PRODUCT_NAME_TEMP=" + data[6] + "\n")
        member_file = open(member_path + "/user_data.txt", "w")
        member_file.writelines(data_contents)
        member_file.close()
        return True

    # Change the user being new to False
    elif data[1] == 7:
        data_contents[7] = ("IS_NEW=" + "False" + "\n")
        member_file = open(member_path + "/user_data.txt", "w")
        member_file.writelines(data_contents)
        member_file.close()
        return True

# Method to retrieve data from a given users file
# Note, everything is returned as a string
async def get_data(member,line):

    # Files are stored as follows:
    # Line 1 - User ID
    # Line 2 - Current Name
    # Line 3 - General Status
    # Line 4 - Channel ID
    # Line 5 - Website Type
    # Line 6 - Product Link
    # Line 7 - Product Name
    # Line 9 - User maturity (are they new?)

    # Get user data
    member_path = (user_storage_path + "/" + str(member.id))
    member_file = open(member_path + "/user_data.txt", "r")
    data_contents = member_file.readlines()

    # First, there needs to be a check if the user has changed their physical discord name
    # If so, their file stored must be updated
    member_name = str(member)
    if ((data_contents[1][13:-1]) != member_name):
        # File must be closed as the store_data method is going to update it
        member_file.close()
        await store_data([member, 3])
        # Once the file update is complete, then this method can reopen the file (to update data_contents in memory)
        member_file = open(member_path + "/user_data.txt", "r")
        data_contents = member_file.readlines()
        member_file.close()
        return True

    # User ID
    if line == 1:
        return (data_contents[0][8:-1])
    # Current Name
    elif line == 2:
        return (data_contents[1][13:-1])
    # General Status
    elif line == 3:
        return (data_contents[2][7:-1])
    # Channel ID
    elif line == 4:
        return (data_contents[3][11:-1])
    # Website Type
    elif line == 5:
        return (data_contents[4][18:-1])
    # Product Link
    elif line == 6:
        return (data_contents[5][18:-1])
    # Product Name
    elif line == 7:
        return (data_contents[6][18:-1])
    # Create a list of all data_contents and return it
    # Useful if a method wants data from multiple lines in a file
    elif line == 8:
        return [data_contents[0][8:-1],data_contents[1][13:-1],data_contents[2][7:-1],data_contents[3][11:-1],data_contents[4][13:-1],data_contents[5][13:-1],data_contents[6][18:-1], data_contents[7][7:-1]]

    # User maturity
    elif line == 9:
        return (data_contents[7][7:-1])


# Method to test if a given store exists
async def does_store_exist(storefront, specific_store_name):
    # Storefront
    # 1 - CanadaComputers
    # 2 - MemoryExpress

    # CanadaComputers

    if (storefront == 1):

        # For loop through CanadaComputers stores
        for store in canadacomputers.stores:
            if (store == specific_store_name):
                return True

    # MemoryExpress

    elif (storefront == 2):

        # For loop through MemoryExpress stores
        for store in memoryexpress.stores:
            if (store == specific_store_name):
                return True


    return False

# Method to print main settings page
async def print_main_setting(member, channel):

    # Main settings menu
    # Update status
    await store_data([member, 2, None, "SETTINGS_MAIN"])

    # Send back the setting menu
    await channel.send('**//Settings//**')
    await channel.send('|Products| - Product specific settings')
    await channel.send('|Back| - Exit Settings mode')
    await channel.send('Please type and send which category you would like to open in settings (e.g. "Products" (without quotations))')
    await channel.send('Note that product tracking is disabled until you exit settings!')
    await channel.send('*Page loaded*')

# Method to print general settings -- CURRENTLY NOT IN USE, MEANT FOR FUTURE VERSION WHEN NEEDED
async def print_general_settings(member, channel):

    # General settings menu
    # Update status
    await store_data([member, 2, None, "SETTINGS_GENERAL"])

    # Send back the setting menu
    await channel.send('**//General Settings//**')
    await channel.send('|Leave| - Delete all saves and leave the server')
    await channel.send('|Back| - Exit Settings mode')
    await channel.send('*Page loaded*')

# Method to print the main page of products for a given user
async def print_products_main(member, channel):

    # Get all products the user is tracking
    product_list = await product_dealer.retrieve_product_list(member)

    products_in_order = [False, False, False, False, False]
    are_products_full = False

    # Place product names in a new list that are in order
    for product in product_list:
        if int(product[0]) == 1:
            products_in_order[0] = product[1]
        elif int(product[0]) == 2:
            products_in_order[1] = product[1]
        elif int(product[0]) == 3:
            products_in_order[2] = product[1]
        elif int(product[0]) == 4:
            products_in_order[3] = product[1]
        elif int(product[0]) == 5:
            products_in_order[4] = product[1]

    await channel.send('**//Product Settings//**')

    # List all the products a user is tracking
    await channel.send('**/Product List/**')
    await channel.send('*/Products you are currently tracking/*')

    product_count = 1

    for product in products_in_order:
        if (product != False):
            # Split at end because the full line on file is in the product variable (PRODUCT_NAME=...)
            await channel.send('Product ' + str(product_count) + " - " + (product.split("=",1))[1])
        else:
            await channel.send('Product ' + str(product_count) + " - " + "Nothing!")
            are_products_full = True
        product_count += 1

    if (are_products_full):
        await channel.send('|Add Product| - Add a new product to track')
        await channel.send('|Delete Product| - Delete a product listed')
        # Update status
        await store_data([member, 2, None, "SETTINGS_PRODUCTS_MAIN_NOTFULL"])
    else:
        await channel.send('|Delete Product| - Delete a product listed')
        # Update status
        await store_data([member, 2, None, "SETTINGS_PRODUCTS_MAIN_FULL"])

    await channel.send('|Back| - Go back to main settings menu')
    await channel.send('To select a specific product to change settings for from the list, please type "Product-" (without quotations) followed by the number listed (e.g. "Product-1" (without quotations)).')
    await channel.send('*Page loaded*')

# Method to print specific product settings to a given user
async def print_specific_product_settings(member, channel, message, data_content):

    # Update user status back to product specific settings page
    # await store_data([member, 2, None, data_content[2][:-11]]) -- NOT IN USE AS THIS CAUSES THE PROGRAM TO FAIL

    # Check if the product exists in their files
    # Get all products the user is tracking
    product_list = await product_dealer.retrieve_product_list(member)

    # To check if the actual product file exists in the user's file
    products_in_order = [False, False, False, False, False]

    # Place product names in a new list that are in order
    for product in product_list:
        if int(product[0]) == 1:
            products_in_order[0] = product[1]
        elif int(product[0]) == 2:
            products_in_order[1] = product[1]
        elif int(product[0]) == 3:
            products_in_order[2] = product[1]
        elif int(product[0]) == 4:
            products_in_order[3] = product[1]
        elif int(product[0]) == 5:
            products_in_order[4] = product[1]

    # Get the id of the product from the user's message

    requested_product_number = None

    try:
        requested_product_number = int(message.content[8:])
    except:
        # This try except is here because sometimes, the user may back out of changing a specific store setting in a products settings
        if ("STORE_SETUP" in data_content[2]):
            requested_product_number = int(data_content[2][25:-11])
        elif ("STORE_CHANGE" in data_content[2]):
            requested_product_number = int(data_content[2][25:-12])

    if (requested_product_number != None):
        # Check if the requested product exists in the user's save file
        if (products_in_order[requested_product_number - 1] == False):

            await channel.send('The product number you requested does not exist. Please choose an existing product number or if you wish, select a different setting option.')
        else:

            await store_data([member, 2, None, "SETTINGS_PRODUCTS_PRODUCT" + str(requested_product_number)])

            # If it does, get all settings for that product
            product_settings_get = await product_dealer.retrieve_product_settings(member, str(requested_product_number))

            # Print messages to user
            await channel.send('**//Product ' + str(requested_product_number) + ' Settings//**')

            for setting in product_settings_get:
                await channel.send('**' + setting[0] + " =** " + setting[1])

            await channel.send('|Back| - Go back to main product settings menu')
            await channel.send('*Page loaded*')


print("Hello world!")
print("StockBot V0.93B, developed by Davis Lenover, 2021-2022")

print("Checking for save data in files...")

# Check to see if all saved data is present
if (path.isfile(full_dir + '/ignored_users.txt')):
    if (path.isfile(full_dir + '/supported_websites.txt')):
        print("Data has been located!")
            
# If not, create the files       
else:
    print("Save Data does not exist! Preforming file setup...")
    os.makedirs(full_dir)
    file = open(full_dir + "/supported_websites.txt", "a")
    file.close()
    ignored_user_file = open(full_dir + "/ignored_users.txt", "a")
    ignored_user_file.write("840034854959054888" + "\n")
    ignored_user_file.close()
    new_dir_path = (full_dir + "/users")
    os.mkdir(new_dir_path)
    print("Complete! Please fill out admin files generated, then, re-run this script.")
    exit()


print("Retrieving auth token...")
AUTH_TOKEN = str(redis_server.get('AUTH_TOKEN'))
print("Logging into Discord...")

@client.event 
async def on_ready():
    print(f'Bot is now active! {client.user}')
    # Start stock tracking
    run_checks.start()
    
        
@client.event
async def on_member_join(member):
    # When a new user joins the server, they will be put into their own private channel with the bot
    # It is where they will receive stock updates as well as be able to communicate with the bot

    # Get the name of the user who joined
    member_name = str(member)

    # Call methods to setup file storage for the user for the bots reference
    await handle_new_users(member)

    # Setup channel permissions to be applied
    # Default role - No one can see this channel
    # Bot can read and send messages
    overwrites = {
    client.guilds[0].default_role: discord.PermissionOverwrite(read_messages=False),
    client.guilds[0].me: discord.PermissionOverwrite(read_messages=True)
}

    # Create the text channel and apply the permissions above
    channel = await client.guilds[0].create_text_channel("channel-" + member_name, overwrites=overwrites)

    # Store the users channel id in their corresponding file
    # Double-check to see if the user had changed their name during this process
    check = (await store_data([member, 1, channel.id]))
    if (check != True):
        member_name = check
        # If they did, the channel name needs to be updated
        await channel.edit(name=("channel-" + member_name))
        # Preform data store again
        await store_data([member, 1, channel.id])



    # Finally, create permissions for the member to see and send messages in the channel
    overwrite = discord.PermissionOverwrite()
    overwrite.send_messages = True
    overwrite.read_messages = True

    # Apply the permissions
    await channel.set_permissions(member, overwrite=overwrite)

    # Mentioning feature in discord as placeholder
    ping = member.mention

    # Have bot start sending messages inside the channel
    await channel.send(f'Hi {ping}! I am StockBot. I will be watching the stock for a product of your choice on a supported website for you!')
    await channel.send('This is your own text channel. It is where you will communicate with me and recive alerts for stock updates.')
    await channel.send('Please note that as we go through setup I will be storing your responses. Not only is this required to make sure I can assist you, it also provides analytics that Dpikachu1 can use to improve me. If you have any concerns, please visit the Q&A channel in this discord server.')
    await channel.send('If you want to proceed, please type and send the word "ready" (without quotations) in this channel.')

@client.event
async def on_member_remove(member):
    # A user has left
    # Remove their channel and files

    # First, go into their files and find their channel ID
    channel_id = await get_data(member,4)

    # Convert to channel object
    channel = client.get_channel(int(channel_id))

    # Delete the channel
    await channel.delete()

    # Remove all files on them
    shutil.rmtree(user_storage_path + "/" + str(member.id))


@client.event
async def on_message(message):

    # Get author (member) of message
    member = message.author
    member_id = str(member.id)
    channel_id = message.channel.id
    channel = message.channel

    # Check for ignored users
    ignored_users = None
    if (path.exists(full_dir + "/ignored_users.txt")):
        ignored_user_file = open(full_dir + "/ignored_users.txt", "r")
        ignored_users = ignored_user_file.readlines()
        ignored_user_file.close()

    ignore = False

    # Admin command to shutdown the bot
    if (message.content.startswith("close")):
        print("Test-close!")
        if (member.guild_permissions.administrator):

            # Close Bot
            await client.close()

            print("Bot has logged off. Shuting down...")
            try:
                await sys.exit()
            except:
                pass

    if (ignored_users != None):

        # Check for ignored users
        # If there is, set boolean to True to stop the member from being added to the new user file (pretending like it already exists in the save data)
        for ignored in ignored_users:
            if ((member_id) == ignored.strip()):
                ignore = True
                break

    current_user_file_path = None

    if (not ignore):
        # For loop through user save data to find the data stored on the user
        for folder in os.listdir(user_storage_path):
            if folder == member_id:
                current_user_file_path = (user_storage_path + "/" + folder)
                break

        if (current_user_file_path != None):

            # Get all data regarding the member who sent the chat message
            data_content = await get_data(member,8)

            # Check if data_content just contains True
            # If this occurs, this means a members name was changed and was different to the one on-file
            # While the file has been updated, the channel needs to be
            if (data_content == True):
                await channel.edit(name=("channel-" + str(member)))
                # Now we can re-get data_content
                data_content = await get_data(member, 8)

            # Back functionality (for settings)
            if (message.content == "Back"):

                # As a secondary precaution, check to make sure the channel the message sent though matches
                if (int(data_content[3]) == channel_id):

                    # Check the current status of the user and update accordingly
                    if ("DELETE" in data_content[2]):

                        # Call method to print last settings
                        await channel.send('You have exited the delete product module!')
                        await print_products_main(member, channel)

                    
                    if (data_content[2] == "SETTINGS_MAIN"):

                        # Exit the user out of settings by updating their status
                        await store_data([member, 2, None, "WATCH_LINK"])
                        await channel.send('You have exited settings. Active tracking will now resume (assuming a setting for it is enabled).')

                    elif (data_content[2] == "SETTINGS_PRODUCTS_MAIN_NOTFULL" or data_content[2] == "SETTINGS_PRODUCTS_MAIN_FULL"):

                        # Move back to main settings menu
                        await print_main_setting(member, channel)

                    elif (data_content[2] == "SETTINGS_PRODUCTS_PRODUCT1" or data_content[2] == "SETTINGS_PRODUCTS_PRODUCT2" or data_content[2] == "SETTINGS_PRODUCTS_PRODUCT3" or data_content[2] == "SETTINGS_PRODUCTS_PRODUCT4" or data_content[2] == "SETTINGS_PRODUCTS_PRODUCT5"):

                        await print_products_main(member, channel)

                    elif ("STORE_SETUP" in data_content[2]):

                        # Call method to print last settings
                        await channel.send('You have exited the store settings module!')
                        await print_specific_product_settings(member, channel, message, data_content)


                    elif ("STORE_CHANGE" in data_content[2]):

                        # Call method to print last settings
                        await channel.send('You have exited the store settings module!')
                        await print_specific_product_settings(member, channel, message, data_content)


                    if (("LINK_WAIT" in data_content[2]) or ("USER_LINK_WAIT" in data_content[2])):

                        # Check if the user is a new user by checking their user data file
                        if (data_content[7] == "False"):

                            # Call method to print last settings
                            await channel.send('You have exited the adding product module!')
                            await print_products_main(member, channel)


            # Check status to determine what the bot is looking for in a response

            # Check if the bot was waiting on an initial response
            if (data_content[2] == "MSG_WAIT"):

                # As a secondary precaution, check to make sure the channel the message sent though matches
                if (int(data_content[3]) == channel_id):
                    # Check if the user inputted the correct response
                    if (message.content == "ready"):
                        # If they did, update their status on file
                        await store_data([member, 2, None, "LINK_WAIT"])

                        # Get the list of supported websites
                        supported_sites_file = open(full_dir + "/supported_websites.txt", "r")
                        supported_sites_list = supported_sites_file.readlines()
                        supported_sites_file.close()

                        sites_text = ""

                        # Combine the site list into one string
                        for site in supported_sites_list:
                            sites_text += site.strip() + " | "
                        
                        await channel.send('Great! Please paste and send the link to the product you would like to track in this channel.')
                        
                        await channel.send(f'I currently support: **{sites_text}**')
                        await channel.send('*Page loaded*')

            # Check if the bot was waiting on a link response from the user
            if ("LINK_WAIT" in data_content[2]):
                
                # As a secondary precaution, check to make sure the channel the message sent though matches
                if (int(data_content[3]) == channel_id):

                    # Newegg

                    # Check if a newegg link was sent
                    if ("newegg.ca" in message.content):

                        await channel.send('Newegg link detected! Please wait while I attempt to retrieve the product information...')

                        # Get product info from the link
                        product = await newegg.get_product_info(message.content)

                        # Error checking
                        if (product != False):

                            is_combo = False
                            stock_status = None

                            # Check if the product is in stock based on the list sent back from the newegg get product method
                            if (product[0][0] == 1):
                                stock_status = "In Stock"
                                if (product[0][1] == True):
                                    is_combo = True
                            elif (product[0][0] == 2):
                                stock_status = "Out of Stock"
                                if (product[0][1] == True):
                                    is_combo = True
                            elif (product[0][0] == 3):
                                stock_status = "On Backorder"
                                if (product[0][1] == True):
                                    is_combo = True
                            elif (product[0][0] == 4):
                                stock_status = "Preorder"
                                if (product[0][1] == True):
                                    is_combo = True

                            # Check if the user was in settings and is adding a new product
                            if (("SETTINGS_PRODUCTS_MAIN_NOTFULL" in data_content[2]) or ("SETTINGS_PRODUCTS_MAIN_FULL" in data_content[2])):

                                if ("SETTINGS_PRODUCTS_MAIN_NOTFULL" in data_content[2]):
                                    await store_data([member, 2, None, "SETTINGS_PRODUCTS_MAIN_NOTFULLUSER_LINK_WAIT"])

                                elif ("SETTINGS_PRODUCTS_MAIN_FULL" in data_content[2]):
                                    await store_data([member, 2, None, "SETTINGS_PRODUCTS_MAIN_FULLUSER_LINK_WAIT"])

                            else:
                                await store_data([member, 2, None, "USER_LINK_WAIT"])

                            if (is_combo):
                                await store_data([member, 4, None, None, "Newegg-Combo"])
                            else:
                                await store_data([member, 4, None, None, "Newegg"])
                            await store_data([member, 5, None, None, None, message.content])
                            await store_data([member, 6, None, None, None, None, product[1]])
                            
                            await channel.send('Thank you for waiting! Here is what I found: ')
                            
                            # Display found product info to the user
                            await channel.send(f'**Product Name:** {product[1]} | **Product Price:** {product[2]} | **Is a combo?:** {is_combo} | **Product Stock Status:** {stock_status}')
                            await channel.send('Please verify that this information is correct. If it is, type and send the word "yes" (without quotations) in this channel. If not, type and send the word "no" (without quotations) in this channel.')
                            await channel.send('*Page loaded*')

                        else:
                            await channel.send('Thank you for waiting! It seems that I could not retrieve product information. Please double-check the product link and retry sending it in this channel.')
                            await channel.send('If the issue persists, please contact an administrator.')
                            await channel.send('*Page loaded*')


                    # Amazon (as stated in other scripts, amazon is slightly different in how it's script functions)
                    # Check if a amazon link was sent
                    elif ("amazon.ca" in message.content):

                        await channel.send('Amazon link detected! Please wait while I attempt to retrieve the product information...')

                        # Get product info from the link
                        soup = await amazon.get_soup(message.content)
                        product = await amazon.get_product_info(soup, True, True)

                        # Error checking
                        if (product != False and product[2] != False and product[1] != 3):

                            stock_status = None

                            # Check if the product is in stock based on the list sent back from the bestbuy get product method
                            if (product[1] == 1):
                                stock_status = "In Stock"
                            elif (product[1] == 2):
                                stock_status = "Out of Stock"
                            elif (product[1] == 4):
                                stock_status = "Product currently unavailable from amazon.ca as seller"
                            elif (product[1] == 5):
                                stock_status = "Preorder"
                            elif (product[1] == 6):
                                stock_status = "Backorder"

                            # Check if the user was in settings and is adding a new product
                            if (("SETTINGS_PRODUCTS_MAIN_NOTFULL" in data_content[2]) or ("SETTINGS_PRODUCTS_MAIN_FULL" in data_content[2])):

                                if ("SETTINGS_PRODUCTS_MAIN_NOTFULL" in data_content[2]):
                                    await store_data([member, 2, None, "SETTINGS_PRODUCTS_MAIN_NOTFULLUSER_LINK_WAIT"])

                                elif ("SETTINGS_PRODUCTS_MAIN_FULL" in data_content[2]):
                                    await store_data([member, 2, None, "SETTINGS_PRODUCTS_MAIN_FULLUSER_LINK_WAIT"])

                            else:
                                await store_data([member, 2, None, "USER_LINK_WAIT"])

                            await store_data([member, 4, None, None, "Amazon"])
                            await store_data([member, 5, None, None, None, message.content])
                            await store_data([member, 6, None, None, None, None, product[0]])

                            await channel.send('Thank you for waiting! Here is what I found: ')

                            # Display found product info to the user
                            await channel.send(f'**Product Name:** {product[0]} | **Product Price:** {product[2]} | **Product Stock Status:** {stock_status}')
                            if (product[1] == 4):
                                await channel.send('*Please make sure that amazon.ca is a merchant for this listing, otherwise I will never show this product is in-stock*')
                            await channel.send('Please verify that this information is correct. If it is, type and send the word "yes" (without quotations) in this channel. If not, type and send the word "no" (without quotations) in this channel.')
                            await channel.send('*Page loaded*')

                        else:
                            await channel.send('Thank you for waiting! It seems that I could not retrieve product information. Please double-check the product link and retry sending it in this channel.')
                            await channel.send('If the issue persists, please contact an administrator.')
                            await channel.send('*Page loaded*')

                    # Best Buy

                    # Check if a bestbuy link was sent
                    elif ("bestbuy.ca" in message.content):

                        await channel.send('Best Buy link detected! Please wait while I attempt to retrieve the product information...')

                        # Get product info from the link
                        product = await bestbuy.get_product_info(message.content)

                        # Error checking
                        if (product != False):

                            stock_status = None

                            # Check if the product is in stock based on the list sent back from the bestbuy get product method
                            if (product[0] == 1):
                                stock_status = "In Stock"
                            elif (product[0] == 2):
                                stock_status = "Out of Stock"
                            elif (product[0] == 3):
                                stock_status = "On Backorder"
                            elif (product[0] == 4):
                                stock_status = "Available to preorder"
                            elif (product[0] == 5):
                                stock_status = "In Stock - Scheduled Delivery"
                            elif (product[0] == 6):
                                stock_status = "Coming soon"
                            elif (product[0] == 7):
                                stock_status = "Available Online Only"

                            # Check if the user was in settings and is adding a new product
                            if (("SETTINGS_PRODUCTS_MAIN_NOTFULL" in data_content[2]) or ("SETTINGS_PRODUCTS_MAIN_FULL" in data_content[2])):

                                if ("SETTINGS_PRODUCTS_MAIN_NOTFULL" in data_content[2]):
                                    await store_data([member, 2, None, "SETTINGS_PRODUCTS_MAIN_NOTFULLUSER_LINK_WAIT"])

                                elif ("SETTINGS_PRODUCTS_MAIN_FULL" in data_content[2]):
                                    await store_data([member, 2, None, "SETTINGS_PRODUCTS_MAIN_FULLUSER_LINK_WAIT"])

                            else:
                                await store_data([member, 2, None, "USER_LINK_WAIT"])

                            await store_data([member, 4, None, None, "BestBuy"])
                            await store_data([member, 5, None, None, None, message.content])
                            await store_data([member, 6, None, None, None, None, product[1]])

                            await channel.send('Thank you for waiting! Here is what I found: ')

                            # Display found product info to the user
                            await channel.send(f'**Product Name:** {product[1]} | **Product Price:** {product[2]} | **Product Stock Status:** {stock_status}')
                            await channel.send('Please verify that this information is correct. If it is, type and send the word "yes" (without quotations) in this channel. If not, type and send the word "no" (without quotations) in this channel.')
                            await channel.send('*Page loaded*')

                        else:
                            await channel.send('Thank you for waiting! It seems that I could not retrieve product information. Please double-check the product link and retry sending it in this channel.')
                            await channel.send('If the issue persists, please contact an administrator.')
                            await channel.send('*Page loaded*')


                    # CanadaComputers

                    # Check if a CanadaComputers link was sent
                    elif ("canadacomputers.com" in message.content):

                        await channel.send('CanadaComputers link detected! Please wait while I attempt to retrieve the product information...')

                        # Get product info from the link
                        product = await canadacomputers.get_product_info(message.content)

                        # Error checking
                        if (product != False):

                            stock_status = None

                            # Check if the product is in stock based on the list sent back from the bestbuy get product method
                            if (product[0][0] == 1):
                                stock_status = "In Stock"
                            elif (product[0][0] == 2):
                                stock_status = "Out of Stock"
                            elif (product[0][0] == 3):
                                stock_status = "Special Order"
                            elif (product[0][0] == 4):
                                stock_status = "Available for Pickup"

                            # Check if the user was in settings and is adding a new product
                            if (("SETTINGS_PRODUCTS_MAIN_NOTFULL" in data_content[2]) or ("SETTINGS_PRODUCTS_MAIN_FULL" in data_content[2])):

                                if ("SETTINGS_PRODUCTS_MAIN_NOTFULL" in data_content[2]):
                                    await store_data([member, 2, None, "SETTINGS_PRODUCTS_MAIN_NOTFULLUSER_LINK_WAIT"])

                                elif ("SETTINGS_PRODUCTS_MAIN_FULL" in data_content[2]):
                                    await store_data([member, 2, None, "SETTINGS_PRODUCTS_MAIN_FULLUSER_LINK_WAIT"])

                            else:
                                await store_data([member, 2, None, "USER_LINK_WAIT"])

                            await store_data([member, 4, None, None, "CanadaComputers"])
                            await store_data([member, 5, None, None, None, message.content])
                            await store_data([member, 6, None, None, None, None, product[1]])

                            await channel.send('Thank you for waiting! Here is what I found: ')

                            # Display found product info to the user
                            await channel.send(f'**Product Name:** {product[1]} | **Product Price:** {product[2]} | **Product Stock Status:** {stock_status}')
                            await channel.send('Please verify that this information is correct. If it is, type and send the word "yes" (without quotations) in this channel. If not, type and send the word "no" (without quotations) in this channel.')
                            await channel.send('*Page loaded*')

                        else:
                            await channel.send('Thank you for waiting! It seems that I could not retrieve product information. Please double-check the product link and retry sending it in this channel.')
                            await channel.send('If the issue persists, please contact an administrator.')
                            await channel.send('*Page loaded*')


                    # MemoryExpress

                    # Check if a MemoryExpress link was sent
                    elif ("memoryexpress.com" in message.content):

                        await channel.send('MemoryExpress link detected! Please wait while I attempt to retrieve the product information...')

                        # Get product info from the link
                        product = await memoryexpress.get_product_info(message.content)

                        # Error checking
                        if (product != False):

                            stock_status = None

                            # Check if the product is in stock based on the list sent back from the bestbuy get product method
                            if (product[0][0] == 1):
                                stock_status = "In Stock"
                            elif (product[0][0] == 2):
                                stock_status = "Out of Stock"
                            elif (product[0][0] == 3):
                                stock_status = "Special Order"
                            elif (product[0][0] == 4):
                                stock_status = "Backorder"
                            elif (product[0][0] == 5):
                                stock_status = "Online Store Out of Stock"
                            elif (product[0][0] == 6):
                                stock_status = "Preorder"

                            # Check if the user was in settings and is adding a new product
                            if (("SETTINGS_PRODUCTS_MAIN_NOTFULL" in data_content[2]) or ("SETTINGS_PRODUCTS_MAIN_FULL" in data_content[2])):

                                if ("SETTINGS_PRODUCTS_MAIN_NOTFULL" in data_content[2]):
                                    await store_data([member, 2, None, "SETTINGS_PRODUCTS_MAIN_NOTFULLUSER_LINK_WAIT"])

                                elif ("SETTINGS_PRODUCTS_MAIN_FULL" in data_content[2]):
                                    await store_data([member, 2, None, "SETTINGS_PRODUCTS_MAIN_FULLUSER_LINK_WAIT"])

                            else:
                                await store_data([member, 2, None, "USER_LINK_WAIT"])

                            await store_data([member, 4, None, None, "MemoryExpress"])
                            await store_data([member, 5, None, None, None, message.content])
                            await store_data([member, 6, None, None, None, None, product[1]])

                            await channel.send('Thank you for waiting! Here is what I found: ')

                            # Display found product info to the user
                            await channel.send(f'**Product Name:** {product[1]} | **Product Price:** {product[2]} | **Product Stock Status:** {stock_status}')
                            await channel.send('Please verify that this information is correct. If it is, type and send the word "yes" (without quotations) in this channel. If not, type and send the word "no" (without quotations) in this channel.')
                            await channel.send('*Page loaded*')

                        else:
                            await channel.send('Thank you for waiting! It seems that I could not retrieve product information. Please double-check the product link and retry sending it in this channel.')
                            await channel.send('If the issue persists, please contact an administrator.')
                            await channel.send('*Page loaded*')

            # Check if the bot was waiting on confirmation from the user that the information found from the link is correct
            if ("USER_LINK_WAIT" in data_content[2]):
                    
                # As a secondary precaution, check to make sure the channel the message sent though matches
                if (int(data_content[3]) == channel_id):

                    # If the user types yes...
                    if (message.content == "yes"):

                        # Setup is complete

                        # Get temp product data and put it in it's own file
                        website_type = await get_data(member,5)
                        product_link = await get_data(member,6)
                        product_name = await get_data(member, 7)
                        product_data = [member,website_type,product_link,product_name]

                        # Check to make sure the function returned True (to tell if the user has reached the maximum amount of products to be tracked)
                        if (await product_dealer.store_product(product_data) != False):
                            # Update user status

                            # Check if the user was in settings and is adding a new product
                            if ((not("SETTINGS_PRODUCTS_MAIN_NOTFULL" in data_content[2])) and (not("SETTINGS_PRODUCTS_MAIN_FULL" in data_content[2]))):
                                await store_data([member, 2, None, "WATCH_LINK"])
                                await channel.send('Perfect! I will notify you in this channel if the product is in-stock or is available for backorder.')
                                await channel.send('If you would like to change notification preferences (or rather any setting), please type and send the message "Settings" in this channel (without quotations).')
                                await channel.send('Thank you!')
                                await channel.send('*Page loaded*')

                            # Go back to specific settings page
                            elif ("SETTINGS_PRODUCTS_MAIN_NOTFULL" in data_content[2]):
                                await channel.send('Perfect! I will notify you in this channel if the product is in-stock or is available for backorder.')
                                await channel.send('If you would like to change notification preferences (or rather any setting), please type and send the message "Settings" in this channel (without quotations).')
                                await channel.send('Thank you!')
                                await print_products_main(member, channel)

                            elif ("SETTINGS_PRODUCTS_MAIN_FULL" in data_content[2]):
                                await channel.send('Perfect! I will notify you in this channel if the product is in-stock or is available for backorder.')
                                await channel.send('If you would like to change notification preferences (or rather any setting), please type and send the message "Settings" in this channel (without quotations).')
                                await channel.send('Thank you!')
                                await print_products_main(member, channel)


                        else:
                            # If products were full, just update the user status to watch link
                            # There is no message call here and it's probably impossible for someone with full products to get here as there is a check way before this!
                            # This just covers up in-case a user somehow gets this far
                            await store_data([member, 2, None, "WATCH_LINK"])

                        # Check if the user is new
                        if (data_content[7] != "False"):
                            # If they were, set them to false now
                            await store_data([member,7])

                    # If not...  
                    elif (message.content == "no"):

                        # Update user status back to LINK_WAIT so the bot will wait for another link to try and get product info for
                        await store_data([member, 2, None, "LINK_WAIT"])
                        await channel.send('No worries! Please double-check the link and retry sending it in this channel.')
                        await channel.send('If this issue persists, please contact an administrator.')
                        await channel.send('*Page loaded*')

            # Settings specific commands

            # Check if the user was already setup
            if (data_content[2] == "WATCH_LINK"):

                # As a secondary precaution, check to make sure the channel the message sent though matches
                if (int(data_content[3]) == channel_id):

                    # If the user has typed settings...
                    if (message.content == "Settings"):

                        await print_main_setting(member, channel)

        # Check if the user was in settings main page
        if (data_content[2] == "SETTINGS_MAIN"):

            # As a secondary precaution, check to make sure the channel the message sent though matches
            if (int(data_content[3]) == channel_id):

                # If the user has typed product settings...
                if (message.content == "Products"):

                    await print_products_main(member, channel)


        # Check if the user was in the product settings main page
        if (data_content[2] == "SETTINGS_PRODUCTS_MAIN_NOTFULL" or data_content[2] == "SETTINGS_PRODUCTS_MAIN_FULL"):

            # As a secondary precaution, check to make sure the channel the message sent though matches
            if (int(data_content[3]) == channel_id):

                # If the user has typed a specific product settings...
                if (message.content == "Product-1" or message.content == "Product-2" or message.content == "Product-3" or message.content == "Product-4" or message.content == "Product-5"):

                    await print_specific_product_settings(member, channel, message, data_content)

                elif ("Product-" in message.content):
                    await channel.send('Unknown product number. Please choose an existing number from 1-5 (given the save exists).')

                # Delete a product
                elif (message.content == "Delete Product"):

                    await store_data([member, 2, None, data_content[2] + "DELETE"])
                    await channel.send('Please type and send the product number you would like to delete (e.g. for Product 2, you would type the number 2)')
                    await channel.send('Note that once you send the command, the action CANNOT be undone! In order to re-track the product, you must re-enter it as a new product save!')
                    await channel.send('If you do not want to delete anything, you can always type the word "Back" (without quotations) to exit the delete module')
                    await channel.send('*Page loaded*')

                # Add a product
                elif (message.content == "Add Product"):

                    # Return user to main product setting page
                    # Get all products the user is tracking
                    product_list = await product_dealer.retrieve_product_list(member)

                    products_in_order = [False, False, False, False, False]
                    are_products_full = False

                    # Place product names in a new list that are in order
                    for product in product_list:
                        if int(product[0]) == 1:
                            products_in_order[0] = product[1]
                        elif int(product[0]) == 2:
                            products_in_order[1] = product[1]
                        elif int(product[0]) == 3:
                            products_in_order[2] = product[1]
                        elif int(product[0]) == 4:
                            products_in_order[3] = product[1]
                        elif int(product[0]) == 5:
                            products_in_order[4] = product[1]

                    product_count = 1

                    for product in products_in_order:
                        if (product != False):
                            None
                        else:
                            are_products_full = True
                        product_count += 1

                    # If the users product saves are full...
                    if (not are_products_full):
                        await channel.send('Your product saves are full! Please delete a product first before adding a new one!')

                    else:

                        # If not, update user status in files and send according messages
                        await store_data([member, 2, None, data_content[2] + "LINK_WAIT"])
                        await channel.send('Please send the product link in this text channel!')

                        # Get the list of supported websites
                        supported_sites_file = open(full_dir + "/supported_websites.txt", "r")
                        supported_sites_list = supported_sites_file.readlines()
                        supported_sites_file.close()

                        sites_text = ""

                        # Combine the site list into one string
                        for site in supported_sites_list:
                            sites_text += site.strip() + " | "

                        await channel.send(f'I currently support: **{sites_text}**')
                        await channel.send('*Page loaded*')

        # Check if the user is going to delete a product
        if ("DELETE" in data_content[2]):

            # As a secondary precaution, check to make sure the channel the message sent though matches
            if (int(data_content[3]) == channel_id):

                # Check if the user was not trying to exit the delete module
                if (not ("Back" in message.content)):
                    try:
                        # Check if the product exists in their files
                        # Get all products the user is tracking
                        product_list = await product_dealer.retrieve_product_list(member)

                        # To check if the actual product file exists in the user's file
                        products_in_order = [False, False, False, False, False]

                        # Place product names in a new list that are in order
                        for product in product_list:
                            if int(product[0]) == 1:
                                products_in_order[0] = product[1]
                            elif int(product[0]) == 2:
                                products_in_order[1] = product[1]
                            elif int(product[0]) == 3:
                                products_in_order[2] = product[1]
                            elif int(product[0]) == 4:
                                products_in_order[3] = product[1]
                            elif int(product[0]) == 5:
                                products_in_order[4] = product[1]

                        # Get the id of the product from the user's message
                        requested_product_number = int(message.content)

                        # Check if the requested product exists in the user's save file
                        if (products_in_order[requested_product_number - 1] == False):
                            await channel.send('The product number you requested to delete does not exist. Please choose an existing product number.')
                        else:

                            # Delete the product
                            await product_dealer.product_settings(member,[8,requested_product_number])
                            await channel.send(f'Product-{requested_product_number} has been deleted!')

                            # Return user to main products list (setting)
                            await print_products_main(member, channel)

                    except:
                        await channel.send('An error occurred! Please make sure you typed the product save number correctly!')

        # Check if the user was going to edit a specific product setting
        if (data_content[2] == "SETTINGS_PRODUCTS_PRODUCT1" or data_content[2] == "SETTINGS_PRODUCTS_PRODUCT2" or data_content[2] == "SETTINGS_PRODUCTS_PRODUCT3" or data_content[2] == "SETTINGS_PRODUCTS_PRODUCT4" or data_content[2] == "SETTINGS_PRODUCTS_PRODUCT5"):

            # As a secondary precaution, check to make sure the channel the message sent though matches
            if (int(data_content[3]) == channel_id):

                # Used to determine if the bot will print an updated settings list
                to_print_settings_again = False

                # Used to determine if the user did not need to process some store related notification
                store_needs = False

                # Get product save number
                product_save_number = int(data_content[2][25])

                # Check if what the user entered was valid
                # Get product setting data
                settings_list = await product_dealer.retrieve_product_settings(member,str(product_save_number))

                # Check if the user wanted to enable or disable notifications for a specific store (rather than any store)
                if "NOTIFY_STORE_SPECIFIC" in message.content:

                    # For loop through the settings list to make sure the setting actually exists
                    for setting in settings_list:
                        if ("NOTIFY_STORE_SPECIFIC" in setting[0]):

                            # Check if setup will be needed
                            if ("False" in setting[1]):

                                if ("X" in settings_list[9][1]):
                                    # Setup will be needed
                                    await store_data([member, 2, None, data_content[2] + "STORE_SETUP"])
                                    await channel.send('Before I can enable specific store notifications, can you please provide me with the specific store name that you would like to track?')
                                    await channel.send('Please copy and paste the store name (case-sensitive) into this text channel')
                                    await channel.send('*Page loaded*')

                                else:
                                    await product_dealer.product_settings(member, [5, product_save_number])
                                    await channel.send('Specific store notifications have been re-enabled!')

                            elif ("True" in setting[1]):
                                await product_dealer.product_settings(member, [5, product_save_number])
                                await channel.send('Specific store notifications have been disabled! Please note that the specific store is still saved in the system.')

                            store_needs = True
                            break

                # Check if the user wanted to change their specific store name that they would like to receive notifications for
                elif "NOTIFY_STORE_NAME" in message.content:

                    # For loop through the settings list to make sure the setting actually exists
                    for setting in settings_list:

                        if ("NOTIFY_STORE_SPECIFIC" in setting[0]):

                            # Check if setup will be needed
                            if ("False" in setting[1]):

                                if ("X" in settings_list[9][1]):

                                    # Setup will be needed
                                    # First time setup will automatically enable specific store notifications
                                    # Update user status
                                    await store_data([member, 2, None, data_content[2] + "STORE_SETUP"])
                                    await channel.send('Please copy and paste the store name (case-sensitive) into this text channel')

                                    store_needs = True
                                    break

                            elif ("True" in setting[1]):

                                # Update user status
                                await store_data([member, 2, None, data_content[2] + "STORE_CHANGE"])
                                await channel.send('Please copy and paste the store name (case-sensitive) into this text channel')

                                store_needs = True
                                break

                # Check if user wanted to change store notifications
                elif ("NOTIFY_STORE" in message.content):

                    # For loop through the settings list to make sure the setting actually exists
                    for setting in settings_list:

                        if ("NOTIFY_STORE" in setting[0] and (not ("NOTIFY_STORE_SPECIFIC" in setting[0])) and (not ("NOTIFY_STORE_NAME" in setting[0]))):

                            await product_dealer.product_settings(member, [4, product_save_number])

                            # Check if the setting was true or false

                            if ("True" in setting[1]):
                                await channel.send('Store notifications has been set to False. Please note that this also stops any specific store notifications from appearing!')
                            elif ("False" in setting[1]):
                                await channel.send('Store notifications has been set to True. Please note that this also allows any specific store notifications to appear (if NOTIFY_STORE_SPECIFIC is set to True)!')

                            to_print_settings_again = True
                            store_needs = True

                            break


                if (not store_needs):
                    for setting in settings_list:
                        if (message.content == setting[0]):
                            if message.content == "NOTIFY_DISABLE":

                                # Update product setting
                                await product_dealer.product_settings(member,[7, product_save_number])

                                # Send correct message in text channel
                                if "True" in setting[1]:
                                    await channel.send('NOTIFY_DISABLE has been set to False! Notifications will appear for this product.')

                                if "False" in setting[1]:
                                    await channel.send('NOTIFY_DISABLE has been set to True! Notifications will not appear (of any kind) for this product.')

                            elif message.content == "NOTIFY_BACKORDER":

                                # Update product setting
                                await product_dealer.product_settings(member, [1, product_save_number])

                                # Send correct message in text channel
                                if "True" in setting[1]:
                                    await channel.send('NOTIFY_BACKORDER has been set to False! Notifications for backorders will not appear for this product.')

                                if "False" in setting[1]:
                                    await channel.send('NOTIFY_BACKORDER has been set to True! Notifications for backorders will appear for this product.')

                            elif message.content == "NOTIFY_PREORDER":

                                # Update product setting
                                await product_dealer.product_settings(member, [2, product_save_number])

                                # Send correct message in text channel
                                if "True" in setting[1]:
                                    await channel.send('NOTIFY_PREORDER has been set to False! Notifications for preorders will not appear for this product.')

                                if "False" in setting[1]:
                                    await channel.send('NOTIFY_PREORDER has been set to True! Notifications for preorders will appear for this product.')

                            elif message.content == "NOTIFY_PRICE":

                                # Update product setting
                                await product_dealer.product_settings(member, [3, product_save_number])

                                # Send correct message in text channel
                                if "True" in setting[1]:
                                    await channel.send('NOTIFY_PRICE has been set to False! Notifications for price changes will not appear for this product.')

                                if "False" in setting[1]:
                                    await channel.send('NOTIFY_PRICE has been set to True! Notifications for price changes will appear for this product.')

                            to_print_settings_again = True
                            break


                if (to_print_settings_again):
                    # Send updated product settings
                    product_settings_new = await product_dealer.retrieve_product_settings(member, str(product_save_number))

                    # Print messages to user
                    await channel.send('**//Product ' + str(product_save_number) + ' Settings//**')

                    for setting in product_settings_new:
                        await channel.send('**' + setting[0] + " =** " + setting[1])

                    await channel.send('|Back| - Go back to main product settings menu')
                    await channel.send('*Page loaded*')

        # Check if the user was going to enter in a specific store name (this also sets NOTIFY_STORE_SPECIFIC to True in files)
        if ("STORE_SETUP" in data_content[2]):

            # As a secondary precaution, check to make sure the channel the message sent though matches
            if (int(data_content[3]) == channel_id):

                # Make sure the user did not want to exit this module
                if (not ("Back" in message.content)):

                    # Get product save number
                    product_save_number = int(data_content[2][25])

                    # Check if what the user entered was valid
                    # Get product setting data
                    settings_list = await product_dealer.retrieve_product_settings(member,str(product_save_number))

                    is_store_valid = False

                    # Check if the store name exists in the corresponding script
                    # And if so, update the users product file and status accordingly

                    # MemoryExpress

                    if ("MemoryExpress" in settings_list[0][1]):

                        if (await does_store_exist(2,message.content)):
                            await product_dealer.product_settings(member, [5, product_save_number])
                            await product_dealer.product_settings(member, [6, product_save_number, message.content])
                            is_store_valid = True

                    # CanadaComputers

                    elif ("CanadaComputers" in settings_list[0][1]):

                        if (await does_store_exist(1,message.content)):
                            await product_dealer.product_settings(member, [5, product_save_number])
                            await product_dealer.product_settings(member, [6, product_save_number, message.content])
                            is_store_valid = True

                    if (is_store_valid):

                        # Update user status back to product specific settings page
                        await store_data([member, 2, None, data_content[2][:-11]])

                        # Send message confirming
                        await channel.send(f'The store, {message.content}, will be tracked!')
                        await channel.send(f'By default, NOTIFY_STORE_SPECIFIC has been automatically set to True.')

                    else:
                        await channel.send('Hmmm..., I cannot seem to recognize that store name, please double-check that it is spelt exactly as is on the main website and try again!')


        # Check if the user was going to change their specific store name
        if ("STORE_CHANGE" in data_content[2]):

            # As a secondary precaution, check to make sure the channel the message sent though matches
            if (int(data_content[3]) == channel_id):

                # Make sure the user did not want to exit this module
                if (not ("Back" in message.content)):

                    # Get product save number
                    product_save_number = int(data_content[2][25])

                    # Check if what the user entered was valid
                    # Get product setting data
                    settings_list = await product_dealer.retrieve_product_settings(member, str(product_save_number))

                    is_store_valid = False


                    # Check if the store name exists in the corresponding script
                    # And if so, update the users product file and status accordingly

                    # MemoryExpress

                    if ("MemoryExpress" in settings_list[0][1]):

                        if (await does_store_exist(2,message.content)):
                            await product_dealer.product_settings(member, [6, product_save_number, message.content])
                            is_store_valid = True

                    # CanadaComputers

                    elif ("CanadaComputers" in settings_list[0][1]):

                        if (await does_store_exist(1,message.content)):
                            await product_dealer.product_settings(member, [6, product_save_number, message.content])
                            is_store_valid = True

                    if (is_store_valid):

                        # Update user status back to product specific settings page
                        await store_data([member, 2, None, data_content[2][:-12]])

                        # Send message confirming
                        await channel.send(f'The store, {message.content}, will be tracked!')

                    else:
                        await channel.send('Hmmm..., I cannot seem to recognize that store name, please double-check that it is spelt exactly as is on the main website and try again!')

                # TODO Fix how user settings looks -- IN PROGRESS!!
                # TODO Continue to debug stock_tracker and bot -- IN PROGRESS!!
                # TODO Add admin commands
                # TODO Cleanup!

# Tasks to check stock and (potentially) notify users of a stock change every x seconds
@tasks.loop(seconds=random.randrange(minWait, maxWait))
async def run_checks():
    # When ran, change the interval at which the next loop will execute
    run_checks.change_interval(seconds=random.randrange(minWait, maxWait))
    await stock_tracker.run_check(client)

# Discord login
client.run(AUTH_TOKEN[2:-1]) # Pull Auth Token from above
