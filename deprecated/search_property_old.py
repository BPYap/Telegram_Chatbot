import urllib
import urllib2
from bs4 import BeautifulSoup

area = raw_input("Input place to search for nearby rentals: ")
target_url = "https://www.propertyguru.com.sg/singapore-property-listing/property-for-rent"

arguments = {
            'market' : 'residential',
            'freetext' : area,
            'sort' : 'price',
            'order' : 'asc'
            }
data = urllib.urlencode(arguments)

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
headers = {'User-Agent' : user_agent}

req = urllib2.Request(target_url, data, headers)
f = urllib2.urlopen(req)
html_doc = f.read()
print f.getcode()
print html_doc
f.close()

soup = BeautifulSoup(html_doc, 'html.parser')

def get_listing(tag):
    if(tag.name == "li" and tag.has_attr('class') and "listing-item" in tag['class']):
        return tag

print soup.find_all(get_listing)