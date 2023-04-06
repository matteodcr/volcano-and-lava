# Python built-in modules
from bisect import bisect_left      # search sorted keyframe lists

# External, non built-in modules
import OpenGL.GL as GL              # standard Python OpenGL wrapper
import glfw                         # lean window system wrapper for OpenGL

from core import Node
from transform import (lerp, quaternion_slerp, quaternion_matrix, identity, translate, scale)


# -------------- Keyframing Utilities ------------------------------------
class KeyFrames:
    """ Stores keyframe pairs for any value type with interpolation_function"""
    def __init__(self, time_value_pairs, interpolation_function=lerp):
        if isinstance(time_value_pairs, dict):  # convert to list of pairs
            time_value_pairs = time_value_pairs.items()
        keyframes = sorted(((key[0], key[1]) for key in time_value_pairs))
        self.times, self.values = zip(*keyframes)  # pairs list -> 2 lists
        self.interpolate = interpolation_function

    def value(self, time):
        """ Computes interpolated value from keyframes, for a given time """

        # 1. ensure time is within bounds else return boundary keyframe
        time = max(min(time, self.times[-1]), self.times[0])

        # 2. search for closest index entry in self.times, using bisect_left
        closest_index = bisect_left(self.times, time)
        
        fraction = (time - self.times[closest_index-1])/(self.times[closest_index]-self.times[closest_index-1])

        # 3. using the retrieved index, interpolate between the two neighboring
        # values in self.values, using the stored self.interpolate function
        return self.interpolate(self.values[closest_index-1], self.values[closest_index], fraction)


class TransformKeyFrames:
    """ KeyFrames-like object dedicated to 3D transforms """
    def __init__(self, translate_keys, rotate_keys, scale_keys):
        """ stores 3 keyframe sets for translation, rotation, scale """
        self.translation = KeyFrames(translate_keys)
        self.rotation = KeyFrames(rotate_keys, quaternion_slerp)
        self.scale = KeyFrames(scale_keys)
        
        self.min_time = max(self.translation.times[0], max(self.scale.times[0], self.rotation.times[0]))
        self.max_time = min(self.translation.times[-1], min(self.scale.times[-1], self.rotation.times[-1]))

    def value(self, time):
        """ Compute each component's interpolation and compose TRS matrix """
        # 1. ensure time is within bounds else return boundary keyframe
        time = min(max(time, self.min_time), self.max_time)
        
        # 2. search for closest index entry in self.times, using bisect_left
        T = translate(self.translation.value(time))
        R = quaternion_matrix(self.rotation.value(time))    
        S = scale(self.scale.value(time))
        return T @ R @ S


class KeyFrameControlNode(Node):
    """ Place node with transform keys above a controlled subtree """
    def __init__(self, trans_keys, rot_keys, scale_keys, transform=identity(), repeat=False, animationShift=0):
        super().__init__(transform=transform)
        self.repeat = repeat
        self.animationShift = animationShift
        self.keyframes = TransformKeyFrames(trans_keys, rot_keys, scale_keys)

    def draw(self, primitives=GL.GL_TRIANGLES, **uniforms):
        """ When redraw requested, interpolate our node transform from keys """
        if self.repeat :
            self.transform = self.keyframes.value((glfw.get_time()+self.animationShift)%self.keyframes.max_time)
        else :
            self.transform = self.keyframes.value(glfw.get_time()+self.animationShift)
        super().draw(primitives=primitives, **uniforms)