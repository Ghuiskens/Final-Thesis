package structs

type Config struct {
	Threads              int            `yaml:"threads"`
	StatePath            string         `yaml:"state_path"`
	OutputPath           string         `yaml:"output_path"`
	LogLevel             string         `yaml:"log_level"`
	PersistProcessedUrls bool           `yaml:"persist_processed_urls"`
	SourceRateLimit      int            `yaml:"source_rate_limit"`
	ScrapeRateLimit      int            `yaml:"scrape_rate_limit"`
	Sources              []SourceConfig `yaml:"sources"`
	SourcesMap           map[string]SourceConfig
}

type SourceConfig struct {
	Name                string   `yaml:"name"`
	Enabled             bool     `yaml:"enabled"`
	Type                string   `yaml:"type"`
	Url                 string   `yaml:"url"`
	ApiKey              string   `yaml:"api_key"`
	JsonPath            string   `yaml:"json_path"`
	UrlPath             string   `yaml:"url_path"`
	UrlPrefix           string   `yaml:"url_prefix"`
	TitlePath           string   `yaml:"title_path"`
	TextPath            string   `yaml:"text_path"`
	PeriodWeeks         int      `yaml:"period_weeks"`
	NumPeriods          int      `yaml:"num_periods"`
	DateFormat          string   `yaml:"date_format"`
	Paginate            int      `yaml:"paginate"`
	PaginateType        string   `yaml:"paginate_type"`
	StartIndex          int      `yaml:"start_index"`
	SecondaryUrl        string   `yaml:"secondary_url"`
	JoinField           string   `yaml:"join_field"`
	Scrape              bool     `yaml:"scrape"`
	ScrapeRequiredTerms []string `yaml:"scrape_required_terms"`
	TermsList           []string `yaml:"terms_list"`
}
