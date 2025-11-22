#version 120

varying vec3 vFragPos;
varying vec3 vColor;

const float transp = 0.4;

void main()
{
	gl_FragColor = vec4(vColor, transp);
}

