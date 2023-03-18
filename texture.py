from itertools import cycle
import OpenGL.GL as GL              # standard Python OpenGL wrapper
from PIL import Image               # load texture maps
import glfw
import numpy as np                 # all matrix manipulations & OpenGL args
from core import Mesh, Texture


# -------------- OpenGL Texture Wrapper ---------------------------------------
class Texture:
    """ Helper class to create and automatically destroy textures """
    def __init__(self, tex_file, wrap_mode=GL.GL_REPEAT,
                 mag_filter=GL.GL_LINEAR, min_filter=GL.GL_LINEAR_MIPMAP_LINEAR,
                 tex_type=GL.GL_TEXTURE_2D):
        self.glid = GL.glGenTextures(1)
        self.type = tex_type
        try:
            # imports image as a numpy array in exactly right format
            tex = Image.open(tex_file).convert('RGBA')
            GL.glBindTexture(tex_type, self.glid)
            GL.glTexImage2D(tex_type, 0, GL.GL_RGBA, tex.width, tex.height,
                            0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, tex.tobytes())
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_WRAP_S, wrap_mode)
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_WRAP_T, wrap_mode)
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_MIN_FILTER, min_filter)
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_MAG_FILTER, mag_filter)
            GL.glGenerateMipmap(tex_type)
            print(f'Loaded texture {tex_file} ({tex.width}x{tex.height}'
                  f' wrap={str(wrap_mode).split()[0]}'
                  f' min={str(min_filter).split()[0]}'
                  f' mag={str(mag_filter).split()[0]})')
        except FileNotFoundError:
            print("ERROR: unable to load texture file %s" % tex_file)

    def __del__(self):  # delete GL texture from GPU when object dies
        GL.glDeleteTextures(self.glid)


# -------------- Textured mesh decorator --------------------------------------
class Textured:
    """ Drawable mesh decorator that activates and binds OpenGL textures """
    def __init__(self, drawable, **textures):
        self.drawable = drawable
        self.textures = textures

    def draw(self, primitives=GL.GL_TRIANGLES, **uniforms):
        for index, (name, texture) in enumerate(self.textures.items()):
            GL.glActiveTexture(GL.GL_TEXTURE0 + index)
            GL.glBindTexture(texture.type, texture.glid)
            uniforms[name] = index
        self.drawable.draw(primitives=primitives, **uniforms)





# -------------- Textured Objects ---------------------------------




class TexturedSphere(Textured):
    """ Procedural textured sphere """
    #avec l'aide de : http://www.songho.ca/opengl/gl_sphere.html
    def __init__(self, shader, tex_file="Textures/leaves.jpg", position=(0,0,0), r=1, stacks=10, sectors=10):
        # prepare texture modes cycling variables for interactive toggling
        self.wraps = cycle([GL.GL_REPEAT, GL.GL_MIRRORED_REPEAT,
                            GL.GL_CLAMP_TO_BORDER, GL.GL_CLAMP_TO_EDGE])
        self.filters = cycle([(GL.GL_NEAREST, GL.GL_NEAREST),
                              (GL.GL_LINEAR, GL.GL_LINEAR),
                              (GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR)])
        self.wrap, self.filter = next(self.wraps), next(self.filters)
        self.file = tex_file

        # setup plane mesh to be textured
        vertices = ()
        normals = ()
        
        lengthInv = 1.0 / r
        sectorStep = 2 * np.pi / sectors
        stackStep = np.pi / stacks        

        for i in range(stacks+1):
            stackAngle = np.pi / 2 - i * stackStep
            xy = r * np.cos(stackAngle)
            z = r * np.sin(stackAngle)

            for j in range(sectors+1):
                sectorAngle = j * sectorStep
                # vertex position (x, y, z)
                x = xy * np.cos(sectorAngle)
                y = xy * np.sin(sectorAngle)
                vertices = vertices+((x,y,z),)
                #normalized vertex normal (nx, ny, nz)
                nx = x * lengthInv
                ny = y * lengthInv
                nz = z * lengthInv
                normals = normals+((nx,ny,nz),)
        scaled = np.array(vertices, np.float32)+np.array(position, np.float32)
        
        indices = ()
        for i in range(stacks):
            k1 = i * (sectors + 1)
            k2 = k1 + sectors + 1
            for j in range(sectors):
                
                # 2 triangles per sector excluding first and last stacks
                if(i != 0) :
                    indices = indices+((k1, k2, k1+1),)

                if(i != (stacks-1)):
                    indices = indices+((k1+1, k2, k2+1),)
                
                k1 = k1+1
                k2 = k2+1
        indices = np.array(indices, np.uint32)
        mesh = Mesh(shader, attributes=dict(position=scaled), index=indices)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        texture = Texture(tex_file, self.wrap, *self.filter)
        super().__init__(mesh, diffuse_map=texture)
    
    def key_handler(self, key):
        # cycle through texture modes on keypress of F6 (wrap) or F7 (filtering)
        self.wrap = next(self.wraps) if key == glfw.KEY_F6 else self.wrap
        self.filter = next(self.filters) if key == glfw.KEY_F7 else self.filter
        if key in (glfw.KEY_F6, glfw.KEY_F7):
            texture = Texture(self.file, self.wrap, *self.filter)
            self.textures.update(diffuse_map=texture)

