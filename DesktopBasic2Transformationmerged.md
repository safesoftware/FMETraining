# Data Transformation #

Data Transformation is the ability to manipulate data during a data translation, even to the extent of having an output greater than the sum of the inputs!

![](./Images/Img2.001.DataTransformation.png)


# What is Data Transformation?
**Data Transformation** is FME's ability to manipulate data. The transformation step occurs during the process of format translation. Data is read, transformed, and then written to the chosen format.

![](./Images/Img2.002.TransformationInFME.png)


## Data Transformation Types
Data transformation can be subdivided into two distinct types: *Structural Transformation* and *Content Transformation*.


### Structural Transformation
Structural transformation is perhaps better called ‘reorganization'. It refers to FME's ability to channel data from source to destination in an almost infinite number of arrangements. 

This includes the ability to merge data (as in the image above), divide data, re-order data, and define custom data structures.

Transforming the structure of a dataset is carried out by manipulating its schema.


### Content Transformation
Content transformation is perhaps better called ‘revision'. It refers to the ability to alter the substance of a dataset. 

Manipulating a feature's geometry or attribute values is the best example of how FME can transform content.

Content transformation can take place independently or alongside structural transformation.


---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Mr Flibble says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Mr. Flibble - certified FME jester - here to entertain you. Here's a riddle, but can you solve it?
<br><br>The most common format translation defined with FME is from Esri Shapefile to which format?
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=1&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. Esri Geodatabase</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=1&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. AutoCAD DXF/DWG</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=1&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. Google KML</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=1&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. Esri Shapefile</a>
<br><br>If you're in a class, have a group vote!
</span>
</td>
</tr>
</table>

# Structural Transformation #
Transforming a dataset's structure requires using FME to manipulate *schemas*. FME uses the term "schema", but you may know this as *data model*.

## Schema Concepts ##
A ***schema*** defines the structure of a dataset. Each dataset has its own unique schema; it includes layers, attributes, and other rules that define or restrict its content.

### Schema Representation ###
When a new workspace is created, FME scans the source datasets. It creates a ***reader*** whose layers are illustrated on the left side of the workspace canvas, and a ***writer*** whose layers are illustrated on the right side of the workspace canvas:

![](./Images/Img2.003.ReaderWriterFeatureTypes.png)

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
Each object in this illustration represents a subdivision in the source dataset. In FME terminology these objects are called <strong>feature types</strong>. Multiple feature types means there are multiple layers in the source dataset.
</span>
</td>
</tr>
</table>

---

### Reader Schema ###
For the reader, more information about the schema is revealed by clicking the cog-wheel icon on each feature type object:

![](./Images/Img2.004.ReaderFeatureTypePropertiesButton.png)

This Feature Type dialog has a number of tabs. Under the Parameters tab is a set of general parameters, such as the name of the feature type (in this case Libraries) the allowed geometry types, and the name of the parent dataset:

![](./Images/Img2.005.ReaderFeatureTypePropertiesDialog.png)

The User Attributes tab shows a list of attributes. Each attribute is defined by its name, data type, width, and number of decimal places:

![](./Images/Img2.006.ReaderFeatureTypePropertiesAttrs.png)

Each layer has a different name and can also have a completely different set of attributes. All of this information goes to make up the reader schema. It is literally ***"what we have"***.


### Writer Schema ###
As with the reader, each writer has a set of detailed schema information accessed by opening the dialog for a feature type:

![](./Images/Img2.007.WriterFeatureTypePropertiesButton.png)

By default, the writer schema (***"what we want"***) is a mirror image of the source, so the output from the translation will be a duplicate of the input. This allows users to translate from format to format without further edits (*Quick Translation*).

If *"what we want"* is different to the default schema definition, we simply have to change it using a technique called ***Schema Editing***.

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
FME supports 400+ formats and there are almost as many terms for the way data is subdivided. The most common terms are layer, table, class, category, level, or object.
<br><br>Although the general FME term for these subdivisions is <strong>feature type</strong>, all dialogs in FME Workbench use format-specific terminology where the correct term is applicable.
</span>
</td>
</tr>
</table>


# Schema Editing

***Schema Editing*** is the process of altering the writer schema to customize the structure of the output data. One good example is renaming an attribute field. 

After editing, the source schema still represents *"what we have"*, but the destination schema now truly does represent *"what we want"*.


## Editable Components
There are a number of edits that can be performed, including, but not limited to the following:

### Attribute Renaming
Attributes on the destination schema can be renamed, such as renaming POSTALCODE to PSTLCODE.

To rename an attribute open the Feature Type dialog and click the User Attributes tab. Click the attribute to be renamed and enter the new name.

![](./Images/Img2.008.WriterFeatureTypeEditAttr.png)

---

### Attribute Type Changes
Any attribute on the writer schema can have a change of type; for example, changing from an integer field to a character field.

To change an attribute type open the User Attributes tab and set the Type field to the new type:

![](./Images/Img2.009.WriterFeatureTypeEditAttrType.png)

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
The Type column for an attribute shows only values that match the permitted types for that data format. For example, an Oracle schema permits attribute types of varchar or clob. MapInfo does not support these data types so they would never appear in a MapInfo schema. The above screenshot shows data types for the GML format.
</span>
</td>
</tr>
</table>

---

### Feature Type Renaming
To rename a writer feature type open the Parameters tab, click in the Feature Type Name field (the label may vary according to the format type) and edit the name as required:

![](./Images/Img2.010.WriterFeatureTypeEditName.png)

You can also rename a feature type by clicking on it in the Workbench canvas and pressing the F2 key.

---

### Geometry Type Changes
To change the permitted geometry for a feature type, (for example, change the permitted geometries from lines to points) open the Parameters tab and change the permitted geometry type:

![](./Images/Img2.011.WriterFeatureTypeGeometry.png)

This field is only available where the format requires a strict decision on geometry type. Where formats allow any mix of geometry in a single feature type, this setting is not shown.

---

Once the user has made all the required changes to the writer schema, the workspace reflects *"what we want"* - but it doesn't yet specify how the reader and writer schemas should be connected together. This is the next task and it is called ***Schema Mapping***.

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
You might be wondering "what would happen if I edited the <strong>reader</strong> schema, instead of the writer"?
<br><br>Well, by default you can't! The schema fields for a reader are greyed out to prevent this, since changes would put the schema definition out of sync with the source dataset:
<br><br><img src="./Images/Img2.012.GrayedOutFeatureAttrs.png">
<br><br>There are a few, rare, use cases - but they're outside the scope of this training course!
</span>
</td>
</tr>
</table>

# Schema Mapping

Schema Mapping is the second key part towards data restructuring in FME.

In FME Workbench, one side of the workspace shows the reader schema (*"what we have"*) and the other side shows the writer schema (*"what we want"*). Initially the two schemas are automatically joined when the workspace is created, but when edits occur then these connections are usually lost.

***Schema Mapping*** is the process of connecting the reader schema to the writer schema in a way that ensures the correct reader features are sent to the correct writer feature types and the correct reader attributes are sent to the correct writer attributes.

FME permits mapping from source to destination in any arrangement desired. There are no restrictions on what feature types or attributes may be mapped.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Ms. Analyst says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Hi. I'm Ms. Analyst, one of your colleagues at the city. I think of schema editing and schema mapping as a means of reorganizing data.
<br><br>A good analogy is a wardrobe full of clothes. When the wardrobe is reorganized you throw out what you no longer need, reserve space for new clothes that you’re planning to get, and move existing items into a more usable arrangement.
<br><br>The same holds true for spatial data restructuring: it's the act of reorganizing data to make it more usable.
</span>
</td>
</tr>
</table>

---

## Feature Mapping
***Feature Mapping*** is the process of connecting source feature types to destination feature types.

