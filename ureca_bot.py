import time

import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from selenium import webdriver

from common import nlp
# modules for different crawler
import pg.property_scraping as pg
import ninenine.property_scraping as ninenine
import ip.property_scraping as ip

# initializes web driver
driver = webdriver.Firefox()
driver.implicitly_wait(5)

# initializes telegram bot
bot = telepot.Bot("...")

# global variables
quit = False # global flag to handle state of program
user_listing_buffer = {} # store dictionary of chat_id : Listing_buffer

class Listing_buffer:    
    # Use to hold more than 5 properties and allow user to tap "show more" to reveal more
    def __init__(self):
        self.property_listings = [] # stores list of Property_listing objects
        self.current_index = 0 # stores current position in user_listing_buffer

def query_property(chat_id, msg_text, forSale):
    location = nlp.extract_location(msg_text)
    property_type = nlp.extract_property_type(msg_text)
    bot.sendMessage(chat_id, "Searching... Please wait")
    bot.sendChatAction(chat_id, "typing")
    user_listing_buffer[chat_id] = Listing_buffer()
    
    type = "sale" if forSale else "rent"
    print "-------------------------- new property query (" + type + ") ------------------------"
    user_listing_buffer[chat_id].property_listings = pg.get_listing(driver, forSale, location, property_type)
    user_listing_buffer[chat_id].property_listings.append(ninenine.get_listing(driver, forSale, location, property_type))
    user_listing_buffer[chat_id].property_listings.append(ip.get_listing(driver, forSale, location, property_type))
    
    # sort by price
    user_listing_buffer[chat_id].property_listings.sort(key=lambda listing: listing.fee)
    
    if (len(user_listing_buffer[chat_id].property_listings) == 0):
        print "attempted to find " + location + ", but not found"
        return_msg = "Sorry, I can't find any requested property"
        if(location == ""):
            return_msg += (" near " + location)
        bot.sendMessage(chat_id, return_msg)
        return 
    else:    
        for property in user_listing_buffer[chat_id].property_listings:
            # for debugging purpose
            print "=" * 30
            print property.location.encode('utf-8')
            print property.description.encode('utf-8')
            print property.type
            print property.size
            print property.fee
            print str(property.num_bed) + " bed"
            print str(property.num_bath) + " bath"
            print property.listing_url
            print property.img_url
        
        return_msg = "Top 5 cheapest properties for " + type + " near " + location + " :"
        if (location == ""):
            return_msg = "Top 5 cheapest properties for " + type + " :"
        bot.sendMessage(chat_id, return_msg)
        send_listing_properties(chat_id)

def send_listing_properties(chat_id):
    """Sends property listing as message to user.
    
    Information includes the property's location, url to listing, price and image.
    The data came from property_listings associated with each user's chat_id.
    """
    temp = 1
    max = 5 # maximum results to show, could be configured by user in the future
    property_listings = user_listing_buffer[chat_id].property_listings
    current_index = user_listing_buffer[chat_id].current_index
    while(temp <= max and temp <= len(property_listings)):
        message = "<a href='" + property_listings[current_index].img_url + "'>" + "&#8205;</a>" + \
        "<a href='" + property_listings[current_index].listing_url + "'>" + property_listings[current_index].location + \
        "</a>\nlisting price: " + property_listings[current_index].fee
        # bot.sendPhoto(chat_id, property.img_url)
        if (temp == max and current_index + 1 < len(property_listings)):
            markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Show More", callback_data = "press")],])
            bot.sendMessage(chat_id, message, parse_mode = 'HTML', reply_markup = markup)
            current_index += 1
            user_listing_buffer[chat_id].current_index += 1
            return
        else:
            bot.sendMessage(chat_id, message, parse_mode = 'HTML')
        temp += 1
        current_index += 1
        user_listing_buffer[chat_id].current_index += 1

def handle_query(msg):
    send_listing_properties((msg['from'])['id'])

def handle_chat(msg):
    global quit
    
    chat_id = (msg['from'])['id']
    msg_text = msg['text']
    
    entrance = ["hi", "hello", "/help", "/start"]
    start_msg = "Hi there. Currently I am able to search and return cheapest properties for sale/rent based on the following criteria:\
                \n1. location\
                \n2. property types\
                \n3. rent/sale\
                \n\n<i>For example, you can try asking me 'Find me a place to rent near ntu' or 'Search all hdb for sale in Jurong West.'</i>"
            
    if any(word in msg_text.lower() for word in entrance):
        bot.sendMessage(chat_id, start_msg, parse_mode = 'HTML')
        return
    elif msg_text.lower() == "quit":
        quit = True
        driver.quit()
        bot.sendMessage(chat_id, "Service terminated.")
        return
    else:
        context = nlp.get_context(msg_text)
        if (context == "property_rent"):
            query_property(chat_id, msg_text, forSale = False)
        elif (context == "property_sale"):
            query_property(chat_id, msg_text, forSale = True)
        else:
            error_msg = "Sorry, I am currently not smart enough to understand what you meant by <i>'" + msg_text + "'</i>"
            bot.sendMessage(chat_id, error_msg, parse_mode = 'HTML')
            bot.sendMessage(chat_id, "Perhaps you forgot to specify keywords such as 'rent' or 'sale'")

# main
MessageLoop(bot, {'chat' : handle_chat, 'callback_query' : handle_query}).run_as_thread()
print "Waiting for message..."

while not quit:
    time.sleep(10)