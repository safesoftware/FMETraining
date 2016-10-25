<!--Instructor Notes-->

<!--Exercise Section-->
<!--NB: In GitBook world we don't give a number to exercises-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 1</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold"></span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Event Messages (JSON)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Create a workspace to read, parse, and filter WebSocket messages; keeping only events that affect transit stations.</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Creating a workspace to handle a message stream</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2016\Workspaces\ServerAuthoring\DataStream-Ex1-begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2016\Workspaces\ServerAuthoring\DataStream-Ex1-Complete.fmw<br>C:\FMEData2016\Workspaces\ServerAuthoring\DataStream-Ex1-Process-Complete.fmw</td>
</tr>

</table>

---

As a technical analyst in the GIS department you deal with spatial data. Sometimes you need to process that data in real-time and sometimes that data can arrive in great quantities and at great speed.

In one such case, the city has been given access to the monitoring systems of emergency services. That means the ability to access in real-time information about all emergency calls. 

*By emergency calls we mean the equivalent of 911 calls in North America, 999 in the UK, 112 in most of Europe, and 000 in Australia.* 

Of course, these calls can arrive at a tremendous rate, and at unknown intervals. If the city wishes to respond to any of these, and even if they wish to just record a history of the calls, you must implement a message streaming setup in FME Server. 

---

<br>**1) Open Workspace**
<br>Unfortunately (I'm talking from a training point of view) we don't have access to a real-time stream of emergency phone calls, so we will have to generate our own.

Open the workspace C:\FMEData2016\Workspaces\ServerAuthoring\DataStream-Ex1-begin.fmw

![](./Images/Img5.02.Ex1.MessageGeneratingWorkspace.png)

---

<!--Updated Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-bolt fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">.1 UPDATE</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
The Cloner transformer gained a Rejected port in FME2016.1
</span>
</td>
</tr>
</table>

---

Notice that the workspace generates a stream of events. A random number of events are generated, at random times, and at random locations. Additionally random severity and event type attributes are generated. 

Each event is wrapped up into a JSON format message. All that we need to do is push that message out as a stream.

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
This workspace is just generating "events". Those events could be lightning strikes, vehicle locations, traffic accidents, or even UFO sightings! For this exercise, we'll pretend they are emergency phone calls. In real life you would be connecting to an existing stream of data, and wouldn't need to generate one in this way. 
</span>
</td>
</tr>
</table>

---

<br>**2) Add WebSocketSender Transformer**
<br>Add a WebSocketSender transformer after the JSONTemplater. Open the parameters dialog. Set the parameters as follows:

<table>
<tr><td>WebSocket Server URL</td><td>ws://localhost:7078</td></tr>
<tr><td>Verify SSL Certificates</td><td>No</td></tr>
<tr><td>Connection Preamble</td><td>
<pre>
{
    ws_op: "open",
    ws_stream_id: "EmergencyEvents"
}
</pre>
</td></tr>
<tr><td>Data To Transmit</td><td>
<pre>
{
    ws_op: 'send',
    ws_msg: '@Value(EventMessage)'
}
</pre>
</td></tr>

</table>

Click OK to close the parameters dialog and then save the workspace.


<br>**3) Create Workspace**
<br>Now we have the ability to generate a stream of data we will create the workspace that is to process the data. Start Workbench and begin with a blank canvas (don't close the stream generator workspace, as we'll need that as well in a moment). 

In the blank canvas add a Creator transformer and follow it with a WebSocketReceiver. Open the WebSocketReceiver's parameters dialog. Set the parameters as follows:

<table>
<tr><td>WebSocket Server URL</td><td>ws://localhost:7078</td></tr>
<tr><td>Verify SSL Certificates</td><td>No</td></tr>
<tr><td>Connection Preamble</td><td>
<pre>
{
    ws_op: "open",
    ws_stream_id: "EmergencyEvents"
}
</pre>
</td></tr>
<tr><td>Output Attribute</td><td>IncomingMessage</td></tr>

</table>

Close the dialog and add a Logger transformer after the WebSocketSender.


<br>**4) Publish Workspaces**
<br>Let's test what we have by publishing the workspaces and running them on FME Server. 

Publish each workspace in turn. In both cases simply register it with the Job Submitter service. There are no datasets or other parameters we need worry about.


<br>**5) Run Workspace**
<br>Log in to FME Server, locate the data stream generator workspace, and run it. The dialog in response will look like this:

![](./Images/Img5.03.Ex1.MessageGeneratingWorkspaceRun.png)

The workspace will run for a long time and we can leave it to do so. Click the Home button and locate the processing workspace. Now run that.

Again the workspace will run as report that it will continue to do so.


<br>**6) Check Jobs and Cancel**
<br>From the menu select Manage Jobs and click the tab labelled Running. You will see the two jobs:

