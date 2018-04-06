# Best Practice #

If a workspace runs to completion, and produces the output you want, it can’t be bad, can it? Well, yes it can. It's not enough just to put together a functioning workspace, it's also important to use FME in a manner that is both efficient and scalable.

 
## What is Best Practice? ##
In general terms Best Practice means the best way of doing something; in other words, carrying out a task in the most effective and efficient manner.

Despite the word 'best', we're not presuming the ideas here will meet every need and occasion. The best description of this concept I've heard – and one that fits well here – is:

> “a very good practice to consider in this situation based on past experience and analysis”


## Why Use Best Practice? ##
Best Practice in FME can help a user to…

- Create well-styled workspaces that are self-documenting
- Create workspaces that use the correct functionality in the correct place
- Create high-performance workspaces
- Use FME Workbench in a way that’s most efficient
- Debug a workspace when it doesn’t work the way intended
- Use FME in a project-based environment

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Dr. Workbench says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
I'm Dr. Workbench, licensed to practice medicine on FME workspaces.
<br><br>I learned about Best Practice the hard way, when I was tasked with surgery on a set of someone else’s workspaces. They were so badly organized the whole operation took me three times as long as it should have, and ruined my plans to spend the afternoon playing golf!
</span>
</td>
</tr>
</table>

---

In this chapter we'll cover three different aspects of Best Practice.

### Style ###
This section is a guide to the preferred design for workspaces. The correct style makes a workspace easier to interpret, particularly in the long run when the author might return to it after a period of inactivity.

### Methodology ###
This section covers which techniques make efficient use of Workbench and its components - and which don't! Using Workbench the right way makes for a more productive and efficient experience.

### Debugging ###
This section covers tools and methods to help identify and fix problems in translations.

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
FME best practices are very much like software development best practices. For example, a computer programmer adds comments to their code to explain their actions, and you should do the same in FME.
</span>
</td>
</tr>
</table>

# Style #
> *“A good looking well-organized workspace gives the customer the feeling that you have done quality work.”*

Style is perhaps the most obvious component of FME Best Practice. You can tell at a glance when a workspace is well-styled and when it is not. As the quote above implies, a well-designed workspace demonstrates competence. 

But style is more than just looks; a properly designed workspace provides many benefits as it is further developed and edited in the future.


## An FME Workspace Style Guide ##
A good style of design makes it easier to navigate and understand an existing workspace. This is important when workspaces might need to be edited by other users, or when you intend to make edits yourself at a later date. 



Specifically, a good style can help a user to…

- Distinctly define different sections or components of a workspace
- Quickly navigate to a specified section or particular transformer
- Pass a workspace on to another user for editing
- Rename workspaces and content with a more explanatory title


### Example of Poor Design ###
You need proof? Well, would you want to be given the task of editing this workspace? Can you even tell what this section does or - more importantly - why?

![](./Images/Img5.001.BadlyDrawnWorkspaceCloseup.png)

---

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
I'm Aunt Interop. I write a blog helping out users with their various FME problems.
<br><br>As I always say, size doesn't matter! You should always use Best Practice, whether it's a small workspace or training exercise, or a large-scale project. Getting into the habit helps make your smaller projects scalable.
<br><br>If you don't design a workspace well from the very start, it will just become harder and harder to make edits as you work on it.
</span>
</td>
</tr>
</table>

## Annotating Workspaces ##
Annotation is a key method for a clear and comprehensible design.

Annotation helps other users understand what is supposed to be happening in the translation and also helps the creator when returning to a workspace after a long interval (take it from me that this is especially important!)

There are two different types of annotation that can be applied to a workspace.

---

### User Annotation ###
User annotation is a comment created by the user. It can be connected to a workspace object (transformer or feature type), can be connected to a workspace connection, or can float freely within the workspace.

![](./Images/Img5.002.UserAnnotation.png)

To create floating user annotation, right-click the canvas and select Insert Annotation.

To create attached user annotation, right-click a workspace object and select Add Annotation, or use the shortcut Ctrl+K.

When you place an annotation you have the opportunity to change the font style, font size, and background color; plus you can also add hyperlinks, bullet points, and tables.

![](./Images/Img5.003.UserAnnotationOptions.png)

---

### Summary Annotation ###
Summary annotation is an FME-generated comment that provides information about any object within the workspace. This item can be a source or destination feature type, or a transformer.

Summary annotation is always colored blue to distinguish it from other annotation. It's always connected to the item to which it relates and cannot be detached.

![](./Images/Img5.004.SummaryAnnotation.png)

The nice thing about Summary Annotation is that it automatically updates in response to changes. That makes it very useful for checking transformer parameters (or reader/writer schemas) at a quick glance. It's particularly useful in situations where the parameters are set through a wizard and are more awkward to check (for example, the SchemaMapper or FMEServerJobSubmitter transformers).

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
A good idea is to use summary annotation to show <strong>what</strong> actions are taking place; but use user annotation to clarify <strong>why</strong> an action is being carried out.
<br><br>You can convert a summary annotation to a user (attached) annotation by using this context menu option: 
<br><br><img src="./Images/Img5.005.SummaryAnnotationConversion.png">
<br><br>This allows you to extract the information from a summary annotation, but edit it as you would a user annotation. Note that a converted summary annotation no longer updates automatically!
</span>
</td>
</tr>
</table>

## Bookmarks ##
A bookmark, like its real-world namesake, is a means of putting a marker down for easy access.

With FME the bookmark covers an area of workspace that is usually carrying out a specific task, so a user can pick it out of a larger set of transformers and move to it with relative ease.


### Why use Bookmarks? ###
Bookmarks play an important role in a well-styled workspace for a number of reasons, including these.

- Design: As a way to subdivide a workspace and manage those sections
- Access: As a marker for quick access to a certain section of workspace
- Editing: As a means to move groups of transformers at a time
- Performance: As a means to improve workspace performance when caching data


### Adding a Bookmark ###
To add a bookmark, click the Bookmark icon on the toolbar.

![](./Images/Img5.006.AddBookmarkToolbar.png)

Whereas a traditional bookmark marks just a single page in a book, the FME bookmark can cover a wide area of the canvas. A single workspace can be divided into different sections by applying multiple bookmarks.

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
If any objects on the workspace canvas are selected when a bookmark is created, the bookmark is automatically expanded to include those items.
</span>
</td>
</tr>
</table>

---

### Resizing and Editing a Bookmark ###
To resize a bookmark simply hover over a corner or edge and then drag the cursor to change the bookmark size or shape.

![](./Images/Img5.007.BookmarkResizeCursor.png)



### Bookmark Properties ###
Click the cogwheel icon on a bookmark header to open the bookmark properties dialog:

![](./Images/Img5.008.BookmarkProperties.png)

Here you can change both the name and color of the bookmark, and decide about whether contents will move with it (more on that later).

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
The context (right-click) menu for a bookmark reveals options to select all objects within the bookmark, or to disable all of those objects, making it useful for testing purposes:
<br><br><img src="./Images/Img5.009.BookmarkContextMenu.png">
</span>
</td>
</tr>
</table>

### Bookmarks for Design ###
A bookmark is a great way of indicating that a particular section of a workspace is for a particular purpose. By subdividing a workspace in this way, the layout is often a lot easier to follow. 

As one user has put it, bookmarks are like paragraphs for your workspace!

![](./Images/Img5.010.BookmarksForSectioning.png)

The above workspace illustrates nicely how to mark up different sections of a workspace using bookmarks. As you can see, it's permitted to subdivide bookmarks further by *nesting* one bookmark inside another.

#### Collapsible Bookmarks ####

Each bookmark has a small icon in the top-left corner that allows it to be collapsed:

![](./Images/Img5.011.CollapseIcon.png)

Collapsing a bookmark means it is compressed down to the size of a single transformer, displaying none of the contents except for where data enters or exits the bookmark:

![](./Images/Img5.012.CollapsedBookmark.png)

Clicking the icon a second time re-opens the bookmark to its previous size.

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
Collapsible bookmarks are an entirely new feature for FME2018.
</span>
</td>
</tr>
</table>

---

This functionality allows large sections of workspace to be rendered in a much smaller area, and only opened up when editing is required.

For example the section of workspace displayed above might be reduced to this:

![](./Images/Img5.013.CollapsedWorkspace.png)

Re-opening a collapsed bookmark adjusts the layout of the workspace, moving other transformers or bookmarks out of the way so that its contents are shown without overlap. Re-closing the bookmark causes the opposite to occur.

For example, in the above screenshot if bookmark 3 (Style) is expanded, then bookmarks 4 and 5 are moved to one side to accommodate it. When bookmark 3 is collapsed again, the reverse takes place, to give the same compact layout as before.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Mr E. Dict (Attorney of FME Law) says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
The input and output ports on collapsed bookmarks can be renamed to help clarify the data entering and exiting:
<br><br><img src="./Images/Img5.014.RenameCollapsedPorts.png">
<br>This can be achieved by either double-clicking the object, pressing F2, or using the Rename option on the context menu.
</span>
</td>
</tr>
</table>



### Bookmarks for Quick Access ###
Bookmarks are listed in the Workbench Navigator window. Each bookmark is depicted as a folder and can be expanded to show its contents. This may include feature types, transformers, or other - nested - bookmarks:

![](./Images/Img5.015.BookmarksForAccess.png)