class Terrain(Textured):
    """ Procedural textured terrain """
    def __init__(self, shader, tex_file="Textures/grass.png", x=100, y=100, factor=1):
        self.heatMap = np.random.random((x, y))
        # prepare texture modes cycling variables for interactive toggling
        self.wraps = cycle([GL.GL_REPEAT, GL.GL_MIRRORED_REPEAT,
                            GL.GL_CLAMP_TO_BORDER, GL.GL_CLAMP_TO_EDGE])
        self.filters = cycle([(GL.GL_NEAREST, GL.GL_NEAREST),
                              (GL.GL_LINEAR, GL.GL_LINEAR),
                              (GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR)])
        self.wrap, self.filter = next(self.wraps), next(self.filters)
        self.file = tex_file

        # setup plane mesh to be textured
        base_coords = ()
        for i in range(x):
            for j in range(y):
                base_coords = base_coords+((i-x/2, j-y/2, self.heatMap[i][j]/2),) 
        scaled = factor * np.array(base_coords, np.float32)
        
        indices = ()
        for k in range(x, x*y):
            if(k+1<len(base_coords)):
                indices = indices+(k, k+1, k+1-x, k, k+1-x, k-x)
        indices = np.array(indices, np.uint32)
        mesh = Mesh(shader, attributes=dict(position=scaled), index=indices)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        texture = Texture(tex_file, self.wrap, *self.filter)
        super().__init__(mesh, diffuse_map=texture)
    
    def key_handler(self, key):
        # cycle through texture modes on keypress of F6 (wrap) or F7 (filtering)
        self.wrap = next(self.wraps) if key == glfw.KEY_F6 else self.wrap
        self.filter = next(self.filters) if key == glfw.KEY_F7 else self.filter
        if key in (glfw.KEY_F6, glfw.KEY_F7):
            texture = Texture(self.file, self.wrap, *self.filter)
            self.textures.update(diffuse_map=texture)