![](./Images/Img5.04.Ex1.RunningWorkspaces.png)

Let the jobs run for a minute or two. Then choose each of them and click the Cancel button to cancel them:

![](./Images/Img5.05.Ex1.RunningWorkspacesCancel.png)

Once cancelled, go to the Completed jobs tab. You'll see the two cancelled jobs:

![](./Images/Img5.06.Ex1.CancelledWorkspaces.png)

Click on the processing workspace job and check the log. You should see messages in the log like this:

<pre>
|===========================================================================
INFORM|WebSocketReceiver_Output: Feature is:
INFORM|+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
INFORM|Feature Type: `WebSocketReceiver_Output_LOGGED'
INFORM|Attribute(encoded: utf-8): `IncomingMessage' has value `{ "EventID" : 6.....
INFORM|Attribute(string)        : `fme_geometry' has value `fme_undefined'
INFORM|Attribute(encoded: utf-8): `fme_type' has value `fme_no_geom'
INFORM|Geometry Type: Unknown (0)
</pre>

This proves that the WebSocketReceiver is acting as expected and receiving messages from the message stream.

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
You've proved that you can create a workspace to process a message stream, which is the important part of this exercise. But if you have the time, let's see what improvements we can add to make the result more realistic.
</span>
</td>
</tr>
</table>

---

<br>**7) Add JSONFlattener**
<br>The first thing to do with incoming messages is to extract information as attributes. Because the incoming data is JSON format, add a JSONFlattener transformer to the processing workspace. Open the parameters dialog and set the attribute IncomingMessage as the JSON Document to process.

Under Attributes to Expose manually enter:

- EventID
- EventLocation.EventXCoord
- EventLocation.EventYCoord
- EventSeverity
- EventType

![](./Images/Img5.07.Ex1.JSONFlattenerParameters.png)

You will now have the information from the message available as a set of attributes in the workspace.



<br>**8) Add VertexCreator**
<br>Now add a VertexCreator. Set it up to use the X/Y attributes to create a true point feature:

![](./Images/Img5.08.Ex1.VertexCreatorParameters.png)

With this we now have a true geographic feature and can process it as required.


<br>**9) Add Reader**
<br>The public transportation team within the city has learned you are working with this emergency data. They wish to be alerted immediately if there is an emergency event within 200 metres of a transit station. Let's show them how easy it is to set this up.

Firstly we need the transit station data, so select Readers &gt; Add Reader and add the following:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Reader Format</td>
<td style="">Esri Geodatabase (File Geodb API)</td>
</tr>

<tr>
<td style="font-weight: bold">Reader Dataset</td>
<td style="">C:\FMEData2016\Data\CommunityMapping\CommunityMap.gdb</td>
</tr>

</table>

When prompted (or in the parameters dialog) ensure that only the TransitStation table is selected.
  

<br>**10) Filter Data**
<br>Now let's filter the emergencies. 

Firstly, add a Bufferer transformer to the TransitStation feature type and buffer the features by 200 metres.

Secondly, add a PointOnAreaOverlayer to assess whether an emergency falls inside one of these buffers. The workspace will now look like this:

![](./Images/Img5.09.Ex1.WorkspaceWithBufferAndOverlay.png)

---

<!--Updated Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-bolt fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">.1 UPDATE</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
The Bufferer transformer gained a Rejected port in FME2016.1
</span>
</td>
</tr>
</table>

---

At the moment there is one big problem that stops this from working. The PointOnAreaOverlayer transformer is a Group-Based transformer, sometimes called a "blocker". It will hold on to features until it has finished being fed them, before outputting any data. In our case we want to make it Feature-Based; i.e. it will process each message at once.

So, open the PointOnAreaOverlayer parameters and set Areas First to Yes:

![](./Images/Img5.10.Ex1.PointOnAreaParameters.png)

This tells the transformer that all area features (buffered stations) will be first to arrive, therefore any point features (message locations) can be processed immediately. However, we have to ensure that the transit features will arrive first. Therefore open the Creator transformer parameters and set Create at End to Yes:

![](./Images/Img5.11.Ex1.CreatorParameters.png)

Now, all being well, the transit features will arrive first at the PointOnAreaOverlayer

Finally, add a Tester transformer after the PointOnAreaOverlayer. Set up the test to check for _overlaps > 0 (i.e. where the message location falls inside a transit station buffer). Connect some Logger transformers to the Tester output ports:

![](./Images/Img5.12.Ex1.TesterToFilterMessages.png)

Note that, if there were other parameters (for example the transit team were only interested in Event Types 7, 8, 9, and 10) you could add them to this Tester as well.


<br>**11) Publish Workspaces**
<br>Now publish the two workspaces again (you may or may not have to upload the TransitStation Geodatabase along with the workspace) and run them using the same process as before, but leave it for a few minutes longer, as it may take a while for one of the random events to fall inside a transit station buffer. 

