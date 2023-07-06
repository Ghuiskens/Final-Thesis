#Pipeline file for the ah_spider 
#Importing the libraries needed for the pipeline file
from itemadapter import ItemAdapter #To access and manipulate item data in scrapy
import csv #To handle csv writing

class WriteToCsvPipeline(object):
    #Function to write headers for in the csv output of the spider
    def __init__(self):
        self.csvwriter = csv.writer(open('plus_chocolate.csv', 'a', newline='', encoding='utf-8'))
        self.csvwriter.writerow(['product_id', 'product_naam', 'prijs', 'kilo_prijs', 'omschrijving', 'inhoud', 'ingredienten',
        'kenmerken', 'allergie_bevat', 'allergie_kan_bevatten', 'leverancier', 'adres_leverancier', 
        'product_url'])

    #Function to encode the values of the item dictionary and write them into a csv file
    def process_item(self, item, spider):
        self.csvwriter.writerow([item.get('product_id'), item.get('product_naam'), item.get('prijs'), item.get('kilo_prijs'),item.get('omschrijving'),
        item.get('inhoud'), item.get('ingredienten'), item.get('kenmerken'), item.get('allergie_bevat'),
        item.get('allergie_kan_bevatten'), item.get('leverancier'), item.get('adres_leverancier'), item.get('product_url')])
        return item
