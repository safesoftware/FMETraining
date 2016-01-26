# Self-Serve and Parameters

Workspace parameters are the key to controlling Self-Serve and the Data Download service

**What are Parameters?**

Parameters are what control a translation.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Chef Bimm says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“Parameters in a translation are like
the options when making coffee.
The machine can be set with the ingredients to be used,
how they are combined, and what the end result of
the process will be like.”
</span>
</td>
</tr>
</table>

In the hierarchy of different translation components, each different level of the hierarchy has a set of parameters that belong to it.

So there are:

• Workspace Parameters
• Reader Parameters
• Writer Parameters
• Feature Type Parameters

**Published Parameters**

Published Parameters are those that have been exposed to the end-user, so they can set the values themselves. They are also called “User Parameters”.

In a self-serve application, published parameters are important to let the end user control how the data is served in terms of style and structure.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Chef Bimm says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“Published Parameters are like
when you are given control of the
machine to make your own
coffee.”
</span>
</td>
</tr>
</table>

**Parameter Uses in FME Server**

For self-serve systems, parameters can be used to set:

• Coordinate System Selection
• Feature Types (Layers) to Read
• Geographic Area (Bounding Box or Area of Interest)
• Any other Reader, Writer, or Transformer parameters

With FME Server, the key to successful workspace authoring is flexibility. Workspaces need to be flexible to allow end-users to make choices without seeing all of the complexity of the workspace or the data behind it. Parameters are one way to accomplish this.