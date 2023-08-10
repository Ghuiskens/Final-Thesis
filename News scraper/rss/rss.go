package rss

import (
	"github.com/mmcdole/gofeed"
	"github.com/phuslu/log"
	"golang.org/x/time/rate"
	"scraper/structs"
	"scraper/util"
	"strings"
	"time"
)

var (
	fp = gofeed.NewParser()
)

func FetchRSS(url string, rl *rate.Limiter, sourceConfig structs.SourceConfig) []map[string]any {

	r := rl.Reserve()
	time.Sleep(r.Delay())

	feed, err := fp.ParseURL(url)

	// If we get an error, pause and retry once
	if err != nil {
		log.Warn().Msgf("Error fetching RSS feed %s", url)
		time.Sleep(10 * time.Second)
		feed, err = fp.ParseURL(url)
	}
	if err != nil {
		log.Warn().Msgf("Second error fetching RSS feed %s", url)
		return []map[string]any{}
	} else {
		util.Check(err)
		log.Info().Msgf("Fetched RSS feed: %s, Found: %d", feed.Title, len(feed.Items))
		return parseRss(feed, sourceConfig)
	}
}

func parseRss(rssFeed *gofeed.Feed, sourceConfig structs.SourceConfig) []map[string]any {

	var rssMap []map[string]any
	for _, item := range rssFeed.Items {
		outputMap := map[string]any{
			"source":      sourceConfig.Name,
			"url":         item.Link,
			"title":       item.Title,
			"description": item.Description,
			"content":     item.Content,
			"links":       item.Links,
			"updated":     item.Updated,
			"published":   item.Published,
			"authors":     item.Authors,
			"guid":        item.GUID,
			"categories":  item.Categories,
		}

		if !sourceConfig.Scrape {
			outputMap["text"] = strings.Split(item.Description, "\n")
		}

		rssMap = append(rssMap, outputMap)
	}
	return rssMap
}
