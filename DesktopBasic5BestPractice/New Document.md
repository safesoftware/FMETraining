---

### Logger Transformer ###
Besides FME writing information to the log window, the user can force information about a feature to be logged using the Logger transformer.

This transformer is extremely useful for debugging purposes, and has a number of parameters:

![](./Images/Img3.056.LoggerParameters.png)

The 'Log Message:' parameter is especially important. When a feature is logged, the message entered into that parameter appears with the feature in the log window. Setting a unique message helps you locate logged features with the log search function.




---

### Check Timestamps ###
Timestamps in the log have this format:

<table>
<tr><th>Absolute Date</th><th>Absolute Time</th><th>Total FME Time</th><th>FME Time for this Step</th></tr>
<tr><td>2017-05-11</td><td>13:27:07</td><td>0.2</td><td>0.1</td>
</table>

The time taken for the process being logged is the "Time for this Step". Often this is rounded down to 0.0. The Total FME Time is, literally, the amount of time that FME has been actively processing.

Sometimes, this total appears at odds with the absolute date/time:

<table>
<tr><th>Absolute Date</th><th>Absolute Time</th><th>Total FME Time</th><th>FME Time for this Step</th></tr>
<tr><td>2017-05-11</td><td>13:27:07</td><td>0.2</td><td>0.1</td>
<tr><td>2017-05-11</td><td>13:29:30</td><td>68.4</td><td>68.3</td>
</table>

Here the step took 68.3 seconds, but the difference between the two absolute times is 123 seconds! 

The absolute start and end times can differ from FME processing time because non-FME processes, such as a database query, add to the absolute time taken without adding to the FME processing time.

Therefore the log can provide an indication of the efficiency of external processes; for example, database reading. A slow database read would imply database indexing needs to be improved.

---