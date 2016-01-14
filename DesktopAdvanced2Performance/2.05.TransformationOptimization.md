# Transformation Optimization

Now that you can interpret a log file, you can start to work on improving the performance of your data transformation.

**Assessing Transformation Performance**

As with Readers and Writers, you can’t make performance improvements unless you can accurately interpret a log file and measure a baseline performance for your translations.

If you want to be able to assess the time taken in transformation then the first thing to do is calculate the read time so that it can be ignored. So firstly disable everything in the workspace except the Readers and run the workspace. Take a note of the elapsed time.

Now re-enable the transformers, but leave the Writers disabled.

Don’t be tempted to add an Inspector or Logger transformer to the end to see what is happening to the output. This will only slow the translation down and give you a false measure.
And be sure to disable the actual Writer, and not just the feature types or connections to them.

The one Writer that is useful in this scenario is the Null format Writer.

This causes a Writer to be present, but it does nothing except to log features and then discard them.

The benefit is improved logging of feature counts, but without any data having to be written.

Now I know it took 5.4 seconds to read the data, and the whole process took 28.2 seconds, so I can infer that the transformation part takes 22.8 seconds.

With the Reader and Writer figures as well, I now have a complete breakdown of how long each section of my workspace takes.

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
“In a larger workspace you could isolate different sections by disabling
different connections, and therefore determine the performance of
individual parts of the workspace.”
</span>
</td>
</tr>
</table>

However, the time taken to carry out a translation is only one aspect of performance. Another important aspect is the amount of memory used during processing. You can’t tell how much memory each individual transformer used, but you can see the maximum memory used during a translation by examining the very foot of the log file:

*INFORM| Translation was SUCCESSFUL with 0 warning(s) (13597 feature(s) output)*

*INFORM| FME Session Duration: 28.3 seconds. (CPU: 27.3s user, 0.6s system)*

*INFORM| END - ProcessID: 28336, peak process memory usage: 178388 kb*

For performance tuning, the idea is to reduce this number, as the more memory used the more chance there is of laborious disk caching taking place.

**Improving Transformation Performance**

In most cases, slow, memory-consuming translations are caused by group-based transformers.

Remember that in feature-based transformation a transformer performs an operation on a feature-by-feature basis where a single feature at a time is processed. But in a group-based transformation a transformer performs an operation on a group or collection of features.

It is this grouping of data that causes performance degradation. Group-based transformers must store the group of features together (cached either to memory or disk) to be processed, whereas feature-based transformers do not need to do so.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Jake Speedie says….</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“You’ll get better performance when you put the least amount of data
into a group-based transformer as possible.
For example, put feature-based filter transformers BEFORE the group-based process,
not after it (see following exercise)”
</span>
</td>
</tr>
</table>

**Turning Group-based Transformers into Feature-based Transformers**

Obviously, when a group-based transformer is needed, then it must be used. However, most group-based transformers have a parameter that, in effect, turns them into feature-based.

The usual parameter is called "Input is Ordered by Group" and appears near the Group By parameter in most transformer dialogs.

The condition for applying this is that the groups of features are pre-sorted into their groups.
When this is the case, and I can set this parameter to Yes, then FME is able to process the data more efficiently.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Jake Speedie says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Let's think back to the airport departure gate boarding passengers. Most
airlines first call passengers with a physical disability, then passengers
with children, business-class passengers , and finally economy
passengers (starting with passengers at the front).
That's because it's easier to board passengers when they are sorted into similar groups,
and the same applies to FME. When passengers (or spatial features) arrive in a random
order it's not as simple to handle them.
</span>
</td>
</tr>
</table>

Besides the "Input is Ordered by Group" parameter, some transformers have their own, unique, parameters for performance improvements.

For example, the NeighborFinder expects two sets of data: Bases and Candidates. By default FME caches all incoming Bases and Candidates because it needs to be sure it has ALL of the candidates before it can process any bases.

But, if it knows the candidate features will arrive first (i.e. the first Base feature signifies the end of the Candidates) then it doesn’t need to cache Base features. It can process them immediately because it knows there are no more candidates that it could match against.

