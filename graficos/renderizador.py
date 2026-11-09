"""Buffers de vértices e shaders, conforme os exemplos das aulas 15–17."""
import ctypes

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

VERTEX = """
#version 330 core
layout(location=0) in vec3 posicao;
layout(location=1) in vec3 normal;
layout(location=2) in vec2 uv;
layout(location=3) in vec3 corVertice;
uniform mat4 modelo;
uniform mat4 vista;
uniform mat4 projecao;
out vec3 normalMundo;
out vec2 coordenada;
out vec3 corMalha;
void main() {
    gl_Position = projecao * vista * modelo * vec4(posicao, 1.0);
    normalMundo = mat3(modelo) * normal;
    coordenada = uv;
    corMalha = corVertice;
}
"""
FRAGMENT = """
#version 330 core
in vec3 normalMundo;
in vec2 coordenada;
in vec3 corMalha;
uniform vec3 cor;
uniform sampler2D imagem;
uniform int texturizado;
uniform int iluminado;
out vec4 fragmento;
void main() {
    vec4 base = vec4(cor * corMalha, 1.0);
    if (texturizado == 1) base *= texture(imagem, coordenada);
    if (iluminado == 1) {
        vec3 n = normalize(normalMundo);
        float luz = max(dot(n, normalize(vec3(-0.6, 0.9, -0.5))), 0.0);
        float apoio = max(dot(n, normalize(vec3(0.7, 0.3, 0.8))), 0.0);
        base.rgb *= vec3(0.55, 0.52, 0.50) + luz * vec3(0.51, 0.39, 0.27) + apoio * 0.12;
    }
    fragmento = base;
}
"""


class Renderizador:
    def __init__(self):
        self.programa = compileProgram(compileShader(VERTEX, GL_VERTEX_SHADER),
                                      compileShader(FRAGMENT, GL_FRAGMENT_SHADER))
        self.uniformes = {nome: glGetUniformLocation(self.programa, nome) for nome in
                          ("modelo", "vista", "projecao", "cor", "imagem", "texturizado", "iluminado")}
        self.recursos = []
        self.texturas = []

    def malha(self, malha):
        dados = np.asarray(malha.vertices, dtype=np.float32)
        vao, vbo = glGenVertexArrays(1), glGenBuffers(1)
        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, dados.nbytes, dados, GL_STATIC_DRAW)
        for local, tamanho, offset in ((0,3,0), (1,3,12), (2,2,24), (3,3,32)):
            glEnableVertexAttribArray(local)
            glVertexAttribPointer(local, tamanho, GL_FLOAT, GL_FALSE, 44, ctypes.c_void_p(offset))
        recurso = (vao, vbo, len(dados))
        self.recursos.append(recurso)
        return recurso

    def textura(self, imagem, mipmap=True):
        textura = glGenTextures(1)
        self.texturas.append(textura)
        self.atualizar_textura(textura, imagem, mipmap)
        return textura

    def substituir_malha(self, recurso, malha):
        dados = np.asarray(malha.vertices, dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, recurso[1])
        glBufferData(GL_ARRAY_BUFFER, dados.nbytes, dados, GL_DYNAMIC_DRAW)
        return recurso[0], recurso[1], len(dados)

    def atualizar_textura(self, textura, imagem, mipmap=False):
        glBindTexture(GL_TEXTURE_2D, textura)
        dados = imagem.convert("RGBA").transpose(1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, *dados.size, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, dados.tobytes())
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                        GL_LINEAR_MIPMAP_LINEAR if mipmap else GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        if mipmap:
            glGenerateMipmap(GL_TEXTURE_2D)

    def iniciar(self, projecao, vista):
        glUseProgram(self.programa)
        glUniformMatrix4fv(self.uniformes["projecao"], 1, GL_TRUE, np.asarray(projecao, dtype=np.float32))
        glUniformMatrix4fv(self.uniformes["vista"], 1, GL_TRUE, np.asarray(vista, dtype=np.float32))
        glUniform1i(self.uniformes["imagem"], 0)

    def desenhar(self, malha, modelo=None, cor=(1,1,1), textura=0, luz=True):
        modelo = np.eye(4) if modelo is None else modelo
        glUniformMatrix4fv(self.uniformes["modelo"], 1, GL_TRUE, np.asarray(modelo, dtype=np.float32))
        glUniform3f(self.uniformes["cor"], *cor)
        glUniform1i(self.uniformes["texturizado"], bool(textura))
        glUniform1i(self.uniformes["iluminado"], luz)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, textura)
        glBindVertexArray(malha[0])
        glDrawArrays(GL_TRIANGLES, 0, malha[2])

    def liberar(self):
        for vao, vbo, _ in self.recursos:
            glDeleteVertexArrays(1, [vao])
            glDeleteBuffers(1, [vbo])
        if self.texturas:
            glDeleteTextures(self.texturas)
        glDeleteProgram(self.programa)
