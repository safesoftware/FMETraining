# Database Optimization

Using database functionality inefficiently will do more to degrade performance than almost anything else in FME.

Besides the previous performance tips and tricks, there are some that apply only to databases and some that apply only to specific formats of database.

Database Reading

Reading and filtering data (querying) from a database is nearly always faster when you can use the native functionality of the database.

For Readers this means using the various parameters that occur in the Navigator window of Workbench, like this SQL Server Reader:

Here there is a WHERE clause and a bounding box. When you set these then FME’s query to the database includes these parameters.

This is way faster than reading the entirety of a database and filtering it by attribute (Tester) or geometry (SpatialFilter).

Additionally, Reader feature types often contain a set of parameters containing WHERE clauses and SELECT statements, which mean you can set a query to apply to just one particular table in your workspace:

Besides Readers, transformers can also be used to query database data. The best to use is the SQLExecutor (or SQLCreator) as these pass their queries to the database using native SQL. If you don’t want to write SQL then you can use the FeatureReader transformer; but be aware this transformer is more generic and won’t give quite the same performance.

The SQLExecutor is particularly worth being aware of, as it issues a query for each incoming feature. This can be useful where you need to make multiple queries.

For example, here a query is issued to the database for every address feature that enters the SQLExecutor.

Generally the output from the SQLExecutor is an entirely new feature. If you want to simply retrieve attributes to attach to the incoming feature, then the Joiner transformer is more appropriate:

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Jake Speedie says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“FME is fast, but if you can filter or process data in its native
environment, it’s likely to be faster still.
For example, a materialized view (a database object containing the results of a query) is
going to perform better than reading the data and filtering it in FME. Similarly, a SQL
Join is going to perform better than reading two tables into FME and using the
FeatureMerger transformer.
Sometimes it really is a case of working smart, not hard!”
</span>
</td>
</tr>
</table>

**Queries and Indexing**

Of course, all queries will run faster if carried out on indexed fields – whether these are spatial or plain attribute indexes – and where the queries are well-formed.

To assess how good performance is, remember the log interpretation method of checking timings:

For example, take this section of log timings:

2014-07-10 14:43:06| 8.5| 0.0|
2014-07-10 14:43:13| 8.8| 0.3|
2014-07-10 14:46:29| 18.0| 9.1|
2014-07-10 14:49:29| 25.8| 7.9|

The workspace took over six minutes to complete this part, but FME is only reporting 25.8 seconds of processing! If the query is to a database then the conclusion is that the fields are either not indexed or the query is badly formed.

To confirm this you could open a SQL tool – for example the SQL Server Management Studio – and run the query there. If it takes as long to run there as in FME, then you know for sure FME is not the bottleneck in your performance.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Jake Speedie says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“Structure your SQL commands so that indexed attributes are first,
followed by the most limiting of the other matches. For example, if one
portion of the clause matches 10 rows, and another matches 1000 rows,
put the one matching only 10 first.”
</span>
</td>
</tr>
</table>

Besides indexes, there are other inbuilt functions that can cause databases to return data slower than expected.

For example, when reading from a Geodatabase geometric network, all of the connectivity information must be verified. Therefore, reading is faster if the network information is ignored.

This can be achieved using the “Ignore Network Info” parameter for the Geodatabase reader. A similar parameter exists for the Reader to be able to ignore Relationships.

Similarly, Excel formulas can be expensive to read, so turning them off when the schema is generated can speed up reading the data:

**Database Writing**

Whereas the performance of reading from a database is largely dependent on the database setup itself, when writing to a database there are very many FME parameters that can help to fine tune the workspace performance.

Remember that writing to a database incurs network overheads. There has to be a balance between the amount of data being sent (the network traffic), database performance, and the risk of losing uncommitted data.

Each database Writer has a set of parameters for handling the number of features to write for any particular transaction.

The Oracle Spatial Writer parameters look like this:

The two common parameters for controlling database writes are  “Features per Transaction” and “Features per Bulk Write” (chunk).

