package main

import (
	"encoding/gob"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"regexp"
	"scraper/jsonApi"
	"scraper/rss"
	"scraper/scraper"
	"scraper/structs"
	"scraper/util"
	"strings"
	"sync"
	"time"

	"github.com/phuslu/log"
	"golang.org/x/time/rate"
	"gopkg.in/yaml.v2"
)

func LoadConfig(filename string) *structs.Config {
	config := &structs.Config{}
	data, err := ioutil.ReadFile(filename)
	if err != nil {
		log.Fatal().Err(err).Msg("Failed to read configuration file")
	}

	err = yaml.Unmarshal(data, config)
	if err != nil {
		log.Fatal().Err(err).Msg("Failed to parse configuration file")
	}

	return config
}

func Fetcher(config *structs.Config) {

	urlMap := getPreviousURLs(config)
	defer storePreviousURLs(urlMap, config)

	client := &http.Client{
		Timeout: time.Second * 30,
	}

	processingChannel := make(chan map[string]interface{}, 1000)
	outputChannel := make(chan map[string]interface{}, 1000)

	var sourceRateLimit = rate.NewLimiter(rate.Every(time.Duration(config.SourceRateLimit)*time.Millisecond), 1)
	var scrapeRateLimit = rate.NewLimiter(rate.Every(time.Duration(config.ScrapeRateLimit)*time.Millisecond), 1)

	requiredTermsRegexMap := map[string]*regexp.Regexp{}
	// Initialise Processing Workers
	var processingWaitGroup sync.WaitGroup
	for w := 0; w < config.Threads; w++ {
		processingWaitGroup.Add(1)
		go processWorker(processingChannel, outputChannel, client, sourceRateLimit, scrapeRateLimit, requiredTermsRegexMap, config, &processingWaitGroup)
	}

	var outputWaitGroup sync.WaitGroup
	outputWaitGroup.Add(1)
	go outputWorker(outputChannel, config, &outputWaitGroup)

	for _, sourceConfig := range config.Sources {
		if sourceConfig.Enabled {
			log.Info().Msgf("----- Processing %s -----", sourceConfig.Name)

			requiredTermsRegex := makeRequiredTermsRegex(sourceConfig.ScrapeRequiredTerms)
			if requiredTermsRegex != nil {
				requiredTermsRegexMap[sourceConfig.Name] = requiredTermsRegex
			}

			for _, terms := range sourceConfig.TermsList {
				if sourceConfig.PeriodWeeks > 0 {
					endDate := time.Now().AddDate(0, 0, 1)
					startDate := endDate.AddDate(0, 0, -sourceConfig.PeriodWeeks*7)
					for i := 0; i < sourceConfig.NumPeriods; i += 1 {
						url := fmt.Sprintf(sourceConfig.Url, strings.Replace(terms, " ", "%20", -1), startDate.Format(sourceConfig.DateFormat), endDate.Format(sourceConfig.DateFormat))
						log.Info().Msgf("----- Processing %s Terms %s, URL: %s -----", sourceConfig.Name, terms, url)

						documents := parseDocuments(url, sourceConfig, client, sourceRateLimit)
						endDate = endDate.AddDate(0, 0, -sourceConfig.PeriodWeeks*7)
						startDate = endDate.AddDate(0, 0, -sourceConfig.PeriodWeeks*8)

						for _, document := range documents {
							documentUrl := strings.Replace(document["url"].(string), "http://", "https://", 1)
							if !urlMap[documentUrl] {
								urlMap[documentUrl] = true
								processingChannel <- document
							}
						}
					}
				} else if sourceConfig.Paginate > 0 {
					startIndex := sourceConfig.StartIndex
					endIndex := sourceConfig.Paginate
					moreRecords := true

					for moreRecords {
						url := fmt.Sprintf(sourceConfig.Url, strings.Replace(terms, " ", "%20", -1), startIndex, endIndex)
						log.Info().Msgf("----- Processing %s Terms %s, URL: %s -----", sourceConfig.Name, terms, url)

						documents := parseDocuments(url, sourceConfig, client, sourceRateLimit)

						for _, document := range documents {
							documentUrl := strings.Replace(document["url"].(string), "http://", "https://", 1)
							if !urlMap[documentUrl] {
								urlMap[documentUrl] = true
								processingChannel <- document
							}
						}
						if len(documents) > 0 {
							startIndex = startIndex + sourceConfig.Paginate
							if sourceConfig.PaginateType == "max" {
								endIndex = endIndex + sourceConfig.Paginate
							}
						} else {
							moreRecords = false
						}
					}
				}
			}
		}
	}

	close(processingChannel)

	processingWaitGroup.Wait()
	close(outputChannel)

	outputWaitGroup.Wait()

}

