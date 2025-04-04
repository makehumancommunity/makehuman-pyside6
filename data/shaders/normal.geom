#version 330 core

// geometry shader for normal map needs to calculate the tangents and bitagents to get the correct
// normalmap depending to the point of view, shader is called once per triangle

layout (triangles) in;
layout (triangle_strip, max_vertices = 3) out;

in DATA {
	vec3 Normal;
	vec2 texCoord;
	// mat4 projection;
	mat3 model;
	vec3 lightPos[3];
	vec3 camPos;
} data_in[];

out vec3 Normal;
out vec2 texCoord;
out vec3 crntPos;
out vec3 lightPos[3];
out vec3 camPos;

// Default main function
void main()
{
	// calculate edges of triangle by using buildin gl_PerVertex-variable
	// and length of UV edges
	//
	vec3 e0 = gl_in[1].gl_Position.xyz - gl_in[0].gl_Position.xyz;
	vec3 e1 = gl_in[2].gl_Position.xyz - gl_in[0].gl_Position.xyz;
	vec2 dUV0 = data_in[1].texCoord - data_in[0].texCoord;
	vec2 dUV1 = data_in[2].texCoord - data_in[0].texCoord;

	// calculate inverse determinant
	float invDet = 1.0f / (dUV0.x * dUV1.y - dUV1.x * dUV0.y);

	vec3 tangent = vec3(invDet * (dUV1.y * e0 - dUV0.y * e1));
	vec3 bitangent = vec3(invDet * (-dUV1.x * e0 + dUV0.x * e1));

	vec3 T = normalize(data_in[0].model * tangent);
	vec3 B = normalize(data_in[0].model * bitangent);
	vec3 N = normalize(data_in[0].model * (cross(e1, e0)));
	mat3 TBN = mat3(T, B, N);
	// TBN is an orthogonal matrix and so its inverse is equal to its transpose
	TBN = transpose(TBN);

	// or also possible: vec3 B = cross(N, T)

	// create data and change all lighting variables to TBN space
	//
	// gl_Position = data_in[0].projection * gl_in[0].gl_Position;
	gl_Position =  gl_in[0].gl_Position;
	Normal = data_in[0].Normal;
	texCoord = data_in[0].texCoord;
	crntPos = TBN * gl_in[0].gl_Position.xyz;
	for (int i = 0; i < 3; i++) {
		lightPos[i] = TBN * data_in[0].lightPos[i];
	}
	camPos = TBN * data_in[0].camPos;
	EmitVertex();

	// gl_Position = data_in[1].projection * gl_in[1].gl_Position;
	gl_Position =  gl_in[1].gl_Position;
	Normal = data_in[1].Normal;
	texCoord = data_in[1].texCoord;
	crntPos = TBN * gl_in[1].gl_Position.xyz;
	for (int i = 0; i < 3; i++) {
		lightPos[i] = TBN * data_in[1].lightPos[i];
	}
	camPos = TBN * data_in[1].camPos;
	EmitVertex();

	// gl_Position = data_in[2].projection * gl_in[2].gl_Position;
	gl_Position =  gl_in[2].gl_Position;
	Normal = data_in[2].Normal;
	texCoord = data_in[2].texCoord;
	crntPos = TBN * gl_in[2].gl_Position.xyz;
	for (int i = 0; i < 3; i++) {
		lightPos[i] = TBN * data_in[2].lightPos[i];
	}
	camPos = TBN * data_in[2].camPos;
	EmitVertex();

	EndPrimitive();
}