Clicking or double-clicking a bookmark in the Navigator selects that bookmark and brings it into view. So when bookmarks have been used to divide a workspace into sections, they can also be used to navigate between different parts of that workspace.

In this way bookmarks are like the chapter headings in a book!


### Workspace Presentation ###
Bookmarks can also be made to appear on the FME Workbench toolbar:

![](./Images/Img5.016.PresentationOption.png)

Besides being a way to quickly access bookmarks, this tool can be used as what is known as "Presentation Mode" in FME Workbench. By clicking the arrow button (or pressing the keyboard spacebar) you flip from bookmark to bookmark, using animation, in a way that would be very useful when showing the workspace as part of a presentation.

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
To access the functionality you need to make sure it is added to the toolbar. You can do this by right-clicking on the toolbar and using the customize option. 
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
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Dr. Workbench says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
The order of bookmarks in that window is alphabetical and that might not always be the same order that you wish to present a workspace.
<br><br>In that case, right-click on Bookmarks in the Navigator window and turn off the default option to "Sort Alphabetically". 
<br><br><img src="./Images/Img5.017.BookmarkSortOption.png">
<br><br>Bookmarks can then be dragged up and down in the Navigator window to give the correct order. Additionally, a new option on the bookmark Properties dialog allows you to exclude specific bookmarks from the Bookmark Navigator. Nested bookmarks are excluded by default, so must be turned on to be included in the navigator.
<br><br>For more information see this <strong><a href="http://blog.safe.com/2016/03/fmeevangelist146/">article on bookmarks</a></strong> on the Safe Software blog.
</span>
</td>
</tr>
</table>

### Bookmarks for Editing ###
Bookmarks define a section of workspace containing a number of objects. When editing a workspace without bookmarks, moving objects is done by selecting the object or objects, and dragging them to a new position. 

However, when a workspace is divided by bookmarks, objects can be moved by simply dragging the bookmark to a new position. When an object is located inside the bookmark, it moves as the bookmark does. 

![](./Images/Img5.018.MovingBookmark.png)

Using this technique large groups of objects can be moved about the workspace canvas, in order to create a clearer layout. Objects are moved inside a bookmark, whether the bookmark is collapsed or expanded.


---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Dr. Workbench says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Remember that one of the bookmark properties is labelled <strong>Contents</strong> and has the value either "Move with Bookmark" or "Move Independently". Obviously the former value causes objects to move with the transformer; the latter value causes objects to remain in position when a bookmark is moved.
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
Here is a question about bookmarks.
<br><br>Which of the following is NOT a method of creating a bookmark?
<br><br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=3&question=1&answer=1&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">1. Click the Insert Bookmark button on the toolbar</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=3&question=1&answer=2&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">2. Select a transformer, right click, choose Create Bookmark</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=3&question=1&answer=3&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">3. Select multiple transformers, right click, choose Create Bookmark</a>
<br><a href="http://52.73.3.37/fmedatastreaming/Manual/QAResponse2017.fmw?chapter=3&question=1&answer=4&DestDataset_TEXTLINE=C%3A%5CFMEOutput%5CQAResponse.html">4. Use the Ctrl+B shortcut</a>
</span>
</td>
</tr>
</table>

### Bookmarks for Performance ###
When a workspace is run with Data Caching turned on, then features are cached at every transformer. As you can imagine, in larger workspaces this leads to a lot of data being cached, sometimes unnecessarily:

![](./Images/Img5.018a.CachingInBookmark.png)
 
Notice in the above screenshot that every transformer in the Prepare Data for Matching bookmark is being cached.

However, when a bookmark is collapsed, then caching only occurs on the bookmark output objects:

![](./Images/Img5.018b.CachingOnBookmark.png)

This means that data is cached only for the final transformer in the bookmark, saving considerable time and resources:

![](./Images/Img5.018c.NoCachingInBookmark.png)

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Dr. Workbench says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Obviously you don't want to put a workspace into production when caching is turned on, regardless of whether your bookmarks are collapsed. This technique is only recommended for use in the design, authoring, and testing phases of workspace creation.
</span>
</td>
</tr>
</table>

## Object Layout ##

The positioning of workspace objects and the care taken in connecting them can really make the difference between a poorly-designed workspace and one that is visually attractive and efficient.  

### Object Layout ###

Layout methods vary from user to user. Some users like to line up objects so that all *connections* are horizontal:

![](./Images/Img5.019.StraightConnectionTransformers.png)

Others prefer the tops of *objects* to be aligned horizontally, with angled connections:

![](./Images/Img5.020.AlignedTopTransformers.png)

Some prefer to align object edges vertically:

![](./Images/Img5.021.VerticallyAlignedTransformers.png)

The style used is more a personal preference than a definite rule, but what is important is consistency. A workspace that has no obvious layout style, or an inconsistent one, does not inspire confidence in the author's abilities!

---

### Grid and Guides ###
Grids and Guides are a tool to help align workspace objects in a neat and tidy way. This functionality is accessed through View > Grid and Guides on the Workbench menubar.

![](./Images/Img5.022.GridAndGuideMenu.png)

**Show Grid** causes a grid of lines to be displayed on the Workbench canvas. Snap to Grid causes all objects - such as the summary annotation highlighted - to snap onto the intersection of grid lines when moved. In this way objects can be more easily lined up.

![](./Images/Img5.023.GridOptions.png)

**Show Guides** causes guidelines to be displayed on the Workbench canvas whenever an object is moved, and lines up approximately to another canvas object. Snap to Guides allows an object to be snapped onto a highlighted guideline.

![](./Images/Img5.024.GuideOptions.png)

These two tools make it very simple for workspace objects to be aligned in a pleasing style.

---

### Autolayout ###

The Autolayout tool appears on the toolbar of FME Workbench:

![](./Images/Img5.025.AutolayoutMenubar.png)

Clicking the toolbar button will layout either all of the workspace, or just objects that are currently selected:

![](./Images/Img5.026.AutolayoutAfter.png)

As you can see, the autolayout tends to use a horizontal pattern, with the tops of objects aligned. Therefore it's better to select groups of transformers at a time, when using this tool, rather than trying to lay out the entire workspace in a single action.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Dr. Workbench says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
In general, the autolayout algorithm is OK... but it still can't compare with taking the time and effort to manually organize your object layout.
</span>
</td>
</tr>
</table>

## Connection Style ##

It's also worth noting that object positioning is only part of a good layout. The other key part is the connection style. 

As with the positioning of workspace objects, the care taken in connecting them can really make the difference between a poorly-designed workspace and one that is visually attractive and efficient.  

### Connection Styles ###

Connections are the lines between objects on the workspace canvas. There are three different styles of connection that you can create in Workbench:

- Curved: The default style with curved line connections
- Squared: A style that evokes a Manhattan skyline through squared connections 
- Straight: The original connection style; a straight line between two objects

You can switch between styles using either the View menu, the FME Options menu, or the shortcut Ctrl+Shift+C. This image shows a comparison of the three styles:

![](./Images/Img5.027.ConnectionStyleComparison.png)

Once more, there is no right or wrong choice about which style to use; it is more a personal preference. However, object layout and connection style are definitely related; the best FME authors will vary the position of objects according to the connection style used to avoid issues like overlapping connections. 

---

### Overlapping Connections ###

One of the most obvious failings of a workspace design is to have connections that cross over each other, for example like this: 

![](./Images/Img5.028.OverlappingConnections.png)

The visibility and intent of a connection is always compromised when it overlaps with either another connection or another object on the canvas. However, the choice of connection style affects the possibility of an overlap occurring. For example curved connections tend to cross over more than straight ones: 

![](./Images/Img5.029.CrossingCurveConnections.png)

...and squared connections can sometimes cross in ways that are difficult to decipher: 

![](./Images/Img5.030.ManhattanCrossing.png)

Because these issues can spring up when you switch connection style, it's wise to choose a particular connection style and layout technique and stick with it. For example, in a curved connection workspace transformers could perhaps be spaced more widely to avoid overlaps.

---

### Junctions ###

There is one transformer in FME Workbench that is designed to be used to enhance the layout of objects and connections. That transformer is called the **Junction**.

![](./Images/Img5.031.JunctionTransformers.png)

This transformer is a small, node-like object, that carries out no function on the data, but is instead used to tidy connections within a workspace - as in the above screenshot. This makes it an excellent tool for best practice.

As with any other transformer, a junction can be connected to an Inspector or Logger, and it can have annotation objects attached to it. It also works with both Quick Add and Drag/Connect functionality.

---

### Hidden Connections and Tunnels ###

The ability to hide connections is especially useful for avoiding overlaps. To hide a connection, right-click on it and choose the option to Hide:

![](./Images/Img5.032.HideConnection.png)

A hidden connection is represented by a 'transmitter' icon, or by a greyed-out dashed line when the object at one end of the connection is selected:

![](./Images/Img5.033.HiddenConnections.png)

Here the object (transformer or feature type) at the other end of the NotMerged connection must be selected for the connection to be visible.

The other available option is "Create Tunnel". This creates a hidden connection with the addition of an annotated junction transformer at each end:

![](./Images/Img5.034.TunnelConnection.png)

A tunnel makes a hidden connection slightly more obvious, plus allows for annotation at each end.

#### Revisualizing Hidden Connections ####

To view hidden connections, simply click on an object at either end. The connection is highlighted as a greyed-out dashed line.

