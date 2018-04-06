# Practical Transformer Use #
Transformers are at the very heart of FME's capabilities, like a workshop with a variety of machines capable of turning raw materials into a finished product. It's not for nothing that the main application is called FME Workbench!

![](./Images/Img4.000.AWorkshopOfTools.png)

To be able to use FME efficiently, being able to find the right transformer is an important skill, and it helps that many of the most-used transformers have a common theme.

For example, many transformers are related to being able to filter data within a workspace; once you understand the concept of filtering data, it becomes easier to find the transformer you need.

It's also important to understand the common aspects of transformers, to recognize that options and parameters in different transformers often operate in similar ways.

This chapter covers various searching methods for finding transformers, the common themes of the most popular transformers, and how parameter values can be constructed within a single transformer dialog.

# Locating Transformers #
Even experienced FME users find the full list of transformers a daunting sight. In this section you’ll learn to stop worrying and love the transformer gallery.

![](./Images/Img4.001.TransformerWebGallery.png)

With over five hundred (500) transformers, FME possesses a lot of functionality; probably a lot more than a new user realizes and much of which would be very useful to them. This section helps you find the transformer you need, even if you didn’t realize you needed it.

Although the transformer list can look a bit overwhelming, don't panic! The reality is that most users focus on 20-30 transformers that are relevant to their day-to-day workflow. You don't need to know every single transformer to use FME effectively.


## Transformer Gallery ##
The transformer gallery window is the obvious place to start looking for transformers. There are a number of ways in which transformers here can be located.

## Transformer Categories ##
Transformer categories are a good starting point from which to explore the transformer list. Transformers are grouped in categories to help find a transformer relevant to the problem at hand.

![](./Images/Img4.002.TransformerGallery.png)

Although all of them are important, the most commonly used transformers are found in these categories:

- **Attributes**: Operations for attribute/list management
- **Calculated Values**: Operations that return a calculated value
- **Filters and Joins**: Operations for dividing and merging data flows
- **Geometries**: Operations that create geometry or transform it to a different geometry type
- **Spatial Analysis**: Operations that return the result of a spatial analysis
- **Strings**: Operations that manipulate string contents, including dates 

Simply click on the expand button to show all transformers within a particular category.

---

## Transformer Help ##
The FME Workbench Help tool displays information about transformers. Simply click on a transformer and press the F1 key to open the help dialog.

This tool is linked to FME Workbench so that a transformer selected (in the gallery or on the canvas) triggers content to display in the Help tool.

![](./Images/Img4.003.TransformerGalleryHelpConnection.png)

---

<!--Tip Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-info-circle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">TIP</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Another useful - and printable - piece of documentation is the <strong><a href="http://cdn.safe.com/resources/fme/FME-Transformer-Reference-Guide.pdf">FME Transformer Reference Guide</a></strong>.
</span>
</td>
</tr>
</table>

## Transformer Searching ##
There are search functions in both the transformer gallery and Quick Add dialog.

### Transformer Gallery Search

To perform a search in the transformer gallery, simply enter the search terms and either press the <enter> key or click the search icon (the binoculars icon).

The transformer gallery search searches in both name and description. Therefore a search term may be the exact name of a transformer, or it may be a general keyword referring to functionality in general:

![](./Images/Img4.004.TransformerGallerySearch.png)

Search terms can either be full or partial words, and may consist of a number of keywords, including quote marks to enclose a single search reference:

![](./Images/Img4.005.GalleryQuotedSearch.png)

---

### Quick Add Search ###

Quick Add search terms can also be full or partial words:

![](./Images/Img4.006.QuickAddPartName.png)

By default, Quick Add does not look in transformer descriptions, so the search term must be the actual name of a transformer:

![](./Images/Img4.007.QuickAddNameOnly.png)

However, Quick Add will search in the transformer descriptions if you press the &lt;TAB&gt; key:

![](./Images/Img4.008.QuickAddKeywordSearch.png)

Quick Add results include aliases - for example transformers that have an alternative name or which have been renamed - and also include transformers found in the FME Hub:

![](./Images/Img4.009.QuickAddAliasResult.png)

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Firefighter Mapp says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
In case you weren't aware, the FME Hub (hub.safe.com) is a facility for sharing FME functionality such as custom transformers, web connections, and formats:
<br><br><img src="./Images/Img4.010.FMEHubWebSite.png">
<br><br>Transformers from the hub are shown in Quick Add with a small, downwards-pointing arrow, to denote that they will be downloaded if selected.
</span>
</td>
</tr>
</table>

---

#### CamelCase ####
Quick Add also allows the use of CamelCase initials as a shortcut. CamelCase is where a single keyword is made up of several conjoined words, each of which retains an upper case initial; for example AttributeFileWriter (AFW) or ShortestPathFinder (SPF).

![](./Images/Img4.011.QuickAddCamelCase.png)

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td td colspan="2" style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td td colspan="2" style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Try these questions to see if you can search for transformers. 
<br>Which of the following is NOT a category of transformers?
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=1&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. Attributes</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=1&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. Calculations</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=1&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. Data Quality</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=1&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. Workflows</a>
<br><br>Here are four transformers and four categories. Match the transformer to the correct category.
</span>
</td>
</tr>
<tr><td width="50%" style="font-weight: bold; border: 1px solid darkorange">Scenario</td><td style="font-weight: bold; border: 1px solid darkorange">Tool</td></tr>
<tr><td style="border: 1px solid darkorange"><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=2&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">Chopper</a></td><td style="border: 1px solid darkorange">Workflows</td></tr>
<tr><td style="border: 1px solid darkorange"><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=2&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">Terminator</a></td><td style="border: 1px solid darkorange">Strings</td></tr>
<tr><td style="border: 1px solid darkorange"><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=2&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">Matcher</a></td><td style="border: 1px solid darkorange">Geometries</td></tr>
<tr><td style="border: 1px solid darkorange"><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=2&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">DateTimeConverter</a></td><td style="border: 1px solid darkorange">Data Quality</td></tr>
</span>
</td>
</tr>
</table>


# Most Valuable Transformers #

If you have a thorough understanding of the most common transformers then you have a good chance of being a very efficient user of FME Workbench.

Anyone can be proficient in FME using only a handful of transformers, if they are the right ones!

