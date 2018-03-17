import argparse
import time
from threading import Thread

import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from common import nlp
# modules for different crawler
import pg.property_scraping as pg
import ninenine.property_scraping as ninenine
import srx.property_scraping as srx

# handles argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("--headless", default=0)
args = parser.parse_args()

# web driver options
options = Options()
if args.headless:
    options.add_argument("--headless") 

# initializes telegram bot
bot = telepot.Bot("...")

# global variables
quit = False # global flag to handle state of program
# format: {chat_id : {'buffer': Listing_buffer, 'driver_0' : webdriver instance, 'driver_1': ...}}
user_info = {} 
nr_drivers = 3

class Listing_buffer:    
    # Use to hold more than 5 properties and allow user to tap "show more" to reveal more
    def __init__(self):
        self.property_listings = [] # stores list of Property_listing objects
        self.current_index = 0 # stores current position in listing_buffer

def query_property(chat_id, msg_text, forSale):
    location = nlp.extract_location(msg_text)
    property_type = nlp.extract_property_type(msg_text)
    bot.sendMessage(chat_id, "Searching... Please wait")
    bot.sendChatAction(chat_id, "typing")
    
    type = "sale" if forSale else "rent"
    print "-------------------------- new property query (" + type + ") ------------------------"

    ############################# TODO: make this section more modular ########################################
    # pg_listings = pg.get_listing(user_info[chat_id]['driver_0'], forSale, location, property_type)
    # ninenine_listings = ninenine.get_listing(user_info[chat_id]['driver_1'], forSale, location, property_type)
    # srx_listings = srx.get_listing(user_info[chat_id]['driver_2'], forSale, location, property_type)
    pg_listings = []
    thread1 = Thread(target=pg.get_listing, args=(pg_listings, user_info[chat_id]['driver_0'], forSale, location, property_type))
    thread1.start()
    
    ninenine_listings = []
    thread2 = Thread(target=ninenine.get_listing, args=(ninenine_listings, user_info[chat_id]['driver_1'], forSale, location, property_type))
    thread2.start()
    
    srx_listings = []
    thread3 = Thread(target=srx.get_listing, args=(srx_listings, user_info[chat_id]['driver_2'], forSale, location, property_type))
    thread3.start()

    thread1.join()
    thread2.join()
    thread3.join()
    
    user_info[chat_id]['buffer'].current_index = 0
    user_info[chat_id]['buffer'].property_listings[:] = pg_listings
    user_info[chat_id]['buffer'].property_listings.extend(ninenine_listings)
    user_info[chat_id]['buffer'].property_listings.extend(srx_listings)
    ###########################################################################################################
    
    # sort by price
    user_info[chat_id]['buffer'].property_listings.sort(key=lambda listing: listing.sort_key)
    
    if (len(user_info[chat_id]['buffer'].property_listings) == 0):
        print "attempted to find " + location + ", but not found"
        return_msg = "Sorry, I can't find any requested property"
        if(location == ""):
            return_msg += (" near " + location)
        bot.sendMessage(chat_id, return_msg)
        return 
    else:    
        return_msg = "Top 5 cheapest properties for " + type + " near " + location + " :"
        if (location == ""):
            return_msg = "Top 5 cheapest properties for " + type + " :"
        bot.sendMessage(chat_id, return_msg)
        send_listing_properties(chat_id)
        
        for property in user_info[chat_id]['buffer'].property_listings:
            # for debugging purpose
            print "=" * 30
            print property.location.encode('utf-8')
            print property.description.encode('utf-8')
            print property.type
            print property.size
            print property.fee
            print property.num_bed.encode('utf-8', 'ignore') + " bed"
            print property.num_bath.encode('utf-8', 'ignore') + " bath"
            print property.listing_url
            print property.img_url

def send_listing_properties(chat_id):
    """Sends property listing as message to user.
    
    Information includes the property's location, url to listing, price and image.
    The data came from property_listings associated with each user's chat_id.
    """
    temp = 1
    max = 5 # maximum results to show, could be configured by user in the future
    property_listings = user_info[chat_id]['buffer'].property_listings
    current_index = user_info[chat_id]['buffer'].current_index
    while(temp <= max and temp <= len(property_listings)):
        message = "<a href='" + property_listings[current_index].img_url + "'>" + "&#8205;</a>" + \
        "<a href='" + property_listings[current_index].listing_url + "'>" + property_listings[current_index].location + \
        "</a>\nlisting price: " + property_listings[current_index].fee
        # bot.sendPhoto(chat_id, property.img_url)
        if (temp == max and current_index + 1 < len(property_listings)):
            markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Show More", callback_data = "press")],])
            bot.sendMessage(chat_id, message, parse_mode = 'HTML', reply_markup = markup)
            current_index += 1
            user_info[chat_id]['buffer'].current_index += 1
            return
        else:
            bot.sendMessage(chat_id, message, parse_mode = 'HTML')
        temp += 1
        current_index += 1
        user_info[chat_id]['buffer'].current_index += 1

def handle_query(msg):
    send_listing_properties((msg['from'])['id'])

def handle_chat(msg):
    global quit
    
    chat_id = (msg['from'])['id']
    msg_text = msg['text']
    
    if (chat_id not in user_info.keys()):
        bot.sendMessage(chat_id, "Setting up for first time usage...")
        bot.sendChatAction(chat_id, "typing")
        user_info[chat_id] = {}
        user_info[chat_id]['buffer'] = Listing_buffer()
        for i in range(nr_drivers):
            user_info[chat_id]['driver_'+str(i)] = webdriver.Firefox(firefox_options=options)
            bot.sendChatAction(chat_id, "typing")
        bot.sendMessage(chat_id, "Finished setting up. Thanks for waiting!")
    
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
        for i in range(nr_drivers):
            user_info[chat_id]['driver_'+str(i)].quit()
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