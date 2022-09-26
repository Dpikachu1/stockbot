import discord
import os
import shutil

# Get working directory of python script
working_directory = os.getcwd()
# Add a directory userData
full_dir = (working_directory + "/userData")

# Directory for where all users are stored
user_storage_path = (full_dir + "/users")

# Method to create a product
async def store_product(product_data):
    # product_data contains the following
    # user, website_type product_link and product_name

    # Extract the user_id and find their associated directory
    user_id = str(product_data[0].id)
    user_directory = (user_storage_path + "/" + user_id + "/" + "product_data")

    # Check if and how many products are already stored inside their files

    number_of_products = 0

    # Check which file names exist
    product_name_list = [False, False, False, False, False]

    # List all files and folders in the users file
    for directory in os.listdir(user_directory):
        # Join both the name of the item and the whole path before
        item = os.path.join(user_directory, directory)
        # Check if that is a directory
        if os.path.isdir(item):
            product_file_name = int(directory[8:])

            # Why do this? Because directories can be deleted at the users request so it's better to operate it like "save slots"
            product_name_list[product_file_name-1] = True

            # If it is, it must be a product
            number_of_products += 1

    # A maximum of five products check
    if number_of_products == 5:
        return False
    else:
        # Create a new directory for the product

        product_id = 0

        # Find the first available name
        for name in product_name_list:
            if (name == False):
                break
            else:
                product_id += 1


        product_dir = (user_directory + "/" + "product-" + str(product_id + 1))
        os.mkdir(product_dir)

        # Write product data to file
        product_data_file = open(product_dir + "/product_data.txt", "w")
        product_data_file.write("WEBSITE_TYPE=" + product_data[1] + "\n")
        product_data_file.write("PRODUCT_LINK=" + product_data[2] + "\n")
        product_data_file.write("PRODUCT_NAME=" + product_data[3] + "\n")
        product_data_file.write("NOTIFY_DISABLE=False" + "\n")
        product_data_file.write("NOTIFY_BACKORDER=True" + "\n")

        # Newegg, Best Buy and MemoryExpress are the only pre-order enabled websites
        product_data_file.write("NOTIFY_PREORDER=False" + "\n")

        # Note that price will need it's own separate file if enabled
        product_data_file.write("NOTIFY_PRICE=False" + "\n")

        # CanadaComputers and MemoryExpress allow for this bot to grab individual store stock
        # While the specific file will not be created (to save space), it's settings will be
        if (product_data[1] == "CanadaComputers" or product_data[1] == "MemoryExpress"):
            product_data_file.write("NOTIFY_STORE=False" + "\n")
            product_data_file.write("NOTIFY_STORE_SPECIFIC=False" + "\n")
            product_data_file.write("NOTIFY_STORE_NAME=X" + "\n")

        product_data_file.close()

        # Create stock list counter file
        product_stock_file = open(product_dir + "/product_stock_list_count.txt", "a+")
        product_stock_file.write("STOCK_LIST=0" + "\n")
        product_stock_file.write("STOCK_PRICE_LIST=0" + "\n")
        product_stock_file.write("STOCK_STORE_LIST=0" + "\n")
        product_stock_file.close()

        return True

# Method to get a list of all counters that are being used to track stock history data
# In the return list: Index 0 is regular stock, 1 is price history and 2 is store
async def retrieve_counter_data(user, product_number):

    return_list = []

    # Extract the user_id and find their associated directory
    user_id = str(user.id)
    user_directory = (user_storage_path + "/" + user_id + "/" + "product_data")

    # Get product directory
    product_dir = (user_directory + "/" + "product-" + str(product_number))

    product_stock_counter_file = open(product_dir + "/product_stock_list_count.txt", "r")

    data_list = product_stock_counter_file.readlines()
    product_stock_counter_file.close()

    for data in data_list:
        # Split the line on the =. Also strip to get rid of spacing garbage
        line = data.strip().split("=")
        return_list.append(line[1])

    return return_list

# Method to edit the counter data
async def edit_counter_data(user, product_number, data):
    # data is a list that includes the specific line to edit (index zero) and by how much (index one)
    # Negatives values are accepted for index one
    # Extract the user_id and find their associated directory
    user_id = str(user.id)
    user_directory = (user_storage_path + "/" + user_id + "/" + "product_data")

    # Get product directory
    product_dir = (user_directory + "/" + "product-" + str(product_number))

    product_stock_counter_file = open(product_dir + "/product_stock_list_count.txt", "r")

    data_list = product_stock_counter_file.readlines()
    product_stock_counter_file.close()

    # Stock history list
    if (data[0] == 1):

        # Get the current value on file (strip the "/n" and split on the equals sign)
        current_value = int(data_list[0].strip().split("=")[1])

        # Create the new value
        new_value = current_value + data[1]

        # Apply the new value to the list
        data_list[0] = ("STOCK_LIST=" + str(new_value) + "\n")

    # Stock price history list
    elif (data[0] == 2):

        # Get the current value on file (strip the "/n" and split on the equals sign)
        current_value = int(data_list[1].strip().split("=")[1])

        # Create the new value
        new_value = current_value + data[1]

        # Apply the new value to the list
        data_list[1] = ("STOCK_PRICE_LIST=" + str(new_value) + "\n")

    # Stock store history list
    elif (data[0] == 3):

        # Get the current value on file (strip the "/n" and split on the equals sign)
        current_value = int(data_list[2].strip().split("=")[1])

        # Create the new value
        new_value = current_value + data[1]

        # Apply the new value to the list
        data_list[2] = ("STOCK_STORE_LIST=" + str(new_value) + "\n")


    # Open the file again, this time in write mode to erase everything
    product_stock_counter_file = open(product_dir + "/product_stock_list_count.txt", "w")

    # Write new data to the file
    product_stock_counter_file.writelines(data_list)

    product_stock_counter_file.close()

    return True

