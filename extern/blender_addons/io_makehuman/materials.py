import bpy
import os

class MH2B_OT_Material:
    def __init__(self, dirname):
        self.dirname = dirname
        self.blendmat = None
        self.nodes = None
        self.glTFOutputName = "glTF Material Output"

    def glTFOutput(self, x, y):
        if self.glTFOutputName  in bpy.data.node_groups:
            group = bpy.data.node_groups[self.glTFOutputName]
        else:
            group = bpy.data.node_groups.new(self.glTFOutputName, 'ShaderNodeTree')
            group.interface.new_socket("Occlusion", socket_type="NodeSocketFloat")
            thicknessFactor  = group.interface.new_socket("Thickness", socket_type="NodeSocketFloat", )
            thicknessFactor.default_value = 0.0
            group.nodes.new('NodeGroupOutput')
            group_input = group.nodes.new('NodeGroupInput')
            group_input.location = -200, 0

        node_gltf_matoutput = self.nodes.new("ShaderNodeGroup")
        node_gltf_matoutput.node_tree = bpy.data.node_groups[group.name]

        node_gltf_matoutput.location = x, y
        return (node_gltf_matoutput)

    def addTextureNode(self, path, x, y, noncolor, name):
        node = self.nodes.new('ShaderNodeTexImage')
        if self.dirname is not None:
            img = os.path.join(self.dirname, path)
        else:
            img = path
        node.image = bpy.data.images.load(img)
        node.name = name
        node.label = name
        node.location = x,y
        if noncolor:
            node.image.colorspace_settings.name = 'Non-Color'
        return (node)

    def addNodes(self, jdata, texture, alpha, roughness, metallic, normtexture, normscale, aotexture, aoscale, mrtexture):

        # Add the Principled Shader node
        #
        links = self.blendmat.node_tree.links

        node_principled = self.nodes.new(type='ShaderNodeBsdfPrincipled')
        node_principled.location = 0,0

        # Add the Output node, and link to principled
        #
        node_output = self.nodes.new(type='ShaderNodeOutputMaterial')
        node_output.location = 600,0


        # add color, either texture or list
        #
        if isinstance(texture, dict) and "source" in texture:
            img = texture["source"]
            path = jdata["images"][img]["uri"]

            # Add the Image Texture node
            node_tex = self.addTextureNode(path, -600, 300, False, "BASE COLOR")

            links.new(node_tex.outputs["Color"], node_principled.inputs["Base Color"])
            if alpha is not None:
                links.new(node_tex.outputs["Alpha"], node_principled.inputs["Alpha"])
        elif isinstance(texture, list):
            node_principled.inputs["Base Color"].default_value = tuple(texture)

        if roughness is not None:
            node_principled.inputs["Roughness"].default_value = roughness

        if metallic is not None:
            node_principled.inputs["Metallic"].default_value = metallic

        if normtexture is not None:
            # Add the normal Texture node
            #
            img = normtexture["source"]
            path = jdata["images"][img]["uri"]
            node_normtex = self.addTextureNode(path, -600, 0, True, "NORMAL MAP")

            node_normalmap = self.nodes.new('ShaderNodeNormalMap')
            node_normalmap.location = -300, 0
            node_normalmap.inputs["Strength"].default_value = normscale
            links.new(node_normtex.outputs["Color"], node_normalmap.inputs["Color"])
            links.new(node_normalmap.outputs["Normal"], node_principled.inputs["Normal"])

        if mrtexture is not None:
            # add metallic-roughness texture
            #
            img = mrtexture["source"]
            path = jdata["images"][img]["uri"]
            node_mrtex = self.addTextureNode(path, -600, -300, True, "METALLIC ROUGHNESS")
            node_sepcolmr = self.nodes.new('ShaderNodeSeparateColor')
            node_sepcolmr.location = -300,-300

            links.new(node_mrtex.outputs["Color"], node_sepcolmr.inputs["Color"])
            links.new(node_sepcolmr.outputs[2], node_principled.inputs["Metallic"])
            links.new(node_sepcolmr.outputs[1], node_principled.inputs["Roughness"])


        if aotexture is not None:
            # add ambient occlusion texture
            #
            img = aotexture["source"]
            path = jdata["images"][img]["uri"]
            node_aotex = self.addTextureNode(path, -600, -600, True, "OCCLUSION")
            node_sepcol = self.nodes.new('ShaderNodeSeparateColor')
            node_sepcol.location = -300,-600
            node_mixcol = self.nodes.new('ShaderNodeMixRGB')
            node_mixcol.location = -100,-600
            node_mixcol.inputs[0].default_value = aoscale

            node_amboc = self.nodes.new("ShaderNodeAmbientOcclusion")
            node_amboc.location = 100,-600

            node_mixcshader = self.nodes.new("ShaderNodeMixShader")
            node_mixcshader.location = 400, 0

            links.new(node_aotex.outputs["Color"], node_sepcol.inputs["Color"])
            links.new(node_sepcol.outputs[0], node_mixcol.inputs[2])
            links.new(node_mixcol.outputs[0], node_amboc.inputs["Color"])
            links.new(node_amboc.outputs["Color"], node_mixcshader.inputs[0])

            links.new(node_principled.outputs["BSDF"], node_mixcshader.inputs[2])
            links.new(node_mixcshader.outputs[0], node_output.inputs["Surface"])

            output = self.glTFOutput(-100, -450)
            links.new(node_sepcol.outputs[0], output.inputs[0])
        else:
            links.new(node_principled.outputs["BSDF"], node_output.inputs["Surface"])


    def addMaterial(self, jdata, material):
        matj = jdata["materials"][material]
        name = matj["name"] if "name" in matj else 'Material'
        alpha = matj["alphaMode"] if "alphaMode" in matj else None
            
        self.blendmat = bpy.data.materials.new(name=name)
        self.blendmat.use_nodes = True
        if alpha:
            self.blendmat.blend_method = 'BLEND'
        self.nodes = self.blendmat.node_tree.nodes
        self.nodes.clear()

        normtexture = None
        normscale = 0.0
        if "normalTexture" in matj:
            textind = matj['normalTexture']["index"]
            normscale = matj['normalTexture']["scale"]
            normtexture = jdata["textures"][textind]

        aotexture = None
        aoscale = 0.0
        if "occlusionTexture" in matj:
            textind = matj['occlusionTexture']["index"]
            aoscale = matj['occlusionTexture']["strength"]
            aotexture = jdata["textures"][textind]

        if "pbrMetallicRoughness" in matj:
            pbr = matj["pbrMetallicRoughness"]
            roughness = pbr['roughnessFactor'] if "roughnessFactor" in pbr else None
            metallic  = pbr['metallicFactor'] if "metallicFactor" in pbr else None

            mrtexture = None
            if 'metallicRoughnessTexture' in pbr:
                textind = pbr['metallicRoughnessTexture']["index"]
                mrtexture = jdata["textures"][textind]

            if 'baseColorTexture' in pbr:
                textind = pbr['baseColorTexture']["index"]
                texture = jdata["textures"][textind]
                self.addNodes(jdata, texture, alpha, roughness, metallic, normtexture, normscale, aotexture, aoscale, mrtexture)
            elif 'baseColorFactor' in pbr:
                self.addNodes(jdata,  pbr['baseColorFactor'], alpha, roughness, metallic, normtexture, normscale, aotexture, aoscale, mrtexture)
        return(self.blendmat)

