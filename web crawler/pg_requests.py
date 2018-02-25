#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import pickle
import requests
import time

from bs4 import BeautifulSoup

from html_parser import pg_parse

# command line arguments parsing
parser = argparse.ArgumentParser()
parser.add_argument("--start_page", default=1)
parser.add_argument("--end_page", default=0)
args = parser.parse_args()

# global variables
start_page = int(args.start_page)
end_page = int(args.end_page)
property_listings = {} # dictionary to be pickled (key: property type value: list of Property_listing object)
#target_url = for sale url
target_url = "https://www.propertyguru.com.sg/singapore-property-listing/property-for-rent/" + str(start_page) +"?sort=price&order=asc&limit=30"
headers = {
    'Host': "www.propertyguru.com.sg",
    'Connection': "keep-alive",
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
    'Upgrade-Insecure-Requests': "1",
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    'Accept-Encoding': "gzip, deflate, br",
    'Accept-Language': "en-US,en;q=0.9,zh-CN;q=0.8,zh-TW;q=0.7,zh;q=0.6",
}       

if __name__ == "__main__":
    # make request to propertyguru.sg
    response = requests.get(target_url, headers=headers)
    html_doc = response.text

    # generate beautifulsoup's soup object from html document
    soup = BeautifulSoup(html_doc, 'lxml')

    # get total number of pages
    total_pages = 0
    tags = soup.find_all(attrs={"data-page": True})
    for tag in tags:
        text = tag.get_text().encode('ascii','ignore')
        if text.isdigit() and int(text) > total_pages:
            total_pages = int(text)        
    print "Total number of pages: " + str(total_pages)
    if (end_page != 0):
        total_pages = end_page
    
    # scraping codes
    active_page = 0
    while (active_page <= total_pages):
        # get current active page
        tags = soup.find_all(attrs={"data-page": True})
        for tag in tags:
            parent_tag = tag.find_parent("li", class_ = "active") 
            if parent_tag:
                active_page = int(tag.get_text().encode('ascii', 'ignore'))
                break
        print "Current active page: " + str(active_page),
        
        pg_parse(soup, property_listings)
        
        # pickle results of every 50 page to external file
        if (active_page % 50 == 0 or active_page == total_pages):
            with open("pickle-" + str(active_page) + ".p", "wb") as f: 
                pickle.dump(property_listings, f, pickle.HIGHEST_PROTOCOL)
            property_listings.clear()
        
        # go to next page
        if(active_page == total_pages):
            break
        else:
            time.sleep(3)
            target_url = "https://www.propertyguru.com.sg/singapore-property-listing/property-for-rent/" + \
                        str(active_page + 1) + "?sort=price&order=asc&limit=30"
            response = requests.get(target_url, headers=headers)
            html_doc = response.text
            soup = BeautifulSoup(html_doc, 'html.parser')

