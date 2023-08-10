package util

import (
	"flag"
	"os"
	"scraper/structs"

	"gopkg.in/yaml.v3"
)

type Flags struct {
	ConfigPath *string
}

func GetFlags() Flags {

	flags := Flags{
		ConfigPath: flag.String("configPath", "conf/config.yml", "Path to the main config YAML file"),
	}

	flag.Parse()

	return flags
}

func GetConfig() *structs.Config {

	flags := GetFlags()

	var config structs.Config

	readYaml(&config, *flags.ConfigPath)

	config.SourcesMap = map[string]structs.SourceConfig{}
	for _, sourceConfig := range config.Sources {
		if sourceConfig.UrlPath == "" {
			sourceConfig.UrlPath = "url"
		}
		if sourceConfig.TitlePath == "" {
			sourceConfig.TitlePath = "title"
		}
		if sourceConfig.TextPath == "" {
			sourceConfig.TextPath = "text"
		}
		config.SourcesMap[sourceConfig.Name] = sourceConfig
	}

	return &config
}

func readYaml(config interface{}, configPath string) {
	f, err := os.Open(configPath)
	Check(err)

	decoder := yaml.NewDecoder(f)
	err = decoder.Decode(config)
	Check(err)

	err = f.Close()
	Check(err)
}
