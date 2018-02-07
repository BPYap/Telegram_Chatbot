#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from bs4 import BeautifulSoup

from district_code import district_code
from district_code import hdb_estate
from property_code import property_code

class Property_listing:    
    def __init__(self, location, description, type, size, fee, num_bed, num_bath, img_url, listing_url):
        self.location = location
        self.description = description
        self.type = type
        self.size = size
        self.fee = fee
        self.num_bed = num_bed
        self.num_bath = num_bath
        self.img_url = img_url
        self.listing_url = listing_url
        
def get_district_code(location):
    for code, districts in district_code.iteritems():
        if (location.title() in districts):
            return code
    return ""
    
def get_hdb_estate_code(location):
    temp = 1
    for districts in hdb_estate:
        if location.title() in districts:
            return str(temp)
        else:
            temp += 1
    return ""
    
def get_property_code(property_type):
    for code, info in property_code.iteritems():
        if (property_type.lower() == info["type"]):
            return (code, info["isHdb"])
    return ("", None)

def get_listing(web_driver, forSale, location, property_type = ""): 
    # web crawler function to get property listings from propertyguru.com.sg
    # web_driver: selenium webdriver object
    # forSale: boolean value to indicate whether to find properties for Sale/ for Rental
    # location: string value to specify which location to search for
    # property_type: string value to specify property type, separated by '_' if more than one
    
    property_listings = [] # stores list of Property_listing object
    
    # url default to get properties for sale and sort by price in ascending order
    target_url = "https://www.propertyguru.com.sg/singapore-property-listing/property-for-sale?market=residential&freetext=" + location + "&sort=price&order=asc"
    if (not forSale):
        target_url = "https://www.propertyguru.com.sg/singapore-property-listing/property-for-rent?market=residential&freetext=" + location + "&sort=price&order=asc"
    
    containHdb = False
    for p in property_type.split('_'):
        pcode, isHdb = get_property_code(p)
        if isHdb:
            containHdb = True
        if (pcode != ""):
            if(pcode == "N" or pcode == "L" or pcode == "H"):
                target_url += "&property_type=" + pcode
            else:
                target_url += "&property_type_code%5B%5D=" + pcode
       
    # using hdb_estate_code/district_code is more accurate than using freetext
    if containHdb:
        hcode = get_hdb_estate_code(location)
        if hcode != "":
            target_url += "&hdb_estate%5B%5D=" + hcode
    else:
        dcode = get_district_code(location)
        if dcode != "":
            target_url += "&district_code%5B%5D=" + dcode 
    
    # navigate to target_url, then fetch its page source once "search-title" is located (indicate page is fully loaded)
    web_driver.get(target_url)
    WebDriverWait(web_driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "search-title")))
    html_doc = web_driver.page_source

    # grab desire contents from the html documnet with beautifulsoup
    soup = BeautifulSoup(html_doc, 'html.parser')
    
    # return empty list if no result
    result = soup.find(class_="title search-title").find("span").get_text()
    if ("No results" in result):
        return property_listings
    elif (soup.find(class_="search-suggest")):
        if("Sorry" in soup.find(class_="search-suggest").get_text()):
            return property_listings

    # helper callback
    def filter_listing(tag):
        if(tag.name == "li" and tag.has_attr('class') and "listing-item" in tag['class'] and "featured-agent-listing" not in tag['class']):  # filter out featured/sponsored listing
            return tag

    for listing in soup.find_all(filter_listing):
        num_bed = num_bath = 1 # default assumptions
         
        location = listing.find(class_="listing-location").get_text()
        if(location == ""): # get location from other tag
            location = listing.find("h3").find("span").get_text()
            
        description = listing.find(class_="lst-ptype").get_text()
        
        type = ""
        if (listing.find(class_="lst-rooms")):
            for t in listing.find(class_="lst-rooms").find_all(title = True):
                type += t['title'] + " "
                if(t.has_attr('class') and 'bed' in t['class']):
                    num_bed = int(t.get_text())
                elif(t.has_attr('class') and 'bath' in t['class']):
                    num_bath = int(t.get_text())
                
        size = listing.find(class_="lst-sizes").get_text().split('·'.decode('utf-8'))[0]
        
        fee = listing.find(class_="listing-price").get_text()
        if (not forSale):
            fee += "nth"  # to complete the phrase from "per mo" to "per month"
        
        img_url = ""
        try:
            img_url = listing.find(class_="listing-img-a-imgwrap").find("img")["content"]
        except:
            img_url = listing.find(class_="listing-img-a-imgwrap").find("img")["src"]
            
        listing_url = "https://www.propertyguru.com.sg/" + listing.find("a")["href"]
        
        property_listings.append(Property_listing(location, description, type, size, fee, num_bed, num_bath, img_url, listing_url))
    
    return property_listings
    
    