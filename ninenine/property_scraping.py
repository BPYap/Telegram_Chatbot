#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time 

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

from property_code import property_code
from common.Property_listing import Property_listing

# agent may put listings on cheap price to promote their listings
# this variable set a minimum price to filter those listings out
sale_min_price = 30000 
rent_min_price = 80
    
def get_property_code(property_type):
    if (property_type == ""):
        return ""
    for code, info in property_code.iteritems():
        if (any(property_type.lower() == type for type in info["type"])):
            return code
    return ""

def get_listing(result_list, web_driver, forSale, location, property_type = ""): 
    # web_driver: selenium webdriver object
    # forSale: boolean value to indicate whether to find properties for Sale/ for Rental
    # location: string value to specify which location to search for
    # property_type: string value to specify property type, separated by '_' if more than one
    
    property_listings = [] # stores list of Property_listing object
    
    # url default to get properties for sale and sort by price in ascending order
    target_url = "https://www.99.co/singapore/sale?listing_type=sale&price_min=" + str(sale_min_price) + "&sort_field=price&sort_order=asc"
    if (not forSale):
        target_url = "https://www.99.co/singapore/rent?listing_type=rent&price_min=" + str(rent_min_price) + "&sort_field=price&sort_order=asc"
    
    main_flag = False
    sub_flag = False
    for p in property_type.split('_'):
        pcode = get_property_code(p)
        if (pcode != ""):
            if(pcode in ["condo", "landed", "hdb"]):
                if (not main_flag):
                    target_url += "&main_category=" + pcode
                    main_flag = True
                else:
                    target_url += "%2C" + pcode
    
    for p in property_type.split('_'):
        pcode = get_property_code(p)
        if (pcode != ""):
            if(pcode not in ["condo", "landed", "hdb"]):
                if (not sub_flag):
                    target_url += "&sub_categories=" + pcode
                    sub_flag = True
                else:
                    target_url += "%2C" + pcode
    
    # navigate to target_url, then fetch its page source once keywords is located (indicate page is fully loaded)
    web_driver.get(target_url)
    try:
        WebDriverWait(web_driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "ListingItem-innerWrapper")))
    except TimeoutException:
        result_list[:] = []
        return

    # type location in text box and choose first result
    if location:
        input_box = web_driver.find_element_by_xpath("//input[@class='typeahead tt-input']")
        input_box.send_keys(location)
        try:
            WebDriverWait(web_driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "tt-suggestions")))
            attempt = 0
            while (attempt < 10):
                try:
                    web_driver.find_element_by_xpath("//*[@class='tt-suggestions']").send_keys(Keys.ENTER)
                    time.sleep(1.5)
                    break
                except StaleElementReferenceException:
                    attempt += 1
        except TimeoutException:
            result_list[:] = []
            return
        
    html_doc = web_driver.page_source

    # grab desire contents from the html documnet with beautifulsoup
    soup = BeautifulSoup(html_doc, 'html.parser')

    for listing in soup.find_all(attrs={"class":"ListingItem-innerWrapper"}):
        location = listing.find(class_="location").get_text()
        
        description = ""
        description_tag = listing.find(class_="arrowContainer__3JU_o")
        if (description_tag):
            description = description_tag.get_text()
        
        num_bed = ""
        room_tag = listing.find(class_="bedrooms")
        if (room_tag):
            num_bed = room_tag.get_text()
        
        num_bath = ""
        bath_tag = listing.find(class_="bathrooms")
        if (bath_tag):
            num_bath = bath_tag.get_text()
        
        size = ""
        size_tag = listing.find(class_="sqft")
        if (size_tag):
            size = size_tag.get_text()
        
        fee = "S" + listing.find(class_="ListingItem-price").get_text()
        sort_key = int(fee.replace("S$","").replace(",",""))
        if (not forSale):
            fee = fee + " / month"
        
        style = listing.find(class_="listing-carousel-image")["style"]
        print style
        matched_url = re.match(r".*(https.*)['\"]\);", style)
        if (matched_url):
            img_url = matched_url.group(1)
        else:
            img_url = "99.co/static/img/placeholder/image-placeholder.png"
            
        listing_url = "https://99.co" + listing["href"]
        
        property_listings.append(Property_listing(location, description, "", size, fee, 
                                 num_bed, num_bath, img_url, listing_url, sort_key))
    
    result_list[:] = property_listings
    
    