To return a connection back to view, right-click an object to which it is connected and choose Show Connection(s). 

For more information on Tunnels and Junctions see <strong><a href="http://blog.safe.com/2016/05/fmeevangelist150/">this blog post</a></strong>.

# Methodology #

> *“Bad methodology impacts style. A poor style can be indicative of poor methodology.”*

Methodology is a less-obvious component of Best Practice than style. It manifests itself in two key ways:

- Maintenance
- Performance

In both cases the first step in implementing a good project is to learn what methodology is poor, and how to avoid it.

## Maintenance ##

Maintenance is the ability to update the workspace, and scale it up to a larger solution. 

Maintenance relates to the concept of **design patterns**. A design pattern is the optimum layout of transformers to carry out a given task. A poor design pattern leads to major complications when maintaining or scaling a workspace.  

Poor design can often be detected in the style of a workspace; so if a workspace uses bookmarks and annotation correctly, but still doesn't look good, it may indicate flaws in the pattern of transformers.


## Performance ##

Performance is the efficiency of the workspace in carrying out the translation using the fewest resources.

Performance is important to most users, but difficult to quantify. If a workspace runs to completion in an adequate time then performance is often ignored. Any flaws in performance then manifest themselves when an attempt is made to increase the scale of the project to handle more data.  

Poor performance surprisingly also manifests itself in the style of a project, as well as in the design patterns used. 

## Maintenance Methodology ##

Maintenance methodology is weak when a workspace's design doesn't allow easy updates or expansion. There are some key indicators that indicate design weakness.

---

### Duplicated Transformers ###
Duplicating the same transformer again and again – maybe creating multiple streams to do so – indicates a weak design. 

For example, the multiple AttributeManager transformers here will cause maintenance problems:

![](./Images/Img5.035.DuplicatedTransformer.png)

The first problem is that each additional year to be supported requires a new transformer to handle it. The second problem is that should a small change be required in the AttributeManager, then each transformer will need to be individually edited.

We can also say that this layout results in a style that is not as compact as it should be.

The solution here is to replace all of the above with a single AttributeValueMapper transformer (or possibly a SchemaMapper) to allow scaling with the minimum number of edits. 

The general solution is to watch for instances of multiple transformers, and try to assess whether there is a better design.

---

### Complexity ###
A workspace design is weak when it is more complex than necessary. Complexity means a solution becomes harder to maintain and harder to scale, especially when carried out by someone other than the original author.

There are various types of complexity to watch for:

- **Excess Scripting**: The use of Python scripting when an equivalent transformer already exists
- **Low Level Complexity**: The use of FME functions and factories when an equivalent transformer already exists
- **Multiple Workspaces**: When multiple workspaces are chained in a way that is unnecessary
- **Workspace Style**: When workspace style is so convoluted it is difficult to understand

Before putting a project into production it is worth asking a colleague to evaluate it for clarity. Sections of workspace they cannot easily understand are points that future authors will also find difficult to maintain. 

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
For a new FME user with string scripting skills, Python transformers provide particularly tempting shortcuts. However, other workspace authors may not be as skilled in Python, and find it difficult to debug without a full Python development environment.
</span>
</td>
</tr>
</table>

---

### Database Connections ###

Database formats require connection parameters. Sometimes these parameters need to be applied multiple times in the same workspace, and sometimes the parameters need to be changed when switching platforms (for example from testing to a live environment).

It is possible to embed database connection values inside a workspace, adding that information wherever it is required. However, a better solution involves a tool in FME called Database Connections.

Database Connections are a pre-defined set of connection and authentication parameters, stored under a single name. Once created, a connection name is used in lieu of the actual parameters.

#### Creating a Database Connection ####

When using a database format and prompted for connection details, choose the option to add a connection:

![](./Images/Img5.036.AddDatabaseConnection.png)

A new connection is defined by selecting the database type, entering connection parameters, and giving the connection a name:

![](./Images/Img5.037.AddDatabaseConnectionDialog.png)

Now, whenever a database connection is required (here in a SQLExecutor transformer) the pre-defined connection is selected:

![](./Images/Img5.038.UsingDatabaseConnection.png)

Now repeated use of a database does not require repeated entry of the same credentials, and if the credentials change only one connection needs to be edited. Both of these benefit maintenance and scaling of a workspace.

Another benefit is that of security. Embedded connection information is stored inside the workspace file, posing a potential security risk. Database Connections are stored securely, outside of the workspace, and can not easily be accessed by someone else. If the workspace is passed to another user, they will have to set up their own connection with their own parameters.

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
It's better to be safe than sorry. You don't want to get burned by bad designs. If you're unsure about a workspace, consult <a href="https://knowledge.safe.com/questions/index.html">other FME users</a>, or contact the <a href="http://www.safe.com/support">Safe Software support team</a> for advice.
<br><br>Also, be sure to check out this blog post on <a href="https://blog.safe.com/2015/06/fmeevangelist136/">FME and Code Smells.</a></span>
</td>
</tr>
</table>



## Performance Methodology ##

Performance methodology is weak when a workspace's design causes the workspace to use more system resources (CPU and memory) than necessary. Like maintenence methodology, there are some key indicators that indicate design weakness.

Performance methodology means setting up a workspace to run proficiently.


---

### Filtering Input ###

A common scenario in FME is to read data into a workspace and then filter out features (records) that are not required:

![](./Images/Img5.039.DataFilterTester.png) 

However, when data is read and immediately discarded, the resources used to read that data are a direct loss to performance. 

If data is filtered as it is read - rather than afterwards - performance is much better, and many formats have parameters to do just that: 

![](./Images/Img5.040.DataFilterSQLWhere.png)

Here a ‘WHERE Clause’ parameter applies the required filter directly to the Geodatabase reader. Only data that matches the where clause is read and enters the workspace. 

---

### Excess Feature Types ###

The schema of a source dataset is represented on the FME canvas by feature type objects:

![](./Images/Img5.041.ExcessFeatureTypes.png)

Not connecting a feature type is equivalent to reading and discarding data, and is likewise detrimental to performance. 

When adding readers FME prompts the user to select feature types to add to the translation. You should avoid adding feature types you don't need, and remove ones that are already added but not connected. 

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Dr. Workbench says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Not only do excess feature types slow down your work, they clutter the canvas and make it harder to keep a clean and tidy style.
</span>
</td>
</tr>
</table>

---

### Excess Attributes and Lists ###

Once data has been read into a workspace, it still can be reduced in size to assist performance. For example, attributes not defined in the output schema are not necessary to a workspace and can be removed:

![](./Images/Img5.042.ExcessAttrs.png)

Here a workspace author is calculating the number of addresses in each "zone" of a city. The address attributes are not required in the output schema, but are being kept on all address features. Even worse they are being copied on to the zone features, a list of addresses calculated, and everything carried through to the end of the workspace.

In this scenario the author would do well to add an AttributeRemover transformer to delete excess attributes:

![](./Images/Img5.043.RemoveExcessAttrs.png)

This will reduce the amount of memory required to run the translation, with no effect on its output.

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Dr. Workbench says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Lists are the worst attribute type to keep for no reason, since they can have multiple values for each record. Parameters in many join transformers allow the author to generate only the list attributes required:
<br><br><img src="./Images/Img5.044.MinimalListCreation.png">
</span>
</td>
</tr>
</table>

---

### Error Trapping ###

Sometimes scaling up/performance means using more datasets of varying types and quality. If data quality is not considered then future performance can be compromised.

One way to design for future capabilities is using error trapping.

Error trapping is a way to design a workspace such that unexpected data does not cause the workspace to fail. The author attempts to foresee data problems that might arise and build in methods to handle them.

Error trapping can be as simple as adding a test or filter transformer to weed out bad features, or it can be more complex and include ways to process data in different ways depending on different circumstances.

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
The Tester transformer has an operator for testing whether an attribute has a value:
<br><br><img src="./Images/Img5.045.TesterHasValueParameter.png">
<br><br>This is very useful for error trapping, to test whether an attribute has a value before trying to use it as the source for a parameter.

</span>
</td>
</tr>
</table>


# Debugging #
Even skilled FME users seldom produce new workspaces with zero defects. For that reason it's important that all users are aware of the debugging techniques available in FME.


## Debugging Methodology ##

Generally, debugging in FME consists of first determining whether a problem has occurred and then tracking down the source of the problem (i.e. where in the workspace does it occur). Once it's determined where a problem occurs, the nature of the problem can be investigated.

There are various debugging techniques available in FME and it's important to use these in the correct order. For example, it's not particularly useful to change parameters and re-run the workspace when a simple log message already explains the issue!

A logical order would be:

- Check for any problem
	- Interpret the log for warnings and errors
	- Inspect the output datasets
- Locate the problem
	- Review connection feature counts
	- Inspect the data at key stages of the translation
- Determine the problem
	- Check reader, writer, or transformer parameters at the point of failure
	- If necessary, run the workspace in feature debug mode

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Dr. Workbench says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
In the world of software development, debugging a process after completion is called "post-mortem debugging"! We're trying to find out what caused a fatality.
<br><br>If we can't determine the cause by post-mortem, we'll re-run the process with various tracing options turned on. We can call that "interactive debugging."
</span>
</td>
</tr>
</table>