Feature mapping is carried out by clicking the output port of a reader feature type, dragging the arrowhead to the input port of a writer feature type, and releasing the mouse button. Connections are represented by a thick, black line.

Here, a connecting line from source to destination feature type is created by dragging the arrowhead from the source to the destination:

![](./Images/Img2.013.SchemaMappingFeatureConnection.png)

Merging and splitting of data is permitted: 

![](./Images/Img2.014.SchemaMappingMergedConnections.png)

Here a user requires a single layer in the output and so is merging three reader feature types (Parks, Stations, Libraries) into one writer feature type (PublicFacilities).

---

## Attribute Mapping
***Attribute Mapping*** is the process of connecting reader attributes to writer attributes.

Attribute mapping is performed by clicking the output port of a reader attribute, dragging the arrowhead to the input port of a writer attribute, and releasing the mouse button. Attribute connections are shown with a thinner, gray line.

Here feature mapping has been carried out already and attribute connections are being made:

![](./Images/Img2.015.SchemaMappingAttrConnection.png)

Notice the green, yellow, and red color-coding that indicates which attributes are connected.

Green ports indicate a connected attribute. Yellow ports indicate a reader attribute that’s unconnected to a writer. Red ports indicate a writer attribute that’s unconnected to by a reader.

Attributes with the same name in reader and writer feature types are connected automatically, even though a connecting line might not be visible; the port color is the key:

![](./Images/Img2.016.SchemaMappingConnections.png)

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
Names are case-sensitive, therefore ROADS is not the same as roads, Roads, or rOADS.
<br>That's important to know if you are relying on automatic attribute connections!
</span>
</td>
</tr>
</table>

# Transformation with Transformers #

Besides Schema Editing and Schema Mapping, transformation can be carried out using objects called ***transformers***.

## What is a Transformer? ##

As the name suggests, a transformer is an FME Workbench object that carries out transformation of features. There are lots of FME transformers, each of which carry out many different operations.

Transformers are connected somewhere between the reader and writer feature types, so that data flows from the reader, through a transformation process, and on to the writer.

Transformers usually appear in the canvas window as rectangular, light-blue objects.


## Transformer Parameters ##
Each transformer may have a number of parameters (settings). Parameters can be accessed (like feature types) by clicking the cogwheel icon:

![](./Images/Img2.017.TransformerOnCanvas.png)

Alternatively, if the Parameter Editor window is open, parameters can be found there simply by clicking on the transformer (or any other canvas object):

![](./Images/Img2.018.TransformerParametersWindow.png)


---

## Color-Coded Parameter Buttons ##
The parameter button on a transformer is color-coded to reflect the status of the settings.

A blue parameter button indicates that the transformer parameters have been checked and amended as required, and that the transformer is ready to use.

![](./Images/Img2.019.TransformerBlueButton.png)

A yellow parameter button indicates that the default parameters have not yet been checked. The transformer can be used in this state, but the results may be unpredictable.

![](./Images/Img2.020.TransformerYellowButton.png)

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
If the Parameter Editor window is open then you will rarely see a yellow icon, because a transformer's parameters are automatically opened and assumed to be reviewed. If that window is open, you should be sure to check it to ensure you don't miss setting a parameter that you need.
</span>
</td>
</tr>
</table>

---

A red parameter button indicates that there is at least one parameter for which FME cannot supply a default value. The parameter must be provided with a value before the transformer can be used.

![](./Images/Img2.021.TransformerRedButton.png)


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
Good morning everyone, I'm First Officer Transformer and I'd like to welcome you aboard today's training.
<br><br>Please be sure to check your parameters before your try to take off. Your workspaces just won't fly if there are any red-flagged transformers in them!
</span>
</td>
</tr>
</table>

---

## Transformer Ports ##
Far from having just a single input and/or output, a transformer can have multiple input ports, multiple output ports, or both.

This 2DForcer transformer has a single input and output port.

![](./Images/Img2.022.TransformerSingleInputOutput.png)

This Clipper has multiple input and output ports. Notice that not all of them are – or need to be – connected.

![](./Images/Img2.023.TransformerMultiInputOutput.png)

This Inspector has just a single input port...

![](./Images/Img2.024.TransformerOneInput.png)

…whereas this Creator has only a single output port!

![](./Images/Img2.019.TransformerBlueButton.png)

### Transformer Attributes ###
Click on the drop-down arrow of a transformer output port to see all of the attributes that exit the transformer. This includes all changes applied within the transformer.

![](./Images/Img2.025.AttributesOnTransformerPort.png)

This is a good way to visualize which attributes have been created, lost, or otherwise transformed within the transformer.

# Content Transformation #

Content transformations are those that operate on the components of a feature.

 
## What is a Feature? ##
A ***feature*** in FME is an individual item within the translation. For spatial data a feature is generally a geometric object (with or without a set of related attributes). 

For tabular data a feature is generally a record in a database, a row in a spreadsheet, or a line in a text file. Each column or cell is known as an ***attribute***.

![](./Images/Img2.026.FeatureGraphic.png)

Features in FME have a flexible, generic representation that is unrelated to the format from which they originated. That means any transformer can operate on any FME feature, regardless of its source format. Sometimes content transformation operates on single features, sometimes on multiple features at once.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Ms. Analyst says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
You can think of Content Transformation as altering or editing data.
<br><br>The wardrobe analogy still works here. You might take your clothes from the wardrobe to clean them, or alter them, or repair them, or dye them a new color, or all sorts of other tasks, before returning them to their place.
<br><br>The same holds true for spatial data transformation: it's the act of fixing up your data to be cleaner and in the style you really want
</span>
</td>
</tr>
</table>


---

## Geometric Transformation ##
***Geometric Transformation*** is the act of restructuring the spatial component of an FME feature. In other words, the geometry of the feature undergoes some form of change to produce a different output.

Some examples of geometric transformation include the following:

- **Generalization** – a cartographic process that restructures data so it's easily visualized at a given map scale
- **Warping** – adjustment of the size and shape of a set of features to more closely match a set of reference data
- **Topology Computation** – conversion of a set of linear features into a node/line structure
- **Line Intersection** - calculation of the intersection points between line features

![](./Images/Img2.027.GeometricTransformation.png)

Here roads have been intersected with rivers to produce points that mark the location of bridges.


## Attribute Transformation ##
***Attribute Transformation*** is the act of restructuring the tabular components of an FME feature. In other words, the attributes undergo some form of change to produce a different output.

Some examples of attribute transformation are:

- **Concatenation** – joining together of two or more attributes
- **Splitting** – splitting one attribute into many, which is the opposite of Concatenation
- **Measurement** – measuring a feature's length or area to create a new attribute
- **ID Creation** – creating a unique ID number for a particular feature

Attribute concatenation as an example of attribute transformation.

Each line of the address is concatenated to return a single line address.
>  	Address1 	Suite 2017,+
> 	Address2 	7445-132nd Street,+
> 	City  	  	Surrey,+
> 	Province 	British Columbia,+
> 	PostalCode 	V3W 1J8
> 	
> 	= Address 	Suite 2017, 7445-132nd Street, Surrey, British Columbia, V3W 1J8


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
Did you miss me? You did? Well I'll cure that with some new questions for you!
<br><br>Which three colours represent checked, need checking, and unset parameters on transformer objects?
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=2&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. blue, yellow, red</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=2&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. green, yellow, red</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=2&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. red, green, blue</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=2&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. green, blue, yellow</a>
<br><br>If I use a transformer to remove irregularities (like self-intersecting loops) in the boundary of a polygon, what type of transformation is it? 
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=3&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. Structural Transformation of attributes</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=3&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. Structural Transformation of geometry</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=3&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. Content Transformation of attributes</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=3&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. Content Transformation of geometry</a>
</span>
</td>
</tr>
</table>

