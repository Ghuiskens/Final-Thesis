#Settings file for ah_spider
#Name of the bot
BOT_NAME = "AH_scraper"

#Spider module and newspider module
SPIDER_MODULES = ["AH_scraper.spiders"]
NEWSPIDER_MODULE = "AH_scraper.spiders"

#Obey the robots.txt rules on ah.nl
ROBOTSTXT_OBEY = False

#Configure the delay for the crawler
DOWNLOAD_DELAY = 1.5

#Enable the middlware located in the middlware file
DOWNLOADER_MIDDLEWARES = {
    "AH_scraper.middlewares.AhDownloaderMiddleware": 1,
}

#Configure item pipelines that are needed
ITEM_PIPELINES = {
    "AH_scraper.pipelines.WriteToCsvPipeline": 300,
}

#Enable and configure the AutoThrottle extension (disabled by default)
AUTOTHROTTLE_ENABLED = True
#The initial download delay
AUTOTHROTTLE_START_DELAY = 5
#The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60
#The average number of requests Scrapy should be sending in parallel to
#each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1000.0
#Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False
