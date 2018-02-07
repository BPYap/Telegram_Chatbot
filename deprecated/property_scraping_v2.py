#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 

from bs4 import BeautifulSoup

import json

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

target_url = "https://www.propertyguru.com.sg/singapore-property-listing/property-for-rent?market=residential&sort=price&order=asc&limit=30"

# initializes web driver
driver = webdriver.Firefox()
driver.implicitly_wait(5)

# navigate to target_url, then fetch its page source once "search-title" is located (indicate page is fully loaded)
driver.get(target_url)
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "search-title")))
html_doc = driver.page_source

# grab desire contents from the html documnet with beautifulsoup
soup = BeautifulSoup(html_doc, 'html.parser')

# get total number of pages
total_pages = 0
page_data = soup.find_all(attrs={"data-page": True})
for tag in page_data:
    text_data = tag.get_text().encode('ascii','ignore')
    if text_data.isdigit() and int(text_data) > int(total_pages):
        total_pages = text_data        
print "Total number of pages: " + str(total_pages)

property_listings = {}
def add_listing():
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
        # if (not forSale):
            # fee += "nth"  # to complete the phrase from "per mo" to "per month"
        
        img_url = ""
        try:
            img_url = listing.find(class_="listing-img-a-imgwrap").find("img")["content"]
        except:
            img_url = listing.find(class_="listing-img-a-imgwrap").find("img")["src"]
            
        listing_url = "https://www.propertyguru.com.sg/" + listing.find("a")["href"]
        
        #property_listings.append(Property_listing(location, description, type, size, fee, num_bed, num_bath, img_url, listing_url))
        if description.encode('ascii', 'ignore') not in property_listings:
            property_listings[description.encode('ascii', 'ignore')] = []
        property_listings[description.encode('ascii', 'ignore')].append({'location': location, 'type': type, 'size': size, 'fee': fee, 'num_bed': num_bed, 'num_bath': num_bath, 'img_url': img_url, 'listing_url': listing_url})
        
active_page = 0
while (active_page != total_pages): # possible bug where the pages are being updated during scraping
    # get current active page
    page_data = soup.find_all(attrs={"data-page": True})
    for tag in page_data:
        parent_tag = tag.find_parent("li", class_ = "active") 
        if parent_tag:
            active_page = int(tag.get_text().encode('ascii', 'ignore'))
            break
    print "Current active page: " + str(active_page)
    
    add_listing()
    #print "Current listing added: " + str(len(property_listings))
    
    # go to next page
    target_url = "https://www.propertyguru.com.sg/singapore-property-listing/property-for-rent/" + \
                str(active_page + 1) + "?sort=price&order=asc&limit=30"
    driver.get(target_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "search-title")))
    html_doc = driver.page_source
    soup = BeautifulSoup(html_doc, 'html.parser')

driver.quit()

export_json = json.dumps(property_listings)
with open("text.txt", "w") as f: 
    f.write(export_json) 