# Transformers in Series #
Much like a set of components in an electrical circuit, a series of Workbench transformers can be connected together to have a cumulative effect on a set of features.

 
## Chaining Transformers ##
Even with the large number of transformers available in FME, users frequently need a combination - or chain of transformers - instead of a single one.

A string of transformers that graphically represent an overall workflow is a key concept of FME:

![](./Images/Img2.028.TransformersInSeries.png)

In this example, a DuplicateFilter transformer removes duplicate polygon features. A Dissolver transformer merges each remaining (unique) polygon with its neighbor where there is a common boundary. Finally, each merged area gains an ID number from the Counter transformer.

## Feature Count Display##
Look back at the previous example's translation. Did you notice that while the workspace was running, each connection was updated with the number of features that had passed along it?

![](./Images/Img2.029.TransformerCounts.png)


The final feature counts show that 80 features were read, 73 passed the Tester while 7 failed (for being dog parks) and went on to the Logger.

The Log window confirms the number of features written and lists the features that failed the Tester.

These numbers help analyze the results of a workspace and provide a reference for debugging if the output differs from what was expected.

# Transformers in Parallel #
A ***stream*** is a flow of data represented by connections in the workspace. A key concept in FME is the ability to have multiple parallel streams within a workspace. 
 
## Multiple Streams ##
Multiple streams are useful when a user needs to process the same data, but in a number of different ways. A workspace author can split one stream into several, or combine several streams of data into one, as required:

![](./Images/Img2.030.MultipleStreams.png)

## Creating Multiple Streams ##
Splitting data can occur in a number of ways. Sometimes a transformer with multiple output ports (a Tester transformer is a good illustration of this) will divide (or filter) data with several possible output streams:

![](./Images/Img2.031.MultiPortSplit.png)

Additionally, a full stream of data can be duplicated by simply making multiple connections out of a single output port. In effect it creates a set of data for each connection.

Here FME reads 8 features but, because there are multiple connections, creates multiple copies of the data:

![](./Images/Img2.032.DuplicatedStreams.png)


## Bringing Together Multiple Streams ##
When multiple streams are connected to the same input port no merging takes place. The data is simply accumulated into a single stream. This is often called a *union*.

Here, three streams of data converge into a writer feature type:

![](./Images/Img2.033.UnionOfStreams.png)

No merging takes place; the data simply accumulates into 15 distinct features in the output dataset. To carry out actual merging of data requires a specific transformer such as the FeatureMerger or FeatureJoiner.

# Group-By Processing #
Group-By parameters allow features to be processed in groups by a single FME transformer.


## What is a Group? ##
FME transformers carry out transformations on either one feature at a time, or on a whole set of features at once.

For example, the *AreaCalculator* transformer operates on one feature at a time (to measure the area of a single  polygon feature). We call it a ***feature-based transformer***.

The *StatisticsCalculator* operates on multiple features at a time (to calculate an average value for them all). In FME we call this set of features a ***group*** and the transformer is a ***group-based transformer***. 


## Creating Groups ##
So a group is simply a defined set of features being processed by a transformer. By default a group-based transformer treats ALL the features that it is fed as a single group.

However, such transformers also have a ***Group-By*** parameter. This parameter lets the user define several groups based upon the value of an attribute.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Mr. Statistics-Calculator, CFO says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Hi. I don't think we've met yet. I'm Mr. Statistics-Calculator. I bet you can't guess my favourite transformer!
<br><br>To illustrate groups let's consider calculating the mean age of FME users. Don't worry - I'll be discrete (ha ha)! The default group for the calculation includes <strong>all</strong> FME users.
<br><br>But you could instead divide everyone up on into men and women, creating two groups, and calculate average age per gender. Or you could divide everyone into their nationality, and calculate average age per country.
<br><br>This is the same as having a gender (or nationality) attribute in a dataset and selecting that in an FME group-by parameter.
</span>
</td>
</tr>
</table>

---

Here, a LineOnLineOverlayer transformer is being used to intersect a number of line features. The selected Group-By attribute is *Name*:

![](./Images/Img2.034.GroupByParameter.png)

FME creates a series of groups for overlaying, where the features in each group share the same value for the *Name* attribute. The practical outcome is that intersection takes place only where line features share the same name.

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
Let's see if you've picked up the idea of what a group-based transformation is.
<br><br>Which of the following transformers do you think is "group-based"? Feel free to use Workbench to help you answer this question.
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=4&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. StringFormatter</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=4&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. Clipper</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=4&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. Rotator</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=2&question=4&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. AttributeRounder</a>
</span>
</td>
</tr>
</table>

# Data Inspection Using FME Workbench #
To assist in inspecting data, Workbench can route data to the FME Data Inspector from individual transformers.

 
## Using an Inspector Transformer ##
An ***Inspector*** is a Workbench transformer – with its own distinctive look and style – that causes data entering it to be directed to FME Data Inspector, even mid-translation.

An Inspector - like any transformer - can be applied at any point in a translation and does not prevent the data being output to the writer. It also lets a user be selective about which features should be inspected:

![](./Images/Img2.035.InspectorTransformer.png)

In this case it's also a form of parallel streams, since the data is duplicated, but that does not need to be the case.


## Placing an Inspector Transformer ##
The best, and simplest way to apply an Inspector is to right-click the output port of an object in a workspace and select the Connect Inspector option.

Here the user right-clicks the Buffered port of a Bufferer transformer and chooses the option Connect Inspector:

![](./Images/Img2.036.RightClickAddInspector.png)

Notice that an Inspector is named automatically using the transformer and output port names. Here it will be "Bufferer_Buffered". This helps to identify the data from this Inspector (as opposed to any others) in the FME Data Inspector.

Note that the Inspector transformer only opens the FME Data Inspector when there are features to view. If there are zero features, then the Data Inspector will not open!

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
Inspectors are not useful for a workspace that is to be put into production, especially on FME Server. That's because an FME Server engine doesn't have to capability to open a Data Inspector. For that reason, authors of FME Server workspaces tend to use a Logger transformer instead of an Inspector.
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
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Mr. E. Dict, (Attorney of FME Law) says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Pursuant to clause d30 (section 43) in your training course agreement, you are required to re-open the workspace from the previous example and add Inspector transformers to practice using this functionality.
<br><br><img src="./Images/Img2.037.MultipleInspectors.png">
</span>
</td>
</tr>
</table>

# Coordinate System Transformation #
To be located in a particular space on the Earth's surface, the majority of spatial data is related to a particular spatial reference.

Some users call this location of data a "projection," but projection is just one component of what we call a **coordinate system**. A coordinate system includes *projection*, *datum*, *ellipsoid*, *units*, and sometimes a *quadrant*.


## Coordinate System Settings ##

Each reader and writer within FME can be assigned a coordinate system. That coordinate system is set in the Navigator window of Workbench, or in the Generate Workspace dialog.

Like the source schema, the reader coordinate system is ***"what we have"*** and the writer coordinate system is ***"what we want"***. Here the source coordinate system has been defined as UTM83-10 and the destination as BCALB-83:

![](./Images/Img2.038.CoordinateSystemParameters.png)

Each feature processed by the reader is tagged with the coordinate system defined in its parameter.

When a feature arrives at a writer, if it is tagged with a different coordinate system to what is defined for that writer, then FME automatically reprojects the data, so that the output is in the correct location.

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
Once tagged with a coordinate system, each feature retains this throughout the translation; FME knows what coordinate system it belongs to at all times.
<br><br>This is important when carrying out geometric transformations (like calculating area) or when reading multiple datasets that belong to different coordinate systems (yes, FME will handle that).
</span>
</td>
</tr>
</table>

---

## Automatic Detection of Coordinate Systems ##
It's not always necessary to set the coordinate system parameters manually. Some data formats (for example Esri Shapefile) are capable of storing information about the coordinate system in which they are held, and FME will retrieve this information where it can.

![](./Images/Img2.039.CoordinateSystemParametersUnset.png)