## Logging and Log Interpretation ##
FME logs contain a record of all stages and processes within a translation. The contents are therefore vital for debugging purposes.

### Log Message Types ###

There are a number of different message types that show in the log window including:

**Error**: An error, denoted in the log by red text and the term **ERROR**, indicates that a problem has caused FME to terminate processing. For example, FME is unable to write the output dataset because of incorrect user permissions.

**Warning**: A warning, denoted by blue text and the term **WARN**, indicates a processing problem. The problem is sufficiently minor to allow FME to complete the translation, but the output may be adversely affected and should be checked. For example, FME is unable to write features because their geometry is incompatible with the writer format. The features will be dropped from the translation and a warning issued in the log.

**Information**: Information messages, denoted by the term **INFORM**, indicate a piece of information that may help a user determine whether their translation has been processed correctly. For example, FME sometimes log confirmation of a particular dataset parameter, such as coordinate system.

**Statistics**: Statistics messages, denoted by the term **STATS**, provide information on various numbers relating to the translation; for example the number of features read from a source dataset, and the time taken to do so.

---

### Log File Options ###

Log file options are important to set up (*before* running the workspace) so that we receive information in the structure that we require. These options are accessed via the cogwheel icon on the log window:

![](./Images/Img5.046.LogOptionsButton.png)

The log options allow us to control how data is presented and in what format:

![](./Images/Img5.047.LogGeneralSettings.png)

The Log Timestamp Information option is very important when you are debugging a workspace's performance, as it adds information about the length of time taken for each step. It also causes the type of message to be shown (ERROR, WARN, etc).

The ability to filter messages is not particularly important, as message types can be filtered directly in the log window.

The Log Debug option causes FME to show messages from a deeper level in the FME engine. This option should **NOT** be turned on for general use, but only once a workspace has already been shown to fail, and extra information is required. Otherwise it's possible to be confused by unusual messages that are part of the normal process.

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
Log Debug is particularly useful when tracking down HTTP-related issues.
</span>
</td>
</tr>
</table>

---

### Spatial Log File ###

Besides writing the log to a text file (&lt;workspace name&gt;.log) FME also writes a spatial log: 

![](./Images/Img5.048.SpatialLogFile.png)

The spatial log is a dataset of features (in FME Feature Store format) that have been mentioned in the log - either because of a warning from FME or by use of the Logger transformer.

The dataset can be opened within the FME Data Inspector to inspect the features and identify any problems that caused them to be rejected. 

---

### Interpreting the Log Window ###

The log window should be the **first** place to check when a translation is completed. It will tell the user whether there are any errors or warnings to be concerned about.


#### Errors ####
If an ERROR occurs, it is likely that the translation will be halted. There will be a lot of red text and some terminating statements such as:

> Program Terminating
> 
> Translation FAILED.

There may be several ERROR messages, so scroll back up the log window to try and identify the first of these, which is likely to be the root cause of the problem. For example this message:

> ERROR |Error connecting to PostgreSQL database(host='postgis.train.safe.com', port='5432', dbname='fmedata', user='fmedata', password='***'): 'FATAL:  password authentication failed for user "fmedata"
FATAL:  password authentication failed for user "fmedata"

...is an obvious problem with authenticating a database connection.


#### Warnings ####
Even when a translation succeeds, it's important to check the log for the following comment:

> Translation was SUCCESSFUL with X warning(s)

If there are any warnings (i.e. if X > 0) then use the search option to look for the word WARN. Any warning messages might have important consequences for the quality of the output data.

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
FME2018 introduces the ability to filter messages by type interactively in the log window. Here the user has clicked a button to view only ERROR messages within the workspace: 
<br><br><img src="./Images/Img5.049.InteractiveLogFiltering.png">
<br><br>This is useful for debugging, and particularly so for users with a color vision deficiency who cannot easily distinguish red errors from blue warnings. 
</span>
</td>
</tr>
</table>

## Inspecting Output ##
Even if a workspace ran to completion without warnings or errors, it does not follow that the output matches what is expected or required. For whatever reason, the workspace may be producing data in the wrong manner. This we determine by inspecting the translation output.

Inspecting the output is simply a case of viewing it in either the FME Data Inspector, or in the application in which the data is intended to be used. 

As noted already in this manual, a number of different aspects of data may be inspected, including the following:

- **Format**: Is the data in the expected format?
- **Schema**: Is the data subdivided into the correct layers, categories or classes?
- **Geometry**: Is the geometry in the correct spatial location? Are the geometry types correct?
- **Symbology**: Is the color, size, and style of each feature correct?
- **Attributes**: Are all the required attributes present? Are all integrity rules being followed?
- **Quantity**: Does the data contain the correct number of features?
- **Output**: Has the translation process restructured the data as expected?

It should be straightforward to check a dataset and see if any of its components are incorrect. 

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Dr. Workbench says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
This stage is solely to determine IF there are any problems.
<br><br>If there are no problems, then we can be satisfied the translation was a success.
<br>If there are problems, we should go on to determine where the problem occurred. It's important not to jump to conclusions at this point. The fact that the output is incorrect does not tell us <strong>where</strong> that issue was introduced.
</span>
</td>
</tr>
</table>

## Feature Counts ##
A workspace **Feature Count** refers to the numbers shown on each connection once a translation is complete:

![](./Images/Img5.050.FeatureCounts.png)

Once an error or problem has been determined to exist, feature counts help us identify *where* that problem occurred. 

In the above screenshot, if you were expecting 74 output features, but only got 73, then you would inspect the feature counts to find where that missing feature went (it appears to unexpectedly fail the Tester tests).

---

### Incorrect Output ###

When the number of output features is incorrect, then there are several things to check.

If you get zero output, and the feature counts show that all features entered a transformer, but none emerged, then you can be fairly confident that the transformer is the cause of the problem:

![](./Images/Img5.051.FeatureCountNoFeatures.png)

Here, for example, 80 features enter the Clipper transformer (to be clipped against a single boundary) but none emerge. The Clipper transformer is almost certainly the cause of any incorrect output. 

The data is not rejected as invalid; it merely does not pass the test expected. It's possible that Clipper and Clippees don't occupy the same coordinate system, hence one does not fall inside the other. 

Alternatively - and this is a common cause of missing features - the author has connected the wrong output port! For example, this user has connected the StatisticsCalculator Summary output port, when they really wanted the Complete port connected:

![](./Images/Img5.052.MissingFeaturesStatsCalc.png)

The red attribute connectors on the writer feature type are a good indication that something is going wrong.

---

### Rejected Features ###

Sometimes when features go missing they are being rejected by a transformer. Many transformers include a &lt;Rejected&gt; port to output these invalid features:

![](./Images/Img5.053.RejectedPort.png)

Remember, features are automatically counted on a &lt;Rejected&gt; port, even if there is no other transformer attached. Additionally, the rejected features are also saved as a temporary dataset that can be viewed by clicking on the inspect icon.

As an additional benefit, the rejected features will often include a rejection code attribute:

![](./Images/Img5.054.RejectedCause.png)

## Checking Key Stages ##

If the feature counts cannot help to pinpoint the location of a problem, then the next step is inspecting data at key stages of a translation.

Generally, issues in an output dataset occur due to one of these:

- The data was incorrectly read
- The data was incorrectly transformed 
- The data was incorrectly written
- The data is being incorrectly interpreted by another application

For example. You open an FME-generated dataset in application X and find that "Parc national des Pyrénées" is rendered as "Parc national des Pyr�n�es". 

Obviously an encoding problem has occurred, but where? The fact that data appears incorrect in another application is no real indication of where that problem was introduced. 

In this scenario the author should check the data at key stages to determine when the data last looked correct.

---

### Inspect the Source Data Before Reading ###

It's easy to assume source data is correct without checking it. So, if possible, the source data should be inspected in its native application.

Obviously if the data is incorrect at source (in our example it is "Parc national des Pyr�n�es" in its native application) then there is little chance the translation output will be correct.  

---

### Inspect the Source Data After Reading ###

If the source data is correct in its native application, then inspect it using FME. Either open the data directly in the FME Data Inspector, or - if the workspace was run with caching turned on - open it from within FME Workbench.

If the data is incorrect at this point then the process of reading the data with FME is at fault.

---

### Inspect the Data Before Writing ###

This is the point most likely to highlight the problem, and so you may wish to start here.

If the workspace was run with caching turned on (Run &gt; Run with Feature Caching) then the data is available for inspection already. Otherwise turn on this option (or Writers &gt; Redirect to FME Data Inspector) and re-run the workspace. 

Inspect the data to see if it was correct at the point just before it is written to the output. In the above example, if the Data Inspector shows � characters at this point:

![](./Images/Img5.055.BadEncodingDI.png)

...then the problem appears to be in the data transformation.

---

### Inspect the Output Dataset ###

If the data is correct before writing, then it might be that it is being written incorrectly.

Open the output dataset in the FME Data Inspector. This will show the data as FME wrote it (and, of course, read it back). If the data is incorrect here, then the problem will have likely occurred during writing of the data.

In the above example, if the Data Inspector shows � characters at this point, then the data has been mangled when it was being written. 

---

### Inspect the Data After Transformation ###

It's best to start by inspecting the data at the point it is about to be written. This is the point most likely to highlight the problem.

If the workspace was run with caching turned on (Run &gt; Run with Feature Caching) then the data is available for inspection already. Otherwise turn on this option (or Writers &gt; Redirect to FME Data Inspector) and re-run the workspace. 

