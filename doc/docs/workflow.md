# Standard Workflow 

## Preparation

First, you need to get the data needed for the application.
For this version, only data from IGN [https://www.geoportail.gouv.fr/](https://www.geoportail.gouv.fr/) is supported, though with adaptations the software could be adapted for different data providers.

IGN provides data for each Departement. For each zone you want to render, you need to 
download:
  - BD TOPO (terrain and infrastructure definition) [https://geoservices.ign.fr/bdtopo](https://geoservices.ign.fr/bdtopo)
  - RGE Alti (altitude raster) [https://geoservices.ign.fr/rgealti](https://geoservices.ign.fr/rgealti). It is best to chose the 1m resolution dataset rather than the 5m resolution one for more accuracy in the terrain
  - BD ORTHO (orthorectified aerial view) [https://geoservices.ign.fr/bdortho](https://geoservices.ign.fr/bdortho)

!!! note "About the data"

    Since the data is grouped by departements, the databases can be voluminous to download (RGE Alti is usually a couple of GB and BD Ortho can easily reach 50GB), and IGN servers are quite slow, it might take quite a while to get all the data for a departement

Once you have those 3 datasets for each departement covered by the zone you want to render, you need to extract them so the software can read them. Command line helpers are available for that purpose in [Datafiles](datafiles.md)

## Configuration

Before you can render, you need to generate the configuration file for your run. 
To help in that, there are command line helpers available in [Configuration Files Edition](conf.md).

The software is provided with a base file from which you can tweak however you like.

## Run

Once the configuration file is done, open Blender, preferably through a terminal (easier to get the logs this way).
To do so, when you are inside the folder where blender is installed:

    ./blender --python-use-system-env &

You can then set the configuration file used by the plugin, either by going to Edit->Preferences->Add-ons, 
search for MAGE Procgen, and edit the "Configuration File Path" field. 

Alternatively, you can also do it by pression Ctrl + Shift + L; or go to Object->Mage Procgen Config Select.

Once the configuration file is set (you don't have to do it if the name of the file has not changed since the last run),
you can run the plugin by either pressing Ctrl + Shift + M; or go to Object->Mage Procgen

While the program is running, you will not be able to see or do anything inside Blender, 
but you can follow the progression through the logs in the terminal you used to start Blender

Once the run is finished, you will be able to see the scene, and if you have enabled it in the configuration file, you will have a folder containing:
* A copy of the configuration file you used, for tracking purposes
* The rendered images, each paired with another image with is a greyscale semantic map of the image.
