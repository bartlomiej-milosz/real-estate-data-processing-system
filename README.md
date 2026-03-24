# Real Estate Data Processing System

This project implements an automated pipeline for scraping, processing, and normalizing real estate listings (sales and rentals) from the Warsaw market. It handles the transition from raw web data to structured CSV files suitable for data analysis.

## Technical Implementation

### Data Acquisition

The scraping module is built using Requests and BeautifulSoup4. Key technical features include:

- Multi-threaded execution: Uses ThreadPoolExecutor to parallelize the retrieval of property details, increasing throughput.
- Dynamic Query Construction: A configuration system that generates valid search URLs based on district, property type, and price constraints.
- Session Management: Implements persistent HTTP sessions with customized headers to maintain connection stability.

### Data Processing and Normalization

The cleaning engine utilizes Pandas and Regular Expressions to transform raw scraped text into a standardized format:

- Feature Extraction: Parses unstructured text to create boolean indicators for amenities such as balconies, elevators, and security features.
- Location Parsing: Splits complex address strings into district, neighborhood, and street components.
- Value Normalization: Standardizes numeric fields (price, area, year built) by removing non-numeric characters and enforcing consistent data types.
- Data Integration: Automatically combines individual district-level files into unified datasets for both sales and rentals.

## Project Structure

- src/scraper/: Logic for navigating listing pages and extracting property-specific details.
- src/cleaner/: Pandas-based workflows for data validation and normalization.
- src/models/: Data structures and type definitions used throughout the pipeline.
- data/raw/: Initial storage for scraped data, organized by transaction type and district.
- data/clean/: Processed datasets, including unified CSV files in the combined/ subdirectory.

## Requirements

The project requires Python 3.9+ and the following libraries:

- pandas
- beautifulsoup4
- requests
- numpy

## Usage

### 1. Data Collection

To execute the scraping process for all Warsaw districts:

```bash
python -m src.run_scraper_batch
```

This script populates the data/raw directory with CSV files for each district.

### 2. Data Cleaning

To process the raw data and generate the final datasets:

```bash
python -m src.run_cleaner_batch
```

This will normalize all raw files and produce combined outputs in data/clean/combined/warsaw_all_sales.csv and data/clean/combined/warsaw_all_rents.csv.
