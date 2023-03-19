#version 330 core

in vec2 frag_tex_coord;
in vec3 normalized_pos;
in float visibility;

uniform sampler2D diffuse_map;
uniform vec3 skyColour;
uniform vec3 w_camera_position;

out vec4 out_color;

// For eventual non linear smog
// const float gradient = 1.5;

const float density = 0.007;

void main() {
    float distance = distance(w_camera_position, normalized_pos);
    float visibility = (1/distance*density);
    visibility = clamp(visibility, 0.0,1.0);

    out_color = texture(diffuse_map, frag_tex_coord);

    out_color = mix( out_color, vec4(skyColour,1), clamp((1 - ((75.0 - distance) / (75.0 - 50.0))), 0.0, 1.0));

}
