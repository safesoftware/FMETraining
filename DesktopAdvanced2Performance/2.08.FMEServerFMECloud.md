# Performance, FME Server, and FME Cloud


FME Server adds an extra dimension to FME performance.

In terms of performance, the prime reason for using FME Server is one of scalability, and the main consideration is the number of FME engines.

Increasing the number of engines supports a higher volume of jobs and the FME Server Core contains a Software Load Balancer (SLB) to distribute jobs to the FME engines in a balanced way.

In this scenario, FME Server is used not for its web-based abilities, but rather for its potential in processing large amounts of data in relatively less time.

**Using Server for Bulk Translations**

By default, utilizing multiple engines is only possible when you have multiple workspaces that can be run. When you have only a single workspace, and wish to process it more efficiently on FME Server, then you need to divide that workspace into multiple jobs.

For example, I have a very large set of vector data in a spatial database, and want to create a series of map tiles from it. Basically I need to clip the data to a map tile outline, rasterize it, and write it out to a raster format such as PNG:

The problem is that the amount of data being processed is so great, the workspace takes days to run. I need to run the process on FME Server by dividing the work up into different jobs.

So, I upload my workspace to FME Server and create a master workspace to control it. The master workspace calculates the bounds of each tile and runs the main workspace on FME Server using a ServerJobSubmitter transformer:

The bounds of each tile are sent to the main workspace by using published parameters:

So now I have a method by which I can pass the bounds of the tiles to be created to a workspace on FME Server, and share the load over multiple server engines by running the workspace once for each tile.

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
Pushing to FME Cloud
</span>
</td>
</tr>
</table>

FME Cloud is an installation of FME Server hosted by Safe Software on Amazon Web Services technology and used on a pay-as-you-go basis. The benefit is that you don’t have to purchase FME Server, simply make use of it whenever you have a job that can take advantage of its power.

The key to automating this for performance benefits are the FME Cloud custom transformers available on the FME Store:

With the FMECloudInstanceLauncher transformer I can run my master workspace (as in the example above) and have it automatically start an FME Cloud instance and run the job on it.

This way I can start a new instance for each job, or run several jobs on one instance, depending on the type of instance and how many engines it has running on it.