"""
Servidor-ponte entre ROS 2 e Godot.
- Recebe pose + estado do robô (do no_ponte) e expõe para o Godot.
- Recebe comandos de controle.

ATENÇÃO — ORDEM DO PENTEST (Semana 6), NÃO INVERTER:
  1. Rodar pentest/exploit.py contra ESTE arquivo ANTES de aplicar a correção
     (comente/remova temporariamente o Depends(verificar_token) abaixo, ou
     rode contra uma cópia sem autenticação) e capturar vídeo/log do 200 OK.
  2. Preencher pentest/relatorio_template.md com o vetor CVSS.
  3. SÓ ENTÃO usar esta versão com JWT ativo (como está agora) e reter testar
     exploit.py — ele deve falhar com 401.
Se a evidência do ataque (passo 1) ainda não foi capturada, NÃO distribua esta
versão corrigida antes disso — não sobra ataque pra mostrar no relatório.

AUTENTICAÇÃO: JWT (HS256) implementado com a biblioteca padrão do Python
(hmac/hashlib/base64) — sem depender de instalar pyjwt. Chave fixa só para
fins de demonstração do projeto; NÃO é prática de produção.
"""

import base64
import hashlib
import hmac
import json
import os
import time

from collections import deque

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Ponte Héstia")

# estado em memória (o Godot lê daqui)
_estado = {"pose": {"x": 0.0, "y": 0.0, "theta": 0.0}, "atividade": "ocioso"}

# --------------------------------------------------------------------
# Autenticação por token (JWT HS256, implementado sem lib externa)
# --------------------------------------------------------------------
# Chave do JWT: lida da variável de ambiente HESTIA_SECRET_KEY. O fallback
# existe só para não travar a demo caso a variável não esteja setada — NÃO é
# prática de produção (em produção a ausência da variável deveria ser erro).
SECRET_KEY = os.environ.get("HESTIA_SECRET_KEY", "demo-inseguro-troque-em-producao")
ALGORITMO = "HS256"

# Credenciais do operador para emitir token (/token). Antes, /token emitia
# credencial para QUALQUER UM sem autenticação — logo a correção do /comando era
# contornável (o atacante só pedia um token primeiro). Agora /token exige
# usuário+senha. Valores via ambiente; defaults só para a demo.
OPERADOR_USUARIO = os.environ.get("HESTIA_USUARIO", "operador")
OPERADOR_SENHA = os.environ.get("HESTIA_SENHA", "hestia2026")


def _b64url(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).rstrip(b"=").decode()


def _b64url_decode(texto: str) -> bytes:
    padding = "=" * (-len(texto) % 4)
    return base64.urlsafe_b64decode(texto + padding)


def _assinar(header_b64: str, payload_b64: str) -> str:
    mensagem = f"{header_b64}.{payload_b64}".encode()
    assinatura = hmac.new(SECRET_KEY.encode(), mensagem, hashlib.sha256).digest()
    return _b64url(assinatura)