## The Top 30 ##
The [list of transformers](https://www.safe.com/transformers/#/) on the Safe Software web site is ordered by most-used, calculated from user feedback. Having this information tells us where to direct our development efforts in making improvements, but it also gives users a head-start on knowing which of the (500+) FME transformers they’re most likely to need in their work.

The following table (last updated January 2018) provides the list of the most commonly used 30 transformers. The Tester transformer is consistently number one in the list every year, highlighting its importance.

<table style="border-spacing: 0px">
<tr>
<th style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Rank</span></th>
<th style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Transformer</th>
<th style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Rank</span></th>
<th style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Transformer</th>
</tr>
<tr><td style="text-align:center">1</td><td>Tester</td><td style="text-align:center">16</td><td>AttributeRemover</td></tr>
<tr><td style="text-align:center">2</td><td>AttributeCreator</td><td style="text-align:center">17</td><td>StringReplacer</td></tr>
<tr><td style="text-align:center">3</td><td>AttributeManager</td><td style="text-align:center">18</td><td>Counter</td></tr>
<tr><td style="text-align:center">4</td><td>FeatureMerger (FeatureJoiner)</td><td style="text-align:center">19</td><td>Bufferer</td></tr>
<tr><td style="text-align:center">5</td><td>Creator</td><td style="text-align:center">20</td><td>StatisticsCalculator</td></tr>
<tr><td style="text-align:center">6</td><td>Inspector</td><td style="text-align:center">21</td><td>SpatialFilter</td></tr>
<tr><td style="text-align:center">7</td><td>AttributeKeeper</td><td style="text-align:center">22</td><td>GeometryFilter</td></tr>
<tr><td style="text-align:center">8</td><td>TestFilter</td><td style="text-align:center">23</td><td>AttributeExposer</td></tr>
<tr><td style="text-align:center">9</td><td>Clipper</td><td style="text-align:center">24</td><td>Sorter</td></tr>
<tr><td style="text-align:center">10</td><td>Reprojector</td><td style="text-align:center">25</td><td>Dissolver</td></tr>
<tr><td style="text-align:center">11</td><td>AttributeRenamer</td><td style="text-align:center">26</td><td>ListExploder</td></tr>
<tr><td style="text-align:center">12</td><td>Aggregator</td><td style="text-align:center">27</td><td>DuplicateFilter</td></tr>
<tr><td style="text-align:center">13</td><td>AttributeFilter</td><td style="text-align:center">28</td><td>Sampler</td></tr>
<tr><td style="text-align:center">14</td><td>FeatureReader</td><td style="text-align:center">29</td><td>AttributeSplitter</td></tr>
<tr><td style="text-align:center">15</td><td>VertexCreator</td><td style="text-align:center">30</td><td>ExpressionEvaluator</td></tr>
</table>

Besides the obvious transformers for transforming geometry (Clipper, Bufferer, Dissolver) and the obvious transformers for transforming attribute values (StringReplacer, Counter) there are some other distinct groups of transformers.

---

<!--New Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-bolt fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">NEW</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
The FeatureJoiner is a new transformer for FME2018, designed to eventually replace the FeatureMerger.
</span>
</td>
</tr>
</table>

---

### Managing Attributes ###
These transformers - mostly named the *Attribute&lt;Something&gt;* - are primarily for managing attributes (creating, renaming, and deleting) for schema mapping purposes. However they can also be used to set new attribute values or update existing ones.

### Filtering ###
These transformers - mostly named the *&lt;Something&gt;Filter* - subdivide data as it flows through a workspace. Commonly the filter is a conditional filter, where the decision about which features are output to which connection is decided by some form of test or condition.

### Data Joins ###
Joins are the opposite action to filtering; they are when separate streams of data are combined as they flow through a workspace. Like filtering there is a condition to be met - in this case matching key values - that determine how and where the join takes place.

# Managing Attributes #
A high proportion of the top 30 transformers are support transformers for managing attributes. These create new attributes, rename them, set values, and delete them.

A key use for these transformers is to rename attributes for the purpose of schema mapping.

---

## Attribute Managing Transformers ##

The main attribute-management tasks and the transformers that can be used are as follows:


<table style="border-spacing: 0px">
<tr>
<th style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Task</span></th>
<th style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Transformers</th>
</tr>
<tr><td style="text-align:center;font-weight: bold">Create Attributes</td><td>AttributeCreator, AttributeManager</td></tr>
<tr><td style="text-align:center;font-weight: bold">Set Attribute Values</td><td>AttributeCreator, AttributeManager</td></tr>
<tr><td style="text-align:center;font-weight: bold">Remove Attributes</td><td>AttributeKeeper, AttributeManager, AttributeRemover, BulkAttributeRemover</td></tr>
<tr><td style="text-align:center;font-weight: bold">Rename Attributes</td><td>AttributeManager, AttributeRenamer, BulkAttributeRenamer</td></tr>
<tr><td style="text-align:center;font-weight: bold">Copy Attributes</td><td>AttributeCopier, AttributeCreator, AttributeManager</td></tr>
<tr><td style="text-align:center;font-weight: bold">Sort Attributes</td><td>AttributeManager</td></tr>
<tr><td style="text-align:center;font-weight: bold">Change Attribute Case</td><td>BulkAttributeRenamer</td></tr>
<tr><td style="text-align:center;font-weight: bold">Add Prefixes/Suffixes</td><td>BulkAttributeRenamer</td></tr>
</table>

Many of these transformers can carry out similar operations, and you can see that the AttributeManager does so many tasks you can use it almost exclusively. 

---

<!--Warning Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-exclamation-triangle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">WARNING</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Don't misunderstand the BulkAttributeRenamer. It changes the case - or adds suffixes/prefixes - to the attribute <strong>name</strong>, not the attribute value.
</span>
</td>
</tr>
</table>

---

## Lists ##
A ***list*** in FME is a mechanism that allows multiple values per attribute. So, where the attribute *myAttribute* can only contain a single value, the list attribute *myList{}.myAttribute* can contain multiple values as:

<pre>
myList{0}.myAttribute
myList{1}.myAttribute
myList{2}.myAttribute
</pre>

For example, a single polygon representing a forested area, might have a list attribute to record the tree species contained in that area:

<pre>
TreeList{0}.Species = Oak
TreeList{1}.Species = Chestnut
TreeList{2}.Species = Ash 
</pre>

Various transformers can create lists, others include support for lists, and several are designed to operate specifically on list attributes (for example the ListSorter).

---

For further reading check out **[this article on Attribute Management](https://blog.safe.com/2015/11/fmeevangelist141/)** on the Safe Software blog.

## Creating and Setting Attributes ##

Creating attributes and setting a value are probably the primary attribute function used within FME. When an attribute is created, its value can be set in a number of ways.

The transformers capable of creating an attribute - and setting its value - are:

- AttributeCreator
- AttributeManager

***NB:*** *The AttributeCopier and AttributeRenamer transformers can set an attribute value, but only where the attribute doesn't already exist.*

---

### The AttributeManager ###
For most operations we'll concentrate on the AttributeManager, so here is a quick overview of that transformer.

The AttributeManager parameters dialog has a number of fields: Input Attribute, Output Attribute, Attribute Value, and Action. Uniquely among attribute-handling transformers, it is automatically filled in with the details of the attributes connected to it:

![](./Images/Img4.012.AttributeManagerParameters.png)

The action field can be set by the user, but is also set automatically when a change is made to the other fields.

<!--New Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-bolt fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">NEW</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
The AttributeManager has new options in FME2018 to cut/copy/paste/duplicate individual rows in the dialog.
</span>
</td>
</tr>
</table>

---

### Manually Create an Attribute ###
By entering a new attribute name into the Output Attribute field, it will be created in the output.

![](./Images/Img4.013.AttributeManagerCreateAttr.png)

The text &lt;Add new Attribute&gt; highlights where a new attribute can be created. By default, when the Attribute Value field is empty, a new attribute has no value. 

---

### Set a Fixed Attribute Value ###
A fixed (or *constant*) value for an attribute can be created by simply entering a value into the Attribute Value field:

![](./Images/Img4.014.AttributeManagerSetValues.png)

Here, for example, a new attribute called City is being given a fixed value of Vancouver.

However, also note that the existing attribute NeighborhoodName is also being assigned a fixed value. It is being given the value "Kitsilano". Notice how by entering a value into that field, the Action field has automatically changed from "*Do Nothing*" to "Set Value".

Besides entering set values like this, it's possible to construct an attribute value in a number of different ways...

# Constructing Attributes #
Besides constant attribute values FME also allows you to construct values using string manipulation and arithmetic calculations. This is achieved by clicking on the arrow in the Attribute Value field and selecting either Open Text Editor or Open Arithmetic Editor:

![](./Images/Img4.015.AttributeManagerSetMenu.png)

This is very useful because the attribute no longer needs to be a fixed value: it can be constructed from a mix of existing attributes, parameters, and constants.

---

## Text Editor ##
The text editor - as you would expect - allows you to construct a text value. It includes all the usual string-handling functionality you would need, such as concatenation, trimming, padding, and case changing.

The text editor looks like this:

![](./Images/Img4.016.AttributeManagerTextEdit.png)

Here the user is constructing an address string by concatenating various existing attributes with some fixed characters (the commas). 

Notice the menu on the left hand side. Existing attributes are listed here and were added into the string by double-clicking them. Also notice the other menu options. Maybe the most important for text are the String Functions:

![](./Images/Img4.017.AttributeManagerTextEditStrings.png)

These are the functions that can be used to manipulate the strings being used. For example, here the user is making sure the attributes being used are trimmed when used:

![](./Images/Img4.018.AttributeManagerTextTrimFunc.png)

---

<!--Tip Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-info-circle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">TIP</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Notice the Date/Time functions in the text editor, which can be used to manipulate dates, times, datetime strings, including TimeZone components.
</span>
</td>
</tr>
</table>

---

## Arithmetic Editor ##

The arithmetic editor is much the same as the text editor, except that whatever is entered into the dialog will be evaluated as an arithmetic expression and a numeric result returned:

![](./Images/Img4.019.AttributeManagerMathEdit.png)

Here the user is calculating the monthly number of visitors to a park by dividing the annual number of visitors by 12 (twelve). As with the text editor, existing attributes and arithmetic functions were obtained from the menu on the left-hand side.

---

<!--Warning Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-exclamation-triangle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">WARNING</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
The contents of the Arithmetic Editor <strong>must</strong> form an arithmetic expression that can be evaluated mathematically. 
</span>
</td>
</tr>
</table>

---

### FME Feature Functions ##

One other item in the menu of both text and arithmetic editors is FME Feature Functions:

![](./Images/Img4.020.AttributeManagerFMEFunctions.png)

These are functions that reach into the very heart of FME's core functionality. They are the building blocks that transformers are built upon; basic functionality that can return values to the editor. 

For example, the @Area() function returns the area of the current feature (assuming it is a polygon). @CoordSys() returns the coordinate system. They are the functional equivalent of the AreaCalculator and CoordinateSystemExtractor transformers.

Some functions return strings, others return numeric values; therefore the available functions vary depending on whether the text or arithmetic editor is being used. In the screenshot above, the text editor functions are on the left and the arithmetic editor functions on the right. The text editor can use either text or numeric values; the arithmetic editor can only ever accept numeric values.

FME Feature Functions are useful because they allow you to build processing directly into the AttributeManager, instead of using a separate transformer.


### Replacing Other Transformers ###
Integrated text and arithmetic editors provide a great benefit for workspace creation. They allow attribute-creating functions to be carried out directly in a single transformer.

For example, the AttributeManager text editor can be used as a direct replacement for the StringConcatenator and ExpressionEvaluator transformers.

The AttributeManager could also replace the StringPadder and AttributeTrimmer transformers, albeit with a little less user-friendliness. If FME Feature Functions are used inside the editor, this transformer could also technically replace transformers such as the AreaCalculator, LengthCalculator, CoordinateCounter, TimeStamper, and many more.

This is usually a good thing. Workspaces will be more compact and well-defined when as many peripheral operations as possible are directly integrated into a single transformer. However, because it's possible for an AttributeManager to be carrying out many, many operations, it is also more important to use Best Practice and ensure it has proper annotation. 

If an AttributeManager is not properly annotated, it isn't possible to determine from looking at the Workbench canvas what action it is carrying out!

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Here's a question to see if you are paying attention. Look at this screenshot of an editing dialog and tell me what the value returned to the attribute will be:
<br><br><img src="./Images/Img4.021.AttributeManagerMissVectorQuestion.png">
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=3&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. 2+2</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=3&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. 4</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=3&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. 4.0</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=3&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. Error!</a>
</span>
</td>
</tr>
</table>

---



# Constructing Parameters #
Let's just put attributes to one side for a moment and look at transformer parameters.

Transformer parameters are often set in a fixed way (hard-coded) or set to take on the value of a particular attribute. However, in the same way that attributes can be constructed, text or arithmetic editors can be used to build values for transformer parameters. 


## Using Attributes for Parameters ##
As noted, most transformer parameters allow the user to select an attribute value instead of manually entering a fixed value. For example, the LabelPointReplacer can create a label whose contents and height are specified by attribute values:

![](./Images/Img4.022.LabelPointReplacerDialogWithAttrs.png)

This is very useful because it allows the parameters (for example label size) to get a different value for each feature. An attribute could be read from a source dataset, or calculated using an ExpressionEvaluator, so that one feature creates a label 10 units in height, another creates a label 15 units high, and so on. It is no longer a fixed value.


## Constructing Parameter Values ##

If a parameter value needs to be calculated or constructed, instead of using a separate transformer, FME has integrated string and numeric editors built into parameter dialogs.

For example, here the user is choosing to calculate label height using an arithmetic calculator:

![](./Images/Img4.023.LabelPointReplacerDialogPickingCalc.png)

The calculator allows the selection and use of FME attributes, other parameters, plus a number of mathematical and string-based functions. For example, here the user has chosen to calculate the height of their labels using the logarithm of the taxable value:

![](./Images/Img4.024.LabelPointReplacerArithCalc.png)

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Mr. E. Dict (attorney of FME law) says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
It's a fixed rule that the editor dialogs available depend upon the type of parameter being set. For instance, the Label parameter in a LabelPointReplacer opens a text editor because the parameter requires a text value. The Label Height parameter opens an arithmetic editor because that parameter requires a numeric value.
</span>
</td>
</tr>
</table>

---

### Reducing Workspace Congestion ###
Like when attribute values are constructed, workspaces are more compact when as many peripheral operations as possible are directly integrated into a single transformer or parameter. However, as with attributes, it's important to add proper annotation, else it's difficult for a casual observer to understand what the workspace is meant to do.

Another drawback, specific to parameters, is that you don't also get the information as an attribute to use elsewhere. For example, if you construct a label string in the LabelPointReplacer, that string isn't available as an attribute elsewhere in the workspace. 


## Renaming and Copying Attributes ##

Renaming and - to a lesser extent - copying attributes are also key attribute functions within FME. When an attribute is renamed it ceases to exist under its prior name; when it is copied it exists both in its new and old names. 



The transformers capable of renaming an attribute are:

<table style="border-spacing: 0px">
<tr>
<th style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Transformer</span></th>
<th style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Capability</th>
</tr>
<tr><td style="text-align:center;font-weight: bold">AttributeCopier</td><td>Copy</td></tr>
<tr><td style="text-align:center;font-weight: bold">AttributeCreator</td><td>Copy</td></tr>
<tr><td style="text-align:center;font-weight: bold">AttributeManager</td><td>Copy and Rename</td></tr>
<tr><td style="text-align:center;font-weight: bold">AttributeRenamer</td><td>Rename</td></tr>
</table>

---

### Renaming ###

The fundamental purpose of renaming is to manually enter a new name for a selected attribute. The old attribute is removed and replaced with the newly named one:

![](./Images/Img4.025.AttributeManagerRenameAttr.png)

Here an AttributeManager is used to rename a number of fields by entering a different name for the Output Attribute. The Action is automatically set to Rename. Notice that the user is also entering a new constant value for the PSTLCITY/PostalCity attribute.

This type of behaviour is obviously of use when the reader schema ('what we have') needs to be renamed to match the writer schema ('what we want').

---

<!--Tip Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-info-circle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">TIP</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Although you can manually type a new attribute name into the Output Attribute field, if the transformer is connected to a writer feature type with the correct attributes, its attribute names will be automatically available to select from:
<br><br><img src="./Images/Img4.026.AttributeManagerRenameAttrQuickPick.png">
</span>
</td>
</tr>
</table>

---

### Copying ###

Depending on the transformer, copying an attribute can be one of two styles.

![](./Images/Img4.027.AttributeCopier.png)

Here the AttributeCopier consists of selecting the existing attribute and entering a new name for it. Again, when connected to a writer feature type, its schema is available to select from. 

Note how both PSTLCITY and PostalCity exist on the output of the transformer, proving that it is copying the attribute rather than renaming it.


<!--Tip Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-info-circle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">TIP</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
You can (as above) enter a constant attribute value in the AttributeCopier, but in reality it's hardly a copy operation in that case; it's more an attribute creation task.
</span>
</td>
</tr>
</table>

---

For other transformers, the setup style is reversed: a new attribute is created and given the value of an existing attribute:

![](./Images/Img4.028.AttributeManagerCopyAttr.png)

In this AttributeManager transformer the user creates a new attribute (PostalCity) and assigns it the value from another (PSTLCITY). In effect they have made a copy of the original attribute.

## Bulk Attribute Renaming ##

Usual attribute renaming involves selecting individual attributes to operate on. However, in some cases it's important to be able to carry out the same renaming operation on a large number of attributes.

This scenario is catered for by the BulkAttributeRenamer transformer.

![](./Images/Img4.029.BulkAttributeRenamer.png)


### BulkAttributeRenamer ###

The BulkAttributeRenamer carries out the core function of renaming attributes. But instead of manually specifying each attribute, this transformer lets the user select multiple attributes - or all of them:

![](./Images/Img4.030.BulkAttributeRenamerDialog.png)

When multiple attributes are selected, the action must - of course - carry out the same renaming action on them all. These actions are:

- Add String Prefix
- Add String Suffix
- Remove Prefix String
- Remove Suffix String
- Regular Expression Replace
- String Replace
- Change Case

![](./Images/Img4.031.BulkAttributeRenamerDialogActions.png)

The power of the transformer is also in its ability to manipulate multiple attributes at once, without having to individually select them all. Here, for example, the incoming attributes are all being renamed to lower case names in order to match a writer schema that does not support upper case:

![](./Images/Img4.032.BulkAttributeRenamerLowerCase.png)

Multiple transformers can be used to create a cumulative effect. Here, for example, the user has converted to lower case and then used a second transformer to add a prefix:

![](./Images/Img4.033.BulkAttributeRenamerCasePrefix.png)

## Removing Attributes ##

Removing attributes is perhaps seen as a less important task in FME. That's because - for a manual attribute schema - only attributes defined in the writer are written to the output; extra attributes that are not required are just ignored.

However, removing attributes does carry useful benefits:

- Removing attributes that aren’t required tidies up a workspace and makes it easier to understand
- A workspace is a complex network of objects and schemas. Removing attributes simplifies this network and makes the Workbench interface more responsive
- All data processing incurs costs of time and memory. Removing attributes means less data is being processed and so the FME engine performs faster

---

<!--Tip Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-info-circle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">TIP</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
A reader feature type has parameters to hide attributes from the schema. This helps tidy a workspace, but does not help improve the translation performance. However, some formats (mostly databases) also have a setting for "Attributes to Read" and using this will help performance.
</span>
</td>
</tr>
</table>

---

Transformers that can remove attributes are:

- AttributeKeeper
- AttributeManager
- AttributeRemover
- BulkAttributeRemover

---

### Removing Attributes ###

The AttributeManager and AttributeRemover have the same technique; select an attribute to be removed:

![](./Images/Img4.034.AttributeManagerRemoveAttrs.png)

Attributes can be removed in the AttributeManager by selecting it and clicking the - button. Alternatively you can change the action field from *Do Nothing* to Remove. 

Notice in the above that three attributes have been removed. The output attribute (when selected) shows the name struck out to signify that it is no longer present.

---

### Keeping Attributes ###
The AttributeKeeper transformer carries out the same function, but approaches it from the opposite direction. It lets the user specify which attributes are **not** to be removed; in other words, this transformer lets the user specify which ones to keep.

So, the AttributeManager should be used where one or two attributes are to be removed, but the majority of them kept. The AttributeKeeper should be used when the majority of attributes are to be removed, and only one or two of them kept.

---

### Bulk Attribute Removal ###

The BulkAttributeRemover - like the BulkAttributeRenamer - lets the user carry out a process on multiple attributes. In this case, instead of being able to select all attributes, the user enters a string-matching expression in order to define which attributes to remove:

![](./Images/Img4.035.BulkAttributeRemoval.png)

Here the user is removing all attribute whose name ends in the word "Street".

# Conditional Filtering #
Transformers that filter don’t transform data content, yet surveys show that they’re the most commonly used type of transformer there is!
 
## What is Filtering? ##
Filtering is the technique of subdividing data as it flows through a workspace. It’s the case where there are multiple output connections from a transformer, each of which carries data to be processed in a different way. Here (for example) incoming stream A is filtered into two new streams, B and C:

![](./Images/Img4.036.FeatureFilteringDiagramHalfScale.png)

A filtering transformer may be any transformer with multiple output ports, such as the GeometryFilter or Sampler transformers, the latter of which create a sample selection of data and separates it out through Sampled and NotSampled output ports:

![](./Images/Img4.037.SamplerTransformers.png)

However, these are mostly in-built, fixed tests. Conditional filtering is where the decision about which features are output to which connection is decided by some form of *user-defined* test or condition. The Tester transformer is the most obvious example of this. It carries out a test and has different output ports for features that pass and fail the test.


## Transformers that Filter ##
Many transformers in the Filters and Joins category carry out these tests and redirect data according to the results:

![](./Images/Img4.038.FilterTransformers.png)

Although the Tester transformer is the most used of this category, there are many other transformers such as the TestFilter, GeometryFilter, AttributeFilter, SpatialFilter, and Sampler.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Time for a quick question. How many filtering transformers in the Filter and Joins category appear in the top-30 Most-Valuable Transformers list?
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=4&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. One (1)</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=4&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. Four (4)</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=4&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. Seven (7)</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=4&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. Ten (10)</a>
</span>
</td>
</tr>
</table>

## The Tester and TestFilter Transformers ##

The Tester and TestFilter are the two key transformers for conditional filtering. They test the values on attribute values.


### Tester ###

The Tester transformer (number 1 in the top 30) is generally for single tests that produce a Yes/No result. 

For example, here we wish to make a decision whether to send out snow plows (ploughs) to a particular road based on whether the value of the Snowfall attribute is greater than six:

![](./Images/Img4.039.TesterTransformer.png)

If snowfall is greater than six the road feature will pass the test and snow plows will be sent.

---

#### Multiple Clauses ####
Each clause in the Tester is an individual test that allows a Passed/Failed result, for example each of the following criteria might be separate tests: 

- Has there been more than six inches of snowfall?
- Is this a major road?
- Is the temperature less than zero degrees Celsius?
- Was sand last applied more than 24 hours ago?

However, the Tester allows the combination of multiple tests, where a user can combine any number of clauses using an AND and OR statement. So instead of individual tests I might ask:

- Is this a major road AND (has there been more than six inches of snow OR (is the temperature less than zero AND was sand last applied more than 24 hours ago))?

![](./Images/Img4.040.TesterTransformerComplex.png)

When I have multiple tests I control them using the Pass Criteria field. A mix of AND/OR clauses requires a Composite Test, as shown above. But - however complex the test becomes - it still results in a single Yes/No result; features will either pass or fail this set of tests.

Notice we aren't restricted to simple tests of equality (A=B); in the above there are also "greater than" and "less than" tests. That's because there are many different operators available for use in a test clause.

---

#### Operators ####
The list of operators available in the Tester transformer (or in many of the other locations that make use of the Tester dialog) looks like this:

![](./Images/Img4.041.TesterOperators.png)

Besides the usual operators, there are also some based on a SQL where clause. These include:

- In
- Like
- Contains
- Begins With
- Ends With
- Contains Regex

...plus there are other tests that check for the existence of attributes and values:

- Attribute has a value
- Attribute is Null
- Attribute is Empty String
- Attribute is Missing

---

<!--Tip Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-info-circle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">TIP</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
"Attribute has a value" is the opposite of the three other tests; i.e. this attribute is not Null, AND it is not an empty string, AND it is not missing. Incidentally, "missing" means the attribute does not exist at all on the feature being tested.
</span>
</td>
</tr>
</table>

---

<!--Tip Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-info-circle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">TIP</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
"Contains Regex" means only part of the string needs to match. For example...
<pre>
Attribute Value:  abcd
Search String:    ^ab
Contains Regex:  Passed
</pre>
i.e. the entire string doesn't need to match.
</span>
</td>
</tr>
</table>

---

### TestFilter ###
The TestFilter (#8 in the top 30) is essentially a way to combine multiple Tester transformers into one. Instead of the Tester's single Passed and Failed ports, you can create a passed port for each condition (it does not need to be called "Passed") with failed features going on to the next test. There is also an output port for features that fail all of the test conditions.

The TestFilter is very similar to the CASE or SWITCH command in programming or scripting languages.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Sister Intuitive says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
The TestFilter is very good for filtering a feature by a set of cascading conditions, for example here are a set of tests to again determine whether to send out a snow plow:
<br><br>- Has there been more than six inches of snowfall?
<br>- Has there been more than four inches of snowfall AND is this a major road?
<br>- Is the temperature less than zero degrees Celsius AND was sand last applied more than 24 hours ago?

<br><br>It’s a set of cascading tests, because if there has been more than six inches of snow, the plows are sent out anyway; you don’t need to test any other criteria. So the test order can be very important. If every test is a fail, then the plows are not sent out.
<br><br>Also notice that you can include composite tests (those with ANDs or ORs in them).
</span>
</td>
</tr>
</table>

---

The TestFilter has the full set of operators available with the Tester such as equals, greater than, less than, and so forth. Each condition is tested in turn.

Features that pass are output through the matching output port. Features that fail are sent on to the next condition in the list. Therefore it’s very important to get the conditions in the correct order.

In this example the user has used three Tester transformers and multiple connections (using the above logic) to determine whether to send the snow plows:

![](./Images/Img4.042.BadTesterExample.png)

With the TestFilter, the three Testers are now replaced with one single transformer and there are fewer connections:

![](./Images/Img4.043.GoodTestFilterExample.png)

Also notice how the TestFilter output ports have custom naming. This is another advantage to this transformer.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Chef Bimm says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Because the TestFilter can carry out a single test (as well as multiple ones) it's possible to use it exclusively instead of the Tester transformer.
</span>
</td>
</tr>
</table>


## Other Key Filter Transformers ##
The Tester and TestFilter are not the only useful filter transformers.


### AttributeFilter ###
The AttributeFilter transformer (#13 in the top 30) directs features on the basis of values in a chosen attribute. It is best for testing many values for a single attribute, for example:

- Is that road a Primary, Secondary, Residential, Private, or Other type of road?
- Is the forecast for sun, rain, snow, or fog?

In this example Testers divide features into different streams depending on the value of a RoadClass attribute:

![](./Images/Img4.045.BadTesterExample.png)

The repetition of Tester transformers indicates an AttributeFilter transformer might be a better option:

![](./Images/Img4.044.AttributeFilterExample.png)

The AttributeFilter's only "operator" is to find equivalency, so you would rarely use it for arithmetical tests.


### AttributeRangeFilter ###
The AttributeRangeFilter carries out the same operation as the AttributeFilter, except that it can handle a range of numeric values instead of just a simple one-to-one match.

![](./Images/Img4.046.AttributeRangeFilterExample.png)

The AttributeRangeFilter parameters dialog has the option to generate ranges automatically from a set of user-defined extents.

---

### GeometryFilter ###
The GeometryFilter (#22 in the top 30) directs features on the basis of geometry type; for example, point, line, area, ellipse:

![](./Images/Img4.047.GeometryFilterExample.png)

The GeometryFilter is useful for:

- Filtering out unwanted geometry types; for example, removing non-linear features before using an AreaBuilder transformer
- Validating geometry against a list of permitted types; for example, where the dataset is constrained to either point or area features (above) 
- Dividing up geometry types to write to separate destination Feature Types; for example, when writing to a geometry-restricted format such as Esri Shapefile

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Confused from Interopolis says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Dear Aunt Interop,
<br>If the Tester, TestFilter, and AttributeFilter all filter features on the basis of an attribute condition, then what’s the difference? When would I use each?
</span>
</td>
</tr>
</table>

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Aunt Interop says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Dear Confused
<br>The best solution is to check out these two articles on the Safe Software blog:
<br>- <a href="https://blog.safe.com/2013/03/fmeevangelist113/">Conditional Processing in FME</a>
<br>- <a href="https://blog.safe.com/2015/05/fmeevangelist133/">A Simple Guide to FME Filter Transformers</a>
<br>There's also a useful table I put together:
</span>
</td>
</tr>
</table>

<table style="font-size:smaller;font-family:serif" border="1">
<tbody>
<tr style="height: 15.0pt;" valign="bottom">
<td style="height: 15.0pt; width: 103pt;" width="137" height="20"></td>
<td style="width: 130pt;" colspan="2" width="173" align="center">Single Test</td>
<td style="width: 130pt;" colspan="2" width="173" align="center">Multiple Tests</td>
<td style="width: 77pt;" colspan="2" width="103" align="center">Test Type</td>
<td style="width: 63pt;" width="84" align="center">Operators</td>
<td style="width: 63pt;" width="84" align="center">Attributes</td>
</tr>
<tr style="height: 15.0pt;" valign="bottom">
<td></td>
<td align="center">Single<br>Clause</td>
<td align="center">Multi<br>Clause</td>
<td align="center">Single<br>Clause</td>
<td align="center">Multi<br>Clause</td>
<td align="center">String</td>
<td align="center">Numeric</td>
<td></td>
<td></td>
</tr>
<tr style="height: 15.0pt;" valign="bottom">
<td>Tester</td>
<td align="center">Y</td>
<td align="center">Y</td>
<td align="center">–</td>
<td align="center">–</td>
<td align="center">Y</td>
<td align="center">Y</td>
<td align="center">16</td>
<td align="center">Multiple</td>
</tr>
<tr style="height: 15.0pt;" valign="bottom">
<td>TestFilter</td>
<td align="center">Y</td>
<td align="center">Y</td>
<td align="center">Y</td>
<td align="center">Y</td>
<td align="center">Y</td>
<td align="center">Y</td>
<td align="center">16</td>
<td align="center">Multiple</td>
</tr>
<tr style="height: 15.0pt;" valign="bottom">
<td>AttributeFilter</td>
<td align="center">Y</td>
<td align="center">Y</td>
<td align="center">–</td>
<td align="center">–</td>
<td align="center">Y</td>
<td align="center">–</td>
<td align="center">1</td>
<td align="center">1</td>
</tr>
<tr style="height: 15.0pt;" valign="bottom">
<td>AttributeRangeFilter</td>
<td align="center">Y</td>
<td align="center">Y</td>
<td align="center">–</td>
<td align="center">–</td>
<td align="center">–</td>
<td align="center">Y</td>
<td align="center">6</td>
<td align="center">1</td>
</tr>
</tbody>
</table>


# Data Joins #
Transformers that join data together are also very commonly used in FME. It's so related to filtering that the transformer category is called Filters and Joins.


## What is a Data Join? ##
Whereas Filter transformers divide data into different streams, other transformers bring data streams together, merging the data according to a set of user-defined conditions. Here (for example) incoming streams A and B are joined together into a new stream, C:

![](./Images/Img4.048.FeatureJoinDiagramHalfScale.png)

To merge data in FME Workbench it is necessary to do more than just draw two connections into the same input port; that will only combine the data into a single stream, not fuse it together. You may know this as a union of data.

---

<!--New Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-bolt fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">NEW</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
To emphasize this fact, the Junction transformer - which is designed to draw together multiple connections without merging data - has been given the alias of <strong>Union</strong> in FME2018.
</span>
</td>
</tr>
</table>

---

To truly merge data it is necessary to define a relationship for the basis of the join, and this is done with one of a number of transformers.

These transformers allow you to merge not just data that is being processed by the workspace, but provide the ability to form a join against a database or other external dataset.

Joins in FME can either be based on matching attribute values (DatabaseJoiner or FeatureMerger/FeatureJoiner), or they can be based on a spatial relationship such as an overlap between features or proximity from one feature to another (NeighborFinder or SpatialRelator).

## Key-Based Join Transformers ##
There are several transformers that can join data on the basis of a matching attribute value (key). Some of these are more oriented towards geometry, others have a more SQL-like style. Some join streams of data within one workspace, others join one stream of data to an external database. 

Which you use depends on your join requirements and performance needs.


### FeatureMerger ###
The FeatureMerger is a transformer for joining two (or more) streams of data within a workspace based on a key field match.

![](./Images/Img4.049.FeatureMergerOnCanvas.png)

Here, for example, a dataset of facilities has an AddressID number, but no address. The FeatureMerger is being used to combine information from an address table onto the facilities records.

The parameters dialog for the FeatureMerger looks like this:

![](./Images/Img4.050.FeatureMergerDialog.png)

This shows the join is made using AddressID as a key. All Requestor (Facility) features that have a matching postal address will be output through the Merged output port. All Facility features without a matching address are output through the UnmergedRequestor port for inspection to determine why a match did not occur.

There are additional parameters to handle conflicts of information, duplicate keys, and whether to merge attributes only or geometry as well.


### FeatureJoiner ###
The FeatureJoiner is another transformer for joining two streams of data within a workspace based on a key field match.


---

<!--New Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-bolt fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">NEW</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Remember that the FeatureJoiner is a new transformer for FME2018, designed to eventually replace the FeatureMerger.
</span>
</td>
</tr>
</table>

---

![](./Images/Img4.051.FeatureJoinerOnCanvas.png)

Here, for example, is the same Facilities/Address match in the FeatureJoiner. The parameters for the transformer looks like this:

![](./Images/Img4.052.FeatureJoinerDialog.png)

As you can see, this transformer is based more on traditional SQL queries. The Join Mode parameter can take one of three values:


<table>
<tr><th>Mode</th><th>Description</th><th>Depiction</th><th>Joined Output</th><th>Unjoined Left</th><th>Unjoined Right</th></tr>
<tr>
<td style="font-weight:bold">Left</td><td>Left features look for a match and are output whether they find a match or not</td><td><img src="./Images/Img4.053.JoinDiagramLeft.png"></td><td>All matches plus unmatched Left features</td><td>None</td><td>Unused Right features</td>
</tr>
<tr>
<td style="font-weight:bold">Inner</td><td>Left features look for a match and are output if they find one</td><td><img src="./Images/Img4.054.JoinDiagramInner.png"></td><td>All matches only</td><td>Unmatched Left features</td><td>Unused Right features</td>
</tr>
<tr>
<td style="font-weight:bold">Full</td><td>Both Left and Right features output through the Joined output port, whether they find a join or not</td><td><img src="./Images/Img4.055.JoinDiagramFull.png"></td><td>All matches plus unmatched Left and Right features</td><td>None</td><td>None</td>
</tr>
</table>

Other terms you might be familiar with are *Outer Join* and *Right Join*. An Outer join is simply a different name for what the Full Join does here. To do a Right join, you would simply switch which features are being sent to which input port and use the Left Join option.

---

<!--Warning Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-exclamation-triangle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">WARNING</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
The key thing to be aware of here is that a feature is output for every match that occurs.
<br>For example, if 1 Facility feature matches 5 Address records, there will be 5 features output as Joined.
<br><br>Joined features are always output as a Join. Left, Inner, and Full really only control which unmatched records are included in the Joined output.
</span>
</td>
</tr>
</table>

---

With a Left join (in the screenshot above) the user either believes that all facilities will have a matching address record, or it does not matter if there is not a match. In fact no features will ever appear from the Unjoined Left output port. 

If it was important to ensure a match, then the chosen mode should have been Inner. Then records that exited the Unjoined Left output port could be treated as an error and investigated as to why there is no match.

Like the FeatureMerger, there are parameters to handle conflicts of information and whether to merge attributes only or geometry as well.

---

<!--Tip Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-info-circle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">TIP</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
So the key difference between the FeatureMerger and the FeatureJoiner is what happens to multiple matches. 
<br><br>If the FeatureJoiner has multiple matches, it will output multiple features.
<br><br>If the FeatureMerger has multiple matches, it will output one feature only. That feature will either have only one matched record, or a list of matched records, depending on the Process Duplicate Suppliers parameter.
</span>
</td>
</tr>
</table>

---

### DatabaseJoiner ###
The DatabaseJoiner transformer is different to the FeatureMerger and FeatureJoiner because, instead of merging two streams of features, it merges one (or more) stream(s) of data with records from an external database.

![](./Images/Img4.056.DatabaseJoinerOnCanvas.png)

Here is the same example as for the FeatureMerger above. In this case the facilities features are obtaining address data directly from an address table in a PostGIS database. 

The parameters dialog for the DatabaseJoiner looks like this:

![](./Images/Img4.057.DatabaseJoinerDialog.png)

Again, AddressID is being used from both feature and database table to facilitate a merge between the two.

As with the other transformers, there are parameters to control the attributes that are accumulated and how conflicts are resolved.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">First-Officer Transformer says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
The DatabaseJoiner has a number of advantages over the FeatureMerger. Firstly it has parameters to control how multiple matches are handled, as well as parameters for optimizing the database query.
<br><br>Secondly, it allows features to be joined without having to read the entire dataset into a workspace. FME can just query the database and select the individual records it needs. This can improve performance greatly.
<br><br>It does, of course, require the supplier records to be stored in an appropriate database format!
</span>
</td>
</tr>
</table>

---

### InlineQuerier ###

The InlineQuerier transformer accepts features from the workspace and generates a temporary database. With that database it's possible to apply any SQL commands required - including Joins - across a number of tables.

The InlineQuerier has the distinct advantage of allowing its input to be reused multiple times in a single transformer; whereas multiple joins would otherwise require multiple FeatureJoiner transformer. However, there is a performance overhead involved in generating that initial database.

## Spatially Based Join Transformers ##

There are multiple transformers that can join data on the basis of a spatial relationship. Which you use depends on the spatial relationship to be tested and your exact join requirements. The following are some of the key transformers.


### Overlayers ###
There are a number of different "overlayer" transformers, each handling a different form of overlay. 

For example the PointOnAreaOverlayer carries out a spatial join on points that fall inside area (polygon) features. This is sometimes called a "Point in Polygon" operation.

As the help explains, "each point receives the attributes of the area(s) it is contained in, and each containing area receives the attributes of each point it contains"

![](./Images/Img4.058.PointOnAreaOverlayerOnCanvas.png)

Here the facility features are being provided with a postal code depending on which postal code polygon feature they fall inside.

The "_overlaps" attribute is another useful outcome of this transformer. It tells us how many polygons each facility fell inside; in this case it would be an easy way to spot the problem of a facility falling inside more than one postal code.

Conversely, the Area output would have an "_overlaps" attribute that would tell us how many facilities fell inside each postal code.

---

### NeighborFinder ###
The NeighborFinder transformer carries out a spatial join based on a proximity relationship. Here the NeighborFinder is being used to identify the closest fire hall to each facility:

![](./Images/Img4.059.NeighborFinderOnCanvas.png)

The fire hall number, name, and address attributes will be merged onto each Facility feature along with a number of useful attributes recording the X/Y coordinate, direction, and distance of the closest fire hall.

The parameters of the NeighborFinder includes the ability to specify a maximum distance for the relationship, or the maximum number of neighbors to find.

---

### FeatureReader ###
The FeatureReader is the spatial equivalent of the DatabaseJoiner transformer. It reads from an external dataset and forms a match based on a spatial relationship between the initiating feature and features in that dataset.

One difference is that the output is not the original feature, but the queried feature; hence the name FeatureReader:

![](./Images/Img4.060.FeatureReaderOnCanvas.png)

For example, here the FeatureReader is being used to carry out the same overlay of facility and postal code. The Postcode features are read into the workspace and used as a means to spatially query facilities. The facilities are retrieved with the attributes of the postcode feature they fall inside. 

---

### SpatialFilter ###
The SpatialFilter - as its name suggests - filters data according to a spatial relationship. However, it does also merge attributes from one feature to another, therefore can be said to be a type of Spatial Join.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Here is a question on data joins. Look at the following screenshot, then answer how many features will appear in the output connection...
<br><br><img src="./Images/Img4.061.FeatureMergerQuestion.png">
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=6&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. Eight (8)</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=6&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. Eighteen (18)</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=6&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. Twenty-six (26)</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=6&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. Can't tell</a>
</span>
</td>
</tr>
</table>


# Module Review #

This module was designed to introduce you to a wider range of FME transformers, plus a number of techniques for applying transformers more efficiently.

 
## What You Should Have Learned from this Module ##

The following are key points to be learned from this session:


### Theory ###
- There are distinct groups of transformers that do work other than transforming data attributes or geometry
- Integrated editing dialogs allow the author to replace transformers with built in functions
- A large proportion of the most-used transformers are related to attribute-handling
- Filtering is the act of dividing data. Conditional filtering is the act of dividing data on the basis of a test or condition
- Data joins are carried out by transformers that merge data together, from within Workbench or from external data sources



### FME Skills ###
- The ability to locate a transformer to carry out a particular task, without knowing about that transformer in advance
- The ability to build strings and calculate arithmetic values using integrated tools
- The ability to use common transformers for attribute management
- The ability to use transformers for filtering and dividing data
- The ability to use transformers for merging data together

### Further Reading ###

For further reading why not browse blog articles for particular transformers such as the **[TestFilter](http://blog.safe.com/tag/testfilter/)**, **[AttributeCreator](http://blog.safe.com/tag/attributecreator/)**, or **[FeatureMerger](http://blog.safe.com/tag/featuremerger/)**? 



# Questions #

Here are the answers to the questions in this chapter.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Your colleagues asked...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Q) What are the top five, most-used transformers in the Web category?
<br><br>A) At the time of writing they are:
<br><br><span style="font-weight:bold">1. HTTPCaller</span>
<br><span style="font-weight:bold">2. JSONFlattener</span>
<br><span style="font-weight:bold">3. Geocoder</span>
<br><span style="font-weight:bold">4. ParameterFetcher</span>
<br><span style="font-weight:bold">5. Generalizer</span>
<br><br>You can find this out through the <a href="https://www.safe.com/transformers/#/">Transformers Gallery</a> on the Safe Software web site.
<br><br>Although the Generalizer seems an odd web transformer, it can be used to reduce the number of vertices in geometry, making features smaller and more suitable for use on the web.
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Your colleagues asked...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Q) Which transformers are returned by Quick Add for each string of characters?
<br><br>A) They are:
<br><br><span style="font-weight:bold">1. lineco: LineCombiner</span>
<br><span>An example of a string that appears at the start of a transformer's name</span>
<br><br><span style="font-weight:bold">2. reac: AreaCalculator </span>
<br><span>An example of a string that appears in the middle of a transformer's name</span>
<br><br><span style="font-weight:bold">3. rbic: RasterBandInterpretationCoercer</span>
<br><span>An example of a string that represents the CamelCase name of a transformer</span>
<br><br><span style="font-weight:bold">4. drape: SurfaceDraper</span>
<br><span>An example of a string that describes what the transformer does</span>
<br><br><span style="font-weight:bold">5. attributeexpl: AttributeExploder</span>
<br><span>An example of a string that is too long. "eexpl" would be more efficient</span>
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Your colleagues asked...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Q) Which transformer is suitable for each of these scenarios?
<br><br>A) There are often many ways to carry out a task in FME, but in general the best transformers are as follows:
<br><br><span>1. We have some lines of text in a file and want to read that text and add it as an attribute.</span>
<br><span style="font-weight:bold">AttributeFileReader</span>
<br><br><span>2. We have a set of vector contours and want to create a cross-section by transposing the X and Z coordinates.</span>
<br><span style="font-weight:bold">CoordinateSwapper</span>
<br><br><span>3. We have a point cloud dataset and want to reduce its size by resampling it to remove excess points.</span>
<br><span style="font-weight:bold">PointCloudThinner</span>
<br><br><span>4. We have a text string and want to find out how many characters the string contains.</span>
<br><span style="font-weight:bold">StringLengthCalculator</span>
<br><br><span>5. We have a set of addresses and for each address want to find the closest two libraries.</span>
<br><span style="font-weight:bold">NeighborPairFinder</span>
</span>
</td>
</tr>
</table>

