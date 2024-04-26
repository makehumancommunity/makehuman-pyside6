#version 330


layout (location = 0) in vec4 aPos;
layout (location = 1) in vec3 col;

uniform mat4 uMvpMatrix;
uniform mat4 uModelMatrix;

out VS_OUT {
    vec3 FragPos;
    vec3 Color;
} vs_out;

void main()
{
	gl_Position = uMvpMatrix * aPos;
	vs_out.FragPos = vec3(uModelMatrix * aPos);
	vs_out.Color = col;
}

