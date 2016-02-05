# Coordinate System Selection

One of the most obvious requirements in Self-Serve is to be able to set the output coordinate system

One of the most useful parameters in a self-serve system controls the output coordinate system.
Publishing this parameter allows the end-user to receive data in a coordinate system of their choice.

**Coordinate System Parameters**

Coordinate system reprojection can be carried out by setting the parameters under the Reader/Writer in the Navigator window:

Alternatively, a transformer – such as the CSMapReprojector – can be used, in which case the relevant parameters can be found under the Transformers section of the Navigator window:

The obvious advantage to using a transformer is that you have control over other reprojection factors, such as the geographic transformation and grid height.