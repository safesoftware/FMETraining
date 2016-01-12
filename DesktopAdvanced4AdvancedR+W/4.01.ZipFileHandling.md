# Zip File Handling

Zip files are a convenient way to write output datasets that need to be handled as a single unit.

The Basic Desktop course covered how data can be read directly from a zip file. However, it is also possible to write data to a zip file.

Zip files are a convenient way to write output datasets that need to be handled as a single unit.

For example, a single Shape feature type consists of several files; shp, shx, dbf, prj, etc. A Shape dataset can consist of multiple feature types. So, in a scenario where the output data needs to be post-processed – uploaded to a web site, say – it’s more convenient to handle a single zip file than multiple data files.

**Zip File Writing**

The simplest way to create a zipped output is to simply change the file extension to .zip in the output dataset field:

A small icon in the dataset field indicates the zipped status:

When the workspace is run the log file reports the zip creation:

And the output is, indeed, a zipped dataset:

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Sister Intuitive says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“I’m Sister Intuitive from the order of Perpetual Translations. I’ll provide
you with spatial guidance throughout this chapter.
Some users may want to zip data in order to upload it to process it as a single entity.
Here, a TCL or Python shutdown script will know the name of the file just written through
published parameters (macros). With that information the file can be processed – for
example, uploaded to an FTP site – with minimal difficulty.”
</span>
</td>
</tr>
</table>

Another way to force a zip file output is to simply click the new “Zip Output” button in the writer dialog:

Doing so automatically sets up the output to be written with the given name, but inside of a similarly named zip file:

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Sister Intuitive says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“Although the above images show how to achieve a zipped output in the
Generate Workspace dialog, the same functionality is available
regardless of where and how you set the output file (for example,
through the Navigator window). You just need to give it a .zip extension.”
</span>
</td>
</tr>
</table>