Inspect the data to see if it was correct at the point FME just before it is written to the output. In the above example, if the Data Inspector shows � characters at this point:

![](./Images/Img5.055.BadEncodingDI.png)

...then the data was bad before FME even tried to write it. This means the problem is caused in either reading or transforming the data, and you should check those stages.

If the data is correct before writing, then the next step is to inspect the output dataset in FME...

---

### Inspect the Data in a Text Editor ###

Another check to make is to open the data in a text editor: 

![](./Images/Img5.056.GoodEncodingTextEditor.png)

For obvious reasons it will not be possible to do this for every dataset (binary files or databases for example) but for text-based files it can provide definitive proof of whether the data is correct at this point.

---

### Inspect the Output Dataset in Another Application ###

If FME (and a text editor) can display the output data, then it might be that the intended application is not interpreting the data correctly.

So, open the output dataset in the application in which it is intended to be used. If the data is only incorrect here then the problem is more likely to be with how the application interprets the data:

![](./Images/Img5.057.BadEncodingOther.png)

That would be particularly true if the format was non-native to that application (for example, reading a Geodatabase outside of an Esri product). 

---

All of these techniques narrow down where an error might have occurred, but don't always specify the cause. For example, incorrect output could mean that FME has a limitation in that writer or that the workspace author has set an incorrect parameter. Or maybe one application uses a different default encoding to another.

In short, these techniques identify where to investigate first, but won't provide an absolute answer by themselves.

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
Encoding is a good example for us here, but it's also an example of where you should check that your computer is capable of viewing such data at all! If your computer is set up in the wrong locale then it might not even be possible for you.
</span>
</td>
</tr>
</table>

## Feature Debugging ##
Feature Debugging is a tool that allows individual features to be inspected during a translation. It differs from inspecting data at a particular location in that it inspects features one at a time, and allows the author to trace that feature's progress through a workspace.

This is most useful when a problem has been identified as being during transformation, but the point of failure is unknown.

Feature Debugging is triggered by "breakpoints"; workspace connections that are flagged by the user as a location where features should be inspected:

![](./Images/Img5.058.AddBreakpoint.png)

The connection is highlighted in a darker black color with a red "stop" sign, to denote its new status:

![](./Images/Img5.059.BreakpointOnCanvas.png)

Now the workspace is run with the “Run with Breakpoints” option turned on:

![](./Images/Img5.060.RunWithBreakpoint.png)


When the first feature arrives at the breakpoint, the translation is temporarily paused and information about the feature displayed in a Feature Inspector window.

The upper part of the window shows a graphic representation of the feature; the lower part lists properties such as Feature Type and Coordinate System; plus attribute and geometry information.

![](./Images/Img5.061.InspectionDialog.png)

There are four buttons at the foot of the Feature Inspector window:

<table>

<tr>
<th>Button</th>
<th>Operation</th>
<th>Description</th>
</tr>

<tr>
<td><img src="./Images/Img5.062.InspectionDialogNextStepIcon.png"></td>
<td>Step to Next Connection</td>
<td>This tool steps through the workspace one transformer at a time, showing the status of a feature as it is processed.</td>
</tr>

<tr>
<td><img src="./Images/Img5.063.InspectionDialogNextBreakpointIcon.png"></td>
<td>Step to Next Breakpoint</td>
<td>This tool re-starts the translation, stopping the next time a feature reaches an inspection point.</td>
</tr>

<tr>
<td><img src="./Images/Img5.064.InspectionDialogPlayIcon.png"></td>
<td>Continue Translation</td>
<td>This tool re-starts the translation, ignoring all further breakpoints.</td>
</tr>

<tr>
<td><img src="./Images/Img5.065.InspectionDialogRunIcon.png"></td>
<td>Stop Translation</td>
<td>This tool stops the translation.</td>
</tr>

</table>

The currently active connection is highlighted red to show it is the location where the translation is currently paused.

# Module Review #
This module was designed to help you use FME Workbench in the most efficient manner, to effectively manage FME related projects, and to ensure those projects are scalable and portable.

## What You Should Have Learned from this Module ##

The following are key points to be learned from this session:

### Theory ###

- Best Practice is the act of using FME in a manner that is efficient, but also easily comprehensible by other FME users.
- Best Practice in FME can be divided into Style, Methodology, and Debugging.
- Style is a practice that makes it easier to navigate and understand an existing workspace.
- Methodology is a practice that defines the optimum transformers to use for maintenance and performance purposes.
- Debugging is the act of locating and fixing defects within a workspace.

### FME Skills ###

- The ability to use bookmarks and annotation to create a well-designed workspace style.
- The ability to create workspaces that are easier to maintain, edit, and scale.
- The ability to create workspaces that perform in an efficient manner.
- The ability to interpret an FME log file.
- The ability to inspect output and feature counts to locate errors.
- The ability to use feature debugging to trace individual features.

### Further Reading ###

For further reading why not browse **[articles tagged with Best Practice](http://blog.safe.com/tag/Best-Practice/)** on our blog? 

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
Which of the following is NOT a method of creating a bookmark?
<br><br><span style="color:lightslategrey">1. Click the Insert Bookmark button on the toolbar</span>
<br><span style="font-weight:bold">2. Select a transformer, right click, choose Create Bookmark</span>
<br><span style="color:lightslategrey">3. Select multiple transformers, right click, choose Create Bookmark</span>
<br><span style="color:lightslategrey">4. Use the Ctrl+B shortcut</span>
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
It's possible to disable other objects besides connections. Can you pick out which of these objects (there may be more than one) can be disabled in Workbench?
<br><br><span style="font-weight:bold">1. Transformers</span>
<br><span style="font-weight:bold">2. Feature Types</span>
<br><span style="color:lightslategrey">3. Annotation</span>
<br><span style="font-weight:bold">4. Bookmarks</span>
<br><br>OK, technically you can't disable a bookmark, but you can choose to disable all the objects within it.
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
<span style="color:white;font-size:x-large;font-weight: bold">Applying the Style Guide</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Addresses (Esri Geodatabase)<br>Crime Data (CSV - Comma Separated Value)<br>Parks (MapInfo TAB)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Work on Vancouver Walkability Project</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Style Best Practice</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\BestPractice-Ex1-Begin.fmwt</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\BestPractice-Ex1-Complete.fmwt</td>
</tr>

</table>

You have just been assigned to a project to calculate the "walkability" of each address in the city of Vancouver. Walkability is a measure of how easy it is to access local facilities on foot. It will include a measure of the distance to the nearest park, the amount of crime in an area, and other similar measures. 

The workspace for this project has already been started, with crime information being connected to each address, but the author was obviously unaware of the FME style guide, so as well as continuing the project, a certain amount of styling must be added to the existing content.


<br>**1) Start Workbench**
<br>Start FME Workbench. 

Notice that the workspace file is actually a template (it has the file extension .fmwt). This is good because it means that there might be existing caches for the project. Ensure that Run with Feature Caching is turned on and open the workspace template from from C:\FMEData2018\Workspaces\DesktopBasic\BestPractice-Ex1-Begin.fmwt.

![](./Images/Img5.200.Ex1.UnstyledWorkspace.png)

This workspace obviously needs some style applied to it in the form of bookmarks and annotation.


<br>**2) Rearrange Transformers**
<br>Firstly the Inspector transformer is not required - we can inspect caches more easily - and can be deleted. However, because it has two connections into it, and we want to keep track of what they are, once deleted, replace it with a Junction transformer.

Then clean up the transformers around it so that there are no overlapping connections:

![](./Images/Img5.201.Ex1.JunctionNotInspector.png)

Now rearrange the first part of the workspace, avoiding overlapping connections and looking out for transformers that might logically be grouped together in a bookmark:

![](./Images/Img5.202.Ex1.RearrangedFirstPart.png)


<br>**3) Add Style**
<br>Having rearranged the transformers in a pleasing way, now add bookmarks and annotation where appropriate.  This will require some inspection of the transformers to see what each of them is doing. But you should be able to see at least two groups of transformers that can be placed into a bookmark:

![](./Images/Img5.203.Ex1.StyledWorkspace.png)

Don't forget to phrase annotation and bookmark titles so that future users of the workspace will be able to tell at a glance what the workspace is supposed to do. 

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
Overlapping connections can also be cleaned up by rearranging the order of transformer output ports:
<br><br><img src="./Images/Img5.204.Ex1.ReorderPorts.png">
</span>
</td>
</tr>
</table>

---

<br>**4) Run Workspace**
<br>If you wish, run the workspace by using Run to This on the newly place Junction transformer. You should then be able to click on the Junction and press Ctrl+I to inspect the data at that stage of the translation.

One thing to notice is that the CSV (crime) reader is reading data directly from an Excel spreadsheet on the City of Vancouver web site. For this reason it's important that we retained the cached data and do not have to read it all over again. 


<br>**5) Add Parks Data**
<br>Now let's continue the project by handling some parks data. Add a reader with the following parameters:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">MapInfo TAB (MITAB)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\Parks\Parks.tab</td>
</tr>

</table>


<br>**6) Add NeighborFinder**
<br>Add a NeighborFinder transformer, which we can use to determine the nearest park to each address, and how far away it is.