# Method to get a list of all the product settings for a particular product
async def retrieve_product_settings(user, product_number):

    return_list = []

    # Extract the user_id and find their associated directory
    user_id = str(user.id)
    user_directory = (user_storage_path + "/" + user_id + "/" + "product_data")

    # Get product directory
    product_dir = (user_directory + "/" + "product-" + str(product_number))

    # Open data file
    product_data_file = open(product_dir + "/product_data.txt", "r")

    data_list = product_data_file.readlines()
    product_data_file.close()

    for data in data_list:
        # Split the line on the =. Also strip to get rid of spacing garbage
        # The 1 splits this on the equals first occurrence only
        # This is due to URLs containing equal signs in them
        line = data.strip().split("=", 1)
        return_list.append(line)

    return return_list



# Method returns a product list for a given user
async def retrieve_product_list(user):

    product_list = []

    # Extract the user_id and find their associated directory
    user_id = str(user.id)
    user_directory = (user_storage_path + "/" + user_id + "/" + "product_data")

    # List all files and folders in the users file
    for directory in os.listdir(user_directory):
        # Join both the name of the item and the whole path before
        product_path = os.path.join(user_directory, directory)

        # Open product data file and get the name of the product
        product_data_file = open(product_path + "/product_data.txt", "r")
        product_data_text = product_data_file.readlines()
        product_name = product_data_text[2][:-1]

        # [8:] to only get product number in saves
        product_list.append([directory[8:],product_name])

    return product_list

