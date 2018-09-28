This is achieved through the Select Feature Types dialog. In FME, ***feature types*** define the schema of the data being read. They define the dataset to be read or written and the attributes these datasets possess. A ***feature*** is an individual item within the translation.

When working with spatial data, a feature type corresponds to a layer (Esri shapefile *.shp, AutoCAD drawing *.dwg), level (Microstation *.dgn), etc., depending on the format. Features are geometric features such as points, lines, or polygons. When working with spreadsheet data (e.g. *.csv, *.xlsx, a table in a database), a feature type corresponds to a table and features are rows. In all cases, the unit making up a feature type is determined by the data format.

The Select Feature Types dialog determines which layers show in the workspace. Here, for example, is a Select Feature Types dialog where the user has chosen to include all available layers in the workspace:

![](./Images/Img1.018.FeatureTypeSelect.png)
