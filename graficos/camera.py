import math

import numpy as np

from animacao import suave


class Camera:
    def __init__(self):
        self.angulo=math.pi+0.23
        self.inclinacao=0.78
        self.distancia=19.3
        self.alvo_inclinacao=self.inclinacao
        self.alvo_distancia=self.distancia
        self.restante=0
        self.tempo_giro=0
        self.inicio_giro=self.angulo
        self.abertura=0
        self.foco=np.zeros(3)

    def girar_turno(self):
        self.restante=math.pi
        self.inicio_giro=self.angulo
        self.tempo_giro=0

    def atualizar(self,segundos):
        fator=1-math.exp(-12*segundos)
        self.inclinacao+=(self.alvo_inclinacao-self.inclinacao)*fator
        self.distancia+=(self.alvo_distancia-self.distancia)*fator
        if self.restante:
            self.tempo_giro+=segundos
            t=min(1,self.tempo_giro/0.65)
            self.angulo=(self.inicio_giro+math.pi*suave(t))%math.tau
            self.restante=math.pi*(1-t)

    def orbitar(self,dx,dy):
        if not self.restante:
            self.angulo+=dx*0.007
            self.alvo_inclinacao=max(0.18,min(1.44,self.alvo_inclinacao+dy*0.007))

    def zoom(self,passos):
        self.alvo_distancia=max(11,min(31,self.alvo_distancia-passos))

    def restaurar(self,turno=1):
        self.foco=np.zeros(3)
        self.angulo=(math.pi if turno==1 else 0)+0.23
        self.restante=0
        self.alvo_inclinacao=0.78
        self.alvo_distancia=19.3

    def guardar(self):
        return self.angulo,self.alvo_inclinacao,self.alvo_distancia,tuple(self.foco)

    def recuperar(self,estado):
        self.angulo,self.alvo_inclinacao,self.alvo_distancia=estado[:3]
        self.foco=np.array(estado[3] if len(estado)>3 else (0,0,0),dtype=float)
        self.restante=0

    def matrizes(self,aspecto,altura):
        distancia=self.distancia+6*self.abertura
        alvo=np.array([0,altura+2.5*self.abertura,0])+self.foco
        raio=distancia*math.cos(self.inclinacao)
        olho=alvo+[raio*math.sin(self.angulo),distancia*math.sin(self.inclinacao),
                   raio*math.cos(self.angulo)]
        frente=(alvo-olho)/distancia
        direita=np.cross(frente,[0,1,0])
        direita/=np.linalg.norm(direita)
        cima=np.cross(direita,frente)
        vista=np.eye(4)
        vista[:3,:3]=[direita,cima,-frente]
        vista[:3,3]=-vista[:3,:3]@olho
        f=1/math.tan(math.radians(45)/2)
        perto,longe=0.1,140
        projecao=np.array([[f/aspecto,0,0,0],[0,f,0,0],
                          [0,0,(longe+perto)/(perto-longe),2*longe*perto/(perto-longe)],
                          [0,0,-1,0]])
        return projecao,vista

    def ponto_no_plano(self,x,y,largura,altura,aspecto,plano):
        inversa=np.linalg.inv(np.matmul(*self.matrizes(aspecto,plano)))
        nx,ny=2*x/largura-1,1-2*y/altura
        perto=inversa@[nx,ny,-1,1]
        longe=inversa@[nx,ny,1,1]
        perto=perto[:3]/perto[3]
        direcao=longe[:3]/longe[3]-perto
        if abs(direcao[1])<1e-9:
            return None
        t=(plano-perto[1])/direcao[1]
        return perto+t*direcao if t>=0 else None
