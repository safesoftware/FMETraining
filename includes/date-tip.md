{% call template.tip() %}

If you want to use a more realistic - but also more complicated - example, you can generate a [standard FME date/time stamp](https://docs.safe.com/fme/html/FME_Desktop_Documentation/FME_Workbench/!Transformer_Parameters/standard_fme_date_time_format.htm). To do so, copy and paste the following code into the Text Editor:

```
@TimeZoneSet(@Format(%04d,@Value(Year))@Format(%02d,@Value(Month))@Format(%02d,@Value(Day))@Format(<%02d></%02d>,@Value(Hour))@Format(%02d,@Value(Minute))00, local)
```

The details aren't important here, but if you want them, read on. In short, we are using the `@TimeZoneSet` function to add a [UTC offset](https://en.wikipedia.org/wiki/UTC_offset) to each date/time stamp. We are forming the date/time stamp by combining the attributes from our source data into a string matching [FME date/time format]((https://docs.safe.com/fme/html/FME_Desktop_Documentation/FME_Workbench/!Transformer_Parameters/standard_fme_date_time_format.htm)): `yyyymmddhhss-UTC`. Our original data had single digit months, days, hours, and minutes missing the leading zero, so we use the `@Format` function to fix that problem. This new attribute will be easier to use in FME workflows.

{% endcall %}
