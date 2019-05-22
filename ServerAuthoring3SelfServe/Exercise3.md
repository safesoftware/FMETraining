<!--Instructor Notes-->

<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 3.3</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Data Download System: Published Parameters</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Orthophoto images (GeoTIFF)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Create an FME Server Data Download system for orthophotos</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Creating published parameters for user control in Data Download</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2019\Workspaces\ServerAuthoring\SelfServe-Ex3-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2019\Workspaces\ServerAuthoring\SelfServe-Ex3-Complete.fmw</td>
</tr>

</table>

---

As a technical analyst in the GIS department of a city, you have just commenced an initiative to allow other departments to download orthophoto data, rather than having to ask you to create it for them. Not only will their requests be processed quicker, but you will also spend less time on that task.

So far you have created a simple workspace to translate orthophotos to JPEG format, and published it to a Data Download service on FME Server.

Now you need to start customizing the workspace to allow the end-users to have a degree of control over the output.


<br>**1) Open Workspace**
<br>Open the workspace from exercise 2, or the begin workspace listed above.

In this step, we'll give the end-user control over the transformation stages.


<br>**2) Create User Parameter**
<br>If you look at the parameters for the RasterResampler transformer, you'll see parameters for X Cell Spacing and Y Cell Spacing. We should let the end user choose what spacing they want.

So, in the Navigator window of FME Workbench, locate the section marked User Parameters. Right-click on there and choose the option Create User Parameter:

![](./Images/Img5.200.Ex1.CreateParameter.png)

The dialog that opens allows us to create a new parameter. Create one using the following parameters:

<table>
<tr><td style="font-weight: bold">Type</td><td>Number</td></tr>
<tr><td style="font-weight: bold">Name</td><td>CellSpacing</td></tr>
<tr><td style="font-weight: bold">Published</td><td>Yes</td></tr>
<tr><td style="font-weight: bold">Optional</td><td>No</td></tr>
<tr><td style="font-weight: bold">Prompt</td><td>Enter Resolution (1-50)</td></tr>
<tr><td style="font-weight: bold">Configuration</td><td>Lower Limit: Greater than value: 0<br>Upper Limit: Less than value: 51<br>Decimal places of precision: 0</td></tr>
<tr><td style="font-weight: bold">Default Value</td><td>50</td></tr>
</table>


![](./Images/Img5.201.Ex1.CreateParameterDialog.png)

Click OK to close the dialog.


<br>**3) Apply User Parameter**
<br>Now we've created a user parameter, but not applied it to anywhere.

Open the parameters for the RasterResampler transformer. Click the drop-down arrow to the right of the X Cell Spacing parameter, and choose User Parameter &gt; CellSpacing.

Do the same for the Y Cell Spacing parameter. The dialog will now look like this:

![](./Images/Img5.202.Ex1.PublishedRasterResamplerParams.png)

Notice that we're using the same values for the X and Y cell sizes. That's OK. Although we could use rectangular (oblong) raster cells, for this exercise we'll stick with a square.


<br>**4) Create User Parameter**
<br>Another setting we might give control of to the user is file compression. This is not defined in a transformer, but in the writer feature type. However, we can still create a published parameter in the same way.

So, right-click on User Parameters in the Navigator window and choose Create User Parameter again.

This time we'll do this a little bit differently. Compression can be a value from zero to one hundred, but we'll present the user with the choice of None, Low, Medium, and High.

So create a parameter with the following settings:

<table>
<tr><td style="font-weight: bold">Type</td><td>Choice with Alias</td></tr>
<tr><td style="font-weight: bold">Name</td><td>Compression</td></tr>
<tr><td style="font-weight: bold">Published</td><td>Yes</td></tr>
<tr><td style="font-weight: bold">Optional</td><td>No</td></tr>
<tr><td style="font-weight: bold">Prompt</td><td>Select Compression Level</td></tr>
</table>

For the configuration field, click the [...] browse button. In the dialog that opens, set the following:

<table>
<tr><th>Display Name</th><th>Value</th></tr>
<tr><td>None</td><td>0</td></tr>
<tr><td>Low</td><td>25</td></tr>
<tr><td>Medium</td><td>50</td></tr>
<tr><td>High</td><td>75</td></tr>
</table>

![](./Images/Img5.203.Ex1.CreateChoiceParam.png)

Click OK and OK again to close these dialogs and create the parameter.


<br>**5) Apply User Parameter**
<br>To apply the parameter, inspect the parameters for the JPEG feature type. Expand the Compression parameters (if necessary) and set the Compression Level parameter to User Parameter &gt; Compression.

![](./Images/Img5.204.Ex1.SetFTCompression.png)

Click OK to close the dialog. If you press the run button now - with the prompt option set - you'll see that there are now two new prompts for resolution and compression.


<br>**6) Publish and Run Workspace**
<br>Now publish the workspace to FME Server. Publish it to the Training repository and then register it with the Data Download service.

Locate the workspace through the FME Server web interface and run it. This time you will be prompted to set the cell size and compression.

![](./Images/Img5.205.Ex1.RunWorkspace.png)

Run the workspace a few times, varying the cell size and compression, to confirm that the parameters are having an effect. The size of the output file is a good indicator that the process is working correctly.

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
<ul><li>Create an integer user parameter and apply it to two transformer parameters</li>
<li>Create a choice user parameter and apply it to a writer feature type parameter</li>
<li>Publish a workspace and use published parameters</li></ul>
</span>
</td>
</tr>
</table>
