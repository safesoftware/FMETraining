# Notes

## Review to-do

1. Change Date in AttributeManager to `@Value(Year)/@Value(Month)/@Value(Day)` for every workspace

## General

- Structural versus content transformation not coming across well
- Only covered attribute mapping, not feature mapping as a concept
- Consistent formatting, e.g. use of **bold** and `code`
  - do special sections stand out? File paths, names, menu instructions, attributes, etc.
- Accessibility?

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

# Videos for 2019.0

## 1.1.

<iframe width="770" height="433" src="https://www.youtube.com/embed/?listType=playlist&list=PLFxZDg3GNCguPKqew9ZvqCNZCZOoiwtC5&index=1" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
_Video covering schema editing and mapping. This video will be updated to match this exercise for the FME 2019.0 release._

## 2.1

<iframe width="770" height="433" src="https://www.youtube.com/embed/?listType=playlist&list=PLFxZDg3GNCguPKqew9ZvqCNZCZOoiwtC5&index=0" frameborder="0"
 allow="autoplay; encrypted-media" allowfullscreen></iframe>
_Video covering generating a workspace. This video will be updated to match this exercise for the FME 2019.0 release._

## 2.2

<iframe width="770" height="433" src="https://www.youtube.com/embed/?listType=playlist&list=PLFxZDg3GNCguPKqew9ZvqCNZCZOoiwtC5&index=3" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
_Video covering use of the FME Data Inspector. This video will be updated to match this exercise for the FME 2019.0 release._

## 3.1

<iframe width="770" height="433" src="https://www.youtube.com/embed/?listType=playlist&list=PLFxZDg3GNCguPKqew9ZvqCNZCZOoiwtC5&index=2" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
_Video covering adding transformers. This video will be updated to match this exercise for the FME 2019.0 release._

# Unused schema mapping section

Add a new attribute, called `Date`, that we will supply values to later. Carry out the following actions:

|Name|Action|
|-|-|
|`Case_Type`|Rename attribute to `Case Type`|
|`Hundred_Block`|Rename attribute to `Hundred Block`|
|`Street_Name`|Rename attribute to `Street Name`|
|`Local_Area`|Rename attribute to `Local Area`|
|`Date`|Create attribute `Date` of Type `string`|

You can rename attributes by clicking in the Name cell and making your edit. You can add an attribute by clicking in the blank Name cell at the bottom of the table and entering a new attribute name. Alternatively, you can use the `+` button to add a new row.  You can give it the Type `string` by clicking the drop-down menu under Type and selecting `string`.

Once you have made these changes to the writer schema, click OK. The attribute list should now look like this:

![](./Images/user-attributes-edited.png)

However, you might notice that the triangles next to the attribute names we edited and created on the writer feature type have changed color to red! We call these triangles **ports**. When they are on the left side of an object, they are called **input ports**, while triangles on the right side are called **output ports**. You can notice the attributes we edited have changed color to yellow.

{% call template.tip() %}

Colored ports are used to aid schema mapping visually:

<ul>
  <li><span style="color:#23AD19; font-style: normal">Green &#9654;</span>: this attribute is connected.</li>
  <li><span style="color:#E8E058; font-style: normal">Yellow &#9654;</span>: this reader feature type attribute is not mapped to any writer feature type; therefore, this attribute will not be in the output.</li>
  <li><span style="color:#B80909; font-style: normal">Red &#9654;</span>: this writer feature type attribute is not connected; while it exists in the schema, it will not receive any data and therefore will not have any values in the written data.</li>
</ul>

{% endcall %}
