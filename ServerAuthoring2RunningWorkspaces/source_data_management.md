# Source Data Management

Source data may be published to FME Server and stored in a “Resources” folder, where it is available to any workspace

FME Server has several mechanisms for uploading and storing resources for workspaces to use in a translation; for example the source data for a translation.

One such mechanism is called “Resources” or “Resource Management”, and is accessed through the Web User Interface.

The advantage of these Resources, compared to other methods, is that data can be uploaded and referenced by any workspace, without having to upload it every time. This is particularly useful when access to the file system is restricted (like on an FME Cloud system).

If the workspace author does have access to the file system, then Resources are still useful, as a Resources folder can be mapped and shared among many users as a physical drive.

**Accessing Resources**

Resources are accessed through the Manage, then Resources on the main menu.

**Resource Functionality**

The various resource functions are:
- Upload
- New Folder
- Download
- Delete
- Copy
- Move

More information on this functionality is proved in Chapter 3 under Data Upload.

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 2B </span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Uploading to a Resource Folder</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Scenario</td>
<td style="border: 1px solid darkorange">Airphoto Data Vendor</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">GeoTiff Orthophotos</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Uploading data to be used by the previous workspace</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">FME Server resource management</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Starting Workspace</td>
<td style="border: 1px solid darkorange">n/a</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Finished Workspace</td>
<td style="border: 1px solid darkorange">n/a</td>
</tr>

</table>

In this exercise we’ll upload some GeoTiff files as Resources on FME Server. This will make them available for use by a workspace, including the one published in Exercise 2a.

**1. Open Web User Interface**

In a web browser open the FME Server Web User Interface, as we did in Chapter 1, by entering http://<servername>/fmeserver

Alternatively use the Windows shortcut Start > Programs > FME Server 2015.1 > Web User Interface.

Login in using the credentials provided by the instructor, by default these will be

User admin

Password admin

**2. Create New Resources Folder**

Under Manage, click Resources, on the upper right menu.

Click on the Data Folder in the Resource Management dialog.

Click New Folder to create a new subfolder inside Data. Name the folder Orthophotos.

**3. Upload Image Data**

Still in the Resources Management dialog, select the newly created Orthophotos folder. Click Upload.

Click Browse. A file browser window will open. Browse to the folder

C:\FMEData2015\Data\Orthophotos and select the following GeoTiff files for upload.

08-09-NO.tif
08-09-LM.tif
06-07-NO.tif
06-07-LM.tif

**NB:** If you wish, you can choose all of the files; but they total 184mb in size, so uploads and downloads will take longer.

Click Open and the selected files will be uploaded.

Congratulations! You have uploaded a series of source datasets, which are now available for use in any FME Server Workspace.