Here, because the reader coordinate system is marked &lt;not set&gt;, FME will try to determine the coordinate system from the source dataset. If it can't, then the feature will be tagged with a coordinate system of &lt;unknown&gt;.

There are a number of reprojection scenarios that may occur depending on the combination of coordinate system (CS) information available:

<table style="border: 0px">

<tr>
<td style="font-weight: bold;text-align:center;">Dataset CS</td>
<td style="font-weight: bold;text-align:center;">Reader CS</td>
<td style="font-weight: bold;text-align:center;">Writer CS</td>
<td style="font-weight: bold;text-align:center;">Reprojection</td>
</tr>

<tr>
<td style="text-align:center;">N</td>
<td style="text-align:center;">Y</td>
<td style="text-align:center;">Y</td>
<td>Reprojects from Reader CS to Writer CS</td>
</tr>

<tr>
<td style="text-align:center;">Y</td>
<td style="text-align:center;">N</td>
<td style="text-align:center;">Y</td>
<td>Reprojects from Dataset CS to Writer CS</td>
</tr>

<tr>
<td style="text-align:center;">N</td>
<td style="text-align:center;">N</td>
<td style="text-align:center;">Y</td>
<td>Error: Cannot reproject without Dataset or Reader CS</td>
</tr>

<tr>
<td style="text-align:center;">Y</td>
<td style="text-align:center;">Y</td>
<td style="text-align:center;">Y</td>
<td>Reprojects from Reader CS to Writer CS</td>
</tr>

</table>

If the coordinate system is not set on the writer, then no reprojection will take place unless the output format requires it. For example the KML format requires data to be in Latitude/Longitude. If neither the source dataset or the reader coordinate system is defined then the translation will fail.

# Module Review #
This module introduced you to the concept of Data Transformation and explained how to use FME Workbench for more than just quick translations.

 
## What You Should Have Learned from this Module ##
The following are key points to be learned from this session:

### Theory ###

- A ***schema*** describes a dataset’s structure, including its feature types, attributes, and geometries.
- ***Schema editing*** is the act of editing the destination schema to better define what is required out of the translation.
- The act of joining the source schema to the destination is called ***schema mapping***. Differences between the two schemas lead to ***structural transformation***.
- ***Content transformation*** is the modifying of data content during a translation. In FME Workbench data transformation is carried out using objects called ***transformers***.
- ***Groups*** can be created using the Group-By option in a transformer’s parameters.
- Splitting data into multiple streams creates multiple copies and not a division of data. Bringing together multiple streams combines the data, rather than merges it.


### FME Skills ###

- The ability to edit a writer schema
- The ability to restructure data by mapping a reader to a writer schema, both manually and through transformers
- The ability to locate transformers in Workbench and use them to transform data content
- The ability to set transformer parameters in either the Parameter Editor or transformer dialogs
- The ability to define feature groups using the Group-By option
- The ability to reproject data using Workbench


### Further Reading ###

For further reading why not browse **[articles tagged with Transformation](http://blog.safe.com/tag/transformation/)** on our blog? 

# Questions #

Here are the answers to the questions in this chapter.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Mr Flibble says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
The most common format translation defined with FME is from Esri Shapefile to which format?
<br><br><span style="color:lightslategrey">1. Esri Geodatabase</span>
<br><span style="color:lightslategrey">2. AutoCAD DXF/DWG</span>
<br><span style="color:lightslategrey">3. Google KML</span>
<br><span style="font-weight:bold">4. Esri Shapefile</span>
<br><br>Yes! The most common translation is from Esri Shapefile TO Esri Shapefile! It just proves how many people use FME for data transformation instead of format translation.
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
Which three colours represent checked, need checking, and unset parameters on transformer objects?
<br><br><span style="font-weight:bold">1. blue, yellow, red</span>
<br><span style="color:lightslategrey">2. green, yellow, red</span>
<br><span style="color:lightslategrey">3. red, green, blue</span>
<br><span style="color:lightslategrey">4. green, blue, yellow</span>
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
If I use a transformer to remove irregularities (like self-intersecting loops) in the boundary of a polygon, what type of transformation is it? 
<br><br><span style="color:lightslategrey">1. Structural Transformation of attributes</span>
<br><span style="color:lightslategrey">2. Structural Transformation of geometry</span>
<br><span style="color:lightslategrey">3. Content Transformation of attributes</span>
<br><span style="font-weight:bold">4. Content Transformation of geometry</span>
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
Which of the following transformers do you think is "group-based"?
<br><br><span style="color:lightslategrey">1. StringFormatter</span>
<br><span style="font-weight:bold">2. Clipper</span>
<br><span style="color:lightslategrey">3. Rotator</span>
<br><span style="color:lightslategrey">4. AttributeRounder</span>
<br><br>The StringFormatter, Rotator, and AttributeRounder can all operate on one feature at a time. For example, you can rotate one feature independently of any other. However, the Clipper can only operate on a group of features. The "Group-By" parameter is a huge clue to identifying group-based transformers!
</span>
</td>
</tr>
</table>




<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 1</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Grounds Maintenance Project - Schema Editing</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">City Parks (MapInfo TAB)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Calculate the size and average size of each park in the city, to use in Grounds Maintenance estimates for grass cutting, hedge trimming, etc.</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Structural Transformation, Schema Editing</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex1-Complete.fmw</td>
</tr>

</table>


You have just landed a job as technical analyst in the GIS department of your local city.

The team responsible for maintaining parks and other grassed areas needs to know the area and facilities of each park in order to plan their budget for the upcoming year. You have been assigned to this project and will use FME to provide a dataset of this information.

The first step in this example is to rename existing attributes and create new ones in preparation for the later area calculations.


<br>**1) Start Workbench**
<br>Use the Generate Workspace dialog to create a workspace using these parameters:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">MapInfo TAB (MITAB)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\Parks\Parks.tab</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Format</td>
<td style="">MapInfo TAB (MITAB)</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Dataset</td>
<td style="">C:\FMEData2018\Output\Training</td>
</tr>

</table>

Yes! Here we write back to the same format of data we are reading from! You may click the Parameters buttons in the Generate Workspace dialog to check the reader/writer parameters, but none of them need changing in this exercise. Note that the writer needs only a folder and not a specific file name.


<br>**2) Rename Feature Type**
<br>FME creates a workspace where the destination schema matches the source. However, the end user of the data has requested parts of the schema are cleaned up.

Inspect the writer feature type parameters. Click in the field labelled Table Name (remember this label is format-specific and in MapInfo we deal with "tables") and change the name from Parks to ParksMaintenanceData:

![](./Images/Img2.200.Ex1.WriterGeneralSchemaEdited.png)


<br>**3) Update Attributes**
<br>Now inspect the user attributes. They will look like this:

![](./Images/Img2.201.Ex1.WriterAttributeSchema.png)

These must be cleaned up so that unnecessary information is removed. Other attributes need to be updated and some extra ones added to store the calculation results. So carry out the following actions:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Delete Attribute</td>
<td style="">RefParkID</td>
</tr>

<tr>
<td style="font-weight: bold">Delete Attribute</td>
<td style="">DogPark</td>
</tr>

<tr>
<td style="font-weight: bold">Delete Attribute</td>
<td style="">Washrooms</td>
</tr>

<tr>
<td style="font-weight: bold">Delete Attribute</td>
<td style="">SpecialFeatures</td>
</tr>

<tr>
<td style="font-weight: bold">Rename Attribute</td>
<td style="">from: NeighborhoodName</td>
<td style="">to: Neighborhood</td>
</tr>

<tr>
<td style="font-weight: bold">Change Type (VisitorCount)</td>
<td style="">from: smallint</td>
<td style="">to: integer</td>
</tr>

<tr>
<td style="font-weight: bold">Add Attribute</td>
<td style="">ParkArea</td>
<td style="">type: Float</td>
</tr>

<tr>
<td style="font-weight: bold">Add Attribute</td>
<td style="">AverageParkArea</td>
<td style="">type: Float</td>
</tr>

</table>

...and click the Parameter Editor "Apply" button. The attribute list should now look like this:

![](./Images/Img2.202.Ex1.WriterAttributeSchemaEdited.png)

Now when the workspace is run the output will be named ParksMaintenanceData.tab and will contain an updated attribute schema.


<br>**4) Un-Expose Source Attributes**
<br>The workspace will now look like this:

![](./Images/Img2.203.Ex1.EditedSchemaOnCanvas.png)

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
Objects on the canvas can be resized (as in the above screenshot) if the feature type name or attribute names are too large to be displayed properly at the default size. The brown markers around the feature types are called <strong>bookmarks</strong>. They too can be resized to better fit their contents.
</span>
</td>
</tr>
</table>

---

Notice there are several source attributes that are not going to be used in the workspace or sent to the output. We can tidy the workspace by hiding these.

Inspect the User Attributes tab on the reader feature type parameters. It will look like this:

![](./Images/Img2.204.Ex1.ReaderAttrSchema.png)

Uncheck the check box for the following attributes, which we do not need:

- RefParkID
- Washrooms
- SpecialFeatures

This is basically the list of attributes we deleted, except for DogParks, which we will make use of in the translation.

Click Apply/OK to confirm the changes.


<br>**5) Save the Workspace**
<br>Save the workspace – it will be completed in further examples. It should now look like this:

![](./Images/Img2.205.Ex1.EditedSchemaOnCanvas.png)


---
<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Police Chief Webb-Mapp says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Some Writer attributes (ParkArea and AverageParkArea) have red connection arrows because there is nothing yet to map to them, while another (Neighborhood) is just unconnected. 
<br><br>That's OK. I'll let you off with a caution if you promise to connect them later. You can still run this workspace just to see what the output looks like anyway.
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
<ul><li>Edit the attributes on a writer schema</li>
<li>Edit the output layer name on a writer schema</li>
<li>Hide attributes on a reader schema</li></ul>
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
<span style="color:white;font-size:x-large;font-weight: bold">Grounds Maintenance Project - Structural Transformation</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">City Parks (MapInfo TAB)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Calculate the size and average size of each park in the city, to use in Grounds Maintenance estimates for grass cutting, hedge trimming, etc.</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Structural Transformation with Transformers</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex2-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex2-Complete.fmw<br>C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex2-Complete-Advanced.fmw</td>
</tr>

</table>


Let's continue your work on the grounds maintenance project.

In case you forgot, the team responsible for maintaining parks and other grassed areas needs to know the area and facilities of each park in order to plan their budget for the upcoming year. 

In this part of the project we’ll filter out dog parks from the source data (as these have a different scale of maintenance costs) and write them to the log window. We'll also handle the renamed attribute NeighborhoodName.


<br>**1) Start FME Workbench**
<br>Start FME Workbench and open the workspace from the previous exercise. Alternatively you can open
C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex2-Begin.fmw.


<br>**2) Add Transformer**
<br>Let's first handle the source attribute NeighborhoodName, which was renamed Neighborhood on the writer but not yet connected. 

We could do this by simply drawing a connection, but it's generally better to use a transformer. There are two transformers we could use. One is called the AttributeRenamer and the other - which we shall use here - is the AttributeManager.

Therefore click on the feature connection from reader to writer feature type:

![](./Images/Img2.206.Ex2.SelectedFeatureConnection.png)

Start to type the phrase "AttributeManager". This is how we can place a transformer in the workspace. As you type, FME searches for a matching transformer. When the list is short enough for you to see the AttributeManager, select it from the dialog (double-click on it):

![](./Images/Img2.207.Ex2.QuickAddAttrManager.png)

This will place an AttributeManager transformer like so:

![](./Images/Img2.208.Ex2.AttrManagerOnCanvas.png)

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
For a great tip on adding transformers see #5 in our list of <strong><a href="http://blog.safe.com/2014/10/fmeevangelist128/">The Top Ten FME Tips of All Time!</a></strong>
</span>
</td>
</tr>
</table>

---

<br>**3) Set Parameters**
<br>View the AttributeManager parameters (either its dialog or in the Parameter Editor window). It will look like this:

![](./Images/Img2.209.Ex2.AttrManagerParameters.png)

Notice that all of the attributes on the stream in which it is connected will automatically appear in the dialog. 

Where the Input Attribute field is set to NeighborhoodName, click in the Output Attribute field. Click on the button for the drop-down list and in there choose Neighborhood as the new attribute name to use:

![](./Images/Img2.210.Ex2.AttrManagerEditingAttr.png)

In response the Action field will change to read *Rename*.

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
Neighborhood only appears in the list because it already exists on the writer schema. If we had done this step before editing the writer schema, we would have had to manually enter the new attribute name in this dialog.
</span>
</td>
</tr>
</table>

---

Click OK to close the dialog. Now in the Workbench canvas window you will see the Neighborhood attribute is flagged with a green arrow, to confirm that a value is being provided to that attribute.

![](./Images/Img2.211.Ex2.AttrManagerAfterEditing.png)


<br>**4) Add Transformer**
<br>Now we should remove dog parks from the data, because these have their own set of costs.

This can be done with a Tester transformer. Click on the connection from the AttributeManager output port to the ParksMaintenanceData feature type on the Writer.

Start typing the word Tester. When you spot the Tester transformer double-click on it to add one to the workspace. After tidying up the layout of the canvas, the workspace will now look like this:

![](./Images/Img2.212.Ex2.TesterOnCanvas.png)

Notice that the Passed output port is the one connected by default.


<br>**5) Set Parameters**
<br>Inspect the parameters for the Tester transformer. Click in the Left Value field and from there click the down arrow and choose Attribute Value > DogPark:

![](./Images/Img2.213.Ex2.TesterAttrSelection.png)

For the Right Value click into the field and type the value N. The operator field should be filled in automatically as the equals sign (=), which is what we want in this case.

![](./Images/Img2.214.Ex2.TesterTestClause.png)

Click OK to accept the values and close the dialog.

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
The test is for DogParks=N because we want to keep those features, and it is the Passed port that is connected. If the test was DogParks=Y then the Failed port would be the one to connect.
</span>
</td>
</tr>
</table>

---

<br>**6) Add Transformer**
<br>We are now filtering out dog parks from our data, using a test on an attribute value. The question is, what should we do with the features we have filtered out? There are many things we could do, but for now we'll simply log the information to the FME log window.

To do this, right-click on the Tester Failed port and choose the option Connect Logger:

![](./Images/Img2.215.Ex2.TesterConnectLogger.png)

A Logger transformer will be added to the workspace. This will record all incoming features to the log window:

![](./Images/Img2.216.Ex2.WorkspaceWithLogger.png)

Loggers inserted by this method are named after – and reported in the log with – the output port they are connected to, here Tester_Failed.


<br>**7) Run Workspace**
<br>Save and run the workspace. It is not yet complete but running it will prove that everything is working correctly up to this point.


---

<!--Advanced Exercise Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Advanced Exercise</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Readers and writers on the canvas had a bookmark object added around them automatically. You can do the same to the transformers by selecting them all and either clicking Bookmark on the toolbar or pressing the Ctrl+B keys. Give the bookmark a name of your choice that describes the actions being carried out. 
<br><br>A bookmark is an example of what we call <strong>Best Practice</strong> in FME.
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
<ul><li>Add transformers to a workspace</li>
<li>Carry out schema mapping with the AttributeManager transformer</li>
<li>Filter data using the Tester transformer</li>
<li>Record data using the Logger transformer</li>
<li>Add bookmarks to a workspace</li></ul>
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
<span style="color:white;font-size:x-large;font-weight: bold">Grounds Maintenance Project - Calculating Statistics</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">City Parks (MapInfo TAB)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Calculate the size and average size of each park in the city, to use in Grounds Maintenance estimates for grass cutting, hedge trimming, etc.</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Content Transformation. Schema Mapping</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex3-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex3-Complete.fmw<br>C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex3-Complete-Advanced.fmw</td>
</tr>

