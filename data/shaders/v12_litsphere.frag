#version 120

varying vec3 vFragPos;
varying vec3 vNormal;
varying vec2 vTexCoords;

uniform sampler2D Texture;
uniform sampler2D litsphereTexture;
uniform float AdditiveShading = 0.0;

void main()
{
	vec3 color = texture2D(Texture, vTexCoords).rgb;
	float transp = texture2D(Texture, vTexCoords).a;
	if (transp < 0.01) discard;

	// use shading values from litsphere
	vec3 normal = vNormal;
	vec3 shading = texture2D(litsphereTexture, vec2(normal * vec3(0.495) + vec3(0.5))).rgb;

	vec3 outColor = (1.0 - AdditiveShading) * shading * color.rgb * vec3(2.0 - (shading.r + shading.g + shading.b) / 3.0);
	outColor += AdditiveShading * (shading + color.rgb);

	gl_FragColor = vec4(outColor, transp);
}

