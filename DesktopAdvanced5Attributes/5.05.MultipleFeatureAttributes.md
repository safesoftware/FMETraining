# Multiple Feature Attributes

Normally a feature in FME is self-contained. It might get processed as a group at some point, but other than that it doesn’t have any sort of relationship to other features in the workspace.

However, in some cases the ability for a feature to access the attributes of other features would be quite useful.

For example, take a tabular dataset of coordinates that are recorded as follows:

XY

+0.0 +3.0

+3.2 +0.0

-3.2 +0.0

+0.0 +3.4

+4.2 +0.0

In this case each row is not an absolute coordinate; instead it is an offset from the previous one. Therefore, to calculate the true coordinates, each feature would need to know the coordinates of the previous feature, so that it could apply the offset.

This sort of scenario is catered for by Multiple Feature Attributes in FME.

**Multiple Feature Functionality**

Multiple feature functionality is activated by checking the box labelled Prior/Subsequent Feature Attribute Retrieval in an AttributeCreator transformer:

This opens up a section of dialog in which the author can specify how many features preceding the current feature, or how many features that succeed it, should be made available.

There is also an option to specify what should happen if the attributes are missing from a prior/subsequent feature. There is the ability to use a fallback value (which might just be an empty string), to use the value of the closest feature that does contain the attribute, or to use an attribute value instead.

Using Multiple Feature Attributes

The simplest way to make use of the attributes retrieved from prior/subsequent features is through the text or arithmetic editors.

In the editors, the list of feature attributes will have an expandable section for prior and subsequent features:

When a feature is expanded then its list of attributes becomes available for use:

Double-clicking an attribute adds it to the expression window:

So, you can see that prior and subsequent attribute values can be accessed simply by using feature[x].<attribute name> where x is a positive or negative number that refers to a subsequent or prior feature.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Professor Lynn Guistic says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“This is a first class piece of functionality, cool to the highest degree; just
one that you might not use very often.
Also, be aware that because extra resources are used for storage of the
surrounding features, performance will take a (very minor) hit when using these
capabilities.
</span>
</td>
</tr>
</table>

Here we have a dataset of precipitation for the city of Interopolis. Unfortunately, the numbers are all cumulative and the planning department wants them as absolute figures per month.
Rather than reaching into your desk drawer for a calculator, you decide to use FME to do the calculations!

**1)** Inspect Data

Open the source dataset (C:\FMEData2015\Data\ElevationModel\Precipitation.xlsx)

Notice that it is an Excel spreadsheet that records precipitation, but cumulative rather than as numbers for each individual month.

We can subtract the previous month’s figure to get the precipitation for any given month, but in FME that requires us to use Multiple Feature Attributes.

**2)** Open Workbench

Open FME Workbench and generate a workspace from Microsoft Excel to Microsoft Excel, using the above file as the source dataset.

When creating the workspace, check the parameters for the Reader to ensure FME is recognizing the headers at the top of each column.

**3)** Place AttributeCreator

In the newly created workspace, place an AttributeCreator transformer between the Reader and Writer feature types.

**4)** Set AttributeCreator Parameters – Part 1

Open the AttributeCreator parameters dialog. In the Attribute Name field select the existing attribute called Precipitation. This will overwrite it with a new value.

Then check the box marked Prior/Subsequent Feature Attribute Retrieval. In the fields provided enter 1 for the Number of Prior Features to be kept.

Next set the ‘If Attribute is Missing’ field to Use Fallback Value and enter 0 into the Fallback Value field.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Professor Lynn Guistic says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“The “Attribute is Missing” parameter is more important than perhaps most
people recognize.
Think about it: the first feature to be processed can’t have a prior feature,
and the last feature to be processed won’t ever have a subsequent one.
Therefore you always have to be careful in what you have set here. In this exercise
we’re calculating a numeric value; therefore it makes sense to use 0 (zero) as the
default replacement.”
</span>
</td>
</tr>
</table>

**5)** Set AttributeCreator Parameters – Part 2

Now let’s deal with the Value field. Double-click in the field and open the Arithmetic Editor.

Using the menu on the left double-click:
- The FME Feature Attribute Precipitation
- The Math Operator – (minus)
- The FME Feature Attribute Precipitation for feature[-1]

All of which should leave you with an expression looking like this:

Now you can see why it was so important to set the “Attribute is Missing” field, because it’s uncertain what result would occur from the above when feature[-1].Precipitation is missing!


Click OK to close the Arithmetic Editor dialog, and then click OK again to close the main
AttributeCreator dialog.

**6)** Save and Run Workspace

Save the workspace and then run it. Inspect the output.

The numbers start out looking correct, but quickly become wrong. Not even in Vancouver (I mean, Interopolis) does it rain 623mm in a single month!

The problem is this: unlike other occasions in FME, here we can’t simply overwrite the attribute we are working with. That’s because it skews the next calculation. i.e. the calculation for March needs to operate on February’s original number, not the value we’ve just overwritten it with!

**7)** Adjust Workspace

OK. Return to the workspace. Edit the Writer schema by renaming the destination attribute Precipitation to MonthlyPrecipitation.

Now return to the AttributeCreator and change the attribute it is creating to MonthlyPrecipitation:

**8)** Re-Run Workspace.

Save the workspace.

Before you re-run the workspace, check the Writer Parameter called "Overwrite Existing File" in the Navigator window.

Set it to Yes – if it isn’t already – so the output overwrites the destination dataset and doesn’t just append this data onto the same spreadsheet.

Also make sure the file you are writing to is not already open in Excel (or any other editor).

Re-run the workspace.

Inspect the output. This time the numbers should be correct: