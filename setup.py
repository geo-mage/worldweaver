from distutils.core import setup

setup(
    name="mage_procgen",
    version="0.0.0.1",
    description="Procedural Generator for satellite images",
    author="Armand Verstraete",
    author_email="armand.verstraete@lecnam.net",
    url="",
    packages=[
        "mage_procgen",
        "mage_procgen.Utils",
        "mage_procgen.Renderer",
        "mage_procgen.Processor",
        "mage_procgen.Parser",
        "mage_procgen.Manager",
        "mage_procgen.Loader",
    ],
)
