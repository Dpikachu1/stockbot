# Amazon stock checker script
# This script gathers information about a product on amazon.ca given an amazon.ca url
# Note this ONLY checks if amazon.ca is stocking the product and will ignore third-party merchants!
# 2022 - Davis Lenover

import requests
from bs4 import BeautifulSoup
# Due to a delay in page loading, selenium and a headless browser (firefox) need to be used
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import traceback

# Wait time for browser to wait before grabbing page source (because amazon takes time to load everything) (in seconds)
default_wait_time = 4

# After each failed attempt to grab page information, increase wait time by x seconds (default_wait_time + wait_time_increment)
wait_time_increment = 2


headers = {"authority": "www.amazon.ca", "method": "GET", "scheme": "https", "pragma": "no-cache","cache-control": "no-cache","user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36","accept": "*/*", "sec-fetch-site": "same-origin", "sec-fetch-mode": "cors", "sec-fetch-dest": "empty", "accept-language": "en-US,en;q=0.9"}

# Method to get all product info
async def get_product_info(soup, need_price, need_name):

    # Variable declaration
    stock = None
    product_name = None

    try:
        # Get all product aspects

        # Sometimes, the webpage may not load correctly, so try at least 3 times
        attempts_stock = 1
        extra_wait_time = 0
        end = False
        while (attempts_stock < 5):
            # The page may just need more time to load so add wait time to browser as specified by variables
            if (attempts_stock == 1):
                extra_wait_time = 0
            else:
                extra_wait_time = extra_wait_time + wait_time_increment
            stock = await get_stock_and_price_status(soup, extra_wait_time, need_price)
            # Return codes for stock[0]:
            # 1 - In-Stock
            # 2 - Out of Stock
            # 3 - Offers page failed to load
            # 4 - Amazon may not be a seller of this item
            # 5 - Pre-order
            # 6 - Backorder
            # stock[2] codes:
            # xx.xx - Price found (x's replaced with actual price)
            # False - Fatal Error
            # None - Product is out of stock and/or an error from stock[0] occurred
            if (stock[0] == 3 and attempts_stock != 4):
                print("Offers page failed to load correctly, retrying...(Attempts: " + str(attempts_stock) + ")")
                attempts_stock = attempts_stock + 1
            if (stock[0] == 3 and attempts_stock == 4):
                end = True
                break
            if (stock[0] != 3):
                break

        if (end == True):
            print("Offers page failed to load correctly after 3 attempts!")
            print("If this error is persistent, please check that this script is using the most up to date html code.")
            return False


        # Error check
        if (stock[0] != False):
            if (need_name == True):
                product_name = await get_product_name(soup)
        else:
            return False

        # Error check
        if (product_name != False and stock[0] != False and stock[1] != False):
            # Return list of product data [Name, Stock, Price]
            return [product_name, stock[0], stock[1]]
        else:
            return False
    except:
        traceback.print_exc()
        return False

    return False


# Method to get product name
async def get_product_name(soup):

    # Variable declaration
    title = None
    columnData = None

    try:
        # Navigate through html and find product title
        for div in soup.body.findAll("div", id="ppd"):
            columnData = div.find("div", id="centerCol")
            title = columnData.find('span', id="productTitle")
            return title.text.strip()
    except:
        traceback.print_exc()
        return False

    return False

async def get_stock_and_price_status(soup, extra_time, need_price):

    try:

        # Top methods check if the first page has any information on stock and price
        # This removes the need to use selenium
        # Some pages may just show that the item is currently unavailable so quickly check
        avail = soup.find("div", id="outOfStock")
        # Check for None as if object is not found, bs4 returns none
        if (avail != None):
            return [2, None]

        # Some items only amazon sells (no other seller) so check if front page says product is in stock quickly
        avail = soup.find("div", id="availability")
        if (avail != None):
            # Got to be careful with text here as amazon has stock messaging that may confuse the script (like the word "in stock" as a backorder)
            if (("In Stock" in avail.getText()) or ("in stock" in avail.getText())) and (not (("out of stock" in avail.getText()) or (("Out of stock" in avail.getText())) or (("Usually ships within" in avail.getText())))):

                # Check if Amazon is actual seller
                merchant = soup.find("div", id="merchant-info")

                # It's ok if main listing is not from amazon, we will have to check offer list (aka use selenium)
                if (merchant != None):
                    if "Ships from and sold by Amazon.ca" in merchant.getText():
                        # Check if pricing is needed
                        if (need_price == True):
                            # Get price
                            price_check_whole = soup.find("span", attrs={'class': 'a-price-whole'})
                            price_check_fraction = soup.find("span", attrs={'class': 'a-price-fraction'})

                            # Error check
                            if (price_check_whole != None and price_check_fraction != None):
                                return [1,"$"+price_check_whole.getText().strip() + price_check_fraction.getText().strip()]
                            else:
                                return [1,False]
                        else:
                            return [1, None]

            # Check if the product is available for pre-order
            if ("Pre-order" in avail.getText()):

                # Check if Amazon is actual seller
                merchant = soup.find("div", id="merchant-info")

                # It's ok if main listing is not from amazon, we will have to check offer list (aka use selenium)
                if (merchant != None):
                    if "Ships from and sold by Amazon.ca" in merchant.getText():
                        # Check if pricing is needed
                        if (need_price == True):
                            # Get price
                            price_check_whole = soup.find("span", attrs={'class': 'a-price-whole'})
                            price_check_fraction = soup.find("span", attrs={'class': 'a-price-fraction'})

                            # Error check
                            if (price_check_whole != None and price_check_fraction != None):
                                return [5,"$"+price_check_whole.getText().strip() + price_check_fraction.getText().strip()]
                            else:
                                return [5,False]
                        else:
                            return [5, None]

            # Check if the product is available for back-order
            if ("Temporarily out of stock" in avail.getText()) or (("Usually ships within" in avail.getText())):

                # Check if Amazon is actual seller
                merchant = soup.find("div", id="merchant-info")

                # It's ok if main listing is not from amazon, we will have to check offer list (aka use selenium)
                if (merchant != None):
                    if "Ships from and sold by Amazon.ca" in merchant.getText():
                        # Check if pricing is needed
                        if (need_price == True):
                            # Get price
                            price_check_whole = soup.find("span", attrs={'class': 'a-price-whole'})
                            price_check_fraction = soup.find("span", attrs={'class': 'a-price-fraction'})

                            # Error check
                            if (price_check_whole != None and price_check_fraction != None):
                                return [6,"$"+price_check_whole.getText().strip() + price_check_fraction.getText().strip()]
                            else:
                                return [6,False]
                        else:
                            return [6, None]


        # Navigate through html to find offer listings
        # By default, Amazon hides the all seller listings for a specific product under a link
        # So, we need to find that link which will open all listings
        offer_listing_link = soup.select_one("a[href*='gp/offer-listing']")

        # If the offer listing link doesn't exist, then amazon.ca is not a seller of this item
        if (offer_listing_link == None):
            return[4,None]

        # If we pass the if statement, continue to get link to offers list
        offer_listing_link = soup.select_one("a[href*='gp/offer-listing']").get("href")

        # Now, we goto that page
        try:

            # Code below does not work!
            # This fails because the page has not fully loaded. We need to use a headless browser instead
            #response = requests.get("https://www.amazon.ca/" + offer_listing_link, headers=headers)

            # Spoofed useragent
            linux_useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"

            # Create and run a headless version of firefox
            fireFoxOptions = Options()
            fireFoxOptions.headless=True
            profile = webdriver.FirefoxProfile()
            opts = webdriver.FirefoxOptions()
            # Add optional arguments
            opts.add_argument("--headless")
            opts.add_argument("user-agent=#{linux_useragent}")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-web-security")
            opts.add_argument("--disable-xss-auditor")
            # Apply optional arguments
            browser = webdriver.Firefox(options=opts)

            # Tell browser to wait x seconds when loading webpage
            browser.implicitly_wait(default_wait_time + extra_time)
            # Open new page
            browser.get("https://www.amazon.ca" + offer_listing_link)
            # Get page source
            html = browser.page_source

            # Convert to HTML
            soup = BeautifulSoup(html, 'html.parser')
            # Close browser (no longer needed)
            browser.quit()

            # Navigate through html (pinned offer is typically reserved for amazon)
            # If not, there's code below to deal with that
            pinned_offer = soup.find("div", id="aod-pinned-offer")

            # Error check to see if soup did not find a pinned-offer (indicates website may not have loaded correctly and needs to be refreshed or website html may have changed and this script needs to be updated)
            if (pinned_offer == None):
                # Indicate to main script that website may have not loaded correctly, try again
                return [3,None]

            check_stock = pinned_offer.find("input", attrs={'name':'submit.addToCart'})

            # If check_stock is none type, then bs4 did not find add to cart button, indicating the product is out of stock
            if (check_stock != None):
                # If the pinned offer has a "add to cart" button, product is in-stock
                if "Add to Cart from seller Amazon.ca" in check_stock.get("aria-label"):
                    # 1 = In Stock
                    # 2 = Out of Stock

                    # Check if price is needed
                    if (need_price == True):
                        # Find price (whole is the number before decimal)
                        price_check_whole = pinned_offer.find("span", attrs={'class':'a-price-whole'})
                        price_check_fraction = pinned_offer.find("span", attrs={'class': 'a-price-fraction'})

                        # Return data accordingly
                        if (price_check_whole != None and price_check_fraction != None):
                            return [1,"$"+price_check_whole.getText().strip()+price_check_fraction.getText().strip()]
                        else:
                            return [1, False]
                    else:
                        return[1, None]

            # Amazon may not be the pinned seller, check all offers
            # Navigate html
            offer_display = soup.body.find("div", id="all-offers-display-scroller")
            offers = offer_display.find("div", id="aod-container")

            # For loop all offers, checking their seller
            # I love nested if statements :(
            for offer in offers.find_all("div", attrs={'id':'aod-offer'}):
                soldby = offer.find("div", id="aod-offer-soldBy")
                if (soldby != None):
                    # If "Amazon.ca" is found as a seller, check if the add to cart button is on and price
                    if "Amazon.ca" in soldby.getText():
                        cart_button = offer.find("input", attrs={'name':'submit.addToCart'})
                        if (cart_button != None):
                            # Find price (whole is the number before decimal)
                            if (need_price == True):
                                price_check_whole = offer.find("span", attrs={'class': 'a-price-whole'})
                                price_check_fraction = offer.find("span", attrs={'class': 'a-price-fraction'})
                                if (price_check_whole != None and price_check_fraction != None):
                                    return [1, "$"+price_check_whole.getText().strip() + price_check_fraction.getText().strip()]
                            else:
                                return[1, None]

            # At this point, amazon.ca is likely not a seller (currently)
            return[4,None]



        except:
            traceback.print_exc()
            return [False, False]
    except:
        traceback.print_exc()
        return [False, False]

    return [False, False]

# Method to get soup object from url
async def get_soup(url):
    try:
        # Download page content
        res = requests.get(url, headers=headers)

        # Convert to HTML
        soup = BeautifulSoup(res.content, 'html.parser')

        return soup
    except:
        traceback.print_exc()
        return False

# Debugging
# To use script independently, delete all traces of async and await
# print(get_product_info(get_soup("insert amazon.ca link"), True, True))