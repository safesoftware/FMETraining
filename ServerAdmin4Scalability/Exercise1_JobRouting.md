<!--Exercise Section-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 1</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Job Routing</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">N/A</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Send a job through a specific engine</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Creating a job routing tag for an engine and sending a job through that particular engine</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2017\Workspaces\ServerAdmin\JobRouting-Ex1-Complete.fmw</td>
</tr>

</table>

---

Your GIS department is all onboard with FME Server and translating jobs with the Web User Interface, but jobs are always being queued, even the quick translations. You are wondering if there is a way to set aside one of the FME Server engines for quick translations only so that you and your fellow technical analysts do not have to wait too long for your smaller jobs to complete. With Job Routing you can allocate specific engines to specific tasks.

---

<!--Miss Vector says...--> 

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
If you completed the Configure for HTTPS exercise in chapter 3, remember: 
<br><br>the URL to connect to FME Server is </span><span style="font-family:serif; font-style:italic; font-weight:bold; font-size:larger">https://localhost:8443</span><span style="font-family:serif; font-style:italic; font-size:larger"> NOT http://localhost!
</span>
</td>
</tr>
</table>

---

<br>
**1) Create a Job Routing Tag**

A job routing tag is how you assign a job to a specific FME Engine. Tags are not automatically assigned to engines so we will first have to create a tag and assign it.

To configure a Job Routing Tag, we must go to the FME Server REST API V3 interactive page where you can try each method live.

Login to the FME Server Web User Interface either through the Web User Interface option on the Windows Start Menu or directly in your web browser (http://localhost/fmeserver), and log in using the username and password *admin*.

Click **Developers &gt; REST API &gt; API &gt; transformations: Transformation Manager &gt; /transformations/jobroutes/tags**

![](./Images/4.432.DevelopersRestAPI.png)

![](./Images/4.401.RESTAPI_pageLink.png)

![](./Images/4.402.JobRouting_APIPost.png)

This is where we will specify the tag we want to create.

**2) Name Your Tag**

Under Parameters, fill in **name** with the unique name of the tag you want to create, for example *JobRouting2017*:

![](./Images/4.403.JobRouting_APIPostParameters.png)

---

<!--Sister Intuitive says...--> 

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
Parameters documented in boldface are required while parameters in normal font are optional.
</span>
</td>
</tr>
</table>

---

You also have the option to specify a description of the tag, which engine(s) you want this tag to be associated with, and the repository assignments for the tag.

For now let's fill in **name** with the name of one of your engines found in the *Engines & Licensing* tab of FME Server. This is the engine that will be associated with the tag and that we will route a job through.

Next, click the button **Try it out!** located at the bottom of the form:

![](./Images/4.404.JobRouting_APIPost1.png)

**3) Generate a Token**

You will be prompted for a Username and Password to acquire a Token. A token is required to access the REST API. This must be provided with every request, and can be specified in a header or querystring or form parameter.

In this case, your Username and Password are the username and password of your FME Server Administrator’s account.

![](./Images/4.405.JobRouting_APIGetParameters2.png)

Click **Lookup Existing Token** and then **Generate Token** to authorize the token request.

Click **Try it out!** once more to run the method now that your token is registered

A Response Code value of **201** means you have successfully created your tag!

![](./Images/4.406.JobRouting_APIPostPrintOut.png)

Now you can use the tag to route jobs through the specified engine.

**4) Create a Workspace**

Now we will create a workspace in FME Workbench so that we have a job to test our Job Routing Tag with.

Open FME Workbench and create a new Blank Workspace.

For this exercise we do not need a complicated workspace, just a job that will run.

Add a **Creator** transformer and connect it to a **Logger** transformer.

![](./Images/4.407.jobRouting_workspace1.png)

**5) Run the Workspace**

Test that the workspace does run correctly by clicking the run button:

![](./Images/4.431.RunButton.png)

Translation was successful, and now we have a job that we can route. 

**6) Publish to FME Server**

Publish the workspace to FME Server from the file menu in FME Workbench:

![](./Images/4.408.publishToServer.png)

When prompted, publish the workspace to:

- **Repository Name:** testing
- **Workspace Name:** JobRouting_Job.fmw
- **Service:** Job Submitter

**7) Connect to FME Server**

Open the FME Server Web User Interface, either through the Web User Interface option on the Windows Start Menu or directly in your web browser (http://localhost/fmeserver), and log in using the username and password *admin*.

**8) Run the Workspace**

Once you have a published to FME Server, you can run the **JobRouting_Job** workspace and utilize the Job Routing option.

![](./Images/4.409.RunJob.png)

In *Run Workspace*, fill out the parameters as follows:

- **Repository:** testing
- **Workspace:** JobRouting_Job
- **Service:** Job Submitter 

![](./Images/4.410.runWorkspace.png)

**9) Advanced Options**

If you then expanded the *Advanced* options, there is the *Job Routing Tag* which can be used to associate the scheduled job with a specific FME Engine by specifying the name of the job routing tag associated with that engine. Enter *JobRouter2017* (the name of the tag that you created from the FME Server REST API).:

![](./Images/4.411.runWorkspaceAdvancedOptions.png)

Click **Run**.

**10) Ensure the Job Routed correctly**

You want to make sure the job was routed to the correct engine and not just the first available engine.

Check **Jobs &gt; Completed**:

![](./Images/4.412.Job_Completed_area.png)

Select the workspace that you just ran to open the job details.

In the *Request Data* section you can see your tag name that the job was routed through: 

![](./Images/4.413.jobRouting_finalCheck.png)

**11) Resubmit the Job**

Click the *Resubmit Job* button at the top of the page:

![](./Images/4.414.JobRouting_resubmitButton.png)

Click the *Resubmit Job* button several times; we want to make sure that every time we run the workspace with the Job Routing Tag that it is sending the job to the correct engine.

**12) Verify the Subsequent Jobs Routed Correctly**

Go back to **Jobs &gt; Completed** to verify that the job was always sent to the correct engine.

![](./Images/4.415.JobRouting_engineCheck.png)

If, under *Engine*, you see a list of the correct engine for each time you ran **JobRouting_Job**, then you have successfully routed the job!

---

<!--Exercise Congratulations Section--> 

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-thumbs-o-up fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">CONGRATULATIONS!</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
By completing this exercise you have learned how to:
<br>
<ul><li>Create a Job Routing Tag</li>
<li>Successfully route a job through a specific engine</li>
</ul>
</span>
</td>
</tr>
</table>

---

