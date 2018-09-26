# 3.03.ex3.1.md

[method with multiple clauses instead of just one]

Now, we know from inspecting the data that the missing values were entire empty rows. However, if you browse through the data again, you will notice that some attributes have scattered missing values. Let's guard against those coming to bother us in the future by removing features missing values in **any** attribute we might want to use.

To do this, we can copy the existing statement and change the attribute name. Click in the Left Value cell with `Day`. This action will select this row. Then click the Copy button located in the bottom left of the Test Clauses table:

This will copy this row to the clipboard. Next, click in the empty Left Value cell below and click the Paste button. This will duplicate the first row. Change the attribute value to `Department`. Repeat this procedure for the following attributes:

- `Hour`
- `Local_Area`
- `Minute`
- `Month`
- `Year`

[SIMPLIFY IF POSSIBLE. MAKE SURE IT IS ONLY AS COMPLICATED AS THE WRITER. IF DOING ALL THE ATTR, MAKE IT AN AND TEST]