---

<!--Exercise Congratulations Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-thumbs-o-up fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">CONGRATULATIONS</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
By completing this exercise you have learned how to:
<br>
<ul><li>Use the online Transformer Gallery</li>
<li>Use various combinations of Quick Add characters to search for transformers</li>
<li>To find the ideal transformer using the Workbench Transformer Gallery and Quick Add search capability</li></ul>
</span>
</td>
</tr>
</table>





# Questions #

Here are the answers to the questions in this chapter.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Which of the following is NOT a category of transformers?
<br><br><span style="color:lightslategrey">1. Attributes</span>
<br><span style="font-weight:bold">2. Calculations</span>
<br><span style="color:lightslategrey">3. Data Quality</span>
<br><span style="color:lightslategrey">4. Workflows</span>
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td colspan="2" style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td colspan="2" style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Here are four transformers and four categories. Match the transformer to the correct category.
</span>
</td>
</tr>
<tr><td width="50%" style="font-weight: bold; border: 1px solid darkorange">Scenario</td><td style="font-weight: bold; border: 1px solid darkorange">Tool</td></tr>
<tr><td style="border: 1px solid darkorange">Chopper</td><td style="border: 1px solid darkorange;font-weight:bold">Geometries</td></tr>
<tr><td style="border: 1px solid darkorange">Terminator</td><td style="border: 1px solid darkorange;font-weight:bold">Workflows</td></tr>
<tr><td style="border: 1px solid darkorange">Matcher</td><td style="border: 1px solid darkorange;font-weight:bold">Data Quality</td></tr>
<tr><td style="border: 1px solid darkorange">DateTimeConverter</td><td style="border: 1px solid darkorange;font-weight:bold">Strings</td></tr>
<tr>
<td colspan="2" style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Did you look through the transformer gallery to find these? The quicker way is to look at the help page for the transformer. While we are on the subject, transformers can belong to more than one category. The DateTimeConverter (for example) belongs to both Strings and Calculated Values.
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Look at this screenshot of an editing dialog and tell me what the value returned to the attribute will be:
<br><br><img src="./Images/Img4.021.AttributeManagerMissVectorQuestion.png">
<br><br><span style="font-weight:bold">1. 2+2</span>
<br><span style="color:lightslategrey">2. 4</span>
<br><span style="color:lightslategrey">3. 4.0</span>
<br><span style="color:lightslategrey">4. Error!</span>
<br><br>The key is to notice that the header of this dialog says "String Editor". Therefore the value returned to this attribute will be the literal string "2+2". If the user wishes to add 2+2 to get 4, they should have used the arithmetic editor!
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
How many of the transformers in the Filters and Joins category appear in the top-30 Most-Valuable Transformers list?
<br><br><span style="color:lightslategrey">1. One (1)</span>
<br><span style="color:lightslategrey">2. Four (4)</span>
<br><span style="color:lightslategrey">3. Seven (7)</span>
<br><span style="font-weight:bold">4. Ten (10)</span>
<br><br>As of January 2018 (and FME 2018.0) there are ten. They are the Tester (1st), FeatureMerger (4th), TestFilter (8th), Aggregator (12th), AttributeFilter (13th), FeatureReader (14th), SpatialFilter (21st), GeometryFilter (22nd), DuplicateFilter (27th), and Sampler (28th). So one-third of the top transformers come from the Filters and Joins category!
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
So... why the Tester? Why not use the AttributeFilter? 
<br><br><span style="font-weight:bold">Because we only need to test for one value in a simple Yes/No format. The AttributeFilter is better for testing multiple values. Also the AttributeFilter doesn't let us do "Begins With" tests.
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Look at the following screenshot, then answer how many features will appear in the output connection...
<br><br><img src="./Images/Img4.061.FeatureMergerQuestion.png">
<br><br><span style="color:lightslategrey">1. Eight (8)</span>
<br><span style="color:lightslategrey">2. Eighteen (18)</span>
<br><span style="color:lightslategrey">3. Twenty-six (26)</span>
<br><span style="font-weight:bold">4. Can't tell</span>
<br><br>It's impossible to tell from the screenshot, because you don't know how many attribute values will be a match. Because there are eight fire halls it will be anywhere from zero to eight, but that's all we can tell. In fact if it was a FeatureJoiner transformer there could be as many as 144 matches, if every fire hall somehow matched to every postcode boundary!
</span>
</td>
</tr>
</table>

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Why do we use the StringCaseChanger on the roads data (to change it to UPPERCASE) rather than on the crime data (to change it to TitleCase)?
<br><br><span style="font-weight:bold">Because uppercase is easier to match and has no risk of bad data. If a block was wrongly labelled W Georgia ST in the original data, a title case match would fail. An uppercase conversion would not.
<br><br>Also, be sure not to confuse the StringCaseChanger (changes attribute values) with the BulkAttributeRenamer (changes attribute names)!
</span>
</td>
</tr>
</table>

