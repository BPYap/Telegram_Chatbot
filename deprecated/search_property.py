#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.common.keys import Keys

from bs4 import BeautifulSoup

area = raw_input("Input place to search for nearby rentals: ")
# Create a new instance of the Firefox driver
driver = webdriver.Firefox()
driver.implicitly_wait(5)
# go to the propertyguru page
driver.get("https://www.propertyguru.com.sg/singapore-property-listing/property-for-rent?market=residential&freetext=" + area + "&sort=price&order=asc")
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "listing-item")))
html_doc = driver.page_source
driver.quit()

soup = BeautifulSoup(html_doc, 'html.parser')

# find tags that contain infomation about rental infomation 
def get_listing(tag):
    if(tag.name == "li" and tag.has_attr('class') and "listing-item" in tag['class'] 
        and "featured-agent-listing" not in tag['class']):
        return tag

for listing in soup.find_all(get_listing):
    print "========================================="
    i = -1
    for info in listing.find(class_="listing-info").find_all('span'):
        i = i + 1
        if (i == 2 or i == 3):
            continue # avoid printing redundant info
        info_text = info.get_text()
        if(info.has_attr('class') and 'bed' in info['class']):
            info_text += "bed(s)"
        elif(info.has_attr('class') and 'bath' in info['class']):
            info_text += "bath(s)"
        print info_text.encode('utf-8')
    print listing.find(class_="lst-sizes").get_text().split('·'.decode('utf-8'))[0]
    print listing.find(class_="listing-price").get_text()
        
    
    