func parseDocuments(url string, sourceConfig structs.SourceConfig, client *http.Client, rl *rate.Limiter) []map[string]interface{} {
	var outputMap []map[string]interface{}
	if sourceConfig.Type == "rss" {
		outputMap = rss.FetchRSS(url, rl, sourceConfig)
	} else if sourceConfig.Type == "json" {
		outputMap = jsonApi.FetchMultiJson(url, client, rl, sourceConfig)
	}
	return outputMap
}

func processWorker(processingChannel chan map[string]interface{}, outputChannel chan map[string]interface{}, client *http.Client, sourceRateLimit *rate.Limiter, scrapeRateLimit *rate.Limiter, requiredTermsRegexMap map[string]*regexp.Regexp, config *structs.Config, wg *sync.WaitGroup) {

	defer wg.Done()

	for document := range processingChannel {
		docName := document["source"].(string)
		sourceConfig := config.SourcesMap[docName]
		output := true
		if sourceConfig.Scrape {
			r := scrapeRateLimit.Reserve()
			time.Sleep(r.Delay())
			documentText := scraper.ScrapePage(document["url"].(string))
			document["text"] = documentText
			if requiredTermsRegex, ok := requiredTermsRegexMap[sourceConfig.Name]; ok {
				if !requiredTermsRegex.MatchString(strings.ToLower(strings.Join(documentText, " "))) {
					output = false
				}
			}
		}
		if sourceConfig.SecondaryUrl != "" {
			joinValue := document[sourceConfig.JoinField].(string)
			secondaryUrl := fmt.Sprintf(sourceConfig.SecondaryUrl, strings.Replace(joinValue, " ", "%20", -1))
			secondaryDocument := jsonApi.FetchSingleJson(secondaryUrl, client, sourceRateLimit, sourceConfig)
			// Add in values from secondary call to primary document
			for k, v := range secondaryDocument {
				document[k] = v
			}
		}
		if output {
			outputChannel <- document
		}
	}
}

func outputWorker(outputChannel chan map[string]interface{}, config *structs.Config, wg *sync.WaitGroup) {

	defer wg.Done()

	fileMap := map[string]*os.File{}

	for sourceName, sourceConfig := range config.SourcesMap {
		if sourceConfig.Enabled {
			f, err := os.Create(fmt.Sprintf("%s/%s.jsonl", config.OutputPath, sourceName))
			util.Check(err)
			fileMap[sourceName] = f
		}
	}

	for document := range outputChannel {

		docType := document["source"].(string)
		delete(document, "source")
		documentJson, err := json.Marshal(document)
		util.Check(err)

		f := fileMap[docType]
		_, err = f.WriteString(string(documentJson) + "\n")
		util.Check(err)
	}

	for _, file := range fileMap {
		closeErr := file.Close()
		util.Check(closeErr)
	}
}

func getPreviousURLs(config *structs.Config) map[string]bool {

	mapFilePath := fmt.Sprintf("%s/urlMap.gob", config.StatePath)

	if _, err := os.Stat(mapFilePath); err == nil && config.PersistProcessedUrls {
		var urlMap map[string]bool

		// open data file
		dataFile, err2 := os.Open(mapFilePath)
		util.Check(err2)

		dataDecoder := gob.NewDecoder(dataFile)
		err = dataDecoder.Decode(&urlMap)
		util.Check(err)

		err = dataFile.Close()
		util.Check(err)

		return urlMap
	} else {
		return map[string]bool{}
	}
}

func storePreviousURLs(urlMap map[string]bool, config *structs.Config) {

	if config.PersistProcessedUrls {

		mapFilePath := fmt.Sprintf("%s/urlMap.gob", config.StatePath)
		dataFile, err := os.Create(mapFilePath)
		util.Check(err)

		// serialize the data
		dataEncoder := gob.NewEncoder(dataFile)
		err = dataEncoder.Encode(urlMap)
		util.Check(err)

		err = dataFile.Close()
		util.Check(err)
	}
}

func makeRequiredTermsRegex(requiredTerms []string) *regexp.Regexp {

	if len(requiredTerms) > 0 {
		return regexp.MustCompile(strings.Join(requiredTerms, "|"))
	} else {
		return nil
	}
}
