#version 120

attribute vec4 aPos;
attribute vec3 col;

uniform mat4 uMvpMatrix;
uniform mat4 uModelMatrix;

varying vec3 vFragPos;
varying vec3 vColor;

void main()
{
	gl_Position = uMvpMatrix * aPos;
	vFragPos = vec3(uModelMatrix * aPos);
	vColor = col;
}

