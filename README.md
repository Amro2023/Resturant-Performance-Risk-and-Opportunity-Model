# Restaurant Performance Risk and Opportunity Model

## Capstone Project Overview

This project develops a Restaurant Performance Risk and Opportunity Model focused on restaurant locations within the United States. The goal is to determine whether public customer reputation data and market-context indicators can be used to identify restaurant locations with higher performance risk or stronger opportunity for improvement.

The initial public-data analysis will use U.S.-based restaurant records from the Yelp Open Dataset. The Yelp data will provide restaurant business information, categories, ratings, review counts, and customer review text. Later in the project, model patterns may be compared against available Denny’s U.S. business intelligence data as an enterprise validation layer.

## Business Problem

Restaurant operators manage large portfolios of locations but often need earlier indicators of potential performance risk. Public reputation signals, such as customer ratings and review sentiment, may help identify restaurant locations that require operational attention before performance declines become more significant.

This project will explore whether restaurant reputation and market-context indicators can be combined into a practical risk and opportunity framework.

## Project Objectives

1. Build a clean U.S.-only restaurant sample from the Yelp Open Dataset.
2. Analyze restaurant ratings, review counts, categories, and customer review text.
3. Develop sentiment or reputation-based performance risk indicators.
4. Incorporate nationwide market-context data where feasible.
5. Compare public-data patterns against available Denny’s U.S. business intelligence data.
6. Present findings through visualizations, a scoring framework, and business recommendations.

## Initial Data Sources

| Data Source                        | Purpose                                                                | Status      |
| ---------------------------------- | ---------------------------------------------------------------------- | ----------- |
| Yelp Open Dataset                  | Restaurant businesses, ratings, review counts, reviews, and categories | Downloaded  |
| USDA Food Environment Atlas        | U.S. county-level restaurant and market environment indicators         | Planned     |
| U.S. Census ACS                    | Population, income, poverty, and demographic variables                 | Planned     |
| Denny’s Business Intelligence Data | Enterprise validation of identified patterns                           | Later Phase |

## Geographic Scope

The business scope of the project is the United States restaurant industry. The initial modeling sample will be limited to U.S.-based restaurant locations represented in the Yelp Open Dataset. This limitation will be clearly documented because the Yelp Open Dataset does not represent all U.S. restaurants.

## Planned Deliverables

* Cleaned restaurant dataset
* Data dictionary
* Exploratory data analysis
* Sentiment or reputation risk indicators
* Restaurant risk and opportunity scoring framework
* Visualizations or dashboard outputs
* Final business recommendations

## Tools

* Google Colab for notebook development and exploratory analysis
* Visual Studio Code for local project organization and code management
* GitHub for version control
* Python for data cleaning, analysis, and modeling

## Current Project Status

### Week 1: Finalize Scope and Acquire Data

* Project scope defined as U.S. restaurants only
* Yelp Open Dataset downloaded
* Local project folder established
* GitHub repository created
* Initial README and data dictionary planned
* Next step: load and inspect Yelp business data in Google Colab
