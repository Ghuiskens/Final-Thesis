import scrapy
import json

class ChocoSpider(scrapy.Spider):
    name = 'ah_spider'
    allowed_domains = ['ah.nl']
    crawled_urls = []
    category_urls = ['https://www.ah.nl/producten/snoep-koek-chips-en-chocolade/chocolade/bonbons-en-pralines',
                    'https://www.ah.nl/producten/snoep-koek-chips-en-chocolade/chocolade/chocolade-geschenken',
                    'https://www.ah.nl/producten/snoep-koek-chips-en-chocolade/chocolade/chocoladesnoepjes?page=1',
                    'https://www.ah.nl/producten/snoep-koek-chips-en-chocolade/chocolade/nougat',
                    'https://www.ah.nl/producten/snoep-koek-chips-en-chocolade/chocolade/smeltchocolade',
                    'https://www.ah.nl/producten/snoep-koek-chips-en-chocolade/chocolade/lactosevrije-chocolade',
                    'https://www.ah.nl/producten/snoep-koek-chips-en-chocolade/chocolade/chocolade-suikerbewust',
                    'https://www.ah.nl/producten/snoep-koek-chips-en-chocolade/chocolade/candybars?page=4',
                    'https://www.ah.nl/producten/snoep-koek-chips-en-chocolade/chocolade/luxe-chocolade',
                    'https://www.ah.nl/producten/snoep-koek-chips-en-chocolade/chocolade/kerstchocolade',
                    'https://www.ah.nl/producten/snoep-koek-chips-en-chocolade/chocolade/chocolade-superfoods',
                    'https://www.ah.nl/producten/snoep-koek-chips-en-chocolade/chocolade/repen-en-tabletten?page=5'
                    ]

    def start_requests(self):
        for category_url in self.category_urls:
            self.crawled_urls.append(category_url)
            yield scrapy.Request(url=category_url, callback=self.parse)


    def parse(self, response):
        products = response.css('#search-lane article')
        for product in products:
            link = product.css('a::attr(href)').get()
            detail_url = response.urljoin(link)
            self.logger.debug(f'Detail URL: {detail_url}')
            yield scrapy.Request(url=detail_url, callback=self.parse_detail)

    def save_html(self, response):
        with open('response.html', 'wb') as file:
            file.write(response.body)


    def parse_detail(self, response):            
            #Extract the desired data from the detail page
            product_id = response.css('#start-of-content > div:nth-child(2) > div > div:nth-child(2) > div > p::text').get().strip()
            product_naam = response.css('#start-of-content div.product-hero_root__meolU h1 span::text').get()
            kilo_prijs = response.css('div.product-card-header_unitInfo__ddXw6 span.product-card-header_unitPriceWithPadding__oW5Pe::text').getall()
            kilo_prijs = ''.join(kilo_prijs).split('€')[-1].strip()
            omschrijving = response.css('#start-of-content > div:nth-child(2) > div > div:nth-child(1) > div.column.xlarge-6.large-8.small-12.xlarge-offset-1 > div:nth-child(1) > div:nth-child(2) > ul > li::text').getall()
            inhoud = response.css('#start-of-content > div:nth-child(2) > div > div:nth-child(1) > div.column.xlarge-6.large-8.small-12.xlarge-offset-1 > div:nth-child(1) > div.product-info-content-block.product-info-content-block--compact > p::text').get()
            ingredienten = response.css('#start-of-content > div:nth-child(2) > div > div:nth-child(1) > div.column.xlarge-6.large-8.small-12.xlarge-offset-1 > div:nth-child(2) > p > span::text').getall()
            kenmerken = response.css('#start-of-content div:nth-child(2) div div:nth-child(1) div.column.xlarge-6.large-8.small-12.xlarge-offset-1 div:nth-child(1) ul li').css('p::text').getall()
            allergie_bevat = response.css('#start-of-content div:nth-child(2) div div:nth-child(1) div.column.xlarge-6.large-8.small-12.xlarge-offset-1 div:nth-child(2) dl span:nth-child(1) dd::text').get()
            allergie_kan_bevatten = response.css('#start-of-content div:nth-child(2) div div:nth-child(1) div.column.xlarge-6.large-8.small-12.xlarge-offset-1 div:nth-child(2) dl span:nth-child(2) dd::text').get()
            leverancier = response.css('#start-of-content div:nth-child(2) div div:nth-child(1) div.column.xlarge-6.large-8.small-12.xlarge-offset-1 div:nth-child(5) main div div address div div:nth-child(1)::text').get()
            adres_leverancier = response.css('#start-of-content > div:nth-child(2) > div > div:nth-child(1) > div.column.xlarge-6.large-8.small-12.xlarge-offset-1 > div:nth-child(5) > main > div > div > address > div > div:nth-child(2)::text').get().strip()
            product_url = response.url
            
            #Extract the price from JSON data
            script_data = response.css('script[type="application/ld+json"]::text').get()
            data = json.loads(script_data)
            prijs = data['offers']['price']

            yield {
            'product_id': product_id,
            'product_naam': product_naam,
            'prijs': prijs,
            'kilo_prijs': kilo_prijs,
            'omschrijving': omschrijving,
            'inhoud': inhoud,
            'ingredienten': ingredienten,
            'kenmerken': kenmerken,
            'allergie_bevat': allergie_bevat,
            'allergie_kan_bevatten': allergie_kan_bevatten,
            'leverancier': leverancier,
            'adres_leverancier': adres_leverancier,
            'product_url': product_url
    }
    def closed(self, reason):
        # Log or print the crawled URLs
        self.logger.info(f"Crawled URLs: {self.crawled_urls}")
        print(f"Crawled URLs: {self.crawled_urls}")  