class TexturedPlane(Textured):
    """ Simple first textured object """
    def __init__(self, shader, tex_file):
        # prepare texture modes cycling variables for interactive toggling
        self.wraps = cycle([GL.GL_REPEAT, GL.GL_MIRRORED_REPEAT,
                            GL.GL_CLAMP_TO_BORDER, GL.GL_CLAMP_TO_EDGE])
        self.filters = cycle([(GL.GL_NEAREST, GL.GL_NEAREST),
                              (GL.GL_LINEAR, GL.GL_LINEAR),
                              (GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR)])
        self.wrap, self.filter = next(self.wraps), next(self.filters)
        self.file = tex_file

        # setup plane mesh to be textured
        base_coords = ((-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0))
        scaled = 100 * np.array(base_coords, np.float32)
        indices = np.array((0, 1, 2, 0, 2, 3), np.uint32)
        mesh = Mesh(shader, attributes=dict(position=scaled), index=indices)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        texture = Texture(tex_file, self.wrap, *self.filter)
        super().__init__(mesh, diffuse_map=texture)

    def key_handler(self, key):
        # cycle through texture modes on keypress of F6 (wrap) or F7 (filtering)
        self.wrap = next(self.wraps) if key == glfw.KEY_F6 else self.wrap
        self.filter = next(self.filters) if key == glfw.KEY_F7 else self.filter
        if key in (glfw.KEY_F6, glfw.KEY_F7):
            texture = Texture(self.file, self.wrap, *self.filter)
            self.textures.update(diffuse_map=texture)

class TexturedCylinder(Textured):
    """ Simple first textured object """
    def __init__(self, shader, tex_file="Textures/tronc.jpg", height=1, divisions=50, r=0.5, position=(0,0,0)):
        # prepare texture modes cycling variables for interactive toggling
        self.wraps = cycle([GL.GL_REPEAT, GL.GL_MIRRORED_REPEAT,
                            GL.GL_CLAMP_TO_BORDER, GL.GL_CLAMP_TO_EDGE])
        self.filters = cycle([(GL.GL_NEAREST, GL.GL_NEAREST),
                              (GL.GL_LINEAR, GL.GL_LINEAR),
                              (GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR)])
        self.wrap, self.filter = next(self.wraps), next(self.filters)
        self.file = tex_file
        
        self.height = height
        self.divisions = divisions
        self.ray = r

        # setup plane mesh to be textured
        vertices = ()
        vertices = vertices + ((0, 0, self.height/2),)
        for x in np.arange(0, 2*np.pi, 2*np.pi/self.divisions):
            vertices = vertices + ((self.ray*np.cos(x), self.ray*np.sin(x), self.height/2),)
        vertices = vertices + ((0, 0, -self.height/2),)
        for x in np.arange(0, 2*np.pi, 2*np.pi/self.divisions):
            vertices = vertices + ((self.ray*np.cos(x), self.ray*np.sin(x), -self.height/2),)
        scaled = np.array(vertices, np.float32)+np.array(position, np.float32)
        
        index = ()
        #top face
        for x in range(1, self.divisions, 1):
            index = index + (0,x,x+1)
        index = index + (0,self.divisions,1)
        #bottom face
        for x in range(1, self.divisions, 1):
            index = index + (self.divisions+1,self.divisions+x+2,self.divisions+x+1)
        index = index + (self.divisions+1, self.divisions+2,self.divisions*2+1)
        #side
        for x in range(1, self.divisions, 1):
            index = index + (x,self.divisions+x+1,x+1,x+1,self.divisions+x+1,self.divisions+x+2)
        index = index + (self.divisions,self.divisions*2+1,1,1,self.divisions*2+1,self.divisions+2)
        indices = np.array(index, np.uint32)
        mesh = Mesh(shader, attributes=dict(position=scaled), index=indices)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        texture = Texture(tex_file, self.wrap, *self.filter)
        super().__init__(mesh, diffuse_map=texture)

    def key_handler(self, key):
        # cycle through texture modes on keypress of F6 (wrap) or F7 (filtering)
        self.wrap = next(self.wraps) if key == glfw.KEY_F6 else self.wrap
        self.filter = next(self.filters) if key == glfw.KEY_F7 else self.filter
        if key in (glfw.KEY_F6, glfw.KEY_F7):
            texture = Texture(self.file, self.wrap, *self.filter)
            self.textures.update(diffuse_map=texture)