Look at this log file for a workspace that uses a NeighborFinder. By default it looks like this:

*Translation was SUCCESSFUL with 0 warning(s) (13597 feature(s) output)*

*FME Session Duration: 29.6 seconds. (CPU: 27.7s user, 1.5s system)*

*END - ProcessID: 28540, peak process memory usage: 231756 kb*

With Candidates First turned on it looks like this:

*Translation was SUCCESSFUL with 0 warning(s) (13597 feature(s) output)*

*FME Session Duration: 28.4 seconds. (CPU: 27.4s user, 0.8s system)*

*END - ProcessID: 26429, peak process memory usage: 178412 kb*

It’s about 5% faster than before, but more importantly it’s used nearly 25% less memory!

But how do we ensure the Candidate features arrive first? Well, like Writers you can change the order of Readers in the Navigator, so that the Reader at the top of the list is read first.

It doesn’t improve performance per se, but it does let you apply performance-improving parameters like this.

**Transformer Selection**

If you’ve used FME for any length of time, you’ll know that it’s possible to do almost any task in several different ways.

For example, you could check for matching features in two different datasets using either the Matcher transformer, or the ChangeDetector, or even the FeatureMerger!

Another example would be isolating all road features that pass through a park.

One could use either the Clipper, like so:

Or the LineOnAreaOverlayer, with a test for _overlaps => 1, like so:

The performance for the LineOnAreaOverlayer would be this:

While the Clipper (in Multiple Clippers mode) would be this:

And in Clippers First mode would be this:

So the result is the same, but the performance vastly different.

Obviously in the above example the Clipper is the fastest (and be sure to note how the Clippers First mode has reduced memory use by nearly 90%).

But each transformer has different functionality, and if you wanted to output park features with a list of roads or a count of the roads passing through the park, then the LineOnAreaOverlayer would be the transformer of choice, because it has a specific list parameter.

Basically, each transformer works in a different way, has subtle variances in functionality, and
will have different performance for any given task. Therefore a translation will benefit in
performance if the author is careful in their choice of transformers, and maybe carries out
some testing first.

**Attributes and Transformation**

As mentioned (in Reader Performance) reducing data helps performance because it saves FME
from either holding it in memory or caching it to a disk.

However, this isn’t just helped by reducing the number of features; it is also helped by reducing the size of each individual feature.

One aspect of this is attributes. Carrying attributes through a translation impacts performance, so if the attributes are not required in the output, it’s best to remove them as early as possible in the translation.

For example, the incoming schema looks like this:

But the outgoing schema looks like this:

Since so many of the source attributes are not required in the output, it makes sense to remove them from the translation, and as early as possible by using an AttributeRemover (or Keeper) directly after the source feature type:

One specific type of attribute to beware of is a List. A List is an attribute that can have multiple values. Because of this it can be a big drain on resources.

For example, use a Joiner to join a feature to 1000 records and the list for that feature will have 1,000 sets of records. This is bad enough, but if the list is exploded and all of the original attributes kept, then there will be 1,000 features each with 1,000 sets of attributes!

Another particular problem is carrying around spatial data as attributes. Spatial database formats - for example Oracle or GeoMedia - usually store geometry within a field in the database; for example GEOM. When FME reads the data it converts the GEOM field into FMEstyle geometry and drops the field from the data.

However, if you read a geometry table with a non-geometry Reader, the translation could end up with the geometry stored as an FME attribute. A similar thing could happen when a workspace reads only one geometry column of a multiple geometry table.

Geometry will create very large and complex attributes, which take up a great deal of resources. If you don’t need them, then it’s worth removing them.

Basically, you should only carry through the translation any geometry and attributes you need for the output of your workspace. If the data is not required, then it can and should be removed as early in the workspace as possible.

**Geometry and Transformation**

Like attributes, geometry can be removed from a feature using the GeometryRemover transformer.

Many FME users create translations that handle tabular – non-spatial – data. If you are reading a spatial dataset, then writing it to a tabular format, be sure to remove the geometry early in the workspace, just as you would an attribute.

