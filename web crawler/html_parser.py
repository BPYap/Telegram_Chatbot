#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup

class Property_listing:    
    """Data structure to organize property listing."""
    
    def __init__(self, location, type, room_description, size, price, num_bed, num_bath, img_url, listing_url):
        self.location = location
        self.type = type
        self.room_description = room_description
        self.size = size
        self.price = price
        self.num_bed = num_bed
        self.num_bath = num_bath
        self.img_url = img_url
        self.listing_url = listing_url
        
def pg_parse(soup, property_listings):
    """Parse soup and append structured data to property_listings."""
    
    def filter_listing(tag):
        """ Callback to filter out featured/sponsored listing. """
    
        if (tag.name == "li" and tag.has_attr('class') and
                "listing-item" in tag['class'] and 
                "featured-agent-listing" not in tag['class']):  
            return tag
    
    print " number of items: ", (len(soup.find_all(filter_listing)))
    for listing in soup.find_all(filter_listing):
        num_bed = num_bath = 1 # default assumptions
        
        location = listing.find(class_="listing-location").get_text()
        if(location == ""): 
            # get location from other tag
            location = listing.find("h3").find("span").get_text()
            
        type = listing.find(class_="lst-ptype").get_text()
        
        room_description = ""
        if (listing.find(class_="lst-rooms")):
            for t in listing.find(class_="lst-rooms").find_all(title = True):
                room_description += t['title'] + " "
                if(t.has_attr('class') and 'bed' in t['class']):
                    num_bed = int(t.get_text())
                elif(t.has_attr('class') and 'bath' in t['class']):
                    num_bath = int(t.get_text())
        
        size = 0
        if (listing.find(class_="lst-sizes")):
            size = listing.find(class_="lst-sizes").get_text().split('·'.decode('utf-8'))[0]
        
        # some property do not have listing price
        if (listing.find(class_="listing-price")):
            price = listing.find(class_="listing-price").get_text()
        else:
            # skip if property does not have listing price
            continue
        # if (not forSale):
            # fee += "nth"  # to complete the phrase from "per mo" to "per month"
        
        img_url = ""
        try:
            img_url = listing.find(class_="listing-img-a-imgwrap").find("img")["content"]
        except:
            img_url = listing.find(class_="listing-img-a-imgwrap").find("img")["src"]
            
        listing_url = "https://www.propertyguru.com.sg/" + listing.find("a")["href"]
        
        # Adds key-value pair to property_listings
        key = type.encode('ascii', 'ignore')
        if key not in property_listings:
            property_listings[key] = []
        property_listing = Property_listing(location, type, room_description, size, price, 
                                            num_bed, num_bath, img_url, listing_url)
        property_listings[key].append(property_listing)