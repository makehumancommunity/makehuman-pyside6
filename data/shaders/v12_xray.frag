#version 120

varying vec3 vFragPos;
varying vec3 vNormal;
varying vec2 vTexCoords;

uniform sampler2D Texture;
uniform vec3 lightPos1;
uniform vec3 lightPos2;
uniform vec3 lightPos3;
uniform vec3 lightWeight;
uniform vec4 ambientLight;
uniform vec4 lightVol1;
uniform vec4 lightVol2;
uniform vec4 lightVol3;
uniform vec3 viewPos;
uniform bool blinn;

// globals
// Falloff value (between 0 and 4)
uniform float edgefalloff = 1.0;
// Intensity value (between 0 and 4)
uniform float intensity = 0.7;
uniform vec3 ambient = vec3(0.1, 0.1, 0.1);
uniform vec3 diffuse = vec3(1.0, 1.0, 1.0);

void main()
{
	float opac = dot(normalize(-vNormal), normalize(-vFragPos));
	float ambientf = (ambient.r + ambient.g + ambient.b) / 3.0;
	opac = ambientf + intensity*(1.0-pow(abs(opac), edgefalloff));

	gl_FragColor.rgb = opac * diffuse;
	gl_FragColor.a = opac;
}

