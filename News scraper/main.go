package main

import (
	"scraper/fetcher"
	"scraper/util"
)

func main() {

	// Load config
	config := util.GetConfig()

	fetcher.Fetcher(config)
}
