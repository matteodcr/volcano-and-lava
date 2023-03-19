import OpenGL.GL as GL
from PIL import Image
import os

from core import Mesh

class TexturedCube:
    """ Drawable mesh decorator that activates and binds OpenGL textures """
    def __init__(self, drawable, **textures):
        self.drawable = drawable 
        self.textures = textures

    def draw(self, primitives=GL.GL_TRIANGLES, **uniforms):
        GL.glDepthFunc(GL.GL_LEQUAL);
        for index, (name, texture) in enumerate(self.textures.items()):
            GL.glActiveTexture(GL.GL_TEXTURE0 + index)
            GL.glBindTexture(texture.type, texture.glid)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, 36)
            GL.glBindVertexArray(0)
            uniforms[name] = index
        self.drawable.draw(primitives=primitives, **uniforms)
        GL.glDepthFunc(GL.GL_LESS); # set depth function back to default

class CubeMapTexture(TexturedCube):
    """ Simple first textured object """
    def __init__(self, shader, tex_path):
        self.file = tex_path

        base_coords = ((-1, 1, -1), (-1, -1, -1), (1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1)) + \
                      ((-1, -1, 1), (-1, -1, -1), (-1, 1, -1), (-1, 1, -1), (-1, 1, 1), (-1, -1, 1)) + \
                      ((1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, 1), (1, 1, -1), (1, -1, -1)) + \
                      ((-1, -1, 1), (-1, 1, 1), (1, 1, 1), (1, 1, 1), (1, -1, 1), (-1, -1, 1)) + \
                      ((-1, 1, -1), (1, 1, -1), (1, 1, 1), (1, 1, 1), (-1, 1, 1), (-1, 1, -1)) + \
                      ((-1, -1, -1), (-1, -1, 1), (1, -1, -1), (1, -1, -1), (-1, -1, 1), (1, -1, 1))
        mesh = Mesh(shader, attributes=dict(position=base_coords))

        class CubeMapTex:
            def __init__(self, tex_path):
                self.glid = GL.glGenTextures(1)
                self.type = GL.GL_TEXTURE_CUBE_MAP
                i = 0
                for filename in sorted(os.listdir(tex_path)):

                    # Load the texture
                    tex_file = os.path.join(tex_path, filename)
                    tex = Image.open(tex_file).convert('RGBA')
                    GL.glBindTexture(self.type, self.glid)
                    GL.glTexImage2D(GL.GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL.GL_RGBA, tex.width, tex.height,
                                    0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, tex.tobytes())

                    # Set parameters to smooth the limit between skybox textures
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR);
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR);
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE);
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE);
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_R, GL.GL_CLAMP_TO_EDGE);
                    print(f'Loaded texture {tex_file} ({tex.width}x{tex.height}')
                    i += 1

        # setup & upload texture to GPU, bind it to shader name 'cube_map'
        texture = CubeMapTex(tex_path)
        super().__init__(mesh, cube_map=texture)