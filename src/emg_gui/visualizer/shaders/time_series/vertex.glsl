#version 330

in vec2 in_position;

uniform float u_channel_index;
uniform float u_channel_count;

void main() {
    float plot_height = 1.0 / u_channel_count;
    float channel_group_top = 1.0 - u_channel_index * plot_height * 2.0;
    float time_series_bottom = channel_group_top - plot_height;

    vec2 pos = in_position;
    pos.y = time_series_bottom + pos.y * plot_height;

    gl_Position = vec4(pos, 0.0, 1.0);
}