# Configuration file generation

The project contains command line helpers to generate and edit configuration files 

These helpers are located in the Utils.ConfigGen module

## Guidelines for configuration edition

For performances reasons, keep the window at a reasonable size (above 10 km² seems to be a bit big especially if there is flooding involved).

The terrain size and resolution will weight heavily on the performances, but having a scene that is large and detailed enough is also important to get realistic results especially if you use flooding.

If you modify assets, make sur they are not too polygon-heavy to avoid saturating Blender (especially for trees, because there can easily be a lot of them in a scene).

## Configuration file structure detail

### Render Window:

* `window_type` is used to determine how the window will be defined.If it is "COORDS", it will be from the `x_min`, `x_max`, `y_min` and `y_max` coordinates; if it is "TOWN", it will be from the shape of the town indentified by `town_dpt` and `town_name`; and if it is "FILE", it will be from the bounds of the objects described in the shapefile at `window_shapefile`. 

* `window_x_min` is the min X of the render window. Only used if window type is "COORDS".
* `window_y_min` is the min Y of the render window. Only used if window type is "COORDS".
* `window_x_max` is the max X of the render window. Only used if window type is "COORDS".
* `window_y_max` is the max Y of the render window. Only used if window type is "COORDS".
* `window_from_crs` is the CRS code the xmin, xmax, ymin and ymax are given. Only used if window type is "COORDS".

* `town_dpt` is the number of the departement in which the town is. Only used if window type is "TOWN".
* `town_name` is the name of the town that will determine the render window. Only used if window type is "TOWN".

* `window_shapefile` is the path of the file that will define the render window. The software will read the features described in the file, extract the bounds from them and create the render window from that. Only used if window type is "FILE".

### Render parameters:

* `terrain_resolution` is the spatial resolution of the terrain in the render. Ideally it should be the same as the terrain raster data resolution to get the best ratio of accuracy vs performance but it can be lowered for big scenes.
* `use_sat_img` is the flag that if True, the software will use BDORTHO images as texture for the terrain. If False, it will use a base texture.

### Flood parameters:

* `flood` is the flag that if True, will tell the software to generate a flood on the scene . For more precise info on how the flood is generated, go to [Flooding Algorithm](flood.md)
* `flood_height`  Only used if flood is True. Height of the flood in meters.
* `flood_cell_size` (float): Only used if flood is True. Spatial resolution of the flood

### Output parameters:

* `export_img` is the flag that if True, will thell the software generate png files from aerial views the scene. If False, will show all the buildings, cars, trees etc in the whole render scene.
* `out_img_resolution` is the resolution of the output images
* `out_img_pixel_size` is the size of a pixel, in m.

### Assets

All assets are configured with the same setup:

* `geometry_node_file` is the name of the Blender asset file for the object. It must be in the Assets folder. 
* `geometry_node_name` is the name of the geometry node setup for the object. For more info on how assets should be generated, go to [Assets Management](assets.md). 
* `tagging_index` is the index using which object will be tagged in the output semantic map.

The objects that can be customized are:
* "Normal" Buildings (buildings that do not have a special semantic tag in the BDTOPO)
* Churches (buildings that are tagged with the "Religieux" tag in the BDTOPO)
* Factories (buildings that are tagged "Industriel" in the BDTOPO)
* Malls (buildings that are tagged with the "Commercial et services" tag in the BDTOPO)
* Flood (the flood water)
* Forests (areas that are tagged as forests in the BDTOPO)
* Roads (roads surface deducted from BDTOPO info)
* Water (surface of lakes, rivers, etc)
* Cars (cars are put on semi-random locations along the roads)

## Module methods

::: mage_procgen.Utils.ConfigGen