**Features per Transaction**

Features per Transaction controls how many features are entered into a database before a commit command is issued. Each commit command adds delay to the writing process, so setting this parameter is a way to balance the speed of the translation (a higher number) against the risk that a translation may fail and features need to be rolled-back (a lower number).

For example, if this parameter is set to a value of 1, then each and every feature is committed individually. If the process fails then only the last feature will be lost from the database, but the costs is much reduced performance.

Alternatively, if the parameter is set to a very high value (more than the number of features being written) then only one commit takes place and performance improves. However, if the translation fails, then all features previously written will be rolled-back and lost to the database.

**Features per Bulk Write**

The Features per Bulk Write parameter tells FME how many features to send at a time to the database. Features sent to a database Writer will get cached in memory by FME until this number of features is reached, and only then will they be sent to the database. This is also known as chunk size.

This parameter is a way to balance server performance and network traffic with FME performance. The higher the number the more features FME caches, but the fewer requests it needs to make to the database (and therefore less network traffic).

A lower number means FME caches less data, but there are more requests made to the database.

Features per Bulk Write also needs to be considered against the value of Features per Transaction.

If Features per Transaction is less or equal to Features per Bulk Write, then FME basically caches a number of features and sends them to the database where they are immediately committed.

If Features per Transaction is greater than Features per Bulk Write, then FME is sending features to the database where they will be cached until the transaction commit total is reached.

 <table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Jake Speedie says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“The Transaction and Chunk parameters can differ from format to
format. For example, SQL Server has a single Bulk Option flag rather
than a numeric setting.
Therefore it’s very important that you check out the FME Readers and Writers Manual to
confirm what parameters are available for your database, and how exactly they
operate.”
</span>
</td>
</tr>
</table>

**Writing and Indexing**

Whereas indexes can improve performance for reading data, for writing they can cause a great reduction in the speed of translation.

That’s because the index will often get re-built with every feature (or every transaction) that is committed to the database.

To remedy this it’s suggested that indexes are dropped (deleted) before carrying out bulk inserts of data into a database table.

A Writer feature type also has options to truncate or drop tables when writing to them.

For the above reason, dropping a table is more efficient than truncating it because the drop action also removes the indexes.

For similar reasons, you may want to turn off networking connectivity when writing data to a Geodatabase geometric network.

The city has an online service powered by FME Server, where a resident can input their postal code and receive information about their garbage collection.

The system works, but is perhaps slower than it should be. Let’s run this short exercise to discover why.

**1)** Start Workbench

Open the workspace C:\FMEData2015\Workspaces\DesktopAdvanced\Exercise2d-Begin.fmw

The workspace used for the service looks something like this:

This shows the workspace is reading 13,500+ addresses and filtering out ones that don’t match the required postal code. However, it makes sense to use a WHERE clause if possible, so we don’t have to read so much data to start with.

**2)** Run Workspace

To get a comparison, run the workspace. The statistics for features read will look like this:

The performance will read like this:

*FME Session Duration: 4.3 seconds. (CPU: 4.0s user, 0.2s system)*

*END - ProcessID: 103496, peak process memory usage: 79428 kB*

**3)** Open Feature Type Properties

The Geodatabase Reader doesn’t have a WHERE clause, but the feature type does.

So, open the properties dialog for the PostalAddress feature type and click the Format Parameters tab.

In the WHERE Clause parameter enter: POSTALCODE = 'V6E1Y8.'

**4)** Delete Tester

Now we have the WHERE clause, the Tester transformer is no longer required, so delete it.

**5)** Re-Run Workspace

Re-run the workspace. This time only 4 features are read from the database (because 4 addresses match that postal code). The performance improves accordingly:

*FME Session Duration: 0.6 seconds. (CPU: 0.4s user, 0.2s system)*

*END - ProcessID: 99108, peak process memory usage: 84404 kB*

Memory usage hasn’t improved, but the translation ran 80% faster.