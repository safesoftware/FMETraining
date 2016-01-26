# Module Review

This module introduced you to FME Server’s Self-Serve Services and related functionality in FME Workbench

**What You Should Have Learned from this Module**

The following are key points to be learned from this module.

**Theory**

• Services handle communication between FME Server and its clients. Each workspace published to FME Server can be registered with any number of services.

• The Data Download service overrides the destination dataset parameter and presents data to the end-user as a link to a zip file

• Parameters control the different actions of a Data Download system, including the output coordinate system.

• The Generic Writer is a writer whose format is only defined at run time. This can be provided by the user through a published parameter.

• Selection of source data by layer is achieved using the Feature Types to Read parameter

• Selection of source data by area can be achieved using Bounding Box parameters, or a transformer such as the Clipper or FeatureReader

• Other FME Services allow data to be streamed live into a suitable application 

**FME Skills**

• The ability to publish a workspace and register it to the FME Server Data Download service

• The ability to create and use published parameters

• The ability to give the end-user control over format, coordinate system, layers, and area of interest.

• The ability to use Data Streaming and KML Network Link services