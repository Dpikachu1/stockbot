import traceback

import requests
from bs4 import BeautifulSoup

# Spoofing header
headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}

# Stores are checked by the main bot script to tell if a certain store can be tracked
stores = ["Calgary NE", "Calgary NW", "Calgary SE", "Edmonton South", "Edmonton West", "Burnaby", "Langley", "Vancouver", "Victoria", "Winnipeg West", "Hamilton", "London", "Ottawa", "Saskatoon", "Online Store"]

# Method to get all product info
async def get_product_info(url):

    # Variable declaration
    stock = None
    product_name = None
    product_price = None
    soup = None

    try:
        # Download page content
        res = requests.get(url, headers=headers)

        # Convert to HTML
        soup = BeautifulSoup(res.content, 'html.parser')

        # Get all product aspects
        stock = await get_stock_status(soup)

        # Error check
        if (stock != False):
            product_name = await get_product_name(soup)
            product_price = await get_product_price(soup)
        else:
            return False

        # Error check
        if (product_name != False and product_price != False):
            # Return list of product data
            return [stock, product_name, product_price]
        else:
            return False
    except:
        return False

    return False

# Method to get the stock status of a product
async def get_stock_status(soup):

    # Variable declaration
    stock_status = None
    stock_status_stores = None
    store_stock_list = []
    return_code = [0,0]

    # Avoid errors stopping the bot
    try:
        # Check item ship status
        # Find the status span using beautifulsoup, navigating through the html file

        # Firstly, check the main availability, this will tell the bot if all stores are out of stock
        # Hence, avoiding a whole for loop mess
        status = soup.find('div', {"class": "c-capr-inventory__availability"})
        stock_status = status.text

        # Now check if shipping_status contains text that says the product is out of stock (or on special order)
        if ("Out of Stock" in stock_status):
            return_code[0] = 2
        elif ("Special Order" in stock_status):
            return_code[0] = 3
        elif ("Backorder" in stock_status):
            return_code[0] = 4
        elif ("Preorder" in stock_status):
            return_code[0] = 6

        # If this product is not out of stock everywhere, now check all stores for stock
        else:

            # Find the inventory box
            stock_status_stores = soup.find('div', {"class": "c-capr-inventory__selector"})

            # For loop through all store regions
            for region in stock_status_stores.findAll('li', attrs={'data-role': 'region'}):

                # Get the inventory data for that region
                store_list = region.find('div', {"class": "c-capr-inventory-region"})

                # For loop through every store in the region
                for store in store_list.findAll('div', {"class": "c-capr-inventory-store"}):

                    # Get the store name, it's stock number and append it to the list
                    store_name = store.find('span', {"class": "c-capr-inventory-store__name"})
                    store_stock_number = store.find('span', {"class": "c-capr-inventory-store__availability"})

                    # Strip to remove all the spacing garbage memoryexpress uses in it's html
                    store_stock_list.append([store_name.text.strip(), store_stock_number.text.strip()])

            # Get online store stock
            online_store_status = stock_status_stores.find('div', {"class": "c-capr-inventory-selector__details-online"})
            online_store_stock_number = online_store_status.find('span',{"class": "c-capr-inventory-store__availability InventoryState_InStock"})
            if (online_store_stock_number != None):
                store_stock_list.append(["Online Store:", online_store_stock_number.text.strip()])
                return_code[0] = 1
            else:
                store_stock_list.append(["Online Store:", "Out of Stock"])
                return_code[0] = 5

            return_code[1] = store_stock_list
        return return_code

    except:
        traceback.print_exc()
        return False

# Method to get product name
async def get_product_name(soup):

    try:
        # Find name of product
        product_name_object = soup.find('header', {"class": "c-capr-header"})
        product_name_text_object = product_name_object.find('h1')

        # Strip as per usual
        product_name = product_name_text_object.text.strip()
        return product_name
    except:
        return False

# Method to get product price
async def get_product_price(soup):

    try:
        # Get product price
        product_price_object = soup.find('div', {"class": "c-capr-pricing"})

        # Lots of stripping and splitting because of the garbage string that the html file from memoryexpress gives
        return product_price_object.text.strip().split("Only")[-1]
    except:
        return False

# Method to get soup object from url
async def get_soup(url):
    try:
        # Download page content
        res = requests.get(url, headers=headers)

        # Convert to HTML
        soup = BeautifulSoup(res.content, 'html.parser')

        return soup
    except:
        return False