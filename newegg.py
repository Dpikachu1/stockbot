import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}

# Method to get all product info
async def get_product_info(url):

    # Variable declaration
    stock = None
    product_name = None
    product_price = None
    soup = None

    try:
        # Download page content
        res = requests.get(url)

        # Convert to HTML
        soup = BeautifulSoup(res.content, 'html.parser')

        # Get all product aspects
        stock = await get_stock_status(soup)

        # Error check
        if (stock != False):
            product_name = await get_product_name(soup, stock[1])
            product_price = await get_product_price(soup, stock[1])
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
    button = None
    isCombo = False

    # Avoid errors stopping the bot
    try:
        # Check for cart button assuming a non-combo product
        # Find the cart button using beautifulsoup, navigating through the html file
        for div in soup.body.findAll("div", {"class": "product-buy"}):
            button = div.find('button', {"class": "btn btn-primary btn-wide"})
            # Button class may be secondary in html code so if primary does not work, try it
            if (button == None):
                button = div.find('button', {"class": "btn btn-secondary btn-wide"})

        # Check for cart button assuming a combo product
        # This will only run if the non-combo part of the script fails to find the button
        if (button == None):
            for div in soup.body.findAll("div", id="container"):
                body_area = div.find("div", id="bodyArea")
                button = body_area.find("a", {"class": "atnPrimary"})
                if (button != None):
                    isCombo = True
                
        # [Stock Status, Is the item a combo]           
        # 1 - In Stock
        # 2 - Out of Stock (Notify)
        # 3 - Item is available for back-order
        # 4 - Item is available for pre-order
        if (button != None and isCombo != True):
            if ("Add to cart" in button.text):
                return [1, False]
            elif ("Auto Notify" in button.text):
                return [2, False]
            elif ("Back order" in button.text):
                return [3, False]
            elif ("Pre-order" in button.text):
                return [4, False]
            
        elif (button != None and isCombo != False):
            if ("Add to Cart" in button.text):
                return [1, True]
            elif ("Auto Notify" in button.text):
                return [2, True]
            elif ("Pre-order" in button.text):
                return [4, True]

        # Return False if everything completes but the button text is not found
        return False
    
    except:
        # If anything wonky occurs, just return False
        return False

# Method to get product name    
async def get_product_name(soup, is_combo):

    # Variable declaration
    combo = is_combo
    title = None

    try:
        # Non combo method to finding the product name
        if (not combo):
            # Navigate through html
            for div in soup.body.findAll("div", {"class": "product-wrap"}):
                title = div.find("h1", {"class": "product-title"})
                return title.text

        # Combo method to finding the product name
        elif (combo):
            for div in soup.body.findAll("div", id="container"):
                body_area = div.find("div", id="bodyArea")
                title = body_area.find("span", itemprop="name")
                return title.text
    except:
        return False

    return False
    

# Method to get the product price
async def get_product_price(soup, is_combo):

    # Variable declaration
    combo = is_combo
    price = None

    try:
        # Non combo method to finding the product price
        if (not combo):
            for div in soup.body.findAll("div", {"class": "product-price"}):
                price = div.find("li", {"class": "price-current"})
                return price.text

        # Combo method  
        elif (combo):
            for div in soup.body.findAll("div", id="container"):
                body_area = div.find("div", id="bodyArea")
                price = body_area.find("div", id="singleFinalPrice")

                # The way the price is stored in the html file is a little wonky so, this fixes it
                if ("Now:" in price.text):
                    # Basically a split but keep the split parameter
                    price_data = price.text.partition("$")
                    price_text = price_data[1] + price_data[2]
                    return price_text
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