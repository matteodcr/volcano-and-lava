#version 330 core

// fragment position and normal of the fragment, in WORLD coordinates
in vec3 w_position, w_normal;
in vec3 normalized_pos;

uniform sampler2D diffuse_map;
in vec2 frag_tex_coords;

// light dir, in world coordinates
uniform vec3 light_dir;

// material properties
uniform vec3 k_a;
uniform float s;
// world camera position
uniform vec3 w_camera_position;
uniform vec3 skyColour;
const float density = 0.007;

out vec4 out_color;

void main() {
    // Compute all vectors, oriented outwards from the fragment
    vec3 n = normalize(w_normal);
    vec3 l = normalize(-light_dir);
    vec3 v = normalize(w_camera_position - w_position);
    vec3 r = reflect(-l, n);

    vec3 diffuse_color = texture(diffuse_map, frag_tex_coords).rgb * max(dot(n, l), 0);
    vec3 specular_color = texture(diffuse_map, frag_tex_coords).rgb * pow(max(dot(r, v), 0), s);

    float distance = distance(w_camera_position, normalized_pos);
    float visibility = (1/distance*density);
    visibility = clamp(visibility, 0.0,1.0);

    out_color = vec4(k_a, 1) + vec4(diffuse_color, 1)*1 + vec4(specular_color, 1);

    out_color = mix( out_color, vec4(skyColour,1), clamp((1 - ((75.0 - distance) / (75.0 - 50.0))), 0.0, 1.0));
    
}
