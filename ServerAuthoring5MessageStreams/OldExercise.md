<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 4E </span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Message
Streaming</span>
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
<td style="border: 1px solid darkorange">Web
Map
Application
with
WebSockets</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">WebSockets</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Starting Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise4e-­‐Begin.fmw
C:\FMEData2015\Workspaces\ServerAuthoring\Exercise4e-­‐Begin-­‐Advanced.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Finished Workspace</td>
<td style="border: 1px solid darkorange">n/a</td>
</tr>

</table>

This exercise uses FME Server’s WebSockets service and WebSockets transformers to power a Web Map application. The method shown here is suitable for high frequency messaging in excess of 1 message per second.

**1. Open the Starting Workspace**

In FME Workbench open the starting workspace Exercise4e-Begin.fmw

Notice that it contains two WebSocket transformers – one for receiving and one for sending. The workspace will listen for information coming through the WebSockets channel. Incoming data will be processed with an offset in its coordinates, and then sent back. The workspace will run continuously, processing each incoming message, until stopped manually.

**2. Update Server Name**

The first task is to update the hostname for the server to match the one you are using.

Locate the published parameter server_url in the Navigator window.
Double-click the parameter to open it for editing and replace the host with your own FME Server host name and port. It will need a “ws” prefix to denote the WebSockets protocol.

If you are working on the same machine as your FME Server you can use localhost for example: ws://localhost:7078/websocket

**3. Examine the WebSocketReceiver and WebSocketSender Transformers**

Open the parameters dialog for the WebSocketReceiver transformer.

Notice that the Server URL is being obtained from the published parameter you just updated.

Click the […] button to open the Connection Preamble parameter.

What this means is that the transformer will make a connection to the specified FME Server and listen for features coming through a WebSocket stream called “points”.

If you open the parameters for the WebSocketSender transformer, you’ll see it sends features back using a stream id called “disp_pnts”.

The data being sent back through the WebSocket channel is the amended lat/long coordinates of the feature being processed.

**4. Start the Workspace**

Run the workspace and notice the initial connection messages printed to the log window. Also notice that the workspace keeps running, waiting for messages via the WebSocket stream it is listening to.

**5. Edit the Web Map Application**

In order to test this setup, a basic web mapping application has been provided in C:\FMEData2015\Resources\WebSockets

Some minor updates will be needed before we can use this. In a text editor open the main HTML file C:\FMEData2015\Resources\WebSockets\www\index.html

Find the two lines below which define the host WebSockets connections for the application. If you are using localhost you can leave this as is, otherwise replace localhost with your own hostname.

var sendconn = new WebSocket('ws://localhost:7078/websocket');
var rcvconn = new WebSocket('ws://localhost:7078/websocket');

Now find the block of code starting with the comment

/*** connect to server input stream ***/

Notice that the web application is sending points to FME Server using the stream id “points” – the same one that the workspace is currently listening to.

connmsg = '{ ws_op : "open", ws_stream_id : "points" }';

If you look you’ll also find a block of code that listens for data using the stream id “disp_pnts”

connmsg = '{ ws_op : "open", ws_stream_id : "disp_pnts" }';

Save the file index.html if you have made any edits.

**6. Run the Web Application**

Open the index file that we’ve just inspected in a web browser.
As the Web map loads you will see two message sections logging messages sent to and from the FME Workspace:

Click on any point of the map.

Notice that immediately the point is recorded and returned with a random offset applied (it doesn’t matter what happens here, just the fact that something does).

Also notice that messages to and from the workspace are being logged.
If you switch back to the workspace you’ll notice that not only is it still running, but a feature was logged as it was received via the WebSocketReceiver, displaced and transmitted out via the
WebSocketSender.

**7. Publish the Workspace to FME Server**

Up to now we’ve just run the workspace on FME Desktop, but it can also be run on FME Server.

Stop the workspace in FME Desktop if it is still running and publish the workspace to FME Server into the Training repository. Simply register the workspace with the Job Submitter Service.

**8. Run the WebSockets Workflow on FME Server**

In the Web User Interface browse to the workspace in its repository, choose the Job Submitter and click Run

The workspace will keep running indefinitely and FME Server’s job recovery functionality will restart the job if it ever fails.

Try placing a few more points on the web map application to confirm that points are being displaced. This time the process is being carried out by FME Server.

Go back to the Web User Interface and click on the Manage menu > Jobs and then click the

Running tab where you will see your workspace running.

Click on the job and then on the Log tab. You’ll see the log of the workspace as it is running and can examine it to see your last few map clicks passing through the workspace as features.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Police Chief Webb-Mapp says …</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“The ability to view a log file while the translation is still in progress
is a new feature of FME Server 2014”
</span>
</td>
</tr>
</table>

**Advanced Tasks (Exercise 4f)**

The use of a continuously running workspace has advantages and disadvantages.

On the plus side, it can process many messages – several thousand – per second. However, it does take up an FME Server engine on a continuous basis too.

If the same workflow was configured to run using the Notification Service it would not use an FME Engine at all times; however it would not be suitable for systems with multiple messages per second.

As an optional task, let’s try configuring the system to use notifications instead if WebSockets.

**1. Cancel the Job from the Above Exercise**

Under Jobs > Running in the Web User Interface, put a checkmark next to the job and press the Cancel button. This will stop the existing job from running, as we no longer need it.

**2. Add a Topic**

In the Notification part of the Web User Interface, add a Topic named points.

**3. Add a Web Sockets Publication**

Now add a new Publication with the following settings:

Publication Name MapPoints
Topics to Publish To points
Protocol WebSocket
Target Url ws://localhost:7078/websocket
(or use your own host)
Stream ID sample_stream_in

**4. Edit the Web Map Application**

In a text editor open the file 

C:\FMEData2015\Resources\WebSockets\www\index.html

Comment out the default send connection message (line 86) and uncomment the one below:

//connmsg = '{ ws_op : "open", ws_stream_id : "points" }';
connmsg = '{ ws_op : "open", ws_stream_id : "sample_stream_in" }';
Save the updated file.

**5. Open the Advanced Workspace**

Open the workspace Exercise4e-Begin-WebSockets-Advanced.fmw and edit the server_url parameter if necessary.

Publish this workspace to FME Server and register it with the Notification Service.

In the service settings set the workspace to subscribe to the topic points and ensure the Notification Reader is set to the TEXTLINE reader.

Click OK to close the dialog and Publish to finish publishing the workspace.

**6. Use the Web Application in Notification Mode**

Reload the web application in your browser or simply reopen the file index.html.

Click some points on the map to ensure they are being processed and offset.

Examine the Jobs history in Web User Interface. You will see a job is run each time you click.