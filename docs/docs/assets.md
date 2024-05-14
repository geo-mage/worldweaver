# Assets Management

The assets used for the different objects created in Blender are customizable.

The software is packaged with base assets that can be used as templates. 

On each kind of object there are restriction on what the asset should contain, depending on how the object is modeled internally.

Most assets are based on Blender's [Geometry Nodes](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/introduction.html).

## Buildings

There are 4 kinds of buildings ("Normal", Churches, Factories and Malls), but render-wise they are managed the same way:
the footprint of the building is extracted from the datasets, raised to the correct altitude to fit the terrain, and a surface is generated in Blender.
The asset we use is a geometry node based on [Buildify](https://paveloliva.gumroad.com/l/buildify) and takes this surface and transforms it into a building

## Flood
[TODO]
The flood object consists of square cells linked together to create a surface, and then the asset we use is inspired from [this tutorial](https://www.youtube.com/watch?v=0SJ-__0gK_k&feature=youtu.be) to create the aspect of realistic water

## Forests

The software creates the footprint of forests using the input data, a surface is craated from it, and then the asset samples random points on the surface and places a tree on it.

## Roads

The software creates the footprint of roads using the input data, a surface is created from it, and then the asset applies a texture on it and ensures it is place just over the top of the terrain surface

## Water

The software creates the footprint of water using the input data, a surface is created from it, and then the asset applies a texture on it.

## Cars

Along road lanes, the software generates vectors that should indicate the orientation of the car. The asset aligns a car model along this vector
