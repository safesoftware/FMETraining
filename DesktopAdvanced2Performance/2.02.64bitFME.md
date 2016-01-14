# 64-Bit FME

64-bit FME is not for everyone, but used in the right place it can have tremendous benefits.

**What is 64-bit FME?**

A 32-bit operating system is capable of using memory addresses up to 232, meaning it can use a maximum of 4 GB of memory. However, a 64-bit operating system can use memory addresses up to 264, which technically allows up to 16 billion GB of memory.

In practice, a 64-bit system uses nowhere near that much memory; still it allows a vast amount of additional memory which can be taken advantage of by 64-bit software.

64-bit FME is a version of FME specifically designed to take advantage of a 64-bit operating system. It is well-suited to processing very large amounts of data, due to its ability to use a greater amount of memory.

**What are the Disadvantages of 64-bit?**

There are a number of disadvantages to using 64-bit FME.

Firstly it requires a 64-bit operating system and the hardware to support it. On a 32-bit operating system you would only be able to run 32-bit FME.

Secondly – and more importantly – not every format in FME is supported on 64-bit. Usually that’s because the format itself – or its proprietary software – isn’t available on 64-bit platforms. In that situation you would need to use 32-bit FME.

Additionally, you need to take care to use the correct clients; for example when reading 64-bit Oracle you’ll need to install a special 64-bit client for FME to be able to connect.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Jake Speedie says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“The Safe Software web site has a list of supported formats
(safe.com/formats) with info on which are supported on 64-bit.”
</span>
</td>
</tr>
</table>

**FME and 64-Bit**

Here are some helpful hints and tips on using 64-bit FME:

- If you are using 32-bit Windows then you’ll need to use 32-bit FME. If you are using 64-bit Windows then you can use either 32-bit or 64-bit FME. Both will work, but only 64-bit FME will take advantage of any extra memory available to it.
- It is possible to install both 32-bit and 64-bit FME on the same 64-bit computer. That way you can use the 32-bit version to access all of the formats you might require, and use the 64-bit version for more intensive processing.
- It is also possible to install 32-bit and 64-bit FME engines on the same FME Server core.
Job Routing techniques will allow you to designate which jobs should be processed by which engine.
- If you are running 32-bit FME on a 64-bit system then you would need the 32-bit client to connect to, for example, an Oracle database. There are similar requirements for reading Microsoft Office files. FME, with either client, can read and write to a 32-bit or 64-bit Oracle database, provided your license level is sufficient.
- There are many helpful articles on 64-bit on the FME knowledgebase, FMEpedia.
- 
