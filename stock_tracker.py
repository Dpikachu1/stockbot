import asyncio
import shutil
import os.path
from os import path
import datetime
import pickle

import product_dealer

# Website scripts
import bestbuy
import canadacomputers
import memoryexpress
import newegg
import amazon

# Get working directory of python script
working_directory = os.getcwd()
# Add a directory userData
full_dir = (working_directory + "/userData")

# Directory for where all users are stored
user_storage_path = (full_dir + "/users")

async def run_check(client):

    # For loop through each directory (titled with the users id)
    for user in os.listdir(user_storage_path):

        # Go through the users products
        # Get the link for the product
        member_path = (user_storage_path + "/" + user)
        products_path = (member_path + "/" + "product_data")

        member_file = open(member_path + "/user_data.txt", "r")
        data_contents = member_file.readlines()
        member_file.close()

        # Check if the users status is not currently correct
        if ((data_contents[2][7:-1]) != "WATCH_LINK"):

            # If this statement is true, skip this user and move onto the next one
            # continue skips the current iteration of the for loop
            continue

        channel_string = (data_contents[3][11:-1])

        channel = client.get_channel(int(channel_string))

        user = client.get_user(int(user))

        # Go through all products and open their settings
        for product in os.listdir(products_path):

            # Get specific product path
            product_path = (products_path + "/" + product)

            product_number = int(product[8:])

            product_data = await product_dealer.retrieve_product_settings(user, product_number)

            # Check if notifications are enabled (NOTIFY_DISABLE is set to False)
            if (product_data[3][1] == "False"):

                # Check website type and call the according script to check the stock of said item
                if (product_data[0][1] == "Newegg" or product_data[0][1] == "Newegg-Combo"):

                    # Get beautifulSoup object
                    soup = await newegg.get_soup(product_data[1][1])

                    # From object, get the stock status
                    stock_status = await newegg.get_stock_status(soup)

                    if (stock_status != False):

                        # Check if the users stock history file exists
                        if (await does_stock_file_exist(1, product_path)):

                            # If it does, open the file and read all lines
                            general_stock_file = open(product_path + "/stock_history.pkl", "rb")

                            # Pickle load to grab list from file
                            stock_history = pickle.load(general_stock_file)

                            general_stock_file.close()

                            # Check if the last item in the file stock status differs from the one just checked
                            if (int(stock_history[-1][0]) != stock_status[0]):

                                # If it does, that means the stock has changed from the last check

                                # Append the new status and a timestamp to the list gathered from the file previously
                                stock_history.append([(stock_status[0]), str(datetime.datetime.now())])

                                # Open the same file again, however, in write mode, erasing everything in it
                                stock_file = open(product_path + "/stock_history.pkl", "wb")

                                # Write new list to file
                                pickle.dump(stock_history, stock_file)

                                stock_file.close()

                        else:
                            # If the file does not exist, create a blank list
                            stock_history = []

                            # Append the new status and a timestamp to the list gathered from the file previously
                            stock_history.append([(stock_status[0]), str(datetime.datetime.now())])

                            # Open the same file again, however, in write mode, erasing everything in it
                            stock_file = open(product_path + "/stock_history.pkl", "wb")

                            pickle.dump(stock_history, stock_file)

                            stock_file.close()

                    # Check price (if required)
                    if (product_data[6][1] != "False"):

                        current_price = None

                        # Check if the users price history file exists
                        if (await does_stock_file_exist(2, product_path)):

                            # Check if the product is a newegg combo
                            # Get the current price accordingly
                            if (product_data[0][1] == "Newegg-Combo"):
                                current_price = await newegg.get_product_price(soup, True)
                            else:
                                current_price = await newegg.get_product_price(soup, False)

                            # Error-checking
                            if (current_price != False):

                                # Open the price history file for reading
                                price_file = open(product_path + "/price_history.pkl", "rb")

                                price_history = pickle.load(price_file)

                                price_file.close()

                                # Check if the prices differ from the one on file
                                # Strip gets rid of the "\n"
                                if (price_history[-1][0] != current_price):

                                    # If they do, the prices have changed
                                    # Append the new price to the gathered list, include a timestamp
                                    price_history.append([current_price, str(datetime.datetime.now())])

                                    # Open the price history file for writing. This will erase the contents of the file
                                    price_file = open(product_path + "/price_history.pkl", "wb")

                                    # Write list into the file
                                    pickle.dump(price_history, price_file)

                                    price_file.close()

                        else:

                            # Check if the product is a newegg combo
                            # Get the current price accordingly
                            if (product_data[0][1] == "Newegg-Combo"):
                                current_price = await newegg.get_product_price(soup, True)
                            else:
                                current_price = await newegg.get_product_price(soup, False)

                            # If the price history file does not exist, create it and write the price into the file
                            price_history = []

                            price_history.append([current_price, str(datetime.datetime.now())])

                            price_file = open(product_path + "/price_history.pkl", "wb")

                            pickle.dump(price_history, price_file)

                            price_file.close()

                # Amazon is slightly different in how methods are called
                # One method handles name, stock and price (while it's much more messy, it removes the need to load a webpage multiple times)
                elif (product_data[0][1] == "Amazon"):

                    # Get beautifulSoup object
                    soup = await amazon.get_soup(product_data[1][1])

                    # Check stock status (and price if needed)
                    stock_status = await amazon.get_product_info(soup, bool(product_data[6][1]), False)

                    if (stock_status != False):

                        # Check if the users stock history file exists
                        if (await does_stock_file_exist(1, product_path)):

                            # If it does, open the file and read all lines
                            general_stock_file = open(product_path + "/stock_history.pkl", "rb")

                            stock_history = pickle.load(general_stock_file)

                            general_stock_file.close()

                            # Check if the last item in the file stock status differs from the one just checked
                            if (int(stock_history[-1][0]) != stock_status[1]):

                                # If it does, that means the stock has changed from the last check

                                # Append the new status and a timestamp to the list gathered from the file previously
                                stock_history.append([str(stock_status[1]), str(datetime.datetime.now())])

                                # Open the same file again, however, in write mode, erasing everything in it
                                stock_file = open(product_path + "/stock_history.pkl", "wb")


                                pickle.dump(stock_history, stock_file)

                                stock_file.close()
                        else:
                            # If the file does not exist, create a blank list
                            stock_history = []

                            # Append the new status and a timestamp to the list gathered from the file previously
                            stock_history.append([str(stock_status[1]), str(datetime.datetime.now())])

                            # Open the same file again, however, in write mode, erasing everything in it
                            stock_file = open(product_path + "/stock_history.pkl", "wb")


                            pickle.dump(stock_history, stock_file)

                            stock_file.close()


                        # Check price (if required) (this time, deal with files, don't re-check webpage)
                        if (product_data[6][1] != "False"):

                            current_price = None

                            # Check if the users price history file exists
                            if (await does_stock_file_exist(2, product_path)):

                                # Get the current price accordingly
                                current_price = stock_status[2]

                                # Error-checking
                                if (current_price != False or current_price != None):

                                    # Open the price history file for reading
                                    price_file = open(product_path + "/price_history.pkl", "rb")

                                    price_history = pickle.load(price_file)

                                    price_file.close()

                                    # Check if the prices differ from the one on file
                                    # Strip gets rid of the "\n"
                                    if (price_history[-1][0] != current_price):
                                        # If they do, the prices have changed
                                        # Append the new price to the gathered list, include a timestamp
                                        price_history.append([current_price, str(datetime.datetime.now())])

                                        # Open the price history file for writing. This will erase the contents of the file
                                        price_file = open(product_path + "/price_history.pkl", "wb")

                                        # Write list into the file
                                        pickle.dump(price_history, price_file)

                                        price_file.close()

                            else:

                                # Get the current price accordingly
                                current_price = stock_status[2]

                                # If the price history file does not exist, create it and write the price into the file
                                price_history = []

                                price_history.append([current_price, str(datetime.datetime.now())])

                                price_file = open(product_path + "/price_history.pkl", "wb")

                                pickle.dump(price_history, price_file)

                                price_file.close()


                elif (product_data[0][1] == "BestBuy"):

                    # Get beautifulSoup object
                    soup = await bestbuy.get_soup(product_data[1][1])

                    # From object, get the stock status
                    stock_status = await bestbuy.get_stock_status(soup)

                    if (stock_status != False):

                        # Check if the users stock history file exists
                        if (await does_stock_file_exist(1, product_path)):

                            # If it does, open the file and read all lines
                            general_stock_file = open(product_path + "/stock_history.pkl", "rb")

                            stock_history = pickle.load(general_stock_file)

                            general_stock_file.close()

                            # Check if the last item in the file stock status differs from the one just checked
                            if (int(stock_history[-1][0]) != stock_status):

                                # If it does, that means the stock has changed from the last check

                                # Append the new status and a timestamp to the list gathered from the file previously
                                stock_history.append([str(stock_status), str(datetime.datetime.now())])

                                # Open the same file again, however, in write mode, erasing everything in it
                                stock_file = open(product_path + "/stock_history.pkl", "wb")


                                pickle.dump(stock_history, stock_file)

                                stock_file.close()
                        else:
                            # If the file does not exist, create a blank list
                            stock_history = []

                            # Append the new status and a timestamp to the list gathered from the file previously
                            stock_history.append([str(stock_status), str(datetime.datetime.now())])

                            # Open the same file again, however, in write mode, erasing everything in it
                            stock_file = open(product_path + "/stock_history.pkl", "wb")


                            pickle.dump(stock_history, stock_file)

                            stock_file.close()

                    # Check price (if required)
                    if (product_data[6][1] != "False"):

                        current_price = None

                        # Check if the users price history file exists
                        if (await does_stock_file_exist(2, product_path)):

                            # Get the current price accordingly
                            current_price = await bestbuy.get_product_price(soup)

                            # Error-checking
                            if (current_price != False):

                                # Open the price history file for reading
                                price_file = open(product_path + "/price_history.pkl", "rb")

                                price_history = pickle.load(price_file)

                                price_file.close()

                                # Check if the prices differ from the one on file
                                # Strip gets rid of the "\n"
                                if (price_history[-1][0] != current_price):

                                    # If they do, the prices have changed
                                    # Append the new price to the gathered list, include a timestamp
                                    price_history.append([current_price, str(datetime.datetime.now())])

                                    # Open the price history file for writing. This will erase the contents of the file
                                    price_file = open(product_path + "/price_history.pkl", "wb")

                                    # Write list into the file
                                    pickle.dump(price_history, price_file)

                                    price_file.close()

                        else:

                            # Get the current price accordingly
                            current_price = await bestbuy.get_product_price(soup)

                            # If the price history file does not exist, create it and write the price into the file
                            price_history = []

                            price_history.append([current_price, str(datetime.datetime.now())])

                            price_file = open(product_path + "/price_history.pkl", "wb")

                            pickle.dump(price_history, price_file)

                            price_file.close()

                elif (product_data[0][1] == "CanadaComputers"):

                    # Get beautifulSoup object
                    soup = await canadacomputers.get_soup(product_data[1][1])

                    # From object, get the stock status
                    stock_status = await canadacomputers.get_stock_status(soup)

                    if (stock_status != False):

                        # Check if the users stock history file exists
                        if (await does_stock_file_exist(1, product_path)):

                            # If it does, open the file and read all lines
                            general_stock_file = open(product_path + "/stock_history.pkl", "rb")

                            stock_history = pickle.load(general_stock_file)

                            general_stock_file.close()

                            # Check if the last item in the file stock status differs from the one just checked
                            if (int(stock_history[-1][0]) != stock_status[0]):

                                # If it does, that means the stock has changed from the last check

                                # Append the new status and a timestamp to the list gathered from the file previously
                                stock_history.append([(stock_status[0]), str(datetime.datetime.now())])

                                # Open the same file again, however, in write mode, erasing everything in it
                                stock_file = open(product_path + "/stock_history.pkl", "wb")


                                pickle.dump(stock_history,stock_file)

                                stock_file.close()
                        else:
                            # If the file does not exist, create a blank list
                            stock_history = []

                            # Append the new status and a timestamp to the list gathered from the file previously
                            stock_history.append([(stock_status[0]), str(datetime.datetime.now())])

                            # Open the same file again, however, in write mode, erasing everything in it
                            stock_file = open(product_path + "/stock_history.pkl", "wb")


                            pickle.dump(stock_history,stock_file)

                            stock_file.close()

                    # Check if store notifications are on
                    if (product_data[7][1] != "False"):

                        # If so, check if the user is tracking a specific store
                        if (product_data[8][1] != "False"):

                            # If so, get store name to be tracked
                            store_name = product_data[9][1]

                            # Error checking
                            if (stock_status[1] != False):

                                # Loop through each store in stock_status
                                for store in stock_status[1]:

                                    # Find the correct store name
                                    # -1 gets rid of the ":"
                                    if (store[0] == store_name):

                                        # Check if the store stock history file exists
                                        if (await does_stock_file_exist(3, product_path)):

                                            # If so, compare the current stock to the one on file

                                            # Open store history file
                                            store_stock_history_file = open(product_path + "/store_stock_history.pkl", "rb")

                                            # Readlines
                                            store_stock_list = pickle.load(store_stock_history_file)

                                            store_stock_history_file.close()

                                            # Get the last list from the file
                                            last_stock_list = store_stock_list[-1][0]

                                            # Loop through that list
                                            for store_in_list in last_stock_list:

                                                # Find the correct store name
                                                if (store_in_list[0] == store_name):

                                                    # Check if the stock number does not match
                                                    if (store_in_list[1] != store[1]):
                                                        # If it doesn't, append the new stock list
                                                        store_stock_list.append([stock_status[1], str(datetime.datetime.now())])
                                                        break

                                            # Open the stock history file, delete all it's contents
                                            store_stock_history_file = open(product_path + "/store_stock_history.pkl", "wb")

                                            # Write the elements (including the new append) to the file
                                            pickle.dump(store_stock_list, store_stock_history_file)

                                            store_stock_history_file.close()
                                            break

                                        else:

                                            # If the store stock file does not exist, create an empty list and write the updated stock into a new file

                                            store_stock_list = []

                                            # Open store history file
                                            store_stock_history_file = open(product_path + "/store_stock_history.pkl", "wb")

                                            # Append updated store stock status to file list along with a timestamp
                                            store_stock_list.append([stock_status[1], str(datetime.datetime.now())])

                                            # Write the elements (including the new append) to the file
                                            pickle.dump(store_stock_list, store_stock_history_file)

                                            store_stock_history_file.close()

                        else:

                            # If the user is not tracking a specific store but has store notifications turned on, this part will check if any stock status of any given store has changed

                            # Check if the store stock history file exists
                            if (await does_stock_file_exist(3, product_path)):
                                # If so, compare the current stock to the one on file

                                is_change = False

                                # Open store history file
                                store_stock_history_file = open(product_path + "/store_stock_history.pkl", "rb")

                                # Readlines
                                store_stock_list = pickle.load(store_stock_history_file)

                                store_stock_history_file.close()

                                # Get the last list from the file (strip takes out the "\n")
                                last_stock_list = store_stock_list[-1][0]

                                # For loop through each store stock status recently found
                                for store in stock_status[1]:

                                    # Loop through the stock status list on file
                                    for store_in_list in last_stock_list:

                                        # Find matching stores
                                        if (store[0] == store_stock_list[0]):

                                            # Check if their stock disagrees
                                            if (store[1] != store_stock_list[1]):
                                                # This means stock needs to be updated in files
                                                # Change boolean according
                                                is_change = True
                                                break

                                    if (is_change):
                                        break  # It is okay to break both loops as the whole list of stores is updated regardless if only one store has a change

                                if (is_change):
                                    # Append updated store stock status to file list along with a timestamp
                                    store_stock_list.append([stock_status[1], str(datetime.datetime.now())])

                                    # Open stock history file, deleting everything inside
                                    store_stock_history_file = open(product_path + "/store_stock_history.pkl", "wb")

                                    # Write the elements (including the new append) to the file
                                    pickle.dump(store_stock_list, store_stock_history_file)

                                    store_stock_history_file.close()

                            else:

                                # If the store stock file does not exist, create an empty list and write the updated stock into a new file

                                store_stock_list = []

                                # Open store history file
                                store_stock_history_file = open(product_path + "/store_stock_history.pkl", "wb")

                                # Append updated store stock status to file list along with a timestamp
                                store_stock_list.append([stock_status[1], str(datetime.datetime.now())])

                                # Write the elements (including the new append) to the file
                                pickle.dump(store_stock_list, store_stock_history_file)

                                store_stock_history_file.close()

                    # Check price (if required)
                    if (product_data[6][1] != "False"):

                        current_price = None

                        # Check if the users price history file exists
                        if (await does_stock_file_exist(2, product_path)):

                            # Get the current price accordingly
                            current_price = await canadacomputers.get_product_price(soup)

                            # Error-checking
                            if (current_price != False):

                                # Open the price history file for reading
                                price_file = open(product_path + "/price_history.pkl", "rb")

                                price_history = pickle.load(price_file)

                                price_file.close()

                                # Check if the prices differ from the one on file
                                # Strip gets rid of the "\n"
                                if (price_history[-1][0] != current_price):

                                    # If they do, the prices have changed
                                    # Append the new price to the gathered list, include a timestamp
                                    price_history.append([current_price, str(datetime.datetime.now())])

                                    # Open the price history file for writing. This will erase the contents of the file
                                    price_file = open(product_path + "/price_history.pkl", "wb")

                                    pickle.dump(price_history, price_file)

                                    price_file.close()

                        else:

                            # Get the current price accordingly
                            current_price = await canadacomputers.get_product_price(soup)

                            # If the price history file does not exist, create it and write the price into the file
                            price_history = []

                            price_history.append([current_price, str(datetime.datetime.now())])

                            price_file = open(product_path + "/price_history.pkl", "wb")

                            pickle.dump(price_history,price_file)

                            price_file.close()

                elif (product_data[0][1] == "MemoryExpress"):

                    # Get beautifulSoup object
                    soup = await memoryexpress.get_soup(product_data[1][1])

                    # From object, get the stock status
                    stock_status = await memoryexpress.get_stock_status(soup)

                    if (stock_status != False):

                        # Check if the users stock history file exists
                        if (await does_stock_file_exist(1, product_path)):

                            # If it does, open the file and read all lines
                            general_stock_file = open(product_path + "/stock_history.pkl", "rb")

                            stock_history = pickle.load(general_stock_file)

                            general_stock_file.close()

                            # Check if the last item in the file stock status differs from the one just checked
                            if (int(stock_history[-1][0]) != stock_status[0]):

                                # If it does, that means the stock has changed from the last check

                                # Append the new status and a timestamp to the list gathered from the file previously
                                stock_history.append([(stock_status[0]), str(datetime.datetime.now())])

                                # Open the same file again, however, in write mode, erasing everything in it
                                stock_file = open(product_path + "/stock_history.pkl", "wb")


                                pickle.dump(stock_history, stock_file)

                                stock_file.close()
                        else:
                            # If the file does not exist, create a blank list
                            stock_history = []

                            # Append the new status and a timestamp to the list gathered from the file previously
                            stock_history.append([(stock_status[0]), str(datetime.datetime.now())])

                            # Open the same file again, however, in write mode, erasing everything in it
                            stock_file = open(product_path + "/stock_history.pkl", "wb")


                            pickle.dump(stock_history, stock_file)

                            stock_file.close()

                    # Check if store notifications are on
                    if (product_data[7][1] != "False"):

                        # If so, check if the user is tracking a specific store
                        if (product_data[8][1] != "False"):

                            # If so, get store name to be tracked
                            store_name = product_data[9][1]

                            # Error checking
                            if (stock_status[1] != False):

                                # Loop through each store in stock_status
                                for store in stock_status[1]:

                                    # Find the correct store name
                                    # -1 gets rid of the ":"
                                    if (store[0][:-1] == store_name):

                                        # Check if the store stock history file exists
                                        if (await does_stock_file_exist(3, product_path)):

                                            # If so, compare the current stock to the one on file

                                            # Open store history file
                                            store_stock_history_file = open(product_path + "/store_stock_history.pkl","rb")

                                            # Readlines
                                            store_stock_list = pickle.load(store_stock_history_file)

                                            store_stock_history_file.close()

                                            # Get the last list from the file (strip takes out the "\n")

                                            last_stock_list = store_stock_list[-1][0]

                                            # Loop through that list
                                            for store_in_list in last_stock_list:

                                                # Find the correct store name
                                                if (store_in_list[0][:-1] == store_name):

                                                    # Check if the stock number does not match

                                                    if (store_in_list[1] != store[1]):
                                                        # If it doesn't, append the new stock list
                                                        store_stock_list.append([stock_status[1], str(datetime.datetime.now())])
                                                        break

                                            # Open the stock history file, delete all it's contents
                                            store_stock_history_file = open(product_path + "/store_stock_history.pkl","wb")

                                            # Write the elements (including the new append) to the file
                                            pickle.dump(store_stock_list, store_stock_history_file)

                                            store_stock_history_file.close()
                                            break

                                        else:

                                            # If the store stock file does not exist, create an empty list and write the updated stock into a new file

                                            store_stock_list = []

                                            # Open store history file
                                            store_stock_history_file = open(product_path + "/store_stock_history.pkl","wb")

                                            # Append updated store stock status to file list along with a timestamp
                                            store_stock_list.append([stock_status[1], str(datetime.datetime.now())])

                                            # Write the elements (including the new append) to the file
                                            pickle.dump(store_stock_list, store_stock_history_file)

                                            store_stock_history_file.close()

                        else:

                            # If the user is not tracking a specific store but has store notifications turned on, this part will check if any stock status of any given store has changed

                            # Check if the store stock history file exists
                            if (await does_stock_file_exist(3, product_path)):
                                # If so, compare the current stock to the one on file

                                is_change = False

                                # Open store history file
                                store_stock_history_file = open(product_path + "/store_stock_history.pkl", "rb")

                                # Readlines
                                store_stock_list = pickle.load(store_stock_history_file)

                                store_stock_history_file.close()

                                # Get the last list from the file (strip takes out the "\n")
                                last_stock_list = store_stock_list[-1][0]

                                # For loop through each store stock status recently found
                                for store in stock_status[1]:

                                    # Loop through the stock status list on file
                                    for store_in_list in last_stock_list:

                                        # Find matching stores
                                        if (store[0][:-1] == store_stock_list[0][:-1]):

                                            # Check if their stock disagrees
                                            if (store[1] != store_stock_list[1]):
                                                # This means stock needs to be updated in files
                                                # Change boolean according
                                                is_change = True
                                                break

                                    if (is_change):
                                        break  # It is okay to break both loops as the whole list of stores is updated regardless if only one store has a change

                                if (is_change):
                                    # Append updated store stock status to file list along with a timestamp
                                    store_stock_list.append([stock_status[1], str(datetime.datetime.now())])

                                    # Open stock history file, deleting everything inside
                                    store_stock_history_file = open(product_path + "/store_stock_history.pkl", "wb")

                                    # Write the elements (including the new append) to the file
                                    pickle.dump(store_stock_list, store_stock_history_file)

                                    store_stock_history_file.close()

                            else:

                                # If the store stock file does not exist, create an empty list and write the updated stock into a new file

                                store_stock_list = []

                                # Open store history file
                                store_stock_history_file = open(product_path + "/store_stock_history.pkl", "wb")

                                # Append updated store stock status to file list along with a timestamp
                                store_stock_list.append([stock_status[1], str(datetime.datetime.now())])

                                # Write the elements (including the new append) to the file
                                pickle.dump(store_stock_list, store_stock_history_file)

                                store_stock_history_file.close()

                    # Check price (if required)
                    if (product_data[6][1] != "False"):

                        current_price = None

                        # Check if the users price history file exists
                        if (await does_stock_file_exist(2, product_path)):

                            # Get the current price accordingly
                            current_price = await memoryexpress.get_product_price(soup)

                            # Error-checking
                            if (current_price != False):

                                # Open the price history file for reading
                                price_file = open(product_path + "/price_history.pkl", "rb")

                                price_history = pickle.load(price_file)

                                price_file.close()

                                # Check if the prices differ from the one on file
                                # Strip gets rid of the "\n"
                                if (price_history[-1][0] != current_price):

                                    # If they do, the prices have changed
                                    # Append the new price to the gathered list, include a timestamp
                                    price_history.append([current_price, str(datetime.datetime.now())])

                                    # Open the price history file for writing. This will erase the contents of the file
                                    price_file = open(product_path + "/price_history.pkl", "wb")

                                    # Write list into the file
                                    pickle.dump(price_history, price_file)

                                    price_file.close()

                        else:

                            # Get the current price accordingly
                            current_price = await memoryexpress.get_product_price(soup)

                            # If the price history file does not exist, create it and write the price into the file
                            price_history = []

                            price_history.append([current_price, str(datetime.datetime.now())])

                            price_file = open(product_path + "/price_history.pkl", "wb")

                            pickle.dump(price_history, price_file)

                            price_file.close()

    # After the checks for stock have been completed, call the notify_check to notify user (in-case the file storing stock data have changed accordingly)
    finish = await notify_check(client)


