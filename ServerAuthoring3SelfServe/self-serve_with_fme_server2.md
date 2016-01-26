# Self-Serve with FME Server

Self-Serve takes the tedious tasks away from staff and leaves them to concentrate on more important things.

**What is Self-Serve?**

Self-Serve is the term for a system set up to allow the end user to carry out his own data translations and transformations. In this way, routine data management tasks are offloaded from staff to the user, who is empowered to carry out processes at their own convenience.

Usually the system is set up in such a way that the end user needs no prior FME experience or training to carry out their goals; for example, they can access the functionality through a web interface customized to their particular needs. In fact the user does not even need to know of FME, or that FME is the engine driving their applications!

**Self-Serve Types**

In general there are two types of self-serve systems.
Data Upload systems are where the user is able to upload their data to be processed on FME Server. A typical application would be a user uploading data to be validated. The data is run against a number of tests in an FME workspace and the results sent back to the user.

Data Download systems are where the user is able to serve themselves with data. A typical application would be an organization that frequently provides data to either staff or customers. With a Data Download system the user can fetch their own data, rather than having to be provided with it in a more manual way.

**Self-Serve and Services**

Self-Serve is implemented through a number of Services on FME Server. A Service is a particular method of communication between client and server. Different services allow different forms of data distribution to take place.

**Self-Serve and Parameters**

FME translations and transformations are controlled by Parameters. To enable users to select the requirements for their translation, FME includes functionality called Published Parameters. A parameter that is published becomes available for the end-user to set.