package main

import (
	"fmt"
	"io/ioutil"
	"runtime/debug"
	"scraper/structs"

	jsoniter "github.com/json-iterator/go"
	"github.com/phuslu/log"
)

func GetConfig() *structs.Config {
	config := &structs.Config{}

	// Read the YAML configuration file
	yamlFile, err := ioutil.ReadFile("path/to/sustainability-config.yml")
	if err != nil {
		log.Fatal("Failed to read config file: ", err)
	}

	// Unmarshal the YAML data into the Config struct
	err = jsoniter.Unmarshal(yamlFile, config)
	if err != nil {
		log.Fatal("Failed to unmarshal config data: ", err)
	}

	// Print the loaded configuration (optional)
	fmt.Printf("Loaded Config: %+v\n", config)

	return config
}

func Check(err error) {
	if err != nil {
		log.Fatal().Err(err).Msgf("Stack Trace: %s", string(debug.Stack()))
	}
}

func StructPrint(outputStruct any) {
	fmt.Printf("%+v\n", outputStruct)
}

func PrettyPrint(outputStruct any) {
	s, err := jsoniter.MarshalIndent(outputStruct, "", " ")
	Check(err)
	fmt.Println(string(s))
}