# Method to notify a user if a product has gone in stock
# (or something has happened as per their settings)
async def notify_check(client):

    # For loop through each directory (titled with the users id)
    for user in os.listdir(user_storage_path):

        # Go through the users products
        # Get the link for the product
        member_path = (user_storage_path + "/" + user)
        products_path = (member_path + "/" + "product_data")

        member_file = open(member_path + "/user_data.txt", "r")
        data_contents = member_file.readlines()
        member_file.close()

        # Check if the users status is not currently correct
        if ((data_contents[2][7:-1]) != "WATCH_LINK"):

            # If this statement is true, skip this user and move onto the next one
            # continue skips the current iteration of the for loop
            continue

        channel_string = (data_contents[3][11:-1])

        channel = client.get_channel(int(channel_string))

        user = client.get_user(int(user))

        # Go through all products and open their settings
        for product in os.listdir(products_path):

            # Get specific product path
            product_path = (products_path + "/" + product)

            product_number = int(product[8:])

            product_data = await product_dealer.retrieve_product_settings(user, product_number)

            # Check if notifications are enabled (NOTIFY_DISABLE is set to False)
            if (product_data[3][1] == "False"):

                # Get current stock history counter length on file
                counter_list = await product_dealer.retrieve_counter_data(user, product_number)

                # Check website type and call the according script to check the stock of said item

                # Newegg
                if (product_data[0][1] == "Newegg" or product_data[0][1] == "Newegg-Combo"):

                    # Check if the users stock history file exists
                    if (await does_stock_file_exist(1, product_path)):
                        # If it does, open the file and read all lines
                        general_stock_file = open(product_path + "/stock_history.pkl", "rb")

                        # Pickle load to grab list from file
                        stock_history = pickle.load(general_stock_file)

                        general_stock_file.close()

                        # Check if there is a missmatch between what is on file vs new data
                        if (int(counter_list[0]) != len(stock_history)):

                            # Update counter by incrementing by 1
                            counter_edit = await product_dealer.edit_counter_data(user, product_number, [1,1])

                            # Error checking
                            if (counter_edit):

                                # Check what the user needs to be notified about

                                # In-Stock
                                if ((int(stock_history[-1][0]) == 1)):

                                    # Notify user
                                    await channel.send(f'Hey {user.mention}!')
                                    await channel.send(f'The Product, {product_data[2][1]}, is in stock!')
                                    await channel.send(f'{product_data[1][1]}')


                                # Backorder
                                if ((product_data[4][1] != "False") and (int(stock_history[-1][0]) == 3)):

                                    # Notify user
                                    await channel.send(f'Hey {user.mention}!')
                                    await channel.send(f'The Product, {product_data[2][1]}, is available for backorder!')
                                    await channel.send(f'{product_data[1][1]}')


                                # Preorder
                                if ((product_data[5][1] != "False") and (int(stock_history[-1][0]) == 4)):

                                    # Notify user
                                    await channel.send(f'Hey {user.mention}!')
                                    await channel.send(f'The Product, {product_data[2][1]}, is available for preorder!')
                                    await channel.send(f'{product_data[1][1]}')

                    # Check if price needs to be checked (if required)
                    if (product_data[6][1] != "False" and await does_stock_file_exist(2, product_path)):

                        # Open the price history file for reading
                        price_file = open(product_path + "/price_history.pkl", "rb")

                        price_history = pickle.load(price_file)

                        price_file.close()

                        # Check if there is a missmatch between what is on file vs new data
                        if (int(counter_list[1]) != len(price_history)):


                            # Update counter by incrementing by 1
                            counter_edit = await product_dealer.edit_counter_data(user, product_number, [2,1])

                            # Error checking
                            if (counter_edit):

                                # Notify user
                                await channel.send(f'Hey {user.mention}!')
                                if (len(price_history) > 1):
                                    await channel.send(f'The product, {product_data[2][1]}, recently had a price change!')
                                    await channel.send(f'The price went from {price_history[-2][0]} to {price_history[-1][0]}')
                                else:
                                    await channel.send(f'I am just confirming the price for the product, {product_data[2][1]}!')
                                    await channel.send(f'The price is {price_history[-1][0]}')
                                    await channel.send(f'If the price value varies by a significant margin, please contact an administrator')
                                await channel.send(f'{product_data[1][1]}')

                # Amazon
                if (product_data[0][1] == "Amazon"):

                    # Check if the users stock history file exists
                    if (await does_stock_file_exist(1, product_path)):
                        # If it does, open the file and read all lines
                        general_stock_file = open(product_path + "/stock_history.pkl", "rb")

                        # Pickle load to grab list from file
                        stock_history = pickle.load(general_stock_file)

                        general_stock_file.close()

                        # Check if there is a missmatch between what is on file vs new data
                        if (int(counter_list[0]) != len(stock_history)):

                            # Update counter by incrementing by 1
                            counter_edit = await product_dealer.edit_counter_data(user, product_number, [1, 1])

                            # Error checking
                            if (counter_edit):

                                # Check what the user needs to be notified about

                                # In-Stock
                                if (int(stock_history[-1][0]) == 1):
                                    # Notify user
                                    await channel.send(f'Hey {user.mention}!')
                                    await channel.send(f'The Product, {product_data[2][1]}, is in stock (sold by amazon.ca)!')
                                    await channel.send(f'{product_data[1][1]}')

                                # Preorder
                                if ((product_data[5][1] != "False") and (int(stock_history[-1][0]) == 5)):

                                    # Notify user
                                    await channel.send(f'Hey {user.mention}!')
                                    await channel.send(f'The Product, {product_data[2][1]}, is available for preorder (sold by amazon.ca)!')
                                    await channel.send(f'{product_data[1][1]}')

                                # Backorder
                                if ((product_data[4][1] != "False") and (int(stock_history[-1][0]) == 6)):

                                    # Notify user
                                    await channel.send(f'Hey {user.mention}!')
                                    await channel.send(f'The Product, {product_data[2][1]}, is available for backorder (sold by amazon.ca)!')
                                    await channel.send(f'{product_data[1][1]}')

                    # Check if price needs to be checked (if required)
                    if (product_data[6][1] != "False" and await does_stock_file_exist(2, product_path)):

                        # Open the price history file for reading
                        price_file = open(product_path + "/price_history.pkl", "rb")

                        price_history = pickle.load(price_file)

                        price_file.close()

                        # Check if there is a missmatch between what is on file vs new data
                        if (int(counter_list[1]) != len(price_history)):

                            # Update counter by incrementing by 1
                            counter_edit = await product_dealer.edit_counter_data(user, product_number,[2, 1])

                            # Error checking
                            if (counter_edit):

                                # Notify user
                                await channel.send(f'Hey {user.mention}!')
                                if (len(price_history) > 1):
                                    await channel.send(f'The Product, {product_data[2][1]}, recently had a price change!')
                                    await channel.send(f'The price went from {price_history[-2][0]} to {price_history[-1][0]}')
                                else:
                                    await channel.send(f'I am just confirming the price for the product, {product_data[2][1]}!')
                                    await channel.send(f'The price is {price_history[-1][0]}')
                                    await channel.send(f'If the price value varies by a significant margin, please contact an administrator')
                                await channel.send(f'{product_data[1][1]}')

                # BestBuy
                if (product_data[0][1] == "BestBuy"):

                    # Check if the users stock history file exists
                    if (await does_stock_file_exist(1, product_path)):
                        # If it does, open the file and read all lines
                        general_stock_file = open(product_path + "/stock_history.pkl", "rb")

                        # Pickle load to grab list from file
                        stock_history = pickle.load(general_stock_file)

                        general_stock_file.close()

                        # Check if there is a missmatch between what is on file vs new data
                        if (int(counter_list[0]) != len(stock_history)):

                            # Update counter by incrementing by 1
                            counter_edit = await product_dealer.edit_counter_data(user, product_number, [1,1])

                            # Error checking
                            if (counter_edit):

                                # Check what the user needs to be notified about

                                # In-Stock
                                if ((int(stock_history[-1][0]) == 1) or (int(stock_history[-1][0]) == 7) or (int(stock_history[-1][0]) == 5)):

                                    # Notify user
                                    await channel.send(f'Hey {user.mention}!')
                                    await channel.send(f'The Product, {product_data[2][1]}, is in stock!')
                                    await channel.send(f'{product_data[1][1]}')


                                # Backorder
                                if ((product_data[4][1] != "False") and (int(stock_history[-1][0]) == 3)):

                                    # Notify user
                                    await channel.send(f'Hey {user.mention}!')
                                    await channel.send(f'The Product, {product_data[2][1]}, is available for backorder!')
                                    await channel.send(f'{product_data[1][1]}')

                                # Preorder
                                if ((product_data[5][1] != "False") and (int(stock_history[-1][0]) == 4)):

                                    # Notify user
                                    await channel.send(f'Hey {user.mention}!')
                                    await channel.send(f'The Product, {product_data[2][1]}, is available for preorder!')
                                    await channel.send(f'{product_data[1][1]}')

                    # Check if price needs to be checked (if required)
                    if (product_data[6][1] != "False" and await does_stock_file_exist(2, product_path)):

                        # Open the price history file for reading
                        price_file = open(product_path + "/price_history.pkl", "rb")

                        price_history = pickle.load(price_file)

                        price_file.close()

                        # Check if there is a missmatch between what is on file vs new data
                        if (int(counter_list[1]) != len(price_history)):


                            # Update counter by incrementing by 1
                            counter_edit = await product_dealer.edit_counter_data(user, product_number, [2,1])

                            # Error checking
                            if (counter_edit):

                                # Notify user
                                await channel.send(f'Hey {user.mention}!')
                                if (len(price_history) > 1):
                                    await channel.send(f'The Product, {product_data[2][1]}, recently had a price change!')
                                    await channel.send(f'The price went from {price_history[-2][0]} to {price_history[-1][0]}')
                                else:
                                    await channel.send(f'I am just confirming the price for the product, {product_data[2][1]}!')
                                    await channel.send(f'The price is {price_history[-1][0]}')
                                    await channel.send(f'If the price value varies by a significant margin, please contact an administrator')
                                await channel.send(f'{product_data[1][1]}')

                # CanadaComputers
                if (product_data[0][1] == "CanadaComputers"):

                    # Check if the users stock history file exists
                    if (await does_stock_file_exist(1, product_path)):
                        # If it does, open the file and read all lines
                        general_stock_file = open(product_path + "/stock_history.pkl", "rb")

                        # Pickle load to grab list from file
                        stock_history = pickle.load(general_stock_file)

                        general_stock_file.close()

                        # Check if there is a missmatch between what is on file vs new data
                        if (int(counter_list[0]) != len(stock_history)):

                            # Update counter by incrementing by 1
                            counter_edit = await product_dealer.edit_counter_data(user, product_number, [1,1])

                            # Error checking
                            if (counter_edit):

                                # Check what the user needs to be notified about

                                # In-Stock
                                if ((int(stock_history[-1][0]) == 1)):

                                    # Notify user
                                    await channel.send(f'Hey {user.mention}!')
                                    await channel.send(f'The Product, {product_data[2][1]}, is in stock!')
                                    await channel.send(f'{product_data[1][1]}')

                                # Pickup in store
                                if ((product_data[7][1] != "False") and (product_data[8][1] == "False") and (int(stock_history[-1][0]) == 4)):

                                    # Notify user
                                    await channel.send(f'Hey {user.mention}!')
                                    await channel.send(f'The Product, {product_data[2][1]}, is available in-stores!')
                                    await channel.send(f'{product_data[1][1]}')

                    # Check if price needs to be checked (if required)
                    if (product_data[6][1] != "False" and await does_stock_file_exist(2, product_path)):

                        # Open the price history file for reading
                        price_file = open(product_path + "/price_history.pkl", "rb")

                        price_history = pickle.load(price_file)

                        price_file.close()

                        # Check if there is a missmatch between what is on file vs new data
                        if (int(counter_list[1]) != len(price_history)):


                            # Update counter by incrementing by 1
                            counter_edit = await product_dealer.edit_counter_data(user, product_number, [2,1])

                            # Error checking
                            if (counter_edit):

                                # Notify user
                                await channel.send(f'Hey {user.mention}!')
                                if (len(price_history) > 1):
                                    await channel.send(f'The Product, {product_data[2][1]}, recently had a price change!')
                                    await channel.send(f'The price went from {price_history[-2][0]} to {price_history[-1][0]}')
                                else:
                                    await channel.send(f'I am just confirming the price for the product, {product_data[2][1]}!')
                                    await channel.send(f'The price is {price_history[-1][0]}')
                                    await channel.send(f'If the price value varies by a significant margin, please contact an administrator')
                                await channel.send(f'{product_data[1][1]}')

                    # Check if a specific store needs to be checked (if required)
                    if (product_data[8][1] != "False" and await does_stock_file_exist(3, product_path)):

                        store_name = product_data[9][1]

                        # Open store history file
                        store_stock_history_file = open(product_path + "/store_stock_history.pkl", "rb")

                        # Readlines
                        store_stock_list = pickle.load(store_stock_history_file)

                        store_stock_history_file.close()

                        # Get the last list from the file
                        last_stock_list = store_stock_list[-1][0]


                        # Check if there is a missmatch between what is on file vs new data
                        if (int(counter_list[2]) != len(store_stock_list)):

                            # Update counter by incrementing by 1
                            counter_edit = await product_dealer.edit_counter_data(user, product_number, [3,1])

                            # Error checking
                            if (counter_edit):

                                # For loop through stores in list to get exact stock data
                                for store_in_list in last_stock_list:

                                    # Once found, update the user
                                    if (store_in_list[0] == store_name):

                                        await channel.send(f'Hey {user.mention}!')
                                        if (int(counter_list[2]) != 0):
                                            await channel.send(f'The Product, {product_data[2][1]}, recently had a stock change at the {store_name} CanadaComputers store location!')
                                            await channel.send(f'The stock level is now {store_in_list[1]}')
                                            await channel.send(f'{product_data[1][1]}')
                                            break
                                        else:
                                            await channel.send(f'I am just confirming the stock level for the product, {product_data[2][1]}, at the {store_name} CanadaComputers store location!')
                                            await channel.send(f'The stock level is {store_in_list[1]}')
                                            await channel.send(f'If this number (or status) differs from the website, please contact an administrator')
                                            await channel.send(f'{product_data[1][1]}')
                                            break

                # MemoryExpress
                if (product_data[0][1] == "MemoryExpress"):

                    # Check if the users stock history file exists
                    if (await does_stock_file_exist(1, product_path)):
                        # If it does, open the file and read all lines
                        general_stock_file = open(product_path + "/stock_history.pkl", "rb")

                        # Pickle load to grab list from file
                        stock_history = pickle.load(general_stock_file)

                        general_stock_file.close()

                        # Check if there is a missmatch between what is on file vs new data
                        if (int(counter_list[0]) != len(stock_history)):

                            # Update counter by incrementing by 1
                            counter_edit = await product_dealer.edit_counter_data(user, product_number, [1,1])

                            # Error checking
                            if (counter_edit):

                                # Check what the user needs to be notified about

                                # In-Stock
                                if ((int(stock_history[-1][0]) == 1)):

                                    # Notify user
                                    await channel.send(f'Hey {user.mention}!')
                                    await channel.send(f'The Product, {product_data[2][1]}, is in stock!')
                                    await channel.send(f'{product_data[1][1]}')

                                # Pickup in store
                                if ((product_data[7][1] != "False") and (product_data[8][1] == "False")):

                                    # Open store history file
                                    store_stock_history_file = open(product_path + "/store_stock_history.pkl", "rb")

                                    # Readlines
                                    store_stock_list = pickle.load(store_stock_history_file)

                                    store_stock_history_file.close()

                                    # Get the last list from the file
                                    last_stock_list = store_stock_list[-1][0]

                                    # Check if there is a missmatch between what is on file vs new data
                                    if (int(counter_list[2]) != len(store_stock_list)):

                                        # Update counter by incrementing by 1
                                        counter_edit = await product_dealer.edit_counter_data(user, product_number, [3,1])

                                        # Error checking
                                        if (counter_edit):
                                            # Notify user
                                            await channel.send(f'Hey {user.mention}!')
                                            await channel.send(f'The Product, {product_data[2][1]}, is available in-stores!')
                                            await channel.send(f'{product_data[1][1]}')

                                # Preorder
                                if ((product_data[5][1] != "False") and (int(stock_history[-1][0])) == 6):

                                    # Notify user
                                    await channel.send(f'Hey {user.mention}!')
                                    await channel.send(f'The Product, {product_data[2][1]}, is available for preorder!')
                                    await channel.send(f'{product_data[1][1]}')

                    # Check if price needs to be checked (if required)
                    if (product_data[6][1] != "False" and await does_stock_file_exist(2, product_path)):

                        # Open the price history file for reading
                        price_file = open(product_path + "/price_history.pkl", "rb")

                        price_history = pickle.load(price_file)

                        price_file.close()

                        # Check if there is a missmatch between what is on file vs new data
                        if (int(counter_list[1]) != len(price_history)):


                            # Update counter by incrementing by 1
                            counter_edit = await product_dealer.edit_counter_data(user, product_number, [2,1])

                            # Error checking
                            if (counter_edit):

                                # Notify user
                                await channel.send(f'Hey {user.mention}!')
                                if (len(price_history) > 1):
                                    await channel.send(f'The Product, {product_data[2][1]}, recently had a price change!')
                                    await channel.send(f'The price went from {price_history[-2][0]} to {price_history[-1][0]}')
                                else:
                                    await channel.send(f'I am just confirming the price for the product, {product_data[2][1]}!')
                                    await channel.send(f'The price is {price_history[-1][0]}')
                                    await channel.send(f'If the price value varies by a significant margin, please contact an administrator')
                                await channel.send(f'{product_data[1][1]}')

                    # Check if a specific store needs to be checked (if required)
                    if (product_data[8][1] != "False" and await does_stock_file_exist(3, product_path)):

                        store_name = product_data[9][1]

                        # Open store history file
                        store_stock_history_file = open(product_path + "/store_stock_history.pkl", "rb")

                        # Readlines
                        store_stock_list = pickle.load(store_stock_history_file)

                        store_stock_history_file.close()

                        # Get the last list from the file
                        last_stock_list = store_stock_list[-1][0]

                        # Check if there is a missmatch between what is on file vs new data
                        if (int(counter_list[2]) != len(store_stock_list)):

                            # Update counter by incrementing by 1
                            counter_edit = await product_dealer.edit_counter_data(user, product_number, [3,1])

                            # Error checking
                            if (counter_edit):

                                # For loop through stores in list to get exact stock data
                                for store_in_list in last_stock_list:

                                    # Once found, update the user
                                    if (store_in_list[0][:-1] == store_name):

                                        await channel.send(f'Hey {user.mention}!')
                                        if (int(counter_list[2]) != 0):
                                            await channel.send(f'The Product, {product_data[2][1]}, recently had a stock change at the {store_name} MemoryExpress store location!')
                                            await channel.send(f'The stock level is now {store_in_list[1]}')
                                            await channel.send(f'{product_data[1][1]}')
                                            break
                                        else:
                                            await channel.send(f'I am just confirming the stock level for the product, {product_data[2][1]}, at the {store_name} MemoryExpress store location!')
                                            await channel.send(f'The stock level is {store_in_list[1]}')
                                            await channel.send(f'If this number (or status) differs from the website, please contact an administrator')
                                            await channel.send(f'{product_data[1][1]}')

    # Error checking
    return True

# Method to check if a given file exists in a users directory
async def does_stock_file_exist(file_to_check, product_path):

    # file_to_check
    # 1 - General Stock history
    # 2 - Price History
    # 3 - Store Stock History

    # General Stock
    if (file_to_check == 1):

        # Check if the path exists
        if (path.exists(product_path + "/stock_history.pkl")):
            return True
        else:
            return False

    # Price History
    elif (file_to_check == 2):
        if (path.exists(product_path + "/price_history.pkl")):
            return True
        else:
            return False

    # Price History
    elif (file_to_check == 3):
        if (path.exists(product_path + "/store_stock_history.pkl")):
            return True
        else:
            return False

    return False