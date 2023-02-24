import os
from time import time
import bpy
from util.blender import loadSceneFromFile
from util.blender_extra.material import setImage


_exportTemplateFilename = "building_material_templates.blend"

_renderFileFormats = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG"   
}


class TextureExporter:
    
    def __init__(self, assetsDir, assetPackageDir):
        self.assetPackageDir = assetPackageDir
        self.exportTemplateFilename = os.path.join(assetsDir, _exportTemplateFilename)
        # a directory where textures generated by the Compositor File Output node are placed
        self.tmpTextureDir = None
        # Linked template scenes from <_exportTemplateFilename>. They will be unlinked in <self.cleanup(..)>
        self.linkedScenes = []
    
    def cleanup(self):
        tmpTextureDir = self.tmpTextureDir
        if tmpTextureDir:
            os.removedirs(tmpTextureDir)
            self.tmpTextureDir = None
        for sceneName in self.linkedScenes:
            bpy.data.scenes.remove(bpy.data.scenes[sceneName])
    
    def verifyPath(self, textureDir):
        if not os.path.exists(textureDir):
            os.makedirs(textureDir)
    
    def setTmpTextureDir(self, textureDir):
        if not self.tmpTextureDir:
            # use the number of seconds as the name of the subdirectory
            numSeconds = round(time())
            while True:
                tmpTextureDir = os.path.join(textureDir, str(numSeconds))
                if os.path.exists(tmpTextureDir):
                    numSeconds += 1
                else:
                    os.makedirs(tmpTextureDir)
                    self.tmpTextureDir = tmpTextureDir
                    break

    def makeCommonPreparations(self, scene, textureFilename, textureDir):
        self.verifyPath(textureDir)
        self.setTmpTextureDir(textureDir)
        nodes = scene.node_tree.nodes
        fileOutputNode = nodes["File Output"]
        fileOutputNode.base_path = self.tmpTextureDir
        fileOutputNode.file_slots[0].path, extention = os.path.splitext(textureFilename)
        # Set the correct file format for rendering
        fileOutputNode.format.file_format = _renderFileFormats.get(
            extention.lower(), 'PNG'
        )
        return nodes
    
    def renderTexture(self, scene, textureFilepath):
        tmpTextureDir = self.tmpTextureDir
        bpy.ops.render.render(scene=scene.name)
        os.replace(
            # the texture file is the only file in <tmpTextureDir>
            os.path.join(tmpTextureDir, os.listdir(tmpTextureDir)[0]),
            textureFilepath
        )
    
    def getTemplateScene(self, sceneName):
        scene = bpy.data.scenes.get(sceneName)
        if scene:
            # perform a quick sanity check here
            if not scene.use_nodes:
                scene = None
        if not scene:
            scene = loadSceneFromFile(self.exportTemplateFilename, sceneName)
            self.linkedScenes.append(scene.name)
        return scene
    
    def setScaleNode(self, nodes, nodeName, scaleX, scaleY):
        scaleInputs = nodes[nodeName].inputs
        scaleInputs[1].default_value = scaleX
        scaleInputs[2].default_value = scaleY
    
    def setTranslateNode(self, nodes, nodeName, translateX, translateY):
        translateInputs = nodes[nodeName].inputs
        translateInputs[1].default_value = translateX
        translateInputs[2].default_value = translateY
    
    def setImage(self, fileName, path, nodes, nodeName):
        return setImage(
            fileName,
            path,
            nodes,
            nodeName
        )
    
    def setColor(self, color, nodes, nodeName):
        nodes[nodeName].outputs[0].default_value = color