Connect the Junction transformer to the NeighborFinder:Base input port, and the Parks feature type to the NeighborFinder:Candidate input port:

![](./Images/Img5.205.Ex1.NeighborFinderOnCanvas.png)

Inspect the parameters. We want to find only 1 neighbor, with no maximum distance.


<br>**7) Add AttributeRenamer**
<br>Add an AttributeRenamer transformer to rename the attribute _*distance* to *ParkDistance*:

![](./Images/Img5.206.Ex1.AttributeRenamer.png)

Add a bookmark around the section of workspace that deals with parks. Run that section of workspace by selecting the bookmark and choosing Run to Contained:

![](./Images/Img5.207.Ex1.RunToContained.png)

Inspect the output to ensure it is correct.


<br>**8) Save as Template**
<br>Because this project may be continued at a later date, save the workspace but use File &gt; Save As Template. When prompted, be sure to have the Include Feature Caches option checked:

![](./Images/Img5.208.Ex1.SaveCaches.png)

Now if we come back to this project later, we can reopen the template and have all our cached data ready for use.

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
<ul><li>Rearrange transformers into a logical layout that groups those carrying out a single task</li>
<li>Use annotations to clarify the processes taking place in a workspace</li>
<li>Use bookmarks to turn a single workspace into defined sections</li>
<li>Avoid poor design choices like overlapping connections</li>
<li>Run just a single bookmark in a workspace</li>
<li>Save a workspace as a template, including caches</li></ul>
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
<span style="color:white;font-size:x-large;font-weight: bold">Methodology</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Addresses (Esri Geodatabase)<br>Crime Data (CSV - Comma Separated Value)<br>Parks (MapInfo TAB)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Work on Vancouver Walkability Project</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Methodology Best Practice</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\BestPractice-Ex2-Begin.fmwt</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\BestPractice-Ex2-Complete.fmwt</td>
</tr>

</table>


Continuing on from the previous exercise, you have been assigned to a project to calculate the "walkability" of each address in the city of Vancouver. Walkability is a measure of how easy it is to access local facilities on foot. The initial workspace analyzed crime in the area, and you added a section to calculate the distance to the nearest park. 

Now we can extend the project to see if each address falls inside a noise-control area.

---

<br>**1) Add Reader**
<br>Our first task is to read noise-control area data. This can be found in the following dataset:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">OGC GeoPackage</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\Planning\PlanningRestrictions.gpkg</td>
</tr>

</table>

We'll try to improve performance by using a FeatureReader transformer to read this data, using the Addresses as a trigger; so place a FeatureReader transformer and connect it up to the AttributeRenamer.

Inspect the transformer's parameters. Set the Reader parameters as above. Read only the NoiseControlArea feature type and set the Spatial Filter parameter to Initiator is Within Result:

![](./Images/Img5.209.Ex2.FeatureReaderParams.png)

Reading the data this way may benefit performance because we're only reading noise control areas that we know addresses fall inside. We'll see...


<br>**2) Overlay Addresses and Noise Control Zones**
<br>To do the overlay, add a PointOnAreaOverlayer transformer. Connect FeatureReader:&lt;Initiator&gt; to the Point input port, and FeatureReader:NoiseControlArea to the Area input port:

![](./Images/Img5.210.Ex2.POAOCanvas.png)

Inspect the parameters and turn on the Merge Attributes option. Run the workspace using Run to This... sadly the workspace is takes a long time to run, so press the Stop button to cancel the translation. 


<br>**3) Add Creator**
<br>It's clear that the current setup is not the best solution. A polygon feature is output from the FeatureReader for every address that overlaps it, causing the PointOnAreaOverlayer to slow down. Our gamble has failed.

So, add a Creator transformer to trigger the FeatureReader, and disconnect it from the AttributeRenamer, leaving other connections intact:

![](./Images/Img5.211.Ex2.RearrangedFeatureReader.png)

Check the FeatureReader parameters and reset the Spatial Filter parameter to &lt;No Spatial Filter&gt;.

Now re-run this part of the workspace and inspect the output to ensure some address features are receiving AreaID, AreaName, and AreaDescription attributes.


<br>**4) Set a Numeric Value**
<br>To help with assessing walkability, we'll give each different zone a numeric value, relative to the benefit they would provide residents walking through the city:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Schedule F</td>
<td style="">50</td>
</tr>

<tr>
<td style="font-weight: bold">Schedule C</td>
<td style="">200</td>
</tr>

<tr>
<td style="font-weight: bold">Intermediate</td>
<td style="">100</td>
</tr>

</table>

One technique would be to use Tester and AttributeCreator transformers, like so:

![](./Images/Img5.212.Ex2.BadMappingTechnique.png)

However, this is clearly a case of duplication. This is hard to maintain and if extra schedules were added would require an extra Tester/AttributeCreator combination for each.

So, instead of that place an AttributeValueMapper transformer connected to the PointOnAreaOverlayer:Point output port:

![](./Images/Img5.213.Ex2.GoodMappingTechnique.png)


Inspect the AttributeValueMapper's parameters. Set it up to map from AreaName to NoiseZoneScore, with a default value of zero (0):

![](./Images/Img5.214.Ex2.AVMParams1.png)

Now set up the mapping using the values in the table shown above:

![](./Images/Img5.215.Ex2.AVMParams2.png)

You can either set this up manually (by typing in the values) or automatically (by using the Import button).

Put a bookmark around this section of the workspace and run it. Inspect the cached results to prove that addresses are being given the correct value.


<br>**5) Clean Output**
<br>Inspecting the output becomes hard at this point because there are so many excess attributes cluttering the display. These attributes can hardly be helping performance of the workspace either - even if that's mitigated by using caches during development.

Check the size of the template file BestPractice-Ex2-Begin.fmwt. You'll see that it is nearly 46mb in size, which is fairly large for a template. Save the workspace now and the file would likely be even larger. It's not a problem to have a large template file, but it does indicate a lot of data is being cached and that this could affect the workspace's performance.

One aspect of data is the number of attributes and lists. To remove some of these place an AttributeRemover transformer at the end of the workspace. 

Inspect its parameters and set them up to remove any attributes and lists that you suspect are not required in the output.

One item of interest is a list attribute called CrimeList{}, which doesn't appear necessary for any part of this translation. Track down its source by pressing Ctrl+F and searching for that phrase. You will find it is being created by the Aggregator transformer. 

Check the parameters for the Aggregator transformer and turn off the Generate List parameter, to prevent the list from being created. This will cause many caches to become stale, but we will re-run the workspace shortly to solve this.


<br>**5) Collapse Bookmarks**
<br>Another source of excess caching are transformers producing output that we don't need to inspect. These can be prevent by hiding these transformers within a collapsed bookmark.

So, pass through the workspace collapsing bookmarks where we know the transformers within it are producing the correct output:

![](./Images/Img5.216.Ex2.CollapsedBookmarks.png)

You may wish to rename some of the ports on the bookmarks to clarify what they do:

![](./Images/Img5.217.Ex2.RenamedBookmarkPorts.png)


<br>**6) Re-Run Workspace**
<br>Now re-run the workspace by clicking on the AttributeRemover and choosing *Run to This*.

The workspace will run and data will be cached, but only at the output point of bookmarks. Also attributes unnecessary to the output will be removed.

Save the workspace as a new template and check the option to include caches. This way the workspace will be ready to continue later.

Check the file size of the new template. It should be considerably smaller (around 14mb).


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
<ul><li>Assess reader performance and when the FeatureReader is not a good choice</li>
<li>Avoid duplicating transformers to improve maintenance and scalability</li>
<li>Remove unnecessary attributes to improve performance</li>
<li>Track down unnecessary lists and remove them</li>
<li>Improve performance by collapsing bookmarks to prevent excess caching</li></ul>
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
<span style="color:white;font-size:x-large;font-weight: bold">Debugging a Workspace</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Addresses (Esri Geodatabase)<br>Crime Data (CSV - Comma Separated Value)<br>Parks (MapInfo TAB)<br>Swimming Pools (OSM - OpenStreetMap)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Work on Vancouver Walkability Project</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Debugging Best Practice</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\BestPractice-Ex3-Begin.fmwt</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\BestPractice-Ex3-Complete.fmwt</td>
</tr>

</table>


Continuing on from the previous exercise, you have been assigned to a project to calculate the "walkability" of each address in the city of Vancouver. Walkability is a measure of how easy it is to access local facilities on foot. The workspace currently assesses crime, parks, and noise-control areas, but it doesn't give an overall measure of walkability.

So let's do that, and then see if there are any other aspects we can include.

---

<br>**1) Add ExpressionEvaluator**
<br>We can create a measure of walkability that combines all of our current values using the ExpressionEvaluator transformer.

So add an ExpressionEvaluator transformer to the end of the workspace.

Inspect its parameters. Set it up to create a new attribute called Walkability that is:

<pre>
ParkDistance + CrimeValue - NoiseZoneScore
</pre>

![](./Images/Img5.218.Ex3.ExpressionEvaluatorDialog.png)

With this expression, the smaller the result, the better. Run the workspace using Run from This on the ExpressionEvaluator.


<br>**2) Assess Result**
<br>Let's assess whether the result of the translation is correct. 

Firstly check the log window for errors and warnings. There are no errors, but there are over 13,000 warnings, which is not a good sign:

![](./Images/Img5.219.Ex3.LogWarningCount.png) 

