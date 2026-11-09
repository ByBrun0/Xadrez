"""Entrada do jogo. Recursos gráficos têm o mesmo ciclo de vida da janela."""
from time import perf_counter

import glfw
from OpenGL.GL import *

from graficos.camera import Camera
from graficos.cena import Cena
from interface import Interface


def criar_janela(visivel=True):
    if not glfw.init():
        raise RuntimeError("Não foi possível iniciar o GLFW.")
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR,3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR,3)
    glfw.window_hint(glfw.OPENGL_PROFILE,glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.VISIBLE,visivel)
    janela=glfw.create_window(1100,800,"Praça dos Dois Jogos",None,None)
    if not janela:
        glfw.terminate()
        raise RuntimeError("Não foi possível abrir uma janela OpenGL 3.3, usado nas aulas 15–17.")
    glfw.make_context_current(janela)
    glfw.set_window_size_limits(janela,800,600,glfw.DONT_CARE,glfw.DONT_CARE)
    return janela


def main():
    janela=criar_janela()
    cena=None
    try:
        glfw.swap_interval(1)
        cena=Cena()
        interface=Interface(janela,Camera())
        anterior=perf_counter()
        inicio_medicao=anterior
        soma=quadros=0
        while not glfw.window_should_close(janela):
            agora=perf_counter()
            dt=min(agora-anterior,0.1)
            anterior=agora
            interface.atualizar(dt)
            largura,altura=glfw.get_framebuffer_size(janela)
            if largura and altura:
                inicio=perf_counter()
                cena.desenhar(largura,altura,interface,agora)
                soma+=perf_counter()-inicio
                quadros+=1
                if agora-inicio_medicao>=2:
                    interface.metricas=f"{quadros/(agora-inicio_medicao):.0f} FPS  ·  CPU desenho {soma*1000/quadros:.1f} ms"
                    inicio_medicao=agora
                    soma=quadros=0
                glfw.swap_buffers(janela)
                glfw.poll_events()
            else:
                glfw.wait_events_timeout(0.1)
    finally:
        if cena:
            cena.liberar()
        glfw.terminate()


if __name__=="__main__":
    main()
