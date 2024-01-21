#version 330

out vec4 FragColor;

in VS_OUT {
    vec3 FragPos;
    vec3 Normal;
    vec2 TexCoords;
} fs_in;

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

void main()
{
	vec3 color = texture(Texture, fs_in.TexCoords).rgb;
	// ambient
	vec3 ambient = ambientLight[3] * color * vec3(ambientLight);

	// diffuse
	vec3 normal = fs_in.Normal; // normalize(fs_in.Normal);
	vec3 lightDir1 = normalize(lightPos1 - fs_in.FragPos);
	vec3 lightDir2 = normalize(lightPos2 - fs_in.FragPos);
	vec3 lightDir3 = normalize(lightPos3 - fs_in.FragPos);
	float l1 = length(lightPos1 - fs_in.FragPos) / lightVol1.a;
	float l2 = length(lightPos2 - fs_in.FragPos) / lightVol2.a;
	float l3 = length(lightPos3 - fs_in.FragPos) / lightVol3.a;
	float diff1 = max(dot(lightDir1, normal), 0.0) /l1;
	float diff2 = max(dot(lightDir2, normal), 0.0) /l2;
	float diff3 = max(dot(lightDir3, normal), 0.0) /l3;
	vec3 diffuse = diff1 * vec3(lightVol1) * color + diff2 * vec3(lightVol2) * color  + diff3 * vec3(lightVol3) *  color;

	// specular
	vec3 viewDir = normalize(viewPos - fs_in.FragPos);
	vec3 specw = vec3(lightWeight[0]);
	float spec1 = 0.0;
	float spec2 = 0.0;
	float spec3 = 0.0;
	if(blinn) {
		vec3 halfwayDir = normalize(lightDir1 + viewDir);  
		spec1 = pow(max(dot(normal, halfwayDir), 0.0), lightWeight[1]) / l1;
		halfwayDir = normalize(lightDir2 + viewDir);  
		spec2 = pow(max(dot(normal, halfwayDir), 0.0), lightWeight[1]) / l2;
		halfwayDir = normalize(lightDir3 + viewDir);
		spec3 = pow(max(dot(normal, halfwayDir), 0.0), lightWeight[1]) / l3;
	} else {
		vec3 reflectDir = reflect(-lightDir1, normal);
		spec1 = pow(max(dot(viewDir, reflectDir), 0.0), lightWeight[1]) / l1;
		reflectDir = reflect(-lightDir2, normal);
		spec2 = pow(max(dot(viewDir, reflectDir), 0.0), lightWeight[1]) / l2;
		reflectDir = reflect(-lightDir3, normal);
		spec3 = pow(max(dot(viewDir, reflectDir), 0.0), lightWeight[1]) / l3;
	}
	vec3 specular = specw * vec3(lightVol1) * spec1 + specw * vec3(lightVol2) * spec2 + specw * vec3(lightVol3) * spec3;
	FragColor = vec4(ambient + diffuse + specular, 1.0);
}

