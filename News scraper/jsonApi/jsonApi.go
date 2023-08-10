package jsonApi

import (
	"encoding/json"
	"github.com/phuslu/log"
	"github.com/tidwall/gjson"
	"golang.org/x/time/rate"
	"io"
	"net/http"
	"scraper/structs"
	"scraper/util"
	"strings"
	"time"
)

func FetchMultiJson(url string, client *http.Client, rl *rate.Limiter, sourceConfig structs.SourceConfig) []map[string]any {

	req, err := http.NewRequest(http.MethodGet, url, nil)
	util.Check(err)

	if sourceConfig.ApiKey != "" {
		req.Header.Set("x-api-key", sourceConfig.ApiKey)
	}
	req.Header.Set("User-Agent", "rss_reader")

	r := rl.Reserve()
	time.Sleep(r.Delay())

	res, getErr := client.Do(req)
	// If we get an error, pause and retry once
	if getErr != nil {
		log.Warn().Msgf("Error fetching JSON feed %s", url)
		time.Sleep(10 * time.Second)
		res, getErr = client.Do(req)
	}
	util.Check(getErr)

	body, readErr := io.ReadAll(res.Body)
	util.Check(readErr)

	var outArray []map[string]any
	for _, value := range gjson.Get(string(body), sourceConfig.JsonPath).Array() {

		outMap := map[string]any{"source": sourceConfig.Name}

		outMap["url"] = gjson.Get(value.String(), sourceConfig.UrlPath).String()
		delete(value.Map(), "url")

		outMap["title"] = gjson.Get(value.String(), sourceConfig.TitlePath).String()
		delete(value.Map(), "title")

		var outText []string
		for _, str := range strings.Split(gjson.Get(value.String(), sourceConfig.TextPath).String(), "\n") {
			if str != "" {
				outText = append(outText, str)
			}
		}
		outMap["text"] = outText
		delete(value.Map(), "text")

		for k, v := range value.Map() {
			switch v.Type.String() {
			case "Null":
			case "False":
			case "Number":
				outMap[k] = v.Num
			case "String":
				outMap[k] = v.String()
			case "True":
				outMap[k] = v.Bool()
			case "JSON":
				jsonMap, ok := v.Value().(map[string]interface{})
				if !ok {
					var jsonArray []string
					for _, arrayValue := range v.Array() {
						jsonArray = append(jsonArray, arrayValue.String())
					}
					outMap[k] = jsonArray
				} else {
					outMap[k] = jsonMap
				}
			default:
				log.Fatal().Msgf("Invalid type in JSON: " + v.Type.String())
			}
		}

		outArray = append(outArray, outMap)
	}
	return outArray
}

func FetchSingleJson(url string, client *http.Client, rl *rate.Limiter, sourceConfig structs.SourceConfig) map[string]any {

	req, err := http.NewRequest(http.MethodGet, url, nil)
	util.Check(err)

	if sourceConfig.ApiKey != "" {
		req.Header.Set("x-api-key", sourceConfig.ApiKey)
	}
	req.Header.Set("User-Agent", "rss_reader")

	r := rl.Reserve()
	time.Sleep(r.Delay())

	res, getErr := client.Do(req)
	util.Check(getErr)

	body, readErr := io.ReadAll(res.Body)
	util.Check(readErr)

	var outMap map[string]any
	jsonErr := json.Unmarshal(body, &outMap)
	util.Check(jsonErr)
	return outMap
}
