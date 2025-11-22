#version 120

attribute vec4 aPos;
attribute vec4 aNormal;
attribute vec2 aTexCoords;

uniform mat4 uMvpMatrix;
uniform mat4 uModelMatrix;
uniform mat4 uNormalMatrix;

varying vec3 vFragPos;
varying vec3 vNormal;
varying vec2 vTexCoords;

void main()
{
	vFragPos = vec3(uModelMatrix * aPos);
	vNormal = normalize(vec3(uNormalMatrix * aNormal));
	vTexCoords = aTexCoords;
	gl_Position = uMvpMatrix * aPos;
}

