#Import libraries needed for the items file
import scrapy #Mapping the variables as fields for export

#Class to define the strucutre and fields of the item objects
class PlusScraperItem(scrapy.Item):
    product_id = scrapy.Field()
    product_naam = scrapy.Field()
    prijs = scrapy.Field()
    kilo_prijs = scrapy.Field()
    omschrijving = scrapy.Field()
    inhoud = scrapy.Field()
    ingredienten = scrapy.Field()
    kenmerken = scrapy.Field()
    allergie_bevat = scrapy.Field()
    allergie_kan_bevatten = scrapy.Field()
    leverancier = scrapy.Field()
    adres_leverancier = scrapy.Field()
    product_url = scrapy.Field()

    #fields to export
    fields_to_export = ['product_id','product_naam', 'prijs', 'kilo_prijs', 'omschrijving', 'inhoud', 'ingredienten',
     'kenmerken', 'allergie_bevat', 'allergie_kan_bevatten', 'leverancier', 'adres_leverancier', 
     'product_url']