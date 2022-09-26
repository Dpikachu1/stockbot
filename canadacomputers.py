import requests
from bs4 import BeautifulSoup

headers = {"authority": "www.canadacomputers.com", "method": "GET", "scheme": "https", "pragma": "no-cache","cache-control": "no-cache","user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36","accept": "*/*", "sec-fetch-site": "same-origin", "sec-fetch-mode": "cors", "sec-fetch-dest": "empty", "accept-language": "en-US,en;q=0.9"}

# Stores are checked by the main bot script to tell if a certain store can be tracked
stores = ["Online / Main Warehouse", "ON Special Order Warehouse", "BC Special Order Warehouse", "Halifax", "Cambridge", "North York", "Oakville", "Ajax", "Barrie", "Brampton", "Burlington", "Etobicoke", "Hamilton", "Kanata", "Kingston", "London", "Markham", "Mississauga", "Newmarket", "Oshawa", "Downtown Ottawa", "Ottawa Merivale", "Ottawa Orleans", "Richmond Hill", "St. Catharines", "Downtown Toronto", "Scarborough", "Midtown Toronto", "Vaughan", "Waterloo", "Whitby", "Brossard", "Marché Central", "Gatineau", "Laval", "Montréal Downtown", "West Island", "Burnaby", "Port Coquitlam", "East Vancouver", "Richmond", "Vancouver Broadway"]

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
    shipping_status = None
    pickup_status = None
    store_stock_status = []
    return_code = [0,0]

    # Avoid errors stopping the bot
    try:
        # Check item ship status
        # Find the status span using beautifulsoup, navigating through the html file
        for div in soup.body.findAll('div', {"class": "page-product_info container pt-2 overflow-hidden"}):
            ship_status = div.find('div', {"class": "pi_loc-stock__box_online"})
            shipping_status = ship_status.text
        # [Stock Status, Is the item a combo]
        # 1 - In Stock
        # 2 - Out of Stock
        # 3 - Item is available for back-order
        # 4 - Item is available for pre-order
        if (shipping_status != None):
            if ("Online In Stock" in shipping_status or "AVAILABLE TO SHIP" in shipping_status):
                return_code[0] = 1
            elif ("Not Available Online" in shipping_status or "SOLD OUT ONLINE" in shipping_status):
                return_code[0] = 2
            elif ("Online Special Order" in shipping_status or "CUSTOM ORDER" in shipping_status):
                return_code[0] = 3
            elif ("Order Online and Pick Up In-Store" in shipping_status):
                return_code[0] = 4

            # Now Check Store Pickup (NOTE: CanadaComputers has changed how they handle both delivery and store pickup
            # They are both separate modules now!

            main_page = soup.body.find('div', {"class": "page-product_info container pt-2 overflow-hidden"})
            check_if_store_objects = main_page.find('div', {"id": "stock_detail"})

            # Error checking
            if (check_if_store_objects != None):
                pickup_status = check_if_store_objects.text.strip()


            # Check stores
            # pickup_status having a value of none indicates that the there is nothing available in any store location (or that this code is broken)
            if (pickup_status != None):
                try:
                    # For loop through all provinces
                    for div in soup.body.findAll('div', {"class": "item__avail"}):
                        # This class houses all stores for a specific location (all stores in a given province have the same class id so we for loop through all of them)
                        for stores in div.findAll('div', {"class": "item__avail__num"}):

                            # Get store (location) name
                            store_name = stores.find('div', {"class": "col-9"})

                            # Get stock status of store
                            store_stock = stores.find('div', {"class": "item-stock"})
                            stock_number = store_stock.find('span', {"class": "stocknumber"})

                            store_stock_status.append([store_name.text.strip(), stock_number.text.strip()])

                    return_code[1] = store_stock_status

                except:
                    return False

            elif ("In-Store Out Of Stock" in shipping_status):
                return_code[1] = False

            return return_code

        # Return False if everything completes but the button text is not found
        return False

    except:
        # If anything wonky occurs, just return False
        return False

# Method to get product name
async def get_product_name(soup):

    # Variable declaration
    title = None

    try:
        # Navigate through html
        for div in soup.body.findAll("div", {"class": "page-product_info container pt-2 overflow-hidden"}):
            title = div.find("h1", {"class": "h3 mb-0"})
            return title.text
    except:
        return False

    return False

# Method to get product price
async def get_product_price(soup):

    # Variable declaration
    price = None

    try:
        # Navigate through html
        for div in soup.body.findAll("div", {"class": "page-product_info container pt-2 overflow-hidden"}):
            price = div.find("span", {"class": "h2-big"})
            return price.text[1:-1]
    except:
        return False

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