---


<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 1</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Transformer Selection Practice</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Practice searching for and selecting transformers</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

</table>

You've submitted an application to become an **[FME Certified Professional](https://www.safe.com/partners/certification/)**. To help you practice for the exam your colleagues have given you a number of questions to test your knowledge of searching for and selecting transformers.

Can you answer them?


<br>**1) Most-Used Web Transformers**
<br>The first thing your colleagues want to know is, what are the top five, most-used transformers in the Web category?


<br>**2) Quick Add**
<br>Here is what appears to be a list of random characters:

- lineco
- reac
- rbic
- drape
- attributeexpl
 
The second question is, which transformers are returned by Quick Add for each string, and do you know what any of them will be without trying?


<br>**3) Transformer Searching**
<br>Thirdly, your colleagues have come up with a list of different scenarios, and want you to search for a transformer to carry them out:

- We have some lines of text in a file and want to read that text and add it as an attribute.
- We have a set of vector contours and want to create a cross-section by transposing the X and Z coordinates.
- We have a point cloud dataset and want to reduce its size by resampling it to remove excess points.
- We have a text string and want to find out how many characters the string contains.
- We have a set of addresses and for each address want to find the closest two libraries.


---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Your colleagues say...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
The answers to our questions can be found at the end of this chapter... 
</span>
</td>
</tr>
</table>