Additionally, you can reduce the size of individual features by removing vertices. The Generalizer transformer will help you to do so and has very many parameters to control the results.

**General Optimizations**

Here are a few general suggestions that can be used to improve the performance of a workspace. Some of these come straight from our developers.

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
“It’s said that the race driver Michael Schumacher would tilt his head
slightly when racing, to allow more air into the engine intake.
If, like him, you measure performance down to the millisecond, then these tips are for
you!”
</span>
</td>
</tr>
</table>

- Avoid Run with Full Inspection

If you aren’t debugging a translation, then avoid using the Run with Full Inspection option (new for FME2015). It stashes all data for every connection in the workspace, meaning performance is significantly reduced.
- Remove (or Disable) Excess Loggers and Inspectors

Similarly, if you aren’t debugging a translation there’s no need for Logger or Inspector
transformers. Remove – or disable – them and your workspace will run more efficiently.
- Use Inspectors, not Loggers
If you are intending to inspect a large number of features, then use the Inspector and not
the Logger transformer. Logging speeds have improved greatly in the last few versions of
FME, but it is still a relatively slow process compared to sending features to the
Inspector.
- Use the Command Line

Once you have constructed your workspace, run it from the command line instead of
from Workbench. It may operate slightly faster.
- License Type

It might only be a tiny amount, but an FME with a floating (concurrent) license has to query the license server and so is marginally slower than fixed licenses.

Let’s continue to work on the workspace that processes a dataset of cell phone signals.

We’ve already deconstructed the log and cleaned up the Readers and Writers. Now let’s use our new knowledge of transformation performance to try and speed up the workspace.

**1)** Start Workbench

Open the workspace C:\FMEData2015\Workspaces\DesktopAdvanced\Exercise2c-Begin.fmw which follows on from exercise 2b.

**2)** Check for Extra Transformers

The first aspect of the workspace to check is any extra transformers that aren’t needed and that will be slowing performance. The most obvious is the Logger transformer. It was presumably used for debugging the original workspace but is now doing nothing for us.

So, delete the Logger transformer attached to the CSV Reader.

**3)** Remove Attributes

Another quick fix we can do is to remove any attributes we don’t need, right at the start of the workspace. Check the schemas of the Reader and Writer feature types:

The Readers contain quite a lot of attributes, on both datasets. The Writers contain very few attributes, and the GoodLocations feature type has none at all. This suggests we can remove some attributes that are not going to be needed in the output.

Put an AttributeKeeper transformer after the Neighborhood feature type, but before the Clipper.

Use it to keep only the NeighborhoodName attribute.

Now do the same to the CSV (signal) data, keeping only the attributes StationID, Power, and Quality.

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
“Do we really need to remove attributes from only six neighborhood
features?
Yes! Because we’re copying them onto (depending on the source dataset used) 1.7
million CSV features.”
</span>
</td>
</tr>
</table>

**4)** Check Group-Based Processes

The Clipper is a group-based transformer; it has to be since it is processing both the neighborhoods and the cell signal data.

There’s no real indication this is the wrong transformer to use (although there are others) but we should check if there’s a way to turn the transformer into one that operates on a feature basis.

Open the Clipper parameters. Notice that there is a parameter for Clipper Type. Change this to Clippers First:

This will make this a feature-based transformer. Each clippee will not need to be cached because the full set of clippers is already known.

However, we have to make sure the Clippers really do arrive first, and this we can do by making the Clippers the first Reader in the Navigator window.

So, right-click the VancouverNeighborhoods Reader in the Navigator window and choose Move Up to bring it to the top of the list:

**5)** Run Workspace

Let’s run the workspace to see what we have so far.

Remember, after Reader improvements we had this result:

*FME Session Duration: 2 minutes 26.5 seconds. (CPU: 133.8s user, 12.4s system)*

*END - ProcessID: 98972, peak process memory usage: 1734748 kB*

The result now is:

*FME Session Duration: 2 minutes 16.6 seconds. (CPU: 126.6s user, 6.9s system)*

