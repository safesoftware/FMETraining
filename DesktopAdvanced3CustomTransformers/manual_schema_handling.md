# Manual Schema Handling


For full control over how the attribute schema is handled in a custom transformer, the workspace author should create it using the setting ‘Advanced – Fix Manually’.

At that point the custom transformer has no published parameters, and therefore no userdefinable options:

To expose a parameter or attribute, the workspace author must go to the transformer definition and manually create a published parameter:

Then the parameter must be selected wherever it is going to be used:

Compared to the automatic process, in manually defined schema handling it’s more obvious – to an experienced user – what is happening. However, it’s not such an easy process for a newer user to be able to set up.

**Handling Outgoing Attributes**

Besides incoming attributes, there is also the question of what attributes should emerge from the output of a custom transformer.

Best Practice suggests that we really don’t want to output more attributes than are expected by the user.

For example, we would want to hide or remove any attributes that are part of a calculation, or any attributes that are otherwise generated inside the custom transformer but aren’t necessary to the output.

Here the custom transformer is calculating the average area of a number of polygon features.
The required output is an attribute called AverageArea.

However, no effort is being made to clear up other attributes that are being used or generated, such as _area, _min, and _max.

The workspace author should clean up this output. They can do this by visiting the custom transformer definition, clicking on the parameters (cog wheel) button for the output port object, and opening a dialog in which the attributes to be output can be defined:

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
“One suggestion is to prefix all temporary attributes inside a custom
transformer with _temp. Then you’ll know which to keep and which to
clean up.”
</span>
</td>
</tr>
</table>

Let’s go back to the workspace – before creating the custom transformer – and this time createall our references manually.

**1)** Open Workspace

Open the workspace C:\FMEData2015\Workspaces\DesktopAdvanced\Exercise3d-Begin.fmw.
As you’ll see, this is the same as Exercise3a-Begin.fmw – we have a workspace ready to create a custom transformer.

**2)** Create Custom Transformer

As in Exercise 3a, select the AreaCalculator transformer and the first ExpressionEvaluator, right-click on them, and choose the context menu option ‘Create Custom Transformer’.

In the Create Custom Transformer dialog enter a name, category, and description for the new custom transformer. A good name for the transformer will be the DensityEvaluator.

This time, set the Attribute References parameter to “Advanced – Fix Manually” and click OK.

The custom transformer will now be created.

**3)** Create Published Parameter

Examine the custom transformer and this time you’ll see there are no published parameters.

In fact, the ExpressionEvaluator will have a red parameters button, because it has no access to the required attributes:

So, in the custom transformer definition, locate the User Parameters section in the Navigator window. Right-click on the part labelled User Parameters and select Add Parameter.

In the dialog that opens, define a new published parameter as follows:

Type:Attribute Name

Name:DensityAttr

Prompt:Density Attribute

The Published checkmark should be turned on, but turn off the Optional checkmark, as this is a compulsory parameter for this transformer:

Click OK to create the parameter.

**4)** Apply Published Parameter

The parameter we need is now created, but not yet being applied. To do so open the parameters dialog for the ExpressionEvaluator.
You’ll see the problem in the expression; TotalPopulation2001 is highlighted in red because it is not available to the transformer:

So, strip out the TotalPopulation2001 part of the expression:

Now add a reference to the newly created user parameter.

This can be done by locating the parameter in the operators panel and double-clicking it:

This will create an expression like so:

You should also change the Destination Attribute from PopulationDensity2001 to DensityResult.

Click OK to accept the new expression and close the dialog. Notice that the ExpressionEvaluator parameters button turns from red to blue, meaning all is now correct.

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
“In step 4 the @Value() part of the expression needs to remain, because
the parameter only returns an attribute name, not a value.
It’s one reason why automated schema handling is easier to use.”
</span>
</td>
</tr>
</table>

**5)** Check Parameter

Return to the main canvas window. The DensityEvaluator parameter button is marked red, but that’s OK because we haven’t yet picked an attribute to process.

Click the parameter button and select TotalPopulation2001 as the attribute to process.

**6)** Add Second Custom Transformer

Now delete the remaining ExpressionEvaluator from the main canvas as we no longer need it.

Use Quick Add to add a second DensityEvaluator instance. Connect it as a second connection from the CsmapReprojector and select TotalPopulation2011 as the attribute to process.

**7)** Run Workspace

Add an Inspector transformer to each of the custom transformers and run the workspace. Check the output to ensure the results are correct.