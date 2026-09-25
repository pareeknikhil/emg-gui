#version 330 core

uniform mat4 P;
in vec2 in_position;

void main() {
    gl_Position = P * vec4(in_position, 0.0, 1.0);
}