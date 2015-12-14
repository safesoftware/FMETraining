# Custom Transformers and Parallel Processing

Parallel Processing is a way to improve performance on high-end machines.

As noted in the Performance chapter, some FME transformers have the option to allow parallel processing. However, custom transformers have a special mechanism to do this. Whereas not all FME transformers allow parallel processing, you can apply this technique to ANY custom transformer that you like!

**Setting up Custom Transformer Parallel Processing**

Parallel processing for a custom transformer is set up in the Navigator window.
Each custom transformer has a set of transformer parameters that specifically relate to parallel processing. Here you can determine the level of parallel processing, and the attribute that is going to be used to define the processing groups:

By default, these are set to not carry out parallel processing. However, when the author sets a level of parallelism then the Parallel Process By parameter becomes active and a user parameter is automatically created:

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">First Officer Transformer says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“Because of how parallel processing works in a custom transformer, you
can’t use an attribute for the Parallel Process By parameter. Instead you
have to make use of a user parameter that references an attribute.
In short, you can’t select an attribute in this dialog, only user parameters.”
</span>
</td>
</tr>
</table>

The published parameter means that the end user is able to set the attribute to group-by for parallel processing. For example, here the custom transformer is creating a separate process for each different park feature:

If, as an author, I don’t want the end user to be setting the group-by, then what I can do is locate that published parameter, edit its definition, and unset the Published parameter:

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">First Officer Transformer says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“Are you using raster data?
Raster is an oddity in FME as most of the transformers do very little to the
data. For example, the RasterResampler doesn’t actually resample the data; it just tags
it as being resampled. The actual resampling is carried out when the data is written.
On the one hand this is great. It means – for example – if you resample then clip some
raster data, FME knows to resample only data that falls inside the clip boundary as the
rest is ultimately going to be discarded.
On the other hand, it does mean that parallel processing doesn’t help performance that
much, as most work occurs in the Writers. That’s why few raster transformers have
parallel processing options, and why it’s not worth doing in a custom transformer.”
</span>
</td>
</tr>
</table>

For this exercise we have been asked to convert point clouds to a vector point format that another department can use. We already have a workspace to do this, which nicely tiles and thins the data too so the destination datasets aren’t overwhelmed.

However, the workspace takes time to run and it might be better to use parallel processing.
Since none of the transformers used has a parallel processing parameter, we’ll have to create a custom transformer.

**1)** Open Workspace

Open the workspace C:\FMEData2015\Workspaces\DesktopAdvanced\Exercise3f-Begin.fmw

As you’ll see, this workspace processes some incoming point cloud data. Inspect the data to see what we’re dealing with. If you run the workspace as-is it will take approximately three minutes. To make it run a little faster you can increase the Thinning Interval parameter in the PointCloudThinner (say to 25).

Open a task manager (process manager) tool for your operating system. Run the workspace. You’ll see a single FME engine process running (fme.exe)

Of course, you’ll also see an fmeworkbench.exe process, which is the process running the Workbench interface. This isn’t responsible for running a workspace; this is a separate process.

**2)** Create Custom Transformer

Now select the PointCloudThinner and PointCloudCoercer transformers and turn them into a custom transformer. Note; don’t include the Tiler transformer as this is creating the tiles that we’ll be using as a way to parallel process.

You can call the transformer something like PointCloudProcessing. It doesn’t matter what attribute reference handling you choose.
The transformer definition should look something like this:

**3)** Set Parallel Processing

In the Navigator window (of the custom transformer definition) locate and expand the section of custom transformer advanced parameters.

Double-click the Parallel Processing Level parameter to set it. Set the processing level to Moderate.

Click OK to close the dialog and you’ll notice the Parallel Process By parameter is now published.

**4)** Set Process By

Return to the main canvas and click on the parameters button for the custom transformer instance. Select both _column and _row as the attributes to process by.

This means that each unique combination of _column and _row (i.e. each tile) will be run under a separate process, up to a maximum of one process per core processor.

**5)** Run Workspace

Run the workspace, again with a task manager window open. Once the tiling is complete and the rest of the workspace is being processed, you’ll notice a number of FME worker processes (fmeworker.exe).

In moderate mode, you’ll see up to one fmeworker process for each core. This time the translation should be complete is nearly half the time, approximately one minute and thirty seconds.

**6)** Experiment with Parallel Processing Level

If you have time, re-run the workspace with a different processing level, say Aggressive. Does it run any quicker than the Moderate processing level? If not, why might that be?

