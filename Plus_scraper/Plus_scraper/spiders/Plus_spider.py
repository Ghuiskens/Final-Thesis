import scrapy
from scrapy import Selector
import re
from Plus_scraper.items import PlusScraperItem
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class PlusSpiderSpider(scrapy.Spider):
    name = "plus_spider"
    allowed_domains = ["www.plus.nl"]
    crawled_urls = []
    category_urls = ["https://www.plus.nl/producten/snoep-koek-chips-zoutjes-noten/chocolade/chocoladerepen-chocoladetabletten?PageNumber=1&PageSize=12&SortingAttribute=&tn_cid=333333-10000-378-1086-1463&tn_fk_storeid=635",
                        "https://www.plus.nl/producten/snoep-koek-chips-zoutjes-noten/chocolade/candybars?PageNumber=1&PageSize=12&SortingAttribute=&tn_cid=333333-10000-378-1086-1465&tn_fk_storeid=635",
                        "https://www.plus.nl/producten/snoep-koek-chips-zoutjes-noten/chocolade/chocoladesnoepjes?PageNumber=1&PageSize=12&SortingAttribute=&tn_cid=333333-10000-378-1086-1464&tn_fk_storeid=635",
                        "https://www.plus.nl/producten/snoep-koek-chips-zoutjes-noten/chocolade/luxe-chocolade-bonbons?PageNumber=1&PageSize=12&SortingAttribute=&tn_cid=333333-10000-378-1086-1466&tn_fk_storeid=635"
    ]
        
    #Defining a function that iterates over the four different urls that have to be scraped
    def start_requests(self):
        for category_url in self.category_urls:
            self.crawled_urls.append(category_url)
            yield scrapy.Request(url=category_url, callback=self.parse)

    #Defining a function that gets all the product detail page urls 
    def parse(self, response):
        # Parse the HTML content with BeautifulSoup
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

        #IF new products are found then adjust the page number to check the next page
        if new_urls_found:
            #Increment the page number
            next_page_number = page_number + 1

            #Build the URL for the next page
            next_page_url = response.url.replace(f'PageNumber={page_number}', f'PageNumber={next_page_number}')

            #Follow the link to the next page
            yield scrapy.Request(next_page_url, callback=self.parse)

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
        
        #Get special info texts for all rows and get the first 10 words which can help te deduce the trademarks
        kenmerken = response.css('#prod-detail-ctnr div.icons-with-descriptions div.col-sm-9.icon-text::text').getall()
        kenmerken_words = []
        for kenmerk in kenmerken:
            words = kenmerk.strip().split()[:10]  #Extract first 10 words
            kenmerken_words.append(' '.join(words))

        #Check if any of the milieu centraal trademarks are in the text and if so append the name to the trademark list
        kenmerken_lijst = ["Nestle Cocoa Plan",
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

        product_kenmerken = []
        for kenmerk_text in kenmerken_words:
            for label in kenmerken_lijst:
                if label.lower() in kenmerk_text.lower():
                    product_kenmerken.append(label)
                    break

        #Extract product allergen information by checking all rows that have allergen information and appending it to the allergie_bevat list      
        allergen_elements = response.css('div.plus_allergenen_attributes')
        allergie_bevat = []
        for element in allergen_elements:
            allergie_bevat.append(element.css('::text').get().strip())

        leverancier = response.css('#prod-detail-ctnr > div.bg-productdetail.product-dtl-pg > div.content.pro-detail-top-block > div > div > div.col-sm-8.col-lg-9.col-xs-12.product-desc-info.product-right-block > div > div.brand-text::text').get()
      
        element = '<div class="prod-attrib-val-alcohol">Kolvestraat 70<br>8000 Brugge,<br>Belgium</div>'

        #Get the adres form the product pages and clean up the addresses 
        adres_leverancier = response.css('div.prod-attrib-val-alcohol ::text').getall()
        adres_leverancier = [address.strip() for address in adres_leverancier if address.strip()]
        adres_leverancier = ','.join(adres_leverancier)
        if ',' in adres_leverancier:
            last_comma_index = adres_leverancier.rindex(',')
            adres_leverancier = adres_leverancier[:last_comma_index]
        
        product_url = response.css('link[rel="canonical"]::attr(href)').get()

        item = {
            'product_id': product_id,
            'product_naam': product_naam,
            'prijs': product_prijs,
            'kilo_prijs': prijs_per_kg,
            'omschrijving': product_description,
            'inhoud': product_content,
            'ingredienten': product_ingredients,
            'kenmerken': product_kenmerken,
            'allergie_bevat': allergie_bevat,
            'allergie_kan_bevatten': None,
            'leverancier': leverancier,
            'adres_leverancier': adres_leverancier,
            'product_url': product_url
        }

        # Yield the extracted data item
        yield item