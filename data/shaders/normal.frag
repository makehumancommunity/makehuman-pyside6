#version 330 core

// Outputs colors in RGBA
out vec4 FragColor;

// Imports the current position from the Vertex Shader
in vec3 crntPos;
// Imports the normal from the Vertex Shader
in vec3 Normal;
// Imports the texture coordinates from the Vertex Shader
in vec2 texCoord;
// Gets the position of the light from the main function
in vec3 lightPos;
// Gets the position of the camera from the main function
in vec3 camPos;


// Gets the Texture Units from the main function

uniform sampler2D Texture;
uniform sampler2D MRTexture;
uniform sampler2D NOTexture;

// Gets the color of the light from the main function (change this to point lights later)
uniform vec4 ambientLight;

const vec4 extraLight = vec4(1.0, 1.0, 1.0, 1.0);

void main()
{
	vec4 basecolor = texture(Texture, texCoord);
        float transp = basecolor.a;
        if (transp < 0.01) discard;
        vec3 color = basecolor.rgb;

	// used in two variables so I calculate it here to not have to do it twice
	vec3 lightVec = lightPos - crntPos;

	// intensity of light with respect to distance
	float dist = length(lightVec);
	float a = 1.00f;
	float b = 0.70f;
	// float inten = 1.0f / (a * dist * dist + b * dist + 1.0f);
	float inten = 0.5;

	// diffuse lighting
	// Normals are mapped from the range [0, 1] to the range [-1, 1]
	vec3 normal = normalize(texture(NOTexture, texCoord).xyz * 2.0f - 1.0f);
	vec3 lightDirection = normalize(lightVec);
	float diffuse = max(dot(normal, lightDirection), 0.0f);

	// specular lighting
	float specular = 0.0f;
	if (diffuse != 0.0f)
	{
		float specularLight = 0.50f;
		vec3 viewDirection = normalize(camPos - crntPos);
		vec3 halfwayVec = normalize(viewDirection + lightDirection);
		float specAmount = pow(max(dot(normal, halfwayVec), 0.0f), 16);
		specular = specAmount * specularLight;
	};

	vec3 ambient = ambientLight[3] * color * vec3(ambientLight);
	vec3 outcolor = (color * (diffuse * inten) + texture(MRTexture, texCoord).r * specular * inten) * vec3(extraLight);
        color = ambient + outcolor;
        FragColor = vec4(clamp(color, 0.0, 1.0), transp);
}