</table>


Let's continue your work on the grounds maintenance project.

In case you forgot, the team responsible for maintaining parks and other grassed areas needs to know the area and facilities of each park in order to plan their budget for the upcoming year. 

In this part of the project we’ll calculate the size and average size of each park, and ensure that information is correctly mapped to the destination schema.


<br>**1) Start Workbench**
<br>Start Workbench (if necessary) and open the workspace from Exercise 2. Alternatively you can open C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex3-Begin.fmw


<br>**2) Add an AreaCalculator Transformer**
<br>To measure the area of each park feature, an AreaCalculator transformer must be used. “Calculator” is the term for when FME computes new attribute values.

Click onto the connection between Tester:Passed port and the writer feature type *ParksMaintenanceData*. Start typing the letters “areac”. You will see the Quick Add list of matching transformers appear beneath.

Select the transformer named AreaCalculator by double-clicking it:

![](./Images/Img2.217.Ex3.QuickAddAreaCalculator.png)


<br>**3) Add a StatisticsCalculator Transformer**
<br>Using the same method, place a StatisticsCalculator transformer between the AreaCalculator:Output port and the *ParksMaintenanceData* feature type.

**BUT!** Do not click anything else yet! The transformer will now look like this:

![](./Images/Img2.218.Ex3.StatsCalcDefaultConnections.png)

By default the Summary port has been connected, and we need the Complete port connected instead. But notice the little pop-up icons over the top. Click the right-hand icon (the one with the ? character). This pops up a further list of ports:

![](./Images/Img2.219.Ex3.StatsCalcPopUpButtons.png)

Click on the Summary port entry to disconnect that, and then on the Complete port entry to connect that:

![](./Images/Img2.220.Ex3.StatsCalcPopUpButtonsEdited.png)

Notice how the connection has been changed from the incorrect Summary port to the correct Complete port.

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
These pop-up menus are a great help in schema mapping and other feature connections.
</span>
</td>
</tr>
</table>

---

The latter part of the workspace now looks like this:

![](./Images/Img2.221.Ex3.StatsCalcInCanvas.png)


<br>**4) Check AreaCalculator Settings**
<br>Inspect the AreaCalculator parameters:

![](./Images/Img2.222.Ex3.AreaCalcParameters.png)

The default settings cause the calculated value to be placed into an attribute called _area. However, the *ParksMaintenanceData* schema requires an attribute called ParkArea, so change this parameter to create the correct attribute:

![](./Images/Img2.223.Ex3.AreaCalcEditedParameters.png)

Once you click OK or Apply notice that the attribute on the writer feature type is now flagged as connected.


<br>**5) Check StatisticsCalculator Settings**
<br>A red icon indicates the StatisticsCalculator has parameters that need to be defined.

Inspect the StatisticsCalculator transformer's parameters. The attribute to analyze is the one containing the calculated area; so select ParkArea:

![](./Images/Img2.224.Ex3.StatsCalcParameters1.png)

Examine what the default setting is for an attribute name for average (mean) park size. Currently it doesn't match the *ParksMaintenanceData* schema, which requires an attribute named AverageParkArea.

Change the attribute from _mean to AverageParkArea. For Best Practice reasons, delete/unset any StatisticsCalculator output attributes that aren't required (for example _range and _stdev).

![](./Images/Img2.225.Ex3.StatsCalcParameters2.png)


<br>**6) Run the Workspace**
<br>Add another bookmark if you wish, run the workspace, and inspect the result of the translation using the FME Data Inspector:

![](./Images/Img2.226.Ex3.DITableView.png)

The Table View window shows the area of each park and the average area of all parks.


<br>**7) Save the Workspace**
<br>Save the workspace – it will be completed in further examples.


---

<!--Advanced Exercise Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Advanced Exercise</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Notice that the numbers in the Table View show the results have been calculated to 12 decimal places. This is in excess of the precision that you require. As an advanced task - if you have time - use the AttributeRounder transformer to reduce the values to just 2 decimal places.
<br><br>If you wish, you can also calculate the smallest, largest, and total park areas; but don't forget to add them to the writer schema if you want them to appear in the output.
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
<ul><li>Carry out content transformation with transformers (AreaCalculator, StatisticsCalculator)</li>
<li>Manage transformer connections using pop-up buttons</li>
<li>Use transformer parameters to create attributes that match the writer schema</li></ul> 
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
<span style="color:white;font-size:x-large;font-weight: bold">Grounds Maintenance Project - Labelling Features</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">City Parks (MapInfo TAB)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Calculate the size and average size of each park in the city, to use in Grounds Maintenance estimates for grass cutting, hedge trimming, etc.</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Content transformation with parallel transformers</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex4-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex4-Complete.fmw<br>C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex4-Complete-Advanced.fmw</td>
</tr>

</table>


Let's continue your work on the grounds maintenance project.

In this part of the project we’ll create a label for each park and write it to a new output layer. This is best done using a parallel stream of data.


<br>**1) Start Workbench**
<br>Start Workbench (if necessary) and open the workspace from Exercise 3. Alternatively you can open C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex4-Begin.fmw

The previous exercise measured park areas with the AreaCalculator. Now we are asked to add this information as labels to the output dataset.

This can be achieved using the LabelPointReplacer transformer.


<br>**2) Create New Writer Feature Type**
<br>Because we want to write label features to a separate layer (table) in the output, we need to create another feature type object on the canvas. There is more about this in a later chapter, but for now right-click the writer feature type and choose the option Duplicate. This creates a new feature type (layer) in the output dataset.

![](./Images/Img2.227.Ex4.DuplicateFeatureType.png)


Now clean up this feature type's schema. View the feature type's dialog and rename the new type to ParkLabels. In the User Attributes tab delete all of the existing user attributes.


<br>**3) Place a StringConcatenator Transformer**
<br>Click onto a blank area of canvas. Type "StringConcatenator" to add a transformer of this type.

Connect it to the Complete port of the StatisticsCalculator by dragging a second connection from there to the new transformer.

![](./Images/Img2.228.Ex4.StringConcatenatorCanvas.png)

Make a new connection from the StringConcatenator to the new feature type.

<br>**4) Check Transformer Parameters**
<br>View the parameters for the StringConcatenator transformer. There are both basic and advanced dialogs, and the basic one looks like this:

![](./Images/Img2.229.Ex4.StringConcatenatorEmptyParams.png)

Enter *LabelText* as the name for the new attribute to create.

In the String Parts section, set the following four parts:

<table>
<th>String Type</th><th>String Value</th>
<tr><td>Attribute Value</td><td>ParkName</td></tr>
<tr><td>New Line</td><td></td></tr>
<tr><td>Attribute Value</td><td>ParkArea</td></tr>
<tr><td>Constant</td><td> sq metres</td></tr>
</table>

Be sure to include a space character in the constant before "sq metres".

![](./Images/Img2.230.Ex4.StringConcatenatorParams.png)

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
You may find it quicker to switch to the Advanced editor dialog and enter the content directly:
<br>@Value(ParkName)
<br>@Value(ParkArea) sq metres
</span>
</td>
</tr>
</table>

---

<br>**5) Place a LabelPointReplacer Transformer**
<br>Click onto the connection between StringConcatenator:Output and the ParkLabels feature type. Type "LabelPointReplacer" to add a transformer of this type.

The new transformer will be added and automatically connected between those two objects.

![](./Images/Img2.231.Ex4.LabelPointReplacerCanvas.png)