<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 2</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Noise Control Laws Project (Addresses)</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Addresses (File Geodatabase)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Convert a File Geodatabase to Microsoft Excel and map the schema</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Attribute Management for Schema Mapping</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformers-Ex2-Complete.fmw</td>
</tr>

</table>

City councillors have voted to amend noise control laws and local residents living in affected areas must be informed of these changes.

You have been recommended by your manager to take on the task of finding all affected addresses. There's a tight deadline and at least three city councillors are standing watching you work. The pressure is on, and it's up to you to deliver!

This exercise is the first part of the project. You know that the address database for the city is stored in an Esri Geodatabase whose schema matches the Local Government Information Model PostalAddress table. 

However, you are told that the software used to carry out automated bulk mailings requires addresses stored in an Excel spreadsheet using a completely different schema.

So, your first task is to create a workspace that converts addresses from Geodatabase to Excel, mapping the schema at the same time.


<br>**1) Inspect Data**
<br>As usual, the first task is to familiarize yourself with the data. To do this open the following dataset within the FME Data Inspector:


<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">Esri Geodatabase (File Geodb API)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\Addresses\Addresses.gdb</td>
</tr>

</table>


The table that is to be translated is called "PostalAddress." The important thing here is not how the data looks in the graphic display, but more what attributes exist in the Table View window.

