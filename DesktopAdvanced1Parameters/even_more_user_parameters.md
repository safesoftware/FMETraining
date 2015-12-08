



**Scripted Parameters**

A scripted parameter is a special type of user parameter.

Scripted parameters go one step further than an embedded parameter.

Whereas an embedded parameter allows simple construction of a new value by concatenation, a scripted parameter allows a full Python or TCL script to be used to construct a value.

For example, here is the definition for a TCL scripted parameter that, again, concatenates a filename from the user with a set path from the author.

However, in this case, the script is used to test whether the workspace is being run on a Windows or Linux system, so it can set the output path accordingly:

Note that the script must include a return statement, to return a value to the parameter.

All Scripted Parameters are private by default, and can never be published, as it’s obviously absurd for a user to be entering Python code when a workspace runs!

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Ms. Analyst says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“Use the ‘print’ command (in Python) or ‘puts’ command (in TCL) to write
from the script to the FME log file.”
</span>
</td>
</tr>
</table>

**Attribute Name Parameter**

Sometimes an FME parameter is designed to accept either a fixed value or the value of an attribute. We call these parameters _OR_ATTR parameters, because they allow a value OR an attribute.

For example, this LabelPointReplacer allows the label to come from a fixed value, or an attribute:

When the end-user is required to set this FME parameter, then it’s simply a case of turning it into a linked user parameter. When the workspace is run, FME will scan the workspace to find what attributes are available to that transformer, and allow the user to select one or enter a fixed value.

However! Perhaps the workspace author does not want the user to be able to enter a fixed value. They want the user to only be able to select an attribute.

In this scenario we need to create a user parameter with a special type called Attribute Name:

Now when the workspace is run, the user is permitted to select an attribute, and ONLY an attribute:


However, there is a catch to this operation. The user parameter – as the type suggests – is simply returning an attribute name.

If the workspace is run then the LabelPointReplacer is supplied with the attribute name, and uses it as the label, like so:

What the author must do is open the dialog and change the label (either directly in the FME parameter, or via the Text Editor window) to be: @Value($(UserAttrSelection))

The @Value() function replaces the name of the attribute with its actual value:

Now when the workspace is run the output will be correct:

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Ms. Analyst says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
"A set of system parameters exist for use specifically by FME Server. These
are accessed by right-clicking on User Parameters in the Navigator window
and choosing Expose FME Server Parameters."
</span>
</td>
</tr>
</table>

The same colleagues from Exercise 1b are back with another request for help.

This time they have tried to experiment with a shared user parameter, but it is not working properly. Again, your task is to simplify their workspace and fix the User Parameters.

**1)** Start Workbench

Open the workspace C:\FMEData2015\Workspaces\DesktopAdvanced\Exercise1c-Begin.fmw.

This is the workspace created by your colleagues:

There are four tables being read from Geodatabase, and four layers being written to KML.

Open the KMLPropertySetter transformer parameter dialogs in turn. Note that each is using the same user parameter to set the KML name of the features:

The KML name parameter defines a value that will be used as a label when the data is viewed in Google Earth.

**2) **Rename Attributes

The problem reported by your colleagues is that when they run the workspace they cannot select the right attributes for the KML name. They can only enter a hard-coded value (which they don’t want to do) or select the attribute OBJECTID. No other attributes are available.

Run the workspace (using Prompt and Run) to confirm that this is the case.

Can you see why this problem exists?

It is because - for a shared parameter - FME only lists attributes that are available on ALL instances of the user parameter. For example, LibraryName does not appear because it only exists on the library features. OBJECTID is the only attribute that exists at all four KMLPropertySetter transformers.

In other words, the end-user is only provided with the union of all available attributes. To get what the users want, their attributes will have to be renamed to a common name.

So, add AttributeRenamer transformers in each stream of data. For the library features use it to rename:

- LibraryName to Name
- LibraryAddress to Address
- LibraryURL to URL

Then use it to delete OBJECTID. You do this by simply setting it as an old attribute, and leaving out a new attribute name:

Now do the same for all other streams of data.

For parks:
- Rename ParkName to Name
- Rename ParkAddress to Address
- Rename ParkURL to URL
- Delete OBJECTID

For TransitStations:
- Rename StationName to Name
- Delete OBJECTID
- Add Address
- Add URL

For CommunityCentres:
l Rename CentreName to Name
l Rename CentreAddress to Address
l Rename CentreURL to URL
l Delete OBJECTID

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Ms. Analyst says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“While you’re doing that, please do something about all those crooked
lines! They’re driving me crazy!”
</span>
</td>
</tr>
</table>

The workspace will now look like this:

A consequence of this renaming is that you'll now need to re-map the attributes to the Writer schema. While doing so, delete OBJECTID from all Writer feature types, as they are not needed in this output.

Re-run the workspace and you’ll find that it’s possible to now select either Name, Address or URL as the name for the feature in the KML output. That's because all of these attributes exist at each location the "Name" user parameter is being used.

**3)** Add User Parameter

Two problems remain of which the first is that the KML name is an _OR_ATTR parameter. It can also be set as a plain text string, and this is not what your colleagues want. So let’s add a new user parameter to solve that.

Create a new user parameter of type Attribute Name. Set the name and prompt according to what you think would be suitable; something like this:

Preferably turn off the optional checkbox, so the user is forced to select a value for this field.

**4)** Use User Parameter

Now we’ve created a new user parameter, let’s make use of it.

Open up each KMLPropertySetter transformer’s parameter dialog in turn. For each set the Name field to be: @Value($(LabelAttr)) – where LabelAttr is the name you gave to the new parameter.

**NB:** *It’s easiest to set it in one transformer, and then copy/paste it to all the others.
Notice that when you complete the last transformer, the previously used parameter – NAME – is automatically deleted from the Navigator window (you can use undo-redo to prove this is so). So we can tell that it must have been created by FME and linked automatically, not created by the author and then manually linked. If that was the case it wouldn’t be deleted.*

Now when the workspace is run the user can select an attribute, but not enter a value:

**5)** Create User Parameter

The other thing we could perhaps do is fix it so the user can enter an output filename, but not specify where the output folder will be.

So, create a user parameter of type text. Set the name and prompt according to what you think would be suitable; something like this:

You really need to turn off the optional checkbox here, as if there is no value, the workspace will fail.

**6)** Create Embedded Parameter

Now create a second Text type user parameter. This time turn off both Published and Optional checkboxes. It is a parameter we need to use, but the end-user doesn’t need to see.

The value for the parameter will be: C:\FMEData2015\Output\$(FileName).kml

**7)** Link Embedded Parameter

As a final step, link this newly created parameter to the FME parameter for the output KML:

As you do so the existing user parameter – the one automatically created by FME – will be deleted automatically; again, this is because it is no longer used anywhere.

**8)** Save and Run Workspace

Save and then run the workspace to test it. Enter some parameters when prompted:

The data will be written to the file specified and FME will label features with the required attribute:

**NB:** *If you get the error message: "Undefined macro 'xxxx' dereferenced in file" then it's probable that the private parameter is wrongly defined. For example it is:

C:\FMEData2015\Output\$(Filename).kml 

When it should be:

C:\FMEData2015\Output\$(FileName).kml 

(notice the different case of the N in "FileName").*