Once stopped, check the logs and you should see that messages falling within 200 metres of a transit station are logged (with a different header).

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
If you want to adjust the settings to get a result quicker, then go ahead. For example, you might set the buffer size to 500 metres instead of 200, or you might reduce the interval time on the message generator. Feel free to make whatever parameter changes you like to test the setup. You could even bypass the Decelerator transformer altogether to see how fast FME can deal with the incoming messages! But if you do that, be sure to start the processing workspace first, else the generator might finish by the time you do get the processor started!
</span>
</td>
</tr>
</table>

---

<br>**12) Add Writer**
<br>The messages that are being received are not all being used by the transit team, but we should probably keep a record of them. So select Writers &gt; Add Writer from the menubar. Use the following parameters to add a database Writer:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">Writer Format</td>
<td style="">SpatiaLite</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Dataset</td>
<td style="">C:\FMEData2016\Output\EventMessages.sl3</td>
</tr>

<tr>
<td style="font-weight: bold">Writer Parameters</td>
<td style="">Advanced : Transaction Interval = 1</td>
</tr>

<tr>
<td style="font-weight: bold">Add Feature Type(s)</td>
<td style="">Table Definition: Automatic</td>
</tr>

</table>

In the newly added feature type, change the name to events and close the dialog. Connect the feature type to the VertexCreator output port (i.e. we're recording all events, not just the filtered ones):

![](./Images/Img5.13.Ex1.WriterFeatureTypeConnected.png)

The attributes are added automatically, but include a few we don't need. So open up the properties dialog again for the feature type and click the User Attributes tab. Change it from Automatic to Manual and delete the attributes:

- &#95;creation&#95;instance
- incomingmessage
- eventlocation_eventxcoord
- eventlocation_eventycoord

![](./Images/Img5.14.Ex1.WriterFeatureTypeAttributes.png)

Notice that the attributes were automatically renamed (to lower case and removing disallowed characters) to match SpatiaLite requirements.

If you publish and run the workspace now you should be able to see - while the workspace is still running - the results being added to the database. You can inspect the file in the FME Data Inspector to prove this.


<br>**13) Create Notification**
<br>One last task (I promise). The filtered messages are important to the transit team, but at the moment they are going nowhere. We should set up a way to inform them. 

We could add another messaging transformer, such as the WebSocketSender, JMSSender, SQSSender, or even a Tweeter. That would make the processing workspace a "pure" messaging workspace.

On the other hand, the outgoing messages are nothing like the same rate as the incoming messages. With the parameters as described in this exercise, there is only a transit message once every minute. So, we can create a "hybrid" solution by setting output messages to be sent via the notification service.

Go to the FME Server web interface and navigate to Manage &gt; Notifications.

Create a new Topic called EmergencyTransitMessages:

![](./Images/Img5.15.Ex1.NotificationNewTopic.png)

Now create a new notification Subscription. There are various protocols we could realistically use for sending a message (email springs to mind) but for the purposes of this exercise use the Logger protocol. Set the Log Level parameter to High:

![](./Images/Img5.16.Ex1.NotificationNewSubscription.png)
 

<br>**14) Add FMEServerNotifier Transformer**
<br>Back in the processing workspace in Workbench, remove any Logger transformers at the end of the workspace. Add an FMEServerNotifier transformer connected to the Tester:Passed port:

![](./Images/Img5.17.Ex1.FMEServerNotifierOnCanvas.png)

Open the parameters dialog and set it up to send a message to the EmergencyTransitMessages topic. Set the message content to be whatever you like. You could use the text editor dialog to create something out of the available attributes (it can be plain text, it doens't have to be JSON or XML).


<br>**15) Publish and Run Workspaces**
<br>Re-publish and set the workspaces running again. Click Manage &gt; Notifications and click on the Topic Monitoring tab. Set the EmergencyTransitMessages as the topic to monitor.

In a short while you will start to see emergency messages like this: 

![](./Images/Img5.18.Ex1.TopicMonitoringResults.png)

Visit Manage &gt; Resources &gt; Logs &gt; core &gt; current &gt; subscribers &gt; logger.log to find the results as recorded by the Logger protocol notification.
 
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
<ul><li>Send and receive messages via WebSockets</li>
<li>Publish and run message-streaming workspaces</li>
<li>Cancel message-streaming workspaces and check their log files</li>
<li>Extract attributes from JSON messages</li>
<li>Use transformers to transform and filter a message according to its content</li>
<li>Set up workspaces to handle group-based transformers in a real-time scenario</li>
<li>Record incoming messages into a database</li>
<li>Set up a hybrid system with message streaming <strong>and</strong> notifications</li></ul>
</span>
</td>
</tr>
</table>   
