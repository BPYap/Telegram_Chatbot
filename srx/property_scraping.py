#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from property_code import property_code
from common.Property_listing import Property_listing
    
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
    
    pcode = ""
    for p in property_type.split('_'):
        pcode = get_property_code(p)
        if(pcode):
            break # this website only allow one type
    
    location = '+'.join(location.split()) # space is replaced with '+'
    
    if pcode:
        target_url = "https://www.srx.com.sg/search/sale/" + pcode + "/" + location + "/?orderCriteria=priceAsc"
        if(not forSale):
            target_url = "https://www.srx.com.sg/search/rent/" + pcode + "/" + location + "/?orderCriteria=priceAsc"
    elif property_type == "":
        target_url = "https://www.srx.com.sg/search/sale/residential/" + location + "?orderCriteria=priceAsc"
        if (not forSale):
            target_url = "https://www.srx.com.sg/search/rent/residential/" + location + "?orderCriteria=priceAsc"
    else:
        result_list[:] = []
        return
    
    # navigate to target_url, then fetch its page source once keywords is located (indicate page is fully loaded)
    web_driver.get(target_url)
    try:
        WebDriverWait(web_driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "listing")))
    except TimeoutException:
        result_list[:] = []
        return
        
    html_doc = web_driver.page_source

    # grab desire contents from the html documnet with beautifulsoup
    soup = BeautifulSoup(html_doc, 'html.parser')

    for listing in soup.find_all(attrs={"class":"listingContainer"}):
        location = listing.find(class_="listingDetailTitle").find(class_='notranslate').get_text()
        
        description = ""
        description_tag = listing.find(class_="listingDetailSubTitle")
        if (description_tag):
            description = description_tag.get_text()
        
        num_bed = ""
        room_tag = listing.find(class_="listingDetailRoomNo")
        if (room_tag):
            num_bed = room_tag.get_text()
        
        num_bath = ""
        bath_tag = listing.find(class_="listingDetailToiletNo")
        if (bath_tag):
            num_bath = bath_tag.get_text()
                
        size = ""
        size_tag = listing.find(class_="listingDetailSize")
        if (size_tag):
            size = size_tag.get_text()
        
        price_tag = listing.find(class_="listingDetailPrice")
        if(price_tag):
            fee = "S" + price_tag.get_text().strip()
            sort_key = int(fee.strip().replace("S$","").replace(",",""))
            if (not forSale):
                fee = fee + " / month"
        else:
            continue # skip if no price
        
        style = listing.find(class_="listing-carousel-image")["style"]
        if ("url" in style.split(";")[1]):
            if (forSale):
                img_url = style.split(";")[1][24:-2]
            else:
                img_url = style.split(";")[1][22:-2]
        else:
            img_url = "99.co/static/img/placeholder/image-placeholder.png"
        if img_url[0] == "t":
            img_url = "ht" + img_url # temporary work around for truncated image url
            
        img_url = "srx.com.sg" + listing.find(class_="listingPhotoMain").find("a")["href"]
            
        listing_url = "srx.com.sg" + listing.find(class_="listingDetail").find("a")["href"]
        
        property_listings.append(Property_listing(location, description, "", size, fee, 
                                 num_bed, num_bath, img_url, listing_url, sort_key))
    
    result_list[:] = property_listings
    
    