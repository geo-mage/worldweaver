# Installation

WorldWeaver is a Blender addon written in Python. It uses a few Python libraries and other softwares.

## Dependencies

Current dependencies are as follows:
* [Blender](https://www.blender.org/download/) 3.5 and later
* [Python](https://www.python.org/downloads/) 3.10
* [7zip](https://www.7-zip.org/)
* [geopandas](https://geopandas.org/en/stable/index.html) 0.12
* [jsonpickle](https://jsonpickle.github.io/) 3
* [rasterio](https://rasterio.readthedocs.io/en/stable/) 1.3
* [pyogrio](https://pyogrio.readthedocs.io/en/latest/) 0.5
* [scipy](https://scipy.org/) 1.8
* [scikit-image](https://scikit-image.org/) 0.21.0
* [numpy](https://numpy.org/) 1.24
* [tqdm](https://github.com/tqdm/tqdm)
* [OPENEXR](https://openexr.com/en/latest/)
* [PIL](https://he-arc.github.io/livre-python/pillow/index.html)
* [IMath] (https://github.com/AcademySoftwareFoundation/Imath)
* [Sun Position](https://docs.blender.org/manual/en/3.5/addons/lighting/sun_position.html) (Native Blender Add-on)

## Setup instructions

Start by cloning the repository from GitHub or extract the tarball:

```bash
git clone https://github.com/geo-mage/worldweaver
```

Then, you can install all dependencies using `pip`. While technically not required, it is *recommended* to use a virtual environment to do so:
```bash
pip install -r requirements.txt
```

You can then install the WorldWeaver Python module into your Python environment using:
```bash
pip install .
```

### Registering the addon in Blender

Because Blender uses its own Python interpreter, we have to specify that we now want Blender to use the system Python (or the Python from your virtualenv).
This is achieved by passing the `--python-use-system-env` to Blender at startup:

```bash
blender --python-use-system-env &
```

Once Blender has started, we can register the WorldWeaver plugin as an add-on in the software. To do so:

1. Open the *Edit->Preferences->Add-ons* menu.
2. Click the *Install* button.
3. Browse the file explorer to the folder where WorldWeaver has been downloaded and select the `module_mage_procgen.py` file.

This registers WorldWeaver as a Blender add-on. In particular, this makes it possible to run the procedural generation using a simple keyboard shortcut.

### Using WorldWeaver

Once WorldWeaver is installed, check out the [standard workflow](workflow.md) for more details on how to use the plugin.