The warnings say:

<pre>
ExpressionEvaluator: Failed to evaluate expression '@real64(560.3272250455418+&lt;null&gt;-0)'.  
Result is set to null
</pre>

Inspect the output cache and some addresses do indeed have a Walkability value of &lt;null&gt;. 

So we know there is a problem, let's try and figure out where the problem is and why it occurs.


<br>**3) Locate Problem**
<br>We can tell the warning comes from the ExpressionEvaluator, but that doesn't necessarily mean that is where the problem lies. The calculation fails because the middle value is &lt;null&gt;. If the expression is:

<pre>
ParkDistance + CrimeValue - NoiseZoneScore
</pre>

Then we know that it must be the CrimeValue that is an issue. Expand the bookmark that carries out the crime calculation. Then carry out a Run From This on the FeatureJoiner transformer, so that we have caches for transformers in the bookmark, and feature counts for all connections:

![](./Images/Img5.220.Ex3.CrimeBookmarkExpanded.png)

We know that some features from here are getting a &lt;null&gt; result. Firstly check the cache for the AttributeValueMapper. That's where values are set, so perhaps there are nulls coming out of there?

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
A useful test would be to right-click on CrimeValue in the Table View window, and sort by ascending numeric order. That will put any null values to the top of the table.
</span>
</td>
</tr>
</table>

---

On inspection, I find there are no &lt;null&gt; values for the CrimeValue attribute in there. Neither are there nulls for the Aggregator and CenterPointReplacer caches.

So check the feature counts on each connection. There are 4,270 features tagged with a crime, and 9,327 that are not. That gives a total of 13,597, which is correct.

Oh. Do you see it yet? The 9,327 features that are not tagged with a crime: what CrimeValue do they get? Inspect the UnjoinedLeft output from the FeatureJoiner and you will see that they do not have a value. That's why the ExpressionEvaluator says that there are nulls.

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
To confirm this I copied the log into a text editor and searched for the phrase "ExpressionEvaluator: Failed to evaluate expression".
<br>It appeared 9,327 times, the same as the number of features that exit the UnjoinedLeft port. Coincidence?
</span>
</td>
</tr>
</table>

---

<br>**4) Fix Problem**
<br>If those features do not have a CrimeValue attribute, then we should give them one. To do so add an AttributeCreator transformer to the workspace and expand the Manage Crime Data Joins bookmark to enclose it:
 
![](./Images/Img5.221.Ex3.AttributeCreatorOnCanvas.png)

Open up its parameters and create an attribute called CrimeValue with a value of zero (0).

![](./Images/Img5.222.Ex3.AttributeCreatorParams.png)

Collapse the bookmark and re-run the workspace (using Run to This on the ExpressionEvaluator). You should now find that there are way fewer warnings, and that the output contains no &lt;null&gt; values.


<br>**5) Round Attribute**
<br>One issue in the data is that the results are measured to multiple decimal places. This is not necessary. A quick look at the data shows us the ParkDistance result is the one to blame. 

So, locate where the ParkDistance value is created and add an AttributeRounder transformer to round it to zero decimal places:

![](./Images/Img5.222a.Ex3.AttributeRounder.png)


<br>**6) Add Swimming Pools**
<br>Since we now have the ability to calculate walkability values, let incorporate swimming pools into the calculation. To do this add a reader with the following:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">OpenStreetMap (OSM) XML</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2018\Data\OpenStreetMap\leisure.osm</td>
</tr>

</table>

When prompted, select only the leisure feature type:

![](./Images/Img5.223.Ex3.LeisureFeatureType.png)


<br>**7) Filter Leisure Data**
<br>If you inspect the leisure data you'll notice that there are various types of leisure facility, the type being recorded in the *leisure* attribute.

So, set up a Tester transformer to test for leisure = swimming_pool

![](./Images/Img5.224.Ex3.SwimmingPoolTester.png)


<br>**8) Find Nearest Pool**
<br>The technique to find the nearest swimming pool is identical to that to find the nearest park. So simply expand the Nearest Park bookmark, and copy/paste the transformers from inside it. 

Place a bookmark around it and connect it up in the same way as the parks section:

![](./Images/Img5.225.Ex3.NearestSwimmingPoolSection.png)

Inspect the parameters of the newly pasted transformers. The NeighborFinder transformer has nothing that needs to be set, but the AttributeRenamer and AttributeRounder need to use PoolDistance instead of ParkDistance.


<br>**9) Update ExpressionEvaluator**
<br>Now simply update the ExpressionEvaluator to take account of the new PoolDistance attribute:

![](./Images/Img5.226.Ex3.UpdatedExpressionEvaluator.png)

Re-run the workspace. Check the log for warnings and errors, and then inspect the ExpressionEvaluator cache.

Notice that the walkability scores are exceedingly large all of a sudden, due to the PoolDistance. Something is wrong, but what?


<br>**10) Locate Problem**
<br>The PoolDistance is obviously the source of the problem. There is no related log message to give a clue and the Feature Count numbers look correct.

So, right-click the Find Nearest Pool bookmark and choose Select all Objects in Bookmark. Now press Ctrl+I to inspect the selected objects' caches. 

The display window in the Data Inspector shows two small specks of data, a long distance apart. This is typical of a mismatch of coordinate systems.

Query some features and you will see that the main data has a coordinate system of UTM83-10, while the leisure data from OSM has a coordinate system of LL84.

This is why the "nearest" pool to each address is such a high distance.


<br>**11) Fix Coordinate System Problem**
<br>The obvious solution is to reproject the pools to the correct coordinate system. So, add a Reprojector transformer to reproject the leisure data before it gets to the NeighborFinder:

![](./Images/Img5.227.Ex3.ReprojectorOnCanvas.png)

Inspect its parameters and set it up to reproject from LL84 to UTM83-10

Collapse all bookmarks and re-run the appropriate parts of the workspace. Check the log window and inspect the ExpressionEvaluator cache. 

Each address now has a walkability score, with a lower number being better and a higher number worse.

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
<ul><li>use the ExpressionEvaluator transformer</li>
<li>Check the log window for errors and warnings</li>
<li>Locate problems through use of Feature Counts and Data Inspection</li>
<li>Identify and fix problems in a workspace</li></ul>
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
<span style="color:white;font-size:x-large;font-weight: bold">FME Hackathon</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Roads (Autodesk AutoCAD DWG and/or PostGIS)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Find the shortest route from the hackathon to an Italian Cafe</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Data Translation, Transformation, and Best Practice</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\DesktopBasic\BestPractice-Ex4-Complete.fmw</td>
</tr>

</table>


A regional GIS group is holding an FME Hackathon and you have been invited to take part.

You have been provided with a set of source data and asked to create a useful project from it. You decide that it would be interesting to produce a tool that maps the route from the hackathon venue to a cafe where a group get-together will be held that evening.  

So, your task is to use the data available to you to calculate the best route from the convention centre to the cafe, and to write out that data to GPX format so folk can use it in their GPS/mobile device.

---

**1) Create Database Connection**
<br>The source data has been provided in a PostGIS database; therefore our first task should be to create a connection to it. That way we can use the connection instead of having to enter connection parameters.

In a web browser visit [http://fme.ly/database](http://fme.ly/database) - this will show the parameters for a PostGIS database running on Amazon RDS.

In Workbench, select Tools &gt; FME Options from the menubar

Click on the icon for the Database Connections category, then click the [+] button to create a new connection. In the "Add Database Connection" dialog, first select PostgreSQL as the database type. Then enter the connection parameters obtained through the web browser.

![](./Images/Img5.228.Ex4.DatabaseConnectionDialog.png)

Give the connection a name and click Save. Then click OK to close the FME Options dialog.

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
The completed workspace for this exercise uses a database connection called <strong>Hackathon PostGIS Database</strong>
<br>If you wish to open/use this workspace, you should create your connection with the same name. That way when you open the workspace it will automatically find a matching connection. 
<br><br>This is a good illustration of the importance of naming conventions for database (and web) connections.
</span>
</td>
</tr>
</table>

---

**2) Inspect Data**
<br>Start the FME Data Inspector to inspect the dataset we will be using. Select File > Open Dataset and, when prompted, enter the following:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">PostGIS</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">Hackathon PostGIS Database</td>
</tr>

<tr>
<td style="font-weight: bold">Parameters</td>
<td style="">Table List: public.CompleteRoads</td>
</tr>

</table>

Click OK to close the dialogs and open the data. You will see a set of road features each of which has a set of attributes. One attribute specifies whether a feature represents a one-way street. It's important to know this if we want to calculate a route that is actually legal!

![](./Images/Img5.229.Ex4.SourceRoadsData.png)

***NB:*** *If you have any problems using the PostGIS database - for example connectivity problems with a firewall - then the following AutoCAD dataset can be substituted with very few changes required:*

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


<br>**3) Start Workbench**
<br>Start Workbench and use the option to Generate a workspace.


<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">PostGIS</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">Hackathon PostGIS Database</td>
</tr>

<tr>
<td style="font-weight: bold">Parameters</td>
<td style="">Table List: public.CompleteRoads</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Format</td>
<td style="">GPS eXchange Format (GPX)</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Dataset</td>
<td style="">C:\FMEData2018\Output\Training\Route.gpx</td>
</tr>

</table>


The workspace will look like this:

