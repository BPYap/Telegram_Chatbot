import requests

API_KEY = '...'

while True:
    phrase = raw_input("Input location for autocompletion > ")
    request = requests.get("https://maps.googleapis.com/maps/api/place/autocomplete/json" + 
                            "?input=" + phrase +
                            "&key=" + API_KEY +
                            "&components=country:sg")
    
    predictions = request.json()['predictions']
    print("\nAutocomple successful.")
    for prediction in predictions:
        print prediction['description']
    
    simplified = predictions[0]['description'].split(',')[0]
    print "\nSimplified location:", simplified, '\n'
    