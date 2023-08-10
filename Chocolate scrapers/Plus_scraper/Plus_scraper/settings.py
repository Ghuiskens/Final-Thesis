#Scrapy settings for Plus_scraper project
#Name of the bot
BOT_NAME = "Plus_scraper"

#Spider module and newspider module
SPIDER_MODULES = ["Plus_scraper.spiders"]
NEWSPIDER_MODULE = "Plus_scraper.spiders"

#Obey the robot.txt rules on plus.nl
ROBOTSTXT_OBEY = False

#Configure the download delay for the crawler
DOWNLOAD_DELAY = 2

#Enable the middleware lcated in the middleware file
DOWNLOADER_MIDDLEWARES = {
    "Plus_scraper.middlewares.PlusDownloaderMiddleware": 1,
}

#Configure item pipelines
#See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "Plus_scraper.pipelines.WriteToCsvPipeline": 300,
}