![](./Images/Img4.200.Ex2.SourceAddressData.png)



**2) Add Creator/FeatureReader**
<br>Now that you are familiar with the source data, start FME Workbench and begin with an empty workspace. 

We can choose to read the source data using either a reader or a FeatureReader transformer. The FeatureReader will allow us to build in a spatial filter so - because we believe this project may need some filtering - we'll use a FeatureReader transformer with a Creator to create a feature to trigger it.

So place a Creator transformer and connect it to a FeatureReader:

![](./Images/Img4.201.Ex2.CreatorFeatureReader.png)

Inspect the FeatureReader parameter. Set up the paarameters as follows:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">Esri Geodatabase (File Geodb API)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\Addresses\Addresses.gdb</td>
</tr>

<tr>
<td style="font-weight: bold">Feature Types to Read</td>
<td style="">PostalAddress</td>
</tr>

</table>

![](./Images/Img4.202.Ex2.FeatureReaderParams.png)

Ensure Run with Feature Caching is turned on and run the workspace. Inspect the FeatureReader:PostalAddress output cache to confirm that all addresses are being read correctly.


**3) Add Writer**
<br>Now let's add a writer to write the output data. There currently seems no benefit or need to use a FeatureWriter, so select Writers &gt; Add Writer from the menubar and use the following:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Writer Format</td>
<td style="">Microsoft Excel</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Dataset</td>
<td style="">C:\FMEData2018\Output\Training\AddressFile.xlsx</td>
</tr>

<tr>
<td style="font-weight: bold">Sheet Definition</td>
<td style="">Import from Dataset</td>
</tr>

</table>

![](./Images/Img4.203.Ex2.WriterParams.png)

Setting 'Import from Dataset' will let us import an Excel spreadsheet to use as a guide. Click OK to add the writer.


<br>**4) Import Feature Types**
<br>At this point you are prompted to select the dataset to import a schema definition from. The two fields should be set up with the same values as the writer. Set the Dataset parameter as follows:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Resources\DesktopBasic\AddressSchema.xlsx</td>
</tr>

</table>

This file is our guide/template. Click OK to accept the values. The new feature type will be created to match the chosen Excel schema.


<br>**5) Add AttributeManager**
<br>Now we can start to map the schema from reader (FeatureReader) to writer. As you'll have noticed, the two do not currently match up very well.

So, place an AttributeManager connected between the two. 

![](./Images/Img4.204.Ex2.AttrManagerCanvas.png)

Its parameters will look like this:

![](./Images/Img4.205.Ex2.AttrManagerOriginal.png)

Firstly let's clear up the reader schema by removing some of the unwanted attributes. 

Click on the following attributes and press the - button to remove them:

