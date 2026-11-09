from .malhas import Malha, revolucao, caixa, translacao, rotacao


def criar_modelos(segmentos):
    perfil = ((0,0), (0.30,0), (0.35,0.035), (0.365,0.08),
              (0.36,0.14), (0.33,0.19), (0.27,0.20), (0.25,0.175),
              (0.17,0.175), (0.15,0.20), (0,0.20))
    disco = revolucao(perfil,segmentos)
    aneis = revolucao(((0.36,0.065),(0.365,0.08),(0.36,0.10)),segmentos)
    dama = Malha().juntar(disco).juntar(disco,translacao(0,0.20,0))
    coroa = Malha().juntar(aneis).juntar(aneis,translacao(0,0.20,0))
    for angulo in (0,60,120):
        coroa.juntar(caixa(0.23,0.018,0.045),translacao(0,0.405,0) @ rotacao(angulo))
    return {"P": (disco,aneis,Malha()), "D": (dama,coroa,Malha())}