*END - ProcessID: 102032, peak process memory usage: 109780 kB*

It’s improving (especially the memory use). But I think we can still do better!

**6)** Rearrange Transformers

Looking at the workspace, the Neighborhood attribute is only required by the bad (low power) features. It isn’t needed by the good locations.

But, we’re still attaching the information onto all of the features, good or bad.

We could prevent that by moving the Tester transformer to before the Clipper.

So, select the Tester transformer and press Ctrl+X to cut it from the workspace. Notice that the connections are healed automatically, though they aren’t quite right.

Now press Ctrl+V to paste the Tester back into the workspace, but unconnected. Now drag it into the CSV data stream, but before it reaches the Clipper:

Finally, let’s fix the feature mapping.

Click on the connection from Clipper:Inside > GoodLocations, making sure to click closer to the Clipper than the feature type.

Then drag that connection onto the Tester:Failed port.

Re-run the workspace. The result will be something like this:

*FME Session Duration: 1 minutes 41.6 seconds. (CPU: 88.7s user, 12.2s system)*

*END - ProcessID: 220504, peak process memory usage: 110028 kB*

Hurrah! Compared to the original log we’re over 50% faster with 95% less memory use!

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
There is, perhaps, one other way we can upgrade this workspace’s performance. It’s
radical and unintuitive, but it might just work!
</span>
</td>
</tr>
</table>

Do you remember the previous tip about using the PointCloud XYZ reader for CSV data? Let’s give that a try and see what we can do.

Open the workspace C:\FMEData\Workspaces\DesktopAdvanced\Exercise2c-Begin-Advanced.fmw

Firstly, delete the CSV Reader (and feature types), the AttributeRemover/Keeper for the CSV data, and the Tester transformer too.

Now select Reader > Add New Reader and in the Add Reader dialog enter the following values:

Reader Format Point Cloud XYZ

Reader Dataset C:\FMEData2015\Data\CellSignals\CellSignals2015.csv

What are going to be key here are the Reader parameters, so click the Parameters button.

Firstly make sure the Separator Character is set to a comma (not “space”). Also check the option for "File Has Field Names."

Then in the Point Cloud Component Map, set the following:

You can type a component name, which is what you will have to do for all of them except the X and Y fields.

This will cause each column in the CSV data to be stored as a point cloud component.

It’s important to get this exactly right, as you will have to re-add the Reader to fix any problems.

Click OK to close the dialog and OK again to add the Reader.

A point cloud feature is not the same as a number of point features, so we will have to convert the data at some stage. However, let’s see if we can make use of some point cloud functionality first.

Add a PointCloudFilter transformer.
This is the point cloud equivalent to a Tester and may be quicker than testing each point individually.

Open the parameters dialog for this transformer.

Under Expression select the option to open an arithmetic editor. In the editor, look under the list of Point Cloud components to the left and double-click on <user component> at the bottom of that list. Enter Power as the component name.

Now click on the end of the expression, enter a less than operator (<) and type the value -125.
The dialog should look like so:

Click OK to close that dialog. Enter a new port name of Bad Signal. Click OK.

The workspace now looks like this, with a new output port:

Add two PointCloudCoercer transformers to the workspace, one attached to each output from the PointCloudFilter. One output should be directed to the Clipper:Clippee port, the other to the GoodLocations output feature type:

The final step is to set the coercer parameters and expose some attributes.

Open the parameters dialogs for each of the PointCloudCoercers in turn.

In both cases, set Output Geometry to Individual Points.

Again, in both cases, set Preserve Point Components As to Attributes.

For the <Unfiltered> data, which doesn’t need attributes, leave the Point Components to Preserve section empty. For the Bad Signal data, enter the following component names to extract them as attributes:
- StationID
- Power
- Quality

Now save and run the workspace. This time the log will report the performance as:

*FME Session Duration: 54.7 seconds. (CPU: 43.1s user, 10.9s system)*

*END - ProcessID: 111126, peak process memory usage: 124744 kB*

Well done! The memory use is up slightly, but the workspace is running faster than ever.