- OBJECTID
- GlobalID
- OWNERNM1
- OWNERNM2
- INTSTATE
- INTPSTLCD
- REPRESENT
- STATUS
- LASTUPDATE
- LASTEDITOR

![](./Images/Img4.206.Ex2.AttrManagerDeletedAttrs.png)


<br>**6) Rename Attributes**
<br>Several source attributes can be written to the output as they are, but do need renaming first.

In the AttributeManager rename the following:

- PSTLCITY to City
- PSTLPROV to Province
- POSTALCODE to PostalCode
- COUNTRY to Country

![](./Images/Img4.207.Ex2.AttrManagerRenamedAttrs.png)

If the AttributeManager is connected to the writer feature type then you should be able to select the Output Attribute field from a drop-down list instead of typing it in.


<br>**7) Create Attribute (Provider)**
<br>Two attributes on the output (Provider and UpdateDate) are new and cannot be copied from the source data. They must be created. 

In the AttributeManager create the new attribute "Provider". Because the attribute exists on the output schema, you can again select it from the drop-down list.

Set a fixed value such as your own organization name, "Safe Software", or "City of Interopolis."


<br>**8) Create Attribute (UpdateDate)**
<br>Now create the new attribute "UpdateDate". Rather than hard-coding a value click on the drop-down arrow in the Attribute Value field and choose Open Text Editor.

In the text editor locate the Date/Time Function called DateTimeNow and double-click to place it in the editor. By default it creates a datetime in ISO syntax, which is fine for us, so simply click OK to accept this.

Click OK again to close the AttributeManager dialog.


<br>**9) Run Transformer**
<br>Run the workspace by clicking on the AttributeManager transformer and selecting Run to This: 

![](./Images/Img4.208.Ex2.AttrManagerRunToHere.png)

This will run the transformer by itself, using previous caches, but not writing any output (which we don't need yet).

Inspect the AttributeManager:Output cache to confirm that the procedure worked as expected:

![](./Images/Img4.209.Ex2.AttrManagerOutput.png)



<br>**10) Add AttributeSplitter**
<br>Looking at the output schema there are two fields for Number and Street (for example "3305" and "W 10th Av"). However, the source schema condenses that information into one field with &lt;space&gt; characters separating the fields ("3305 W 10th Av"). Therefore we'll have to split the source attribute up in order to match the Writer schema.

Insert an AttributeSplitter transformer. Insert it ***before*** the AttributeManager - then if there are any actions to carry out on the split attributes we can use the same AttributeManager transformer.

View the AttributeSplitter parameters. Set PSTLADDRESS as the attribute to split and enter a space character into the Delimiter parameter. Notice that a list name is set in the List Name parameter (we'll use that  list shortly):

![](./Images/Img4.210.Ex2.AttrSplitterParameters.png)

Click OK to close the dialog. If you run the workspace now and inspect the cache, you'll see the address as a list attribute in the Feature Information window:

<pre>
_list{0} (encoded: utf-8) 3305
_list{1} (encoded: utf-8) W
_list{2} (encoded: utf-8) 10th
_list{3} (encoded: utf-8) Av
</pre>

Remember a list attribute is one that can store multiple values under a single name (_list).


<br>**11) Rename Attribute**
<br>Now let's handle the Number field in the output. Go back to the AttributeManager parameters. 

Notice that there is now an entry for the list attribute called _list{}. However, this is just the list attribute *"in general"* - it isn't showing each element (value) in the list.

What we need to do is create a new attribute and copy the list element we want into it. So, in the Output Attribute field create a new attribute called Number by selecting it from the drop-down list.

For the Attribute Value field click the drop-down arrow and select Attribute Value &gt; _list{}...

You will now be prompted to select the element in the list. Ensure it is set to zero (0) and click OK.

![](./Images/Img4.211.Ex2.AttrManagerListElementRename.png)

Click Apply/OK to confirm the changes. Run the workspace and inspect the AttributeManager:Output cache to ensure the number is being copied.


<br>**12) Construct Attribute**
<br>The final step is to recreate the Street attribute, without it being prefixed by the address number.

View the AttributeManager parameters again. This time in the Output Attribute field create a new attribute called Street by selecting it from the list.

Unlike the Number field, we want to create this value by concatenating several list elements. So click the drop down arrow in the Attribute Value field and choose Open Text Editor.

Locate _list{} in the FME Feature Attributes menu and carry out the following steps:

<ul>
<li>Double-click _list{} and when prompted select element 1. Click OK</li>
<li>Press the spacebar to enter a &lt;space&gt; character</li>
<li>Double-click _list{} and when prompted select element 2. Click OK.</li>
<li>Press the spacebar to enter a &lt;space&gt; character</li>
<li>Double-click _list{} and when prompted select element 3. Click OK.</li>
</ul>

The dialog will now look like this:

![](./Images/Img4.212.Ex2.AttrManagerListElementConcat.png)

In this way we will have concatenated all parts of the street name back together, for example:

<pre>
"W"+"17th"+"St" becomes "W 17th St"
</pre>

We're assuming that no street name has more than three parts to it, but that's reasonable for our example.


<br>**13) Run Workspace**
<br>Save the workspace. Turn off feature caching and then run the workspace.

---

<!--Warning Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-exclamation-triangle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">WARNING</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
The Excel writer has a parameter called <strong>Overwrite Existing File</strong>, which by default is set to <strong>No</strong>.
<br><br><img src="./Images/Img4.213.Ex2.ExcelWriterOverwriteParam.png">
<br><br>This is probably a good time to change the parameter to Yes, because we've been running the workspace multiple times!
</span>
</td>
</tr>
</table>

---

Open the containing folder to check the output has been written. Inspect the data in the FME Data Inspector. The output (in the Table View window) should look like this:

![](./Images/Img4.214.Ex2.ExcelWriterOutput.png)

---

<!--Tip Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-info-circle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">TIP</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
The Event field is still empty at this point, but will be completed in a subsequent exercise.
</span>
</td>
</tr>
</table>

---

<!--Exercise Congratulations Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-thumbs-o-up fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">CONGRATULATIONS</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
By completing this exercise you have learned how to:
<br>
<ul><li>Use the AttributeManager transformer to create, delete, and rename attributes</li>
<li>Use the AttributeSplitter to split attributes into a list attribute</li>
<li>Handle list attributes in the AttributeManager</li>
<li>Use a Date/Time function in the AttributeManager text editor</li></ul>
</span>
</td>
</tr>
</table>


<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 3</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Noise Control Laws Project (Spatial Filtering)</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Addresses (File Geodatabase)<br>Zoning (MapInfo TAB)<br>Roads (AutoCAD DWG)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">To find all residential addresses within 50 meters of an arterial highway</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Methods of conditional filtering</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformers-Ex3-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformers-Ex3-Complete.fmw</td>
</tr>

</table>

As you know, city councillors have voted to amend noise control laws and local residents living in affected areas must be informed of these changes.

You have been recommended by your manager to take on the task, and there's a tight deadline.

In the first part of the project you created a workspace to convert addresses from Geodatabase to Excel, mapping the schema at the same time. 

This exercise is the second part of the project: locating all affected residents. You must locate all single-family residences within 50 metres of a major highway and filter out all others from the stream of address data.


<br>**1) Start Workbench**
<br>Start Workbench (if necessary) and open the workspace from Exercise 2. Alternatively you can open C:\FMEData2018\Workspaces\DesktopBasic\Transformers-Ex3-Begin.fmw

![](./Images/Img4.215.Ex3.StartingWorkspace.png)

The workspace already has a FeatureReader to read addresses, transformers to edit the address schema, and a writer to write data to an Excel spreadsheet.


<br>**2) Add Reader (Roads data)**
<br>Use Readers > Add Reader to add a reader for the roads data. The roads data will be used to determine distance from an arterial route.

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">Autodesk AutoCAD DWG/DXF</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\Transportation\CompleteRoads.dwg</td>
</tr>

</table>

When prompted, select only the feature type (layer) called Arterial. 


<br>**3) Add Reader (Zoning data)**
<br>Use Readers > Add Reader to add a reader for zoning data. The zoning data will be used to determine whether an address is single-family residential or not.

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">MapInfo TAB (MITAB)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\Zoning\Zones.tab</td>
</tr>

</table>

With attribute lists collapsed, the workspace will now look like this:

![](./Images/Img4.216.Ex3.NewReaders.png)

Feel free to inspect all of the source data to familiarize yourself with the contents. You can even run the workspace to make sure all caches are up to date.


<br>**4) Add Tester Transformer**
<br>Add a Tester transformer to the Zoning feature type.

This Tester will be used to filter residential zones from the other zoning areas.
All single-family residential zones will start with RS, so the Tester should be set up like this:

![](./Images/Img4.217.Ex3.TesterParameters.png)

The important thing is to set up the test with the “Begins With” operator.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
So... why the Tester? Why not use the AttributeFilter? <a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=5&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">Do you know?</a>
</span>
</td>
</tr>
</table>

---

<br>**5) Connect to FeatureReader**
<br>One way to filter data is to use a SpatialFilter transformer, and we will do this with the road features. But another method is to use filtering inside the FeatureReader transformer.

So, delete the Creator transformer and connect the Tester:Passed port to the FeatureReader:Initiator port:

![](./Images/Img4.218.Ex3.TesterReplacesCreator.png)


<br>**6) Set up FeatureReader**
<br>Now inspect the FeatureReader's parameters. Set the Spatial Filter parameter to *Initiator Contains Result:*

![](./Images/Img4.219.Ex3.FilteredFeatureReader.png)

This ensures that only addresses that fall inside a Single Family Residence zone will be read from the database. Make sure feature caching is turned on and run the workspace. Inspect the Tester:Passed and FeatureReader:PostalAddress caches to confirm that the results are correct.


<br>**7) Add Bufferer**
<br>Now we can determine which of the filtered addresses fall within 50 metres of an arterial route. This time we'll use a SpatialFilter transformer. 

The SpatialFilter does not have a test for "within X distance" therefore we'll have to set that up a little differently. Add a Bufferer transformer to the workspace. Connect it to the Arterial roads data:

![](./Images/Img4.220.Ex3.BuffererOnCanvas.png)

Set the Bufferer Buffer Amount parameter to be 50.

---

