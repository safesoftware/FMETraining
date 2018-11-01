# Notes

## Review to-do

1. Change Date in AttributeManager to `@Value(Year)/@Value(Month)/@Value(Day)` for every workspace

## General

- Structural versus content transformation not coming across well
- Only covered attribute mapping, not feature mapping as a concept
- Consistent formatting, e.g. use of **bold** and `code`
  - do special sections stand out? File paths, names, menu instructions, attributes, etc.

## Exercise skill progression

**New module**

1.1. Open and run workspace
- Same example, or new one?
2.1. Generate workspace
- XLS: ftp://webftp.vancouver.ca/opendata/xls/CaseLocationsDetails_2017_XLS.zip
- CSV
2.2. Inspect data
- Just feature caches and workspace output
2.3. Schema editing and mapping (do we still call it that? same skills)
- Remove underscores from attribute names
- Remove Hour and Minute attributes?
3.1. Finding transformers
- Looking: Gallery, Quick Add, online
- Adding with drag from Gallery and with Quick Add
- Selecting parts to add with connections
3.2. Common transformations
- Tester
- AttributeValueMapper
- AttributeManager (manage schema; add now, update later)
4.1. Multiple readers and writers, including db and/or web. Adding FT. (no new trans)
- Read and write KML
- AttributePivoter (a kind of odd one, but roughly analogous to StatisticsCalculator, familiar to Excel users)
- AttributeExposer
- FeatureJoiner
- KML Styler
- Format attribute editing (kml_polystyle_fill = 1)
4.2. Feature caching
- Example of error?
4.3. Bookmarks and annotations
- Add to workspace

**Getting Started currently**

Proposal: redo these for 2019.0 to align with training, switch inspect and transform

1. Generate workspace
2. Schema editing (and mapping w/o transformer)
3. Adding a transformer
4. Data Inspector (and feature caching)

## Format and solution

- Format
  - CSV
    - https://knowledge.safe.com/articles/687/using-fme-to-read-or-write-comma-separated-value-c.html
  - Excel
  - XML
  - JSON
  - Database
- Solution
  - ?
- Order
  - Start with basic conversion; file should have coords, but not spatial
  - Change schema
  - Add web data and database table, make spatial, some kind of easy output
    - Feature Types To Read at some point
- Look through existing data for candidates that can be joined either on attr or location
  - Addresses
  - Business Licenses
  - Crime
  - Electric vehicle charging stations
  - Speeding Tickets
- Geospatial PDF with attributes -> CSV...
- Excel with multiple tables and lat/long and/or address -> JSON or GeoJSON

## Potential Changes

- Could do only Feature Caching for inspection. Would be a more obvious choice if DI gets integrated. Might still want to show adding data to DI though.

## Questions

1. How frequently to have quizzes? Is once per unit too infrequent? Could try once per section instead. I think once per section with 2-5 questions might be about right. Trailhead does 1 ~5 question quiz per unit, which range from 5-30 minutes.
