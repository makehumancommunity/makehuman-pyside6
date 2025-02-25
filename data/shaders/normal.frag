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
in vec3 lightPos[3];
// Gets the position of the camera from the main function
in vec3 camPos;



struct PointLight {
    vec3 position;
    vec3 color;
    float intensity;
    int type;
};


uniform sampler2D Texture;
uniform sampler2D MRTexture;
uniform sampler2D NOTexture;
uniform sampler2D AOTexture;

// Gets the color of the light from the main function (change this to point lights later)


uniform float AOMult;
uniform vec4 ambientLight;

uniform PointLight pointLights[3];


void main()
{
	vec4 basecolor = texture(Texture, texCoord);
        float transp = basecolor.a;
        if (transp < 0.01) discard;
        vec3 color = basecolor.rgb;


        float ao = texture(AOTexture, texCoord).r;
	vec3 no = normalize(texture(NOTexture, texCoord).xyz * 2.0f - 1.0f);
	// vec3 no = normalize(Normal);
	vec3 diffuse = vec3(0.0, 0.0, 0.0);
	vec3 specular = vec3(0.0, 0.0, 0.0);
	vec3 viewDir = normalize(camPos - crntPos);
	vec3 specw = vec3(0.5, 0.5, 0.5);

	for (int i = 0; i < 3; i++) {
                if (pointLights[i].intensity > 0.01) {
			// diffuse
			vec3 position = lightPos[i];
                        vec3 L = vec3(0.0);
                        float diff = 0.0;
			vec3 lightVec = position - crntPos;
			float l = length(lightVec) / pointLights[0].intensity;
                        if (pointLights[i].type == 0) {
                                L = normalize(lightVec);
                                diff = max(dot(L, no), 0.0) /l;
                        } else {
                                L = normalize(position);
                                diff = clamp(dot(L, no), 0.0, 1.0) / 2.0;
                        }
                        diffuse += diff * pointLights[i].color * color;

                        // specular
                        vec3 reflectDir = reflect(-L, no);
                        float spec = pow(max(dot(viewDir, reflectDir), 0.0), 8) / l;

                        specular += specw * pointLights[i].color * spec;
		}
        }


	vec3 ambient = ambientLight[3] * color * vec3(ambientLight) * ao * AOMult;
        color = ambient + diffuse + specular * texture(MRTexture, texCoord).r;
        FragColor = vec4(clamp(color, 0.0, 1.0), transp);
}
