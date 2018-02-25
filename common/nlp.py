from string import punctuation

from nltk.stem.lancaster import *
from nltk.tokenize import word_tokenize
from nltk.util import ngrams
from nltk.tokenize.moses import MosesDetokenizer

Stemmer = LancasterStemmer()
Detokenizer = MosesDetokenizer()

def get_context(text):
    """
    understands what the text is looking for
    available context: property_rent, property_sale
    """
    
    rent_keywords = ["rent", "rental"]
    sale_keywords = ["buy", "purchase", "sale"]
    
    # sometimes stemmer would strip away characters in base word. E.g: 'purchase'
    # to 'purchas', hence pre-process keywords by stemming them is necessary
    rent_keywords = [Stemmer.stem(word) for word in rent_keywords]
    sale_keywords = [Stemmer.stem(word) for word in sale_keywords]

    for token in word_tokenize(text):
        stemmed_token = Stemmer.stem(token)
        if stemmed_token in rent_keywords:
            return "property_rent"
        elif stemmed_token in sale_keywords:
            return "property_sale"

def extract_location(text):
    """
    extract location by slicing and return text which appear after one of the keywords
    """
    
    tokens = text.split()
    result = ""
    keywords = ["at", "near", "in"]
    for keyword in keywords:
        if keyword in tokens:
            result = " ".join(tokens[tokens.index(keyword)+1:])
            break
    return "".join(c for c in result if c not in punctuation) # remove any punctuation
    
def extract_property_type(text):
    """
    extract property types from text, return string of property type 
    separated by '_' if more than 1 property type is found
    
    algorithm: 1. tokenize text
               2. get bigrams and trigrams from the tokens
               3. for each tuple of the ngrams, convert the tuple to list then
                  detokenize the list
               4. apply stemming to the detokenize text and compare it against 
                  property_types list
    
    future update: using nltk's collocation function to check against the list
    instead of writing block of if-else logic
    """
    result = []
    text = text.lower()
    property_types = ["condominium", "apartment", "walk-up", "cluster", 
                      "executive condominium", "landed terrace", "detached",
                      "semi-detached", "corner", "bungalow", "good class bungalow",
                      "shophouse", "land", "town house", "conservation", 
                      "landed cluster", "executive apartment", "executive maisonette", 
                      "multi-generation", "terrace", "premium apartment", "adjoined",
                      "Model A maisonette"]
   
    # apply stemming to all property type
    stemmed_property_types = [Stemmer.stem(word) for word in property_types] 
    
    tokens = word_tokenize(text)
    bigrams = list(ngrams(tokens, 2))
    trigrams = list(ngrams(tokens, 3))
    
    def get_index(tokens, words):
        """
        get index of the first word in sublist from tokens
        e.g: 
        >> tokens = ["landed", "cluster", "landed", "terrace"]
        >> words = ["landed", "terrace"]
        >> get_index(tokens, words) # will return 2
        """
        i = 0
        current_index = 0
        for t in tokens:
            if t == words[i]:
                i += 1
                if i == len(words):
                    break
            else:
                i = 0
            current_index += 1
        return current_index - len(words) + 1
        
    for t in (bigrams + trigrams):
        word = Detokenizer.detokenize(list(t), return_str = True)
        stemmed_word = Stemmer.stem(word)
        if stemmed_word in stemmed_property_types:
            idx = stemmed_property_types.index(stemmed_word)
            result.append(property_types[idx])
            # delete successfully matched word from tokens
            start_index = get_index(tokens, list(t))
            for i in range(len(t)): 
                del tokens[start_index] 
                
    for token in tokens:
        stemmed_word = Stemmer.stem(token)
        if stemmed_word in stemmed_property_types:
            idx = stemmed_property_types.index(stemmed_word)
            result.append(property_types[idx])
    
    if (len(result) == 0):
        if "condo" in text:
            result.append("condo")
        elif "landed" in text:
            result.append("landed")
        elif "hdb" in text:
            result.append("hdb")
        
    return "_".join(result)