def criar_token(sub: str, validade_s: int = 3600) -> str:
    """Gera um JWT HS256 válido por `validade_s` segundos."""
    header = {"alg": ALGORITMO, "typ": "JWT"}
    payload = {"sub": sub, "exp": int(time.time()) + validade_s}
    h = _b64url(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    s = _assinar(h, p)
    return f"{h}.{p}.{s}"


def verificar_token(authorization: str = Header(None)) -> dict:
    """Dependência do FastAPI: valida assinatura e expiração do JWT no header
    `Authorization: Bearer <token>`. Levanta 401 em qualquer falha."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="token ausente")
    token = authorization[len("Bearer "):]
    try:
        h, p, s = token.split(".")
    except ValueError:
        raise HTTPException(status_code=401, detail="token malformado")
    esperado = _assinar(h, p)
    if not hmac.compare_digest(esperado, s):
        raise HTTPException(status_code=401, detail="assinatura inválida")
    try:
        payload = json.loads(_b64url_decode(p))
    except Exception:
        raise HTTPException(status_code=401, detail="payload inválido")
    if payload.get("exp", 0) < time.time():
        raise HTTPException(status_code=401, detail="token expirado")
    return payload


class Credencial(BaseModel):
    usuario: str
    senha: str


@app.post("/token")
def emitir_token(cred: Credencial):
    """Emite um token APENAS para quem apresenta usuário+senha válidos.
    Fecha a brecha de a correção do /comando ser contornável (pedir token sem
    autenticação). Usa comparação em tempo constante contra timing attack."""
    usuario_ok = hmac.compare_digest(cred.usuario, OPERADOR_USUARIO)
    senha_ok = hmac.compare_digest(cred.senha, OPERADOR_SENHA)
    if not (usuario_ok and senha_ok):
        raise HTTPException(status_code=401, detail="credenciais inválidas")
    return {"access_token": criar_token(sub=cred.usuario), "token_type": "bearer"}


class Comando(BaseModel):
    """Validação de schema (Pydantic) — a outra correção da Semana 6."""
    tipo: str          # "ir_para", "atender", ...
    x: float
    y: float


@app.get("/status")
def get_status():
    """O Godot consulta este endpoint para atualizar a cena 3D."""
    return _estado


@app.post("/pose")
def post_pose(x: float, y: float, theta: float):
    """O no_ponte (ROS) atualiza a pose aqui."""
    _estado["pose"] = {"x": x, "y": y, "theta": theta}
    return {"ok": True}


@app.post("/atividade")
def post_atividade(texto: str):
    """Telemetria: o no_ponte informa a atividade atual do robô (ronda,
    "atendendo queda", ...). Sem auth — é reporte de estado, não controle
    (diferente de /comando, que é o vetor do pentest e exige JWT). O Godot lê
    isto em /status e acende o realce de emergência."""
    _estado["atividade"] = texto
    return {"ok": True}


# --------------------------------------------------------------------
# Endpoint de controle: agora exige JWT válido (Depends(verificar_token)).
# Era o vetor do pentest (Broken Authentication) — ver nota no topo do
# arquivo sobre a ordem correta de captura da evidência antes da correção.
# --------------------------------------------------------------------
@app.post("/comando")
def post_comando(cmd: Comando, _payload: dict = Depends(verificar_token)):
    _estado["atividade"] = f"executando {cmd.tipo}"
    return {"ok": True, "recebido": cmd.model_dump()}


# --------------------------------------------------------------------
# Pedidos vindos da INTERFACE (Godot): o operador clica "água"/"queda" e a UI
# faz POST /pedido aqui. Um nó ROS (no_ponte) drena GET /pedidos e republica no
# tópico /chamados, onde o gerenciador_chamados aplica prioridade/preempção.
# /pedido exige JWT (mesma credencial do /comando) — a UI autentica em /token.
# --------------------------------------------------------------------
_pedidos: deque = deque(maxlen=50)


class Pedido(BaseModel):
    tipo: str                 # "agua", "queda", ...
    prioridade: str           # "PEDIDO_COMUM" | "EMERGENCIA" | "PATRULHA"
    x: float
    y: float


@app.post("/pedido")
def post_pedido(pedido: Pedido, _payload: dict = Depends(verificar_token)):
    """A interface enfileira um chamado (autenticada). Não publica no ROS
    diretamente (a ponte não fala ROS): só guarda; o no_ponte drena e publica."""
    _pedidos.append(pedido.model_dump())
    return {"ok": True, "na_fila": len(_pedidos)}


@app.get("/pedidos")
def get_pedidos():
    """Drenado pelo no_ponte (ROS): retorna e ESVAZIA a fila de pedidos."""
    itens = list(_pedidos)
    _pedidos.clear()
    return {"pedidos": itens}


# Câmera "pelos olhos do robô": resolvida NO GODOT como painel picture-in-picture
# (SubViewport espelhando a câmera do robô) — ver interface_godot/README.md. Não
# há endpoint /stream aqui: a visão não trafega pela rede. Um /stream HTTP (MJPEG
# da câmera real do Gazebo via no_ponte) fica como evolução futura, fora do escopo.