<!--Tip Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-info-circle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">TIP</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Optionally you can add a Dissolver transformer after the Bufferer, to merge all the buffer features together.
<br><br>The results of the translation will be the same (in terms of addresses selected) but the data will look better in the FME Data Inspector.
</span>
</td>
</tr>
</table>

---

<br>**8) Add SpatialFilter**
<br>Add a SpatialFilter transformer. The buffered arterial routes are the Filter. The Candidate port can be connected between the FeatureReader and the AttributeSplitter:

![](./Images/Img4.221.Ex3.SpatialFilterOnCanvas.png)

This way the AttributeSplitter and AttributeManager are operating only on filtered features. If the SpatialFilter was connected after the AttributeManager, then data would be getting processed and then discarded.


<br>**9) Set SpatialFilter Parameters**
<br>Set up the SpatialFilter parameters as follows:

<table>
<tr><td style="font-weight: bold">Filter Type</td><td>Multiple Filters</td><td>There are multiple buffer polygons</td></tr>
<tr><td style="font-weight: bold">Pass Criteria</td><td>Pass Against One Filter</td><td>A single address cannot be in <strong>all</strong> buffers</td></tr>
<tr><td style="font-weight: bold">Spatial Predicates to Test</td><td>Filter Contains Candidate</td><td>Find addresses contained in the arterial buffers</td></tr>
</table>

![](./Images/Img4.222.Ex3.SpatialFilterParameters.png)

ie there are multiple road buffers, but an address only has to be inside one buffer to pass (not all of them).


**10) Run Workspace**
<br>Run the workspace using Run From This on the SpatialFilter. Inspect the cached output to prove that only addresses inside both a single-family zone and a arterial road buffer have passed the filtering process.


**11) Set Event Field**
<br>As a final step, open the Feature Type dialog for the Excel writer, click on the User Attributes tab, and set a fixed value for the Event field:

![](./Images/Img4.223.Ex3.EventAttrUpdate.png)

Turn off caching, re-run the workspace, and check the output to confirm the dataset has been written correctly. There should be 148 records in the spreadsheet, ready to send to the administration department for a bulk mailing.

---

<!--Exercise Congratulations Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-thumbs-o-up fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">CONGRATULATIONS</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
By completing this exercise you have learned how to:
<br>
<ul><li>Use the Tester transformer to filter by an attribute value</li>
<li>Use the Spatial Filter option in the FeatureReader transformer</li>
<li>Use the Bufferer transformer to set up a "within x distance of" test</li>
<li>Use the SpatialFilter transformer to filter by geometry</li></ul>
</span>
</td>
</tr>
</table>

<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 4</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Noise Control Laws Project (Crime Data Joins)</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Crime Statistics (CSV)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Carry out a join between crime statistics and address features</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Attribute-Based Joins</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformers-Ex4-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformers-Ex4-Complete.fmw</td>
</tr>

</table>

As you know, city councillors have voted to amend noise control laws and local residents living in affected areas were informed of these changes.

In the first part of the project, you created a workspace to convert addresses from Geodatabase to Excel, mapping the schema at the same time. In the second part of the project, you continued the workspace to locate all single-family residences within 50 metres of a major highway and filter out all others from the stream of address data.

Now a data journalist with a national newspaper is concerned that the relaxation of noise control laws may lead to more crime in the city. They have therefore made a request for recent crime figures for each of the affected addresses. They intend to compare this against future data to see if their theory is correct.

This is a major test of the city's open data policy and there's no question of not complying. However, a crisis arises as the current datasets for crime (CSV, non-spatial) is not joined to the address database in any way. 

So, for the final part of this project you must take the existing noise control workspace and amend it to incorporate crime statistics. 

Pull this off and you will be a spatial superhero!


<br>**1) Start Workbench**
<br>Start Workbench (if necessary) and open the workspace from Exercise 3. Alternatively you can open C:\FMEData2018\Workspaces\DesktopBasic\Transformers-Ex4-Begin.fmw

The workspace is already set up to read addresses, filter them spatially, and write them to an Excel spreadsheet.

![](./Images/Img4.225.Ex4.StartingWorkspace.png)


<br>**2) Add Reader**
<br>Now let's start working with crime data. There is no benefit from using a FeatureReader, so add a reader to the workspace using Readers &gt; Add Reader from the menubar. Use the following parameters:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">Comma Separated Value (CSV)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\Emergency\Crime.csv</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Parameters</td>
<td style="">Fields:Delimiter Character: , (Comma)<br>Fields:Field Names Line: 1</td>
</tr>

</table>


<br>**3) Inspect Data**
<br>The next task is to familiarize yourself with the source data. Turn on feature caching and run the CSV reader using Run Just This:

![](./Images/Img4.226.Ex4.CSVRunJustThis.png)

Inspect the cached data. It will look like this in the Data Inspector Table View window:

![](./Images/Img4.224.Ex4.SourceCSV.png)

Notice how there is no spatial data as such, but there is a block number. 

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Police-Chief Webb-Mapp says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Crime?! In my city? I think not. But if there was... be aware that 7XX W Georgia Street means the seventh block on Georgia Street west of Ontario Street and covers building numbers 700-800. 7XX E Georgia Street would be 14 blocks away, the seventh block east of Ontario. Got it? 
</span>
</td>
</tr>
</table>

---

You might have spotted that each address feature has a number (not a block ID like "7XX"), and that the road data is stored in Title case ("W Georgia St") in the roads dataset, whereas the crime dataset is upper case ("W GEORGIA ST").

Both of these will make it harder, but not impossible, to join the two sets of data together.


<br>**4) Add StringReplacer**
<br>To merge the data we need to reduce the address number to a block number that matches the crime data in structure; for example we need 74XX instead of 7445.

So, add a StringReplacer transformer and connect it between the AttributeManager and the PostalAddress feature type. 

Set the following parameters:

<table>
<tr><td>Attributes</td><td>Number</td></tr>
<tr><td>Mode</td><td>Replace Regular Expression</td></tr>
<tr><td>Text to Replace</td><td>..$</td></tr>
<tr><td>Replacement Text</td><td>XX</td></tr>
</table>

The text to replace (..$) means replace the last two characters of the string, and they are replaced with XX to match the crime data. 

![](./Images/Img4.227.Ex4.StringReplacerDialog.png)

Run the workspace (using *Run to Here* on the StringReplacer) and inspect the caches to ensure the transformer is working as expected.


<br>**5) Add StringCaseChanger**
<br>The other difference in crime/road data was in UPPER/Title case street names. This disparity can be fixed with a StringCaseChanger transformer.

Add a StringCaseChanger transformer after the StringReplacer and set the parameters to change the value of Street to upper case:

![](./Images/Img4.228.Ex4.StringCaseChanger.png)

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
So, answer me this. Why do we use the StringCaseChanger on the address data (to UPPERCASE) rather than changing the crime data (to TitleCase)? <a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=5&question=7&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">Do you know?</a>
</span>
</td>
</tr>
</table>

---

<br>**6) Build Join Key**
<br>Having updated the attributes to match the crime data, we now have to construct a key out of them. 

Add an AttributeManager to the canvas after the StringCaseChanger. Create a new attribute called JoinKey. Open the Text Editor for the attribute and enter (select):

<pre>
@Trim(@Value(Number) @Value(Street))
</pre>

This will match the structure of the crime data (be sure to include a space character between the two attributes). The Trim function is there to ensure there are no excess spaces on those attributes. 


<br>**7) Add FeatureJoiner**
<br>Now we've sorted out the structure of our join keys we can merge the data together with a FeatureJoiner.

Add a FeatureJoiner to the canvas. Connect the address data to the Left input port, and the crime data to the Right input port. The Joined output port is connected to the PostalAddress feature type:

![](./Images/Img4.229.Ex4.FeatureJoinerCanvas.png)

Inspect the parameters for the FeatureJoiner.

For the Join Mode select *Left*. This means that we want all of the addresses to be output, whether they match to a crime record or not.

In the Join On parameters select the JoinKey attribute for the Left value, and the Block attribute for the Right value.

Run that part of the workspace to see what the results of this translation are.


<br>**8) Add Aggregator**
<br>Interestingly, although 148 addresses enter the FeatureJoiner, 267 emerge from it:

![](./Images/Img4.230.Ex4.FeatureJoinerResults.png)

That's because there are multiple crimes per block and there were 267 matches with the data.

We can aggregate that data together using an Aggregator transformer. So place an Aggregator transformer after the FeatureJoiner:Joined port:

![](./Images/Img4.231.Ex4.AggregatorOnCanvas.png)

Inspect the parameters. We need to set the group-by parameter by selecting attributes that will group matches back into the original addresses. There is no ID for each address because we removed them in a previous step, so either:

- Return to the AttributeManager, undo the Remove option for OBJECTID, and use OBJECTID as the Aggregator group-by
- Use UpdateDate as the Aggregator group-by (because each address will have received a unique timestamp)

Then set the Count Attribute to a value of NumberCrimes:

![](./Images/Img4.232.Ex4.AggregatorParams.png)

If you expand your attributes for the PostalAddress writer, you will notice that NumberCrimes doesn't appear. When we edited the User Attributes for this writer in an earlier exercise, we changed its Attribute Definition from Automatic to Manual. This means it will not automatically update to add new attributes created during translation. Therefore we have to either switch back to Automatic (which would bring along many other unwanted attributes), or simply add a new attribute called NumberCrimes here. Give it type "number" and cell width 6. The data from the Aggregator will now have its attribute on the writer.

<br>**9) Write Data**
<br>Now we know the workspace is performing correctly, turn off feature caching. Update the Excel writer PostalAddress schema to record the NumberCrimes attribute.

Finally re-run the workspace and check the results in the Data Inspector. The data will include the number of crimes, and the reworking of the attributes means that individual addresses have been anonymized as well. This is important because this data is being made public.

---

<!--Exercise Congratulations Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-thumbs-o-up fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">CONGRATULATIONS</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
By completing this exercise you have learned how to:
<br>
<ul><li>Pre-process data to get join keys with a matching structure</li>
<li>Build a join key for use in a FeatureJoiner</li>
<li>Join non-spatial data with a join key in the FeatureJoiner</li>
<li>Use an Aggregator transformer to merge joins and count the number of joins</li></ul>
</span>
</td>
</tr>
</table>


