import OpenGL.GL as GL
from PIL import Image
import os
from core import Mesh
from texture import TexturedCube

FILE_OPENING_CONFIG = 'RGBA'


class SkyBox(TexturedCube):
    """Create and texture a SkyBox derived from a TexturedCube"""
    def __init__(self, shader, tex_path):
        self.file = tex_path
        coords = ((-1, 1, -1), (-1, -1, -1), (1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1)) + \
                 ((-1, -1, 1), (-1, -1, -1), (-1, 1, -1), (-1, 1, -1), (-1, 1, 1), (-1, -1, 1)) + \
                 ((1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, 1), (1, 1, -1), (1, -1, -1)) + \
                 ((-1, -1, 1), (-1, 1, 1), (1, 1, 1), (1, 1, 1), (1, -1, 1), (-1, -1, 1)) + \
                 ((-1, 1, -1), (1, 1, -1), (1, 1, 1), (1, 1, 1), (-1, 1, 1), (-1, 1, -1)) + \
                 ((-1, -1, -1), (-1, -1, 1), (1, -1, -1), (1, -1, -1), (-1, -1, 1), (1, -1, 1))

        class Texture:
            def __init__(self, tex_path):
                self.glid = GL.glGenTextures(1)
                self.type = GL.GL_TEXTURE_CUBE_MAP
                i = 0
                for file in sorted(os.listdir(tex_path)):
                    # Load the texture
                    tex_file = os.path.join(tex_path, file)
                    tex = Image.open(tex_file).convert(FILE_OPENING_CONFIG)
                    GL.glBindTexture(self.type, self.glid)
                    GL.glTexImage2D(GL.GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL.GL_RGBA, tex.width, tex.height,
                                    0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, tex.tobytes())

                    # Set parameters to smooth the limit between skybox textures
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_R, GL.GL_CLAMP_TO_EDGE)
                    i += 1
                print("Skybox textures loaded.")

        mesh = Mesh(shader, attributes=dict(position=coords))
        texture = Texture(tex_path)
        super().__init__(mesh, cube_map=texture)
