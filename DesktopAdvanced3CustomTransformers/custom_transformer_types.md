# Custom Transformer Types

Custom Transformers come in two flavors: Embedded and Linked.

**Custom Transformer Types**

There are two types of custom transformers: Embedded and Linked.

An embedded transformer is one that exists only in the workspace itself. Its definition is stored (embedded) inside the workspace file and it is not available to any other workspace.

A linked transformer is one that exists outside of a workspace. Its definition is stored in its own file and it is available to any other workspace, which reference it through a link.

On a workspace canvas, embedded transformers are identified by their green color, while linked transformers are colored cyan:

**Linked vs Embedded Transformers**

Both type of transformer can be used in an FME workspace, and there are various advantages and disadvantages to each type.

**Embedded Transformers**

Embedded transformers are perhaps easier to understand and have the advantage of needing no external files, as their definition is embedded into the workspace. However, an embedded transformer cannot easily be shared with other users, unless they are given a copy of the same workspace, and it is not easy to maintain a consistent definition among several users.

**Linked Transformers**

As a separate file, linked transformers are perhaps a little harder to understand and manage.
However, a linked custom transformer is much easier to share among users: any number of users can use the same custom transformer definition. Additionally, maintenance is easier too because any changes made to the definition are automatically propagated to any workspace that uses it.

**Exporting a Custom Transformer**

All custom transformers start out as an embedded version. To create a linked version the custom transformer is exported from the workspace.

This is easily done by clicking on the canvas tab for the embedded definition and choosing File
- Export as Custom Transformer from the menubar:

At this point a dialog opens in which you can confirm the transformer name and category, plus some other parameters including the save location:

Clicking OK creates the custom transformer and opens it in a new instance of Workbench.

**Save Location**

FME has a specific installation folder in which custom transformer files can be saved. If a custom transformer is saved in this folder then it becomes available in Workbench and can be used the same as any other transformer.

When a linked transformer shows up in the transformer gallery – or Quick Add dialog – then it has a special icon to signify that you are about to use a linked version, rather than the embedded.

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
“Note the refresh button on the transformer gallery. If a custom
transformer doesn’t show up when you expect, refreshing the gallery
contents may help to locate it.”
</span>
</td>
</tr>
</table>

**Insertion Mode**

When exporting a custom transformer, the Insert Mode parameter specifies how the custom transformer can be used. There are four different modes.

If a “by Default” option is used, then any instance of this transformer that is placed can be switched back and forth from embedded to linked.

If an “Always” option is used, then any instance of this transformer is fixed in either embedded or linked mode, and cannot be switched.

**Which Mode to Use**

When an author creates a custom transformer for a customer or user who is inexperienced in FME, then Embedded Always is a good choice, since it is easier to manage (no external files) and the user cannot accidentally change it.

When the custom transformer is intended to be shared among users, then Linked Always is a good choice, as any changes to the transformer definition are automatically applied to the end workspaces.

Only when the end-user is experienced in FME and can understand the consequences, is it advisable to use a “by Default” setting and allow type switching.

**Switching Custom Transformer Types**

When a custom transformer is designed to allow type switching, to switch a custom transformer instance from embedded to linked mode is very straightforward. Simply right-click on the instance and choose Link.

Similarly, to switch from Linked to Embedded simply right-click and choose the option Embed.

Of course, to be able to switch types requires that you have already exported the custom transformer!

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
“Switching from Embedded to Linked only works as long as the two
versions are the same.
In other words, if you embed a linked transformer and then make changes to the
embedded definition, you won’t be able to revert to the linked version.”
</span>
</td>
</tr>
</table>

**Password**

The password field (in the Export Custom Transformer dialog) allows you to password-protect the custom transformer. This will make it impervious to edits from unauthorized persons.

Additionally, the file contents are (very mildly) encrypted so that they cannot be copied by opening the source file in a text editor.

This allows authors to make transformers available for purchase without any fear that their work will be copied or edited.
Of course, it’s important not to forget or lose the password, in case you wish to make edits!
Licensing

On the same topic, custom transformers can be licensed so that they cannot be used without the proper registration code. A special transformer – the LicenseChecker – and a license generator tool are provided for authors to implement such a setup.

Here, for example, the LicenseChecker is being used to protect a custom transformer. If the transformer is licensed then it will work as expected. If it is not licensed then it will terminate.

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
“It’s best to debug your custom transformers before exporting them,
because the Run with Breakpoints tool does not work inside exported
transformers, only embedded.”
</span>
</td>
</tr>
</table>

For more information on obtaining licenses for a custom transformer, contact the Safe Software support team at www.safe.com/support.

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
“Did you know that it is possible to nest one custom transformer inside
another?
For example, download the PolylineAnalyzer custom transformer from the FME store and
you’ll find inside its definition it uses other custom transformers such as the
VertexCounter and AzimuthCalculator. Look at the VertexCounter definition and you’ll
find it uses a custom transformer called the LoopFilter!
So nesting transformers – whether linked or embedded – is a perfectly valid technique.”
</span>
</td>
</tr>
</table>