![](./Images/Img5.230.Ex4.InitialWorkspace.png)

Remember, GPX is a fixed-schema format, hence the six different writer feature types that are automatically created.


<br>**4) Add ShortestPathFinder**
<br>Now we need to start calculating a route. The obvious first step is to add a ShortestPathFinder transformer, which is how we can calculate our route.

So, add a ShortestPathFinder transformer. Connect public.CompleteRoads to the Network port.


<br>**5) Add Creator**
<br>The other input port on the ShortestPathFinder is for the From-To path (the start and end points of our journey). There are many ways to create this - or even accept input from a web map - but here we'll just manually create a feature with the Creator transformer. 

So, add a Creator transformer and connect it to the From-To port:

![](./Images/Img5.231.Ex4.CreatorOnCanvas.png)

Inspect the Creator's parameters.

Firstly enter UTM83-10 as the coordinate system of the data we are about to create. For the Geometry Object parameter, click the [...] browse button to the right to open a geometry-creation dialog. Select Line as the geometry type and enter the following coordinates:

<pre>
X 491500 Y 5459550
X 494500 Y 5457440
</pre>

The first coordinate is that of the hackathon venue and the second is the closest point in our network to the cafe we're going to visit.

![](./Images/Img5.232.Ex4.CreatorParams.png)

Click the OK button to confirm the changes.


<br>**6) Check ShortestPathFinder Parameters**
<br>The coordinates of the feature we've added might not sit exactly on the road network. To get around this issue there are parameters we can use in the ShortestPathFinder.

So, inspect the ShortestPathFinder parameters. Under Snap Options set **From-To and Network Snapping** to *Yes* and enter *150* as the **Snapping Tolerance**:

![](./Images/Img5.233.Ex4.SPFSnapParameters.png)

Also notice that there are parameters for network costs - we'll be making use of those later.


<br>**7) Run Workspace**
<br>Ensure feature caching is turned on and run the workspace. Check the log and then inspect the ShortestPathFinder:Path cache. If all has gone well, the output will look like this, with a route defined:

![](./Images/Img5.234.Ex4.SPFInitialRoute.png)
<br><span style="font-style:italic;font-size:x-small">Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC-BY-3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC-BY-SA</a>.

Of course, if all has not gone correctly, you must make use of your debugging skills to try and locate the error!


<br>**8) Add AttributeValueMapper**
<br>The result looks fine, but there are some things we are yet uncertain about: for example what if the route uses slower, residential roads? We can force the route to prefer arterial routes by applying a different cost to each road feature.

The cost will depend on the road type. In essence we are mapping road type to cost and the way to do that is with an AttributeValueMapper transformer.

So, add an AttributeValueMapper transformer to the workspace, between the CompleteRoads feature type and the ShortestPathFinder:Network port:

![](./Images/Img5.235.Ex4.AVMOnCanvas.png)


<br>**9) Edit AttributeValueMapper**
<br>Inspect the AttributeValueMapper's parameters. Enter the following values:

<table>
<tr><td style="font-weight: bold">Source Attribute</td><td align=center>streettype</td></tr>
<tr><td style="font-weight: bold">Destination Attribute</td><td align=center>Cost</td></tr>
<tr><td style="font-weight: bold">Default Value</td><td align=center>2</td></tr>
</table>

![](./Images/Img5.236.Ex4.AttributeValueMapperParams1.png)

Now, underneath those parameters, we'll map some data.

<table>
<tr><th>Source Value</th><th>Destination Value</th></tr>
<tr><td>Arterial</td><td align=center>1</td></tr>
<tr><td>Residential</td><td align=center>3</td></tr>
</table>

![](./Images/Img5.237.Ex4.AttributeValueMapperParams2.png)

Basically, if the route is arterial (a main road) it will get a cost of 1; residential routes will get a cost of 3 and all other types will get a cost of 2 (because that's the default value). Click Accept/OK to confirm the parameters.


<br>**10) Apply Costs**
<br>Now we have to apply the costs we have just created. Inspect the ShortestPathFinder's parameters. Enter the following values:

<table>
<tr><td style="font-weight: bold">Cost Type</td><td align=center>By Two Attributes</td></tr>
<tr><td style="font-weight: bold">Forward Cost Attribute</td><td align=center>Cost</td></tr>
<tr><td style="font-weight: bold">Reverse Cost Attribute</td><td align=center>Cost</td></tr>
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
Why "Two Attributes"? That's because with only a forward cost, I could only ever travel along a stretch of road in the same direction as the vertices are arranged in. Since I don't want to avoid roads based on their vertex direction, using two attributes tells FME the cost is the same in both directions.
</span>
</td>
</tr>
</table>

---

Now re-run the workspace to see if there is any difference in the result. It should look like this:

![](./Images/Img5.238.Ex4.WeightedRoute.png)
<br><span style="font-style:italic;font-size:x-small">Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC-BY-3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC-BY-SA</a>.

So the cost weighting has obviously made a difference. But there is a problem with this result...

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
The route is taking a longer path this time, and I can see a reason why that might be: cost is being used to weight routes <strong>instead</strong> of the distance, not as well as. 
<br><br>To explain this, let's say I want to travel from A to B. There is a single residential road feature that starts at A and ends at B, with a route distance of 1.5 kilometres. 
<br><br>There is also a single arterial road feature that starts at A and ends at B. Rather extremely, it loops around the dark side of the moon with a route distance of 768,000 kilometres. 
<br><br>Currently our solution would choose the 768,000 kilometre trip, because it has a cost of "1" compared to the residential route cost of "3"!
<br><br>Plainly the exercise data here is nowhere near as ridiculous, but it's equally plain that the route might not be the optimum until distance is factored back into the result. 
</span>
</td>
</tr>
</table>

---

<br>**11) Add AttributeManager**
<br>Add an AttributeManager transformer between the AttributeValueMapper:Output port and the ShortestPathFinder:Network port and view the parameters.

In the value field for the Cost attribute, click the dropdown arrow and select Open Arithmetic Editor. In that dialog enter the expression:

<pre>
@Value(Cost)*@Length()
</pre>

![](./Images/Img5.239.Ex4.ExpressionEvaluatorParams.png)

In short, we're now multiplying cost by road length to give us a combined weighting.

Re-run the translation to see if it makes a difference:

![](./Images/Img5.240.Ex4.DistanceWeighted.png)
<br><span style="font-style:italic;font-size:x-small">Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC-BY-3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC-BY-SA</a>.

Yes, it does, proving that the route was longer than it could be. Of course, the expression we've used is again very subjective, and could be made more complex to give a better result (we could try a logarithmic scale to see what that produced).


<br>**12) Edit AttributeManager**
<br>Regardless of our expression, there's another last snag to cover... one-way streets. Currently we have no solution in place to prevent us driving the wrong direction.

Luckily each one-way street is flagged with an attribute, and has its vertices ordered in the direction of permitted travel, so we know which way to avoid. Let's use this information to solve that problem.

We'll need to calculate different cost attributes for each direction now, although the value will only differ when a one-way street is involved. There are - as usual - multiple ways to handle this in FME; let's go with a moderately easy one.

View the AttributeManager parameters again. This time create a new Output Attribute called ReverseCost. In the value field click the drop down arrow and choose Conditional Value.

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
Conditional Values are those that are set dependent on a test condition. It's like incorporating a Tester into the AttributeManager. These are covered in more detail in the FME Desktop Advanced training course.
</span>
</td>
</tr>
</table>

---

In the definition dialog that opens, double-click in the first "If" row and a Test Condition dialog opens. In here set up a test for oneway = Y. For the Output Value (bottom of the dialog) enter the value 9999 (i.e. the cost of travelling the wrong way is *really* expensive)!

![](./Images/Img5.241.Ex4.ConditionalCostY.png)

Click OK to close that dialog. Back in the previous dialog, double-click where it says &lt;No Action&gt; choose the dropdown arrow and select Attribute Value &gt; Cost:

![](./Images/Img5.242.Ex4.ConditionalCostConditions.png)

Click OK again twice more to close these dialogs. 

What we've essentially done is say that if this is a one-way street, set a prohibitively high reverse cost, otherwise just set the usual forward cost.


<br>**13) Apply Cost**
<br>One last change. Check the ShortestPathFinder parameters and change the ReverseCost attribute from Cost to ReverseCost:

![](./Images/Img5.243.Ex4.SPFReverseCost.png)

Now we're ready to go. Re-run the workspace and check the output:

![](./Images/Img5.244.Ex4.FinalOutput.png)

There is at least one change (above) caused by a route that previously travelled the wrong-way (west-east) along a street that is one way (east-west)!


<br>**14) Connect Schema**
<br>Oh! Don't forget to turn off feature caching and connect the Path port to the Route output feature type:

![](./Images/Img5.245.Ex4.FinalWorkspace.png)

Now run the workspace, upload the data to your GPS device, and you are ready to go!

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
Not really advanced, but you did use Best Practice throughout, right? I mean, you have bookmarks and annotations where needed, and no overlapping connections? If not, well you might want to fix that!
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
By completing this exercise you proved you know how to:
<br>
<ul><li>Create and use an FME database connection</li>
<li>Create a prototype FME workspace using a variety of transformers</li>
<li>Use debugging techniques to find any problems encountered in an exercise</li>
<li>Use a good style for developing workspaces</li></ul>
</span>
</td>
</tr>
</table>


