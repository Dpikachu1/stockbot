import traceback

import requests
from bs4 import BeautifulSoup
import logging

import http.client
http.client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

# Method to get all product info
async def get_product_info(url):

    # Variable declaration
    stock = None
    product_name = None
    product_price = None
    soup = None

    # BestBuy does not like the default header sent to their servers
    # So send a much friendlier one!
    headers = {"authority": "www.bestbuy.ca", "method": "GET", "scheme": "https", "pragma": "no-cache","cache-control": "no-cache","user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36","accept": "*/*", "sec-fetch-site": "same-origin", "sec-fetch-mode": "cors", "sec-fetch-dest": "empty","referer": url, "accept-language": "en-US,en;q=0.9"}

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
            product_price = await get_product_price(url)
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
    #pickup_status = None
    isCombo = False
    
    # Avoid errors stopping the bot
    try:
        # Check item ship status
        # Find the status span using beautifulsoup, navigating through the html file
        for div in soup.body.findAll("div", id="root"):
            ship = div.find('p', {"class": "shippingAvailability_2X3xt"})
            ship_status = ship.find('span', {"class": "availabilityMessage_ig-s5 container_1DAvI"})
            shipping_status = ship_status.text
        # Check item pickup status - NOT IN USE
        # This feature would require way too much processing power (or at least more than a standard EC2 can reasonably handle)
        #for div in soup.body.findAll("div", id="root"):
            #try:
                #pick = div.find('div', {"class": "storeAvailabilityContainer_1Ez2A"})
                #store_status = pick.find('span', {"class": "availabilityMessage_ig-s5"})
                #pickup_status = store_status.text
            #except:
                #None

        # [Stock Status, Is the item a combo]           
        # 1 - In Stock
        # 2 - Out of Stock
        # 3 - Item is available for back-order
        # 4 - Item is available for pre-order
        if (shipping_status != None):
            if ("Available to ship" in shipping_status):
                return 1
            elif ("Sold out online" in shipping_status):
                return 2
            elif ("Available for backorder" in shipping_status):
                return 3
            elif ("Available for preorder" in shipping_status):
                return 4
            elif ("Scheduled Delivery" in shipping_status):
                return 5
            elif ("Coming soon" in shipping_status):
                return 6
            elif ("Available online only" in shipping_status):
                return 7

        # Return False if everything completes but the button text is not found
        return False

    except:
        traceback.print_exc()
        # If anything wonky occurs, just return False
        return False

# Method to get product name    
async def get_product_name(soup):

    # Variable declaration
    title = None
    
    try:
        # Navigate through html
        for div in soup.body.findAll("div", id="root"):
            title = div.find("h1")
            return title.text

    except:
        return False

    return False

# Method to get the product price
async def get_product_price(url):

    # Variable declaration
    headers = {"authority": "www.bestbuy.ca", "method": "GET", "scheme": "https", "pragma": "no-cache", "cache-control": "no-cache", "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36", "accept": "*/*", "sec-fetch-site": "same-origin", "sec-fetch-mode": "cors", "sec-fetch-dest": "empty", "referer": url, "accept-language": "en-US,en;q=0.9"}
    price = None

    # Error checking
    try:

        # Using BestBuys api to get the product price
        # Extract web code of the product from link

        # Split the url up unto elements in an array, splitting at each slash
        url_array = url.split("/")
        # The web code is at the end of the link so get that number via the last index of the array
        # We will lookup the price with a default postal code in Ontario (L7L)
        # Download page content
        res = requests.get("https://www.bestbuy.ca/api/offers/v1/products/" + url_array[-1] + "/offers?postalCode=L7L", headers=headers)
        # Convert to HTML
        soup = BeautifulSoup(res.content, 'html.parser')

        # The page that appears is a nice array with all product info
        # Get price
        product_info = soup.text.split(",")
        for element in product_info:
            if "salePrice" in element:
                price = element.split(":")[-1]
                return price
    except:
        return False

    return False

# Method to get soup object from url
async def get_soup(url):
    # BestBuy does not like the default header sent to their servers
    # So send a much friendlier one!
    headers = {"authority": "www.bestbuy.ca", "method": "GET", "scheme": "https", "pragma": "no-cache","cache-control": "no-cache","user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36","accept": "*/*", "sec-fetch-site": "same-origin", "sec-fetch-mode": "cors", "sec-fetch-dest": "empty","referer": url, "accept-language": "en-US,en;q=0.9"}

    try:
        # Download page content
        res = requests.get(url, headers=headers)

        # Convert to HTML
        soup = BeautifulSoup(res.content, 'html.parser')

        return soup
    except:
        return False