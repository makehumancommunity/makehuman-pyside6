#version 330

struct PointLight {
    vec3 position;
    vec3 color;
    float intensity;
};

out vec4 FragColor;

in VS_OUT {
    vec3 FragPos;
    vec3 Normal;
    vec2 TexCoords;
} fs_in;

uniform sampler2D Texture;
uniform PointLight pointLights[3];

uniform vec3 lightWeight;
uniform vec4 ambientLight;
uniform vec3 viewPos;
uniform bool blinn;

void main()
{
	vec3 color = texture(Texture, fs_in.TexCoords).rgb;
	float transp = texture(Texture, fs_in.TexCoords).a;
	if (transp < 0.01) discard;

	// ambient
	vec3 ambient = ambientLight[3] * color * vec3(ambientLight);

	// diffuse
	vec3 normal = fs_in.Normal; // normalize(fs_in.Normal);
        vec3 diffuse = vec3(0.0, 0.0, 0.0);
        vec3 specular = vec3(0.0, 0.0, 0.0);
	vec3 viewDir = normalize(viewPos - fs_in.FragPos);
        vec3 specw = vec3(lightWeight[0]);

        for (int i = 0; i < 3; i++) {
                // diffuse
                vec3 position = pointLights[i].position;
                vec3 lightDir = normalize(position - fs_in.FragPos);
                float l = length(position - fs_in.FragPos) / pointLights[i].intensity;
                float diff = max(dot(lightDir, normal), 0.0) /l;
                diffuse += diff * pointLights[i].color * color;

                // specular
                float spec = 0.0;
                if(blinn) {
                        vec3 halfwayDir = normalize(lightDir + viewDir);
                        spec = pow(max(dot(normal, halfwayDir), 0.0), lightWeight[1]) / l;
                } else {
                        vec3 reflectDir = reflect(-lightDir, normal);
                        spec = pow(max(dot(viewDir, reflectDir), 0.0), lightWeight[1]) / l;
                }
                specular += specw * pointLights[i].color * spec;
        }

	FragColor = vec4(ambient + diffuse + specular, transp);
}

