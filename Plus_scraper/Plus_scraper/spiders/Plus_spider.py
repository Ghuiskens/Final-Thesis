#Importing the libraries that are needed for the plus_spider
import scrapy #Framework for scraping and crawling
from scrapy import Selector #Parsing html content of responses
import re #Extracting price information
from Plus_scraper.items import PlusScraperItem #Creating instances of items and storing extracted data
from bs4 import BeautifulSoup #Parse HTML content and extract selectors
from urllib.parse import urljoin #To construct absolute url links
import re #to execute regular expressions
from fuzzywuzzy import fuzz #Similarity checking for words

class PlusSpiderSpider(scrapy.Spider):
    #Name of the spider
    name = "plus_spider"
    #Allowed domain for the plus spider
    allowed_domains = ["www.plus.nl"]
    #Empty list to fill with urls already crawled  
    crawled_urls = []
    #Urls that have to be crawled and scraped
    category_urls = ["https://www.plus.nl/producten/snoep-koek-chips-zoutjes-noten/chocolade/chocoladerepen-chocoladetabletten?PageNumber=1&PageSize=12&SortingAttribute=&tn_cid=333333-10000-378-1086-1463&tn_fk_storeid=635",
                        "https://www.plus.nl/producten/snoep-koek-chips-zoutjes-noten/chocolade/candybars?PageNumber=1&PageSize=12&SortingAttribute=&tn_cid=333333-10000-378-1086-1465&tn_fk_storeid=635",
                        "https://www.plus.nl/producten/snoep-koek-chips-zoutjes-noten/chocolade/chocoladesnoepjes?PageNumber=1&PageSize=12&SortingAttribute=&tn_cid=333333-10000-378-1086-1464&tn_fk_storeid=635",
                        "https://www.plus.nl/producten/snoep-koek-chips-zoutjes-noten/chocolade/luxe-chocolade-bonbons?PageNumber=1&PageSize=12&SortingAttribute=&tn_cid=333333-10000-378-1086-1466&tn_fk_storeid=635"
    ]
   
    #Defining a function that iterates over the four different urls that have to be scraped and add them to the crawled urls 
    def start_requests(self):
        for category_url in self.category_urls:
            self.crawled_urls.append(category_url)
            yield scrapy.Request(url=category_url, callback=self.parse)

    #Defining a function that gets all the product detail page urls 
    def parse(self, response):
        #Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.body, 'html.parser')

        #Find all the <a> elements with class "product-tile"
        a_elements = soup.find_all('a', class_='product-tile')

        #Set new urls found variable to check if the spider gets new products on the page
        new_urls_found = False  # Flag to indicate if new URLs are found on the page

        #Check the element for product urls and if found change the new_urls_found variable to true
        for a_element in a_elements:
            url = a_element.get('href')
        
            if url not in self.crawled_urls:
                self.crawled_urls.append(url)
                yield response.follow(url, callback=self.parse_detail)
                new_urls_found = True

       #Extract the current page number
        page_number = int(response.url.split('PageNumber=')[1].split('&')[0])

        #If new products are found then adjust the page number to check the next page
        if new_urls_found:
            #Increment the page number
            next_page_number = page_number + 1

            #Build the URL for the next page
            next_page_url = response.url.replace(f'PageNumber={page_number}', f'PageNumber={next_page_number}')

            #Follow the link to the next page
            yield scrapy.Request(next_page_url, callback=self.parse)
            
    #Scraping the information from the detail pages
    def parse_detail(self, response):
        #Extract the product id and name
        product_id = response.css('div[data-product-sku-overlay]::attr(data-product-sku-overlay)').get()
        product_naam = response.css('#prod-detail-ctnr div.product-right-block h1::text').get()
        
        #Extracting price parts from different selectors and joining them
        price_integer = response.css('#prod-detail-ctnr > div.bg-productdetail.product-dtl-pg > div.content.pro-detail-top-block > div > div > div.col-sm-8.col-lg-9.col-xs-12.product-desc-info.product-right-block > div > div.price-detailpage > div.product-detail-priceContainer.product-detail-price-block > div > span.price.normal-price > span::text').get()
        cents = response.css('#prod-detail-ctnr > div.bg-productdetail.product-dtl-pg > div.content.pro-detail-top-block > div > div > div.col-sm-8.col-lg-9.col-xs-12.product-desc-info.product-right-block > div > div.price-detailpage > div.product-detail-priceContainer.product-detail-price-block > div > span.price.normal-price > sup::text').get()
        product_prijs = f'{price_integer}.{cents}'.strip()
        
        #Extracting the other data from the detail page
        prijs_per_kg = response.css('div.ppse-float-left div.ppse-css::text').re_first(r'€ ([\d,]+)')
        
        #Take the content statement get the text, split the text before the number and take the remaining string
        product_content = response.css('div.product-detail-packing::text').get().strip()
        if product_content:
            match = re.search(r'\d', product_content)
            if match:
                product_content = product_content[match.start():]
        
        #Grab all the content in the ingredient selecotr, then remove the initial 'ingredients:' and remove the last snentence which is about allergies
        ingredients = response.css('div.prod-attrib-item.ingredienten div.col-sm-9 *::text').getall()
        if ingredients:
            product_ingredients = []
            for ing in ingredients:
                ing = ing.strip()
                if ing and ":" in ing:
                    ingredient = ing.split(":", 1)[1].strip()
                    product_ingredients.append(ingredient)

        product_description = response.css('div.productIngredientsLeftColumn div.prod-attrib-item.wettelijke_naam div.col-sm-9 div::text').get()
        
        #Getting the trademarks from the product detail page, which are hidden in text
        #Establishing list of trademarks and an empty set to fill with unique trademarks and attach to the product that is being scraped
        trademark_list = ["Nestle Cocoa Plan",
                        "Samen maken we chocolade 100% slaafvrij",
                        "Cocoa Life",
                        "Cocoa Horizons",
                        "Demeter",
                        "EKO",
                        "Europa bio",
                        "Fairglobe",
                        "Fairtrade Original",
                        "Climate Neutral Certified",
                        "Fair for Life",
                        "Fairtrade",
                        "Rainforest Alliance",
                        "UTZ"]
        trademarks_set = set()

        #Select all elements with the class 'icon-text'
        icon_text_elements = response.css('.icon-text')

        #Iterate over each element and process the text
        for element in icon_text_elements:
            text = element.css('::text').get().lower()  # Convert text to lowercase
    
            #Split the text into individual words
            words = text.split()
            #words = re.findall(r'\w+', text)
    
            #Check if any word matches the trademarks
            for word in words:
                word_lower = word.lower()  # Convert word to lowercase
        
                #if the word is similar to any trademark using fuzzy matching
                for trademark in trademark_list:
                    trademark_lower = trademark.lower()  # Convert trademark to lowercase
            
                    #Compare similarity using fuzzy matching
                    similarity_ratio = fuzz.ratio(word_lower, trademark_lower)

                    #Adjust the threshold value as per your requirement
                    if similarity_ratio >= 80:  #Adjust the similarity threshold as needed
                        trademarks_set.add(trademark)
        
        #Convert the set of trademarks to a list
        trademarks = list(trademarks_set)

        #Extract product allergen information by checking all rows that have allergen information and appending it to the allergie_bevat list      
        allergen_elements = response.css('div.plus_allergenen_attributes')
        allergie_bevat = []
        for element in allergen_elements:
            allergie_bevat.append(element.css('::text').get().strip())

        #Getting the producer of the chocolate bar from the contactnaam block
        contactnaam_block = response.css('.prod-attrib-item+ .prod-attrib-item .prod-attrib-val-alcohol')
        leverancier = contactnaam_block.css('::text').get()

        #Get the adres form the product page, strip it from other and clean up the addresses and keep everything that is before the comma
        adres_leverancier = response.css('div.prod-attrib-val-alcohol ::text').getall()
        adres_leverancier = [address.strip() for address in adres_leverancier if address.strip()]
        adres_leverancier = ','.join(adres_leverancier)
        if ',' in adres_leverancier:
            last_comma_index = adres_leverancier.rindex(',')
            adres_leverancier = adres_leverancier[:last_comma_index]
        
        product_url = response.css('link[rel="canonical"]::attr(href)').get()

        #Storing the extracted data for each of the variables that are required
        item = {
            'product_id': product_id,
            'product_naam': product_naam,
            'prijs': product_prijs,
            'kilo_prijs': prijs_per_kg,
            'omschrijving': product_description,
            'inhoud': product_content,
            'ingredienten': product_ingredients,
            'kenmerken': trademarks,
            'allergie_bevat': allergie_bevat,
            'allergie_kan_bevatten': None,
            'leverancier': leverancier,
            'adres_leverancier': adres_leverancier,
            'product_url': product_url
        }

        #Yield the extracted data item
        yield item