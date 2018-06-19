## Placing an Inspector Transformer ##
The best, and simplest way to apply an Inspector is to right-click the output port of an object in a workspace and select the Connect Inspector option.

Here the user right-clicks the Buffered port of a Bufferer transformer and chooses the option Connect Inspector:

![]({{ book.basic_repo }}{{ book.basic_branch }}/DesktopBasic2Transformation/Images/Img2.036.RightClickAddInspector.png)

Notice that an Inspector is named automatically using the transformer and output port names. Here it will be "Bufferer_Buffered":

![]({{ book.basic_repo }}{{ book.basic_branch }}/DesktopBasic2Transformation/Images/Img2.036b.RightClickAddedInspector.png)

This helps to identify the data from this Inspector (as opposed to any others) in the FME Data Inspector.

Note that the Inspector transformer only opens the FME Data Inspector when there are features to view. If there are zero features, then the Data Inspector will not open!