<br>**6) Check LabelPointReplacer Parameters**
<br>Inspect the LabelPointReplacer parameters. 

Firstly click the dropdown arrow to the right of the Label parameter:

![](./Images/Img2.232.Ex4.LabelEditDialog.png)

Select Attribute Value &gt; LabelText to select the label previously defined in the StringConcatenator.

Now click in the Label Height field and type 25 (that’s 25 working units, which in this case is metres).

The “Always Rotate Label” parameter can be left to its default value.

![](./Images/Img2.233.Ex4.LabelPointReplacerParameters.png)

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
Many parameter fields (like Label Height) can be set either as a constant value (by typing it in) or set to an attribute by clicking the drop down arrow and selecting Attribute Value.
<br><br>And - as you'll see shortly - it's also possible to construct a parameter value directly inside the transformer settings
</span>
</td>
</tr>
</table>

---

<br>**7) Run the Translation**
<br>Add another bookmark if you wish, run the translation, and inspect the output.

Notice that the output is in two layers in two files. Use the FME Data Inspector to open both output files in the same view.

![](./Images/Img2.234.Ex4.LabelsInDIView.png)
<br><span style="font-style:italic;font-size:x-small">Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC-BY-3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC-BY-SA</a>.

Save the workspace – it will be completed in further examples.

![](./Images/Img2.235.Ex4.WorkspaceWithLabelPointReplacer.png)

---

<!--Advanced Exercise Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Advanced Exercise</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Now you know how to create a new feature type (layer) in the output, how to test data, and how to use parallel streams, why not try this task: Identify which parks are smaller than average and which parks are larger than average, and write them out to different feature types.
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
<ul><li>Create a new writer feature type</li>
<li>Use multiple streams of transformers in a single workspace</li>
<li>Use the StringConcatenator to construct a string for use elsewhere</li>
<li>Use an attribute as the value of a transformer's parameter</li></ul>
</span>
</td>
</tr>
</table>

<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 5</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Grounds Maintenance Project - Neighborhood Averages</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">City Parks (MapInfo TAB)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Calculate the size and average size of each park in the city, to use in Grounds Maintenance estimates for grass cutting, hedge trimming, etc.</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Group-By Processing</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex5-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex5-Complete.fmw</td>
</tr>

</table>



Let's continue your work on the grounds maintenance project.

The parks team has decided that they do not want the average area of park for the city as a whole. Instead they want the average size of park in each neighborhood; so let's do that for them.


<br>**1) Start Workbench**
<br>Start Workbench (if necessary) and open the workspace from Exercise 4. Alternatively you can open C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex5-Begin.fmw


<br>**2) Set Group-By in StatisticsCalculator**
<br>This is a really simple task to do. View the parameters for the StatisticsCalculator transformer and click the 'browse' button next to the Group By parameter. Select the attribute called Neighborhood:

![](./Images/Img2.236.Ex5.StatsCalcGroupBy.png)

Click OK/Apply to apply the changes to the transformer.


<br>**3) Run the Workspace**
<br>Save and then run the workspace.

Inspect the output data in the Table View window of the FME Data Inspector.

You should see that each neighborhood now has its own value for AverageParkArea:

![](./Images/Img2.237.Ex5.StatsCalcGroupByDI.png)

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
<ul><li>Use the group-by parameter in FME transformers</li></ul>
</span>
</td>
</tr>
</table>


<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 6</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Grounds Maintenance Project - Data Reprojection</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">City Parks (MapInfo TAB)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Calculate the size and average size of each park in the city, to use in Grounds Maintenance estimates for grass cutting, hedge trimming, etc.</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Data reprojection</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex6-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex6-Complete.fmw<br>C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex6-Complete-Advanced.fmw</td>
</tr>

</table>

Let's continue your work on the grounds maintenance project.

The parks team has decided that the output data should be in an Albers Equal Area projection (coordinate system = BCALB-83). They think it will take ages to set this up! We'll show them differently...


<br>**1) Start Workbench**
<br>Start Workbench (if necessary) and open the workspace from Exercise 5. Alternatively you can open C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex6-Begin.fmw


<br>**2) Edit Reader Coordinate System**
<br>In the Navigator window locate the Parks [MITAB] reader, and expand its list of settings.

Locate the setting labelled ‘Coordinate System’. The original value should be &lt;not set&gt;:

![](./Images/Img2.238.Ex6.CoordSysParamNavigator.png)

Double-click the reader Coordinate System parameter to open an edit dialog.

In the Coordinate System field enter the name UTM83-10 or select it from the Coordinate System Gallery by selecting "More Coordinate Systems..." from the bottom of the drop-down list:

![](./Images/Img2.239.Ex6.CoordSysParamEditDialog.png)

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
Remember, when a reader’s Coordinate System parameter is defined as &lt;not set&gt; FME will automatically try to determine the correct coordinate system from the dataset itself.
<br><br>When the source dataset is in a format that stores coordinate system information (as it does in this example) you can safely leave the parameter unset. So this step isn’t really necessary.
<br><br>However, you MUST set this parameter when you wish to reproject source data that does not store coordinate system information; otherwise an error will occur in the translation.
</span>
</td>
</tr>
</table>

---

<br>**3) Edit Destination Coordinate System**
<br>Now locate the coordinate system setting for the destination (writer) dataset.

Again the current value should be the default of &lt;not set&gt;.

Double-click the parameter and enter the coordinate system name BCALB-83 or select it from the Coordinate System Gallery by selecting "More Coordinate Systems..." from the bottom of the drop-down list.

The Navigator window will now look like this:

![](./Images/Img2.240.Ex6.CoordSysParamsSet.png)


<br>**4) Run the Workspace**
<br>Save and then run the workspace.

In the log file you should be able to find:

<pre>
FME Configuration: Source coordinate system for reader MITAB_1[MITAB] set to `UTM83-10'
FME Configuration: Destination coordinate system set to `BCALB-83'
</pre>


<br>**5) Inspect the Output**

Open the newly reprojected dataset and query a feature. The Feature Information window should report that the data is now in BCALB-83. Optionally, click on the coordinate system name in that window; a new dialog will open to display all of the coordinate system parameters.

![](./Images/Img2.241.Ex6.CoordSysResultInDI.png)

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
If the background map is activated when a dataset is opened then the contents of that dataset are automatically reprojected to Spherical Mercator to match the background map. If you wish to see the data as it appears in its own coordinate system, then use Tools > FME Options to turn off background maps <strong>before</strong> opening the source dataset.
</span>
</td>
</tr>
</table>

---

<!--Advanced Exercise Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Advanced Exercise</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Instead of using the reader/writer parameters in the Navigator window, why not try this exercise using the Reprojector (or CSMapReprojector) transformer? Where should the transformer be placed in the workspace and why is this important?
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
<ul><li>Use Coordinate System parameters to reproject spatial data</li>
<li>Query features in the Data Inspector to inspect coordinate system information</li></ul>
</span>
</td>
</tr>
</table>



<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 7</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Voting Analysis Project</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Election Mapping (GML)<br>Election Statistics (Microsoft Excel)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Map statistics of voting patterns</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Data Transformation</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex7-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex7-Complete.fmw<br>C:\FMEData2018\Workspaces\DesktopBasic\Transformation-Ex7-Complete-Advanced.fmw</td>
</tr>

</table>


In a break from grounds maintenance projects, the municipal Elections Officer has heard about your skills and asked for help identifying voting divisions that had a low turnout at the last election, or divisions where there were difficulties understanding the voting process.

He asks for your help and you suggest the results should be presented in Google Earth, so that staff can view them without having to use a full GIS system.


<br>**1) Inspect Data** 
<br>Start the FME Data Inspector and open the two datasets we will be using:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">GML (Geography Markup Language)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\Elections\ElectionVoting.gml</td>
</tr>

</table> 

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">Microsoft Excel</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\Elections\ElectionResults.xls</td>
</tr>

</table>

Notice that both datasets have a Division attribute by which to identify each voting division (area). The Excel data is non-spatial but has a set of other voting attributes:

- **Voters**: Number of registered voters
- **Votes**: Number of voters who voted
- **Blanks**: Number of voters who left a blank or spoiled vote
- **OverVotes**: Number of voters who voted for too many candidates
- **UnderVotes**: Number of votes not cast

The OverVotes and UnderVotes attributes are an indicator of how well the voting process was understood. Each voter gets to vote for up to 10 candidates (out of 30). 

OverVotes are those voters who voted for more than ten candidates. UnderVotes are the number of votes that could have been cast, but were not; for example, the voter only voted for four candidates instead of ten, giving six undervotes.


<br>**2) Start Workbench**
<br>Start Workbench and open the starting workspace. It already has readers and writers added to handle the data; all we need to do is carry out the transformation:

![](./Images/Img2.242.Ex7.VotingProjectStartingWorkspace.png)


<br>**3) Add FeatureJoiner**
<br>The first task is to join the statistical election data onto the actual features. We'll use a FeatureJoiner transformer to do this. A FeatureJoiner is a way to join or merge features together. In this case we are merging election result records onto election boundary features.

Add a FeatureJoiner transformer. Connect the VotingDivisions data to the Left port, and the Councillors (result) data to the Right port:

![](./Images/Img2.243.Ex7.FeatureJoinerOnCanvas.png)

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

<br>**4) Set Parameters**
<br>View the FeatureJoiner parameters. Because we want all of the voting division features we will do a Left join; therefore set the Join Mode to Left.

For both the Left and Right join fields, click in the field and choose the Division attribute from the drop-down list. This is the common key by which our data is joined:

![](./Images/Img2.244.Ex7.FeatureJoinerParameters.png)


<br>**5) Add Inspector Transformer**
<br>Add an Inspector transformer after the FeatureJoiner:Joined output port. Run the workspace, ignoring any warning or log message that reports Unexpected Input.

Examine the data in the FME Data Inspector to ensure all division polygons now include a set of attribute data copied from the Excel spreadsheet:

![](./Images/Img2.245.Ex7.MergedDataInDI.png)


<br>**6) Add ExpressionEvaluator**
<br>Now that we have the numbers we need, we can start to calculate some statistics. To do this we'll use an ExpressionEvaluator transformer to first calculate voter turnout percentage for each division. 

Place an ExpressionEvaluator transformer after the FeatureJoiner - connect it to the FeatureJoiner:Joined output port. View the transformer's parameters. Set the New Attribute to Turnout (to match what we have on the destination schema):

![](./Images/Img2.246.Ex7.ExpressionEvaluatorNewAttr.png)

In the expression window set the expression to:

![](./Images/Img2.247.Ex7.ExpressionEvaluatorMathsEditor.png)

<pre>
(@Value(Votes)/@Value(Voters))*100
</pre>

You don't need to type this in - the @Value(Votes) and @Value(Voters) part can be obtained by double-clicking that attribute in the list to the left.

If you wish, you can reconnect an Inspector and re-run the translation, to see the result.


<br>**7) Add ExpressionEvaluator**
<br>Using a similar technique, add a second ExpressionEvaluator to calculate the number of UnderVotes per voter and put it in an attribute that matches the output schema (for example UnderVoting). The expression will be something like:

<pre>
@Value(UnderVotes)/@Value(Voters)
</pre>

***NB:*** *This isn't a percentage, like the previous calculation.*

Feel free to add a bookmark around the two ExpressionEvaluator transformers.


<br>**8) Add AttributeRounder**
<br>It's a bit excessive to calculate our statistics to 13 decimal places or more. We should truncate these numbers a bit. To do this place an AttributeRounder transformer after the second ExpressionEvaluator.

For the parameters, under Attributes to Round select the newly created Turnout and UnderVoting attributes. Set the number of decimal places to 2:

![](./Images/Img2.248.Ex7.AttributeRounderParameters.png)

Again, run the workspace to check the results if you wish.


<br>**9) Add Annotation**
<br>It doesn't make sense to add a bookmark to the AttributeRounder by itself, so instead right-click the transformer and choose the option to Attach Annotation. 

This will add a label to the transformer. Edit the content to say something like "Round the Turnout and Undervoting to two decimal places":

![](./Images/Img2.249.Ex7.AttributeRounderOnCanvas.png)


<br>**10) Connect Schema**
<br>For the final step let's connect the AttributeRounder to the output schema. Simply make connections from the AttributeRounder to both writer feature types:

![](./Images/Img2.250.Ex7.AttributeRounderSchemaConnections.png)

Run the workspace and examine the output in Google Earth to prove it has the correct attributes and is in the correct location.

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
So this is obviously a form of parallel streams of data, but left until the last step. An alternative layout would be to split the data after the FeatureJoiner, like so:
<br><br><img src="./Images/Img2.251.Ex7.AlternativeLayout.png">
<br><br>There's no difference in the output so the only consideration is which is easier to create and which will perform better. The main method used should win on both counts.
</span>
</td>
</tr>
</table>

---

<!--Advanced Exercise Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Advanced Exercise</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
The project is done, but the output is very plain. It would be much better to improve the look of the results and there are several ways to do this with KML.
<br><br>We could simply color the voting divisions differently according to their turnout/overvotes, but a more impressive method is to use three-dimensional blocks.
<br><br>Follow the steps below to create three-dimensional shapes in the output KML dataset...
</span>
</td>
</tr>
</table>

---

<br>**10) Add ExpressionEvaluator**
<br>The height of each block should be proportional to the turnout for that division. However, for differences to be clearly visible, the vertical scale will need some exaggeration.

Place an ExpressionEvaluator between the AttributeRounder and the Turnout feature type. Set the parameters to multiply the Turnout attribute by a value of 50. Put it into a new attribute called TurnoutScaled.

![](./Images/Img2.252.Ex7.ExpressionEvaluatorExaggeratedScale.png)


<br>**11) Add 3DForcer**
<br>Add a 3DForcer transformer after the new ExpressionEvaluator. This will elevate the feature to the required height. In the parameters dialog set the elevation to Attribute Value > TurnoutScaled.

![](./Images/Img2.253.Ex7.3DForcerParameters.png)


<br>**12) Add KMLPropertySetter**
<br>Add a KMLPropertySetter transformer after the 3DForcer. This will allow us to set up the 3D blocks in the output. Set the geometry parameters as follows:

- Altitude Mode: Absolute
- Extrude: Yes

![](./Images/Img2.254.Ex7.KMLPropertySetterDialog.png)


<br>**13) Add KMLStyler**
Finally add a KMLStyler transformer. The workspace will now look like this:

![](./Images/Img2.255.Ex7.KMLStylerOnCanvas.png)

Check the parameters. Select a color and fill color for the features. Increase the fill opacity to around 0.75.

![](./Images/Img2.256.Ex7.KMLStylerParameters.png)

Save and run the workspace. In Google Earth the output should now look like this:

![](./Images/Img2.257.3DKMLInGoogleEarth.png)

These 3D blocks will show users where the voting turnout is high/low in the city.

If you wish, repeat these steps to give a 3D representation to the UnderVoting statistics.

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
By completing this exercise you proved you know how to:
<br>
<ul><li>Carry out content transformation with transformers (ExpressionEvaluator, AttributeRounder, 3DForcer)</li>
<li>Use transformer parameters to create attributes that match the writer schema</li>
<li>Use multiple streams of transformers in a single workspace</li></ul>
You also learned how to:<br>
<ul><li>Merge multiple streams of data using a common key (FeatureJoiner)</li>
<li>Use FME's built-in maths editor dialog</li>
<li>Use transformers to set a symbology (style) for output features</li></ul>
</span>
</td>
</tr>
</table>





