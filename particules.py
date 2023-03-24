from itertools import cycle
import OpenGL.GL as GL  # standard Python OpenGL wrapper
from PIL import Image  # load texture maps
import glfw
from matplotlib import pyplot as plt
import numpy as np  # all matrix manipulations & OpenGL args
from core import Mesh, Node, Texture
import random
from texture import Texture, Textured, calcNormals
from transform import Trackball, vec, quaternion, quaternion_from_euler
from animation import (KeyFrameControlNode)

class Particule(Textured):
    def __init__(self, viewer, shader, texture, normals, vertices, index, tex_coord, light_dir, position=(0, 0, 0), shinyness=2, scale=1):
        self.viewer = viewer
        self.shader = shader
        self.texture = texture
        self.normals = normals
        self.vertices = np.array(vertices, np.float32)*scale
        self.index = index
        self.tex_coord = tex_coord
        self.light_dir = light_dir
        self.position = np.array(position, np.float32)
        self.shinyness = shinyness
        self.scale = scale
        self.trackball = Trackball()
        mesh = Mesh(shader, attributes=dict(position=self.vertices+self.position, tex_coord=np.array(tex_coord), normal=normals),
                    index=index, s=shinyness, light_dir=light_dir)
        super().__init__(mesh, diffuse_map=texture)
    
    def updateOrientation(self):
        rotationMatrix = self.trackball.matrix()
        a,b,c = rotationMatrix[0], rotationMatrix[1], rotationMatrix[2]
        matrix = np.zeros((3,3), np.float32)
        for i in range(3):
            [a,b,c,d] = rotationMatrix[i]
            matrix[i] = [a,b,c]
        
        vertices_ = np.zeros_like(self.vertices, np.float32)
        for i in range(len(self.vertices)):
            vertices_[i] = self.vertices[i] @ matrix
        vertices_ = vertices_ + np.array(self.position, np.float32)
        (normals_, vertices_, index_) = calcNormals(vertices_, self.index)
        mesh = Mesh(self.shader, attributes=dict(position=vertices_, tex_coord=np.array(self.tex_coord), normal=normals_),
                    index=self.index, s=self.shinyness, light_dir=self.light_dir)
        self.drawable = mesh
    
    def draw(self, primitives=GL.GL_TRIANGLES, **uniforms):
        self.updateOrientation()
        return super().draw(primitives, **uniforms)

class leafParticle(Particule):
    def __init__(self, viewer, shader, light_dir, position=(0,0,0), shinyness=2, scale=1) :
        texture=Texture("Textures/leaf.png")
        vertices = [[-0.5,-0.5,0],[0.5,-0.5,0],[-0.5,0.5,0],[0.5,0.5,0]]
        index = [0,1,3,0,3,2]
        normals = [[0,0,1],[0,0,1],[0,0,1],[0,0,1]]
        tex_coord = [[0,1],[1,1],[0,0],[1,0]]
        super().__init__(viewer, shader, texture, normals, vertices, index, tex_coord, light_dir, position, shinyness, scale)

class FallingLeaf(KeyFrameControlNode):
    def __init__(self, viewer, shader, light_dir, position=(0,0,0), shinyness=2, scale=1):
        trans_keys = {0: vec(0, 0, 0), 8: vec(0, -3, 0), 9: vec(0, -3.3, 0), 10: vec(0, -3.5, 0)}
        rot_keys = {0:quaternion(), 10:quaternion()}
        scale_keys = {0: 1, 8: 0.7, 9:0.3, 10: 0}
        super().__init__(trans_keys, rot_keys, scale_keys, repeat=True)
        self.add(leafParticle(viewer, shader, light_dir, position, shinyness, scale))