# Method to change product specific settings for a given user
# NOTE: This method assumes that data exists in the file!
async def product_settings(user, action):
    # Action list [true action, product file save number, any other info needed]
    # 1 - Change Backorder
    # 2 - Change preorder
    # 3 - Change price checking
    # 4 - Change store stock notifications
    # 5 - Change specific store stock notifications
    # 6 - Change specific store name
    # 7 - Change Disable notifications
    # 8 - Delete product file

    # 1 - Change backorder

    if (action[0] == 1):
        # Extract the user_id and find their associated directory
        user_id = str(user.id)
        product_data_directory = (user_storage_path + "/" + user_id + "/" + "product_data" + "/" + "product-" + str(action[1]))

        # Open file and read the data
        product_data_file = open(product_data_directory + "/product_data.txt", "r")
        product_data_text = product_data_file.readlines()
        product_data_file.close()

        # Reopen the file but this time, wipe it
        product_data_file = open(product_data_directory + "/product_data.txt", "w")

        # Change specified data
        if (product_data_text[4][17:-1] == "True"):
            product_data_text[4] = ("NOTIFY_BACKORDER=False" + "\n")
        elif (product_data_text[4][17:-1] == "False"):
            product_data_text[4] = ("NOTIFY_BACKORDER=True" + "\n")

        # Write new data
        product_data_file.writelines(product_data_text)
        product_data_file.close()

        return True


    # 2 - Change preorder

    if (action[0] == 2):
        # Extract the user_id and find their associated directory
        user_id = str(user.id)
        product_data_directory = (user_storage_path + "/" + user_id + "/" + "product_data" + "/" + "product-" + str(action[1]))

        # Open file and read the data
        product_data_file = open(product_data_directory + "/product_data.txt", "r")
        product_data_text = product_data_file.readlines()
        product_data_file.close()

        # Reopen the file but this time, wipe it
        product_data_file = open(product_data_directory + "/product_data.txt", "w")

        # Change specified data
        if (product_data_text[5][16:-1] == "True"):
            product_data_text[5] = ("NOTIFY_PREORDER=False" + "\n")
        elif (product_data_text[5][16:-1] == "False"):
            product_data_text[5] = ("NOTIFY_PREORDER=True" + "\n")

        # Write new data
        product_data_file.writelines(product_data_text)
        product_data_file.close()

        return True

    # 3 - Change price checking

    if (action[0] == 3):
        # Extract the user_id and find their associated directory
        user_id = str(user.id)
        product_data_directory = (user_storage_path + "/" + user_id + "/" + "product_data" + "/" + "product-" + str(action[1]))

        # Open file and read the data
        product_data_file = open(product_data_directory + "/product_data.txt", "r")
        product_data_text = product_data_file.readlines()
        product_data_file.close()

        # Reopen the file but this time, wipe it
        product_data_file = open(product_data_directory + "/product_data.txt", "w")

        # Change specified data
        if (product_data_text[6][13:-1] == "True"):
            # CODE BELOW IS NOT IN USE! MEANT FOR STOCK ENGINE TO DEAL WITH
            # If it was true, there must have been a file to determine the price
            # It needs to be deleted
            #os.remove(product_data_directory + "/product_data_price.txt")
            product_data_text[6] = ("NOTIFY_PRICE=False" + "\n")
        elif (product_data_text[6][13:-1] == "False"):
            # Create the price file -- NOT IN USE HERE, MEANT FOR STOCK ENGINE TO DEAL WITH
            #product_price_file = open(product_data_directory + "/product_data_price.txt", "r")
            #product_price_file.close()
            product_data_text[6] = ("NOTIFY_PRICE=True" + "\n")

        # Write new data
        product_data_file.writelines(product_data_text)
        product_data_file.close()

        return True

    # 4 - Change store stock notifications

    if (action[0] == 4):
        # Extract the user_id and find their associated directory
        user_id = str(user.id)
        product_data_directory = (user_storage_path + "/" + user_id + "/" + "product_data" + "/" + "product-" + str(action[1]))

        # Open file and read the data
        product_data_file = open(product_data_directory + "/product_data.txt", "r")
        product_data_text = product_data_file.readlines()
        product_data_file.close()

        # Reopen the file but this time, wipe it
        product_data_file = open(product_data_directory + "/product_data.txt", "w")

        # Change specified data
        if (product_data_text[7][13:-1] == "True"):
            product_data_text[7] = ("NOTIFY_STORE=False" + "\n")
        elif (product_data_text[7][13:-1] == "False"):
            product_data_text[7] = ("NOTIFY_STORE=True" + "\n")

        # Write new data
        product_data_file.writelines(product_data_text)
        product_data_file.close()

        return True

    # 5 - Change specific store stock notifications

    if (action[0] == 5):
        # Extract the user_id and find their associated directory
        user_id = str(user.id)
        product_data_directory = (user_storage_path + "/" + user_id + "/" + "product_data" + "/" + "product-" + str(action[1]))

        # Open file and read the data
        product_data_file = open(product_data_directory + "/product_data.txt", "r")
        product_data_text = product_data_file.readlines()
        product_data_file.close()

        # Reopen the file but this time, wipe it
        product_data_file = open(product_data_directory + "/product_data.txt", "w")

        # Change specified data
        if (product_data_text[8][22:-1] == "True"):
            product_data_text[8] = ("NOTIFY_STORE_SPECIFIC=False" + "\n")
        elif (product_data_text[8][22:-1] == "False"):
            product_data_text[8] = ("NOTIFY_STORE_SPECIFIC=True" + "\n")

        # Write new data
        product_data_file.writelines(product_data_text)
        product_data_file.close()

        return True


    # 6 - Change specific store name

    if (action[0] == 6):
        # Extract the user_id and find their associated directory
        user_id = str(user.id)
        product_data_directory = (user_storage_path + "/" + user_id + "/" + "product_data" + "/" + "product-" + str(action[1]))

        # Open file and read the data
        product_data_file = open(product_data_directory + "/product_data.txt", "r")
        product_data_text = product_data_file.readlines()
        product_data_file.close()

        # Reopen the file but this time, wipe it
        product_data_file = open(product_data_directory + "/product_data.txt", "w")
        product_data_text[9] = ("NOTIFY_STORE_NAME=" + action[2] + "\n")

        # Write new data
        product_data_file.writelines(product_data_text)
        product_data_file.close()

        return True

    # 7 - Change disable all notifications

    if (action[0] == 7):
        # Extract the user_id and find their associated directory
        user_id = str(user.id)
        product_data_directory = (user_storage_path + "/" + user_id + "/" + "product_data" + "/" + "product-" + str(action[1]))

        # Open file and read the data
        product_data_file = open(product_data_directory + "/product_data.txt", "r")
        product_data_text = product_data_file.readlines()
        product_data_file.close()

        # Reopen the file but this time, wipe it
        product_data_file = open(product_data_directory + "/product_data.txt", "w")
        # Change specified data
        if (product_data_text[3][15:-1] == "True"):
            product_data_text[3] = ("NOTIFY_DISABLE=False" + "\n")
        elif (product_data_text[3][15:-1] == "False"):
            product_data_text[3] = ("NOTIFY_DISABLE=True" + "\n")

        # Write new data
        product_data_file.writelines(product_data_text)
        product_data_file.close()

        return True

    # 8 - Delete all product data

    if (action[0] == 8):
        # Extract the user_id and find their associated directory
        user_id = str(user.id)
        product_data_directory = (user_storage_path + "/" + user_id + "/" + "product_data" + "/" + "product-" + str(action[1]))

        # Delete all files
        shutil.rmtree(product_data_directory)

        return True