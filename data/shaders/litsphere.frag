#version 330

out vec4 FragColor;

in VS_OUT {
    vec3 FragPos;
    vec3 Normal;
    vec2 TexCoords;
} fs_in;

uniform sampler2D Texture;
uniform sampler2D litsphereTexture;
uniform float AdditiveShading = 0.0;

void main()
{
	vec3 color = texture(Texture, fs_in.TexCoords).rgb;
	float transp = texture(Texture, fs_in.TexCoords).a;
	// ambient
	// vec3 ambient = ambientLight[3] * color * vec3(ambientLight);

	// use shading values from litsphere
	vec3 normal = fs_in.Normal; // normalize(fs_in.Normal);
	vec3 shading = texture2D(litsphereTexture, vec2(normal * vec3(0.495) + vec3(0.5))).rgb;

	vec3 outColor;
	outColor = (1.0 - AdditiveShading)*shading * color.rgb * vec3(2.0 - (shading.r + shading.g + shading.b)/3.0);
        outColor += AdditiveShading*(shading + color.rgb);

	if (transp < 0.01) discard;
	FragColor = vec4(outColor, transp);
}

