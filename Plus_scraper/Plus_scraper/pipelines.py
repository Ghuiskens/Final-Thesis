from itemadapter import ItemAdapter
import csv

class WriteToCsvPipeline(object):
    def __init__(self):
        self.csvwriter = csv.writer(open('plus_chocolate.csv', 'a', newline='', encoding='utf-8'))
        self.csvwriter.writerow(['product_id', 'product_naam', 'prijs', 'kilo_prijs', 'omschrijving', 'inhoud', 'ingredienten',
        'kenmerken', 'allergie_bevat', 'allergie_kan_bevatten', 'leverancier', 'adres_leverancier', 
        'product_url'])

    def process_item(self, item, spider):
        self.csvwriter.writerow([item.get('product_id'), item.get('product_naam'), item.get('prijs'), item.get('kilo_prijs'),item.get('omschrijving'),
        item.get('inhoud'), item.get('ingredienten'), item.get('kenmerken'), item.get('allergie_bevat'),
        item.get('allergie_kan_bevatten'), item.get('leverancier'), item.get('adres_leverancier'), item.get('product_url')])
        return item
