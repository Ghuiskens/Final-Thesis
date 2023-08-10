package util

import (
	"fmt"
	jsoniter "github.com/json-iterator/go"
	"github.com/phuslu/log"
	"runtime/debug"
)

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
