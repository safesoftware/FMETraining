<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 4B </span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Basic
Notifications
and
Email
Subscription</span>
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
<td style="border: 1px solid darkorange">Provide
email-­‐driven
self-­‐serve
access
to
image
files</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Email
Publications
and
Topic
Notification</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Starting Workspace</td>
<td style="border: 1px solid darkorange">n/a</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Finished Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise4b-­‐Complete.fmw</td>
</tr>

</table>

This exercise continues setting up a system that provides email-driven access to image files. In this part we’ll create a workspace that will run in response to the incoming notification.

**1. Create a Workspace**

Now we have a Publication and a Topic that it will trigger when FME Server discovers a new email in the defined email account. However, at the moment there is nothing subscribed to that publication to act upon it. We’ll handle that part of the solution with a workspace.

Start FME Workbench. Begin with a blank canvas and simply add a Creator transformer. This will give us a workspace to run in response to an email; albeit one that doesn’t do much yet.

Save the workspace as Exercise4b.fmw

**2. Publish Workspace**

Now let’s publish the workspace to FME Server. Start the Publishing Wizard using File > Publish to Server on the menubar. When prompted enter the same connection parameters as before.
Publish the workspace to the Training repository. There are no data files that need to be published along with the workspace.

In the services dialog put a checkmark in the Notification Service’s box. Click Edit to see the Service Properties for this service.

Click the […] button next to Subscribe to Topic(s) to retrieve a list of available topics from the server.

Select the ImageProcessing topic created in exercise 4a.

All other parameters can be left as they are, so simply click OK to close the dialog.

Then click Publish to finish publishing the workspace.

**3. Confirm Subscription**

Remember, the workspace is now effectively a subscriber to the email publication. To confirm this, return to the web interface. Select Notifications from the Manage menu and then click the Subscriptions tab.

You should see a push subscription for your workspace associated with the topic ImageProcessing. Click on the subscription to view the details.

Click Cancel as we don’t need to make any changes to this component.

**4. Send an Email**

As before, send an email to trigger the notification and monitor the topic to ensure that it arrives.

**5. Confirm Notification**

To confirm the notification has caused the workspace to run, open the web interface to FME Server and click the Jobs option on the Manage menu. You should see a completed job for workspace Exercise4b.fmw, where FME ran the workspace in response to the email you just sent.

Congratulations! You have now triggered an FME Server notification using email.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Mr. Flibble says …</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“If you’re using IMAP then this is probably a good point to go back
to Notifications > Subscriptions, select the Exercise4b push
subscription, and unsubscribe it from the ImageProcessing topic.
If you don’t do this, then forever more any incoming email to your
account will trigger this workspace! And any attachments would
get stored in the Resources folder. Wouldn’t that be funny! Ha ha!”
</span>
</td>
</tr>
</table>









