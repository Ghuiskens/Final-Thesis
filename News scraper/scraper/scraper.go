package scraper

import (
	"github.com/gocolly/colly/v2"
	"github.com/gocolly/colly/v2/extensions"
	"github.com/jaytaylor/html2text"
	"github.com/phuslu/log"
	"scraper/util"
	"strings"
	"time"
)

func ScrapePage(url string) []string {
	// Initialise collector for scraping
	c := colly.NewCollector(colly.IgnoreRobotsTxt())
	extensions.RandomUserAgent(c)
	extensions.Referer(c)

	var articleStrings, bodyStrings []string

	index := strings.IndexByte(url, '/')
	domain := url[:index]

	err := c.Limit(&colly.LimitRule{
		DomainGlob:  domain + "/*",
		Delay:       2 * time.Second,
		RandomDelay: 1 * time.Second,
	})
	util.Check(err)

	c.SetRequestTimeout(4 * time.Second)

	// Before making a request print "Visiting ..."
	c.OnRequest(func(r *colly.Request) {
		log.Info().Msgf("Visiting: %s", r.URL.String())
	})

	c.OnHTML("article", func(e *colly.HTMLElement) {
		articleStrings = parseHTML(e, articleStrings)
	})

	c.OnHTML("body", func(e *colly.HTMLElement) {
		bodyStrings = parseHTML(e, bodyStrings)
	})

	// Start scraping
	err = c.Visit(url)
	if err != nil {
		log.Warn().Err(err).Msgf("Page could not be scraped: %s", url)
	}

	if len(articleStrings) > 0 {
		return articleStrings
	}
	return bodyStrings
}

func parseHTML(e *colly.HTMLElement, outputList []string) []string {
	elem := e.DOM.Find("p")
	for _, node := range elem.Nodes {
		text, err3 := html2text.FromHTMLNode(node, html2text.Options{
			PrettyTables: true,
			OmitLinks:    true,
			TextOnly:     true,
		})
		util.Check(err3)
		if len(text) > 150 {
			outputList = append(outputList, text)
		}
	}
	return outputList
}
