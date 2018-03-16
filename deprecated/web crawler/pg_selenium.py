#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import pickle
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import FirefoxProfile
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
alt_proxies = []
proxies = []
use_alt_proxy = False

if __name__ == "__main__":
    # initializes web driver
    options = Options()
    options.add_argument("--headless")
    profile = FirefoxProfile()
    profile.set_preference("javascript.enabled", False)
    # desired_capability = webdriver.DesiredCapabilities.FIREFOX
    # desired_capability['proxy'] = {
        # "proxyType": "manual",
        # "httpProxy": proxies[proxy_index],
        # "ftpProxy": proxies[proxy_index],
        # "sslProxy": proxies[proxy_index]
    # }
    #driver = webdriver.Firefox(firefox_options=options, firefox_profile = profile, capabilities=desired_capability)
    driver = webdriver.Firefox(firefox_options=options, firefox_profile = profile)
    
    # navigate to target_url, then fetch its page source once "search-title" is located (indicate page is fully loaded)
    driver.get(target_url)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "show-filters")))
    except Exception:
        driver.quit()
        raise
    html_doc = driver.page_source

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
    
    # data mining codes
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
        
        # rotate proxy ip every 100 pages visited to avoid anti-crawl detection
        if (active_page % 30 == 0):
            time.sleep(6)
            # driver.quit()
            # if(not use_alt_proxy):
                # desired_capability['proxy'] = {
                    # "proxyType": "manual",
                    # "httpProxy": alt_proxies[proxy_index],
                    # "ftpProxy": alt_proxies[proxy_index],
                    # "sslProxy": alt_proxies[proxy_index]
                # }
                # use_alt_proxy = True
            # else:
                # desired_capability['proxy'] = {
                    # "proxyType": "manual",
                    # "httpProxy": proxies[proxy_index],
                    # "ftpProxy": proxies[proxy_index],
                    # "sslProxy": proxies[proxy_index]
                # }
                # use_alt_proxy = False    
            # profile = FirefoxProfile()
            # profile.set_preference("javascript.enabled", False)
            # #driver = webdriver.Firefox(firefox_options=options, firefox_profile = profile, capabilities=desired_capability)
            # driver = webdriver.Firefox(firefox_options=options, firefox_profile = profile)
        # go to next page
        if(active_page == total_pages):
            break
        else:
            target_url = "https://www.propertyguru.com.sg/singapore-property-listing/property-for-rent/" + \
                        str(active_page + 1) + "?sort=price&order=asc&limit=30"
            time.sleep(0.1)
            driver.get(target_url)
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "show-filters")))
            except Exception:
                driver.quit()
                raise
            html_doc = driver.page_source
            soup = BeautifulSoup(html_doc, 'html.parser')

    driver.quit()

