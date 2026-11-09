# Como rodar o Héstia de ponta a ponta

Este guia parte do princípio que o ambiente **já foi montado** (se não foi,
veja primeiro `INSTALL_WSL2.md` + `SETUP.md`). Aqui é só: **o que digitar, em
qual terminal, em qual ordem**, para o sistema inteiro ficar de pé.

> Os launch files já resolvem o caminho internamente — pode rodar com
> `ros2 launch hestia_robot ...` (se já fez `colcon build`) OU direto pelo
> caminho completo do arquivo (como nos comentários de cada `.launch.py`).

---

## ⭐ Caminho recomendado para a demo (casa do Blender, 1 comando)

As seções 1–6 abaixo descrevem o fluxo manual (casa do TurtleBot3, bom como
fallback). Para a **casa do Blender** (fluxo atual), use os scripts da raiz —
eles sobem tudo na ordem certa:

```bash
# pré-requisito (uma vez): laser 16 m + build do workspace
cd /mnt/c/Users/Usuario/Documents/hestia
bash ros2_ws/src/hestia_robot/scripts/ajustar_laser_16m.sh
cd ros2_ws && colcon build --symlink-install && source install/setup.bash && cd ..

export TURTLEBOT3_MODEL=burger

# A) com AMCL (localização "de verdade") + RViz:
bash iniciar_hestia_blender.sh

# B) PLANO B — se o AMCL divergir, localização cravada de simulação + RViz:
bash iniciar_hestia_blender_simples.sh
```

Depois abra o Godot no Windows (`godot --path interface_godot`). Dispare os
chamados para mostrar a **preempção**:

```bash
bash ros2_ws/src/hestia_robot/scripts/publica_chamado.sh agua  PEDIDO_COMUM  5.0 -1.9
bash ros2_ws/src/hestia_robot/scripts/publica_chamado.sh queda EMERGENCIA  -7.9 11.45
```

Derrubar tudo: `bash parar_hestia.sh`. Ambos os launches abrem o **RViz** por
padrão (nuvem de partículas/custo/caminho); para rodar sem RViz, acrescente
`rviz:=false` ao `ros2 launch`.

> **Plano A vs B:** o A usa AMCL (casa o laser com o mapa — é a localização
> "robótica de verdade", melhor de explicar na prova, mas ainda pode divergir em
> áreas abertas desta casa). O B troca o AMCL por uma TF estática `map->odom` +
> odometria do Gazebo (localização perfeita de simulação) — garante a demo
> rodando lisa; honestamente, não é localização "real", então prefira o A se ele
> estiver convergindo.

---

## 0. Checklist antes de começar (uma vez por sessão/dia)

```bash
# em QUALQUER terminal novo, confirme que o ROS está carregado:
echo $ROS_DISTRO        # tem que imprimir "humble"
echo $TURTLEBOT3_MODEL  # tem que imprimir "burger" (ou o que a sala usa)

# se build do workspace ainda não foi feito (ou mudou algo em hestia_robot/):
cd ~/hestia/ros2_ws        # ajuste o caminho se for outro
colcon build --symlink-install
source install/setup.bash
```

Rode `bash verifica_ambiente.sh` se tiver dúvida sobre o ambiente em si.

---

## 1. Robótica — Gazebo + AMCL + Nav2 (1 terminal, fica aberto)

```bash
ros2 launch hestia_robot localizacao.launch.py
```

Isso abre o Gazebo (casa) + Nav2 com AMCL sobre o mapa salvo (`maps/casa.yaml`)
+ RViz2. **Passo manual obrigatório no RViz**, uma vez por execução:

1. Clique **"2D Pose Estimate"** e desenhe a seta onde o robô está no mapa
   (o AMCL precisa de um palpite inicial).
2. Espere a nuvem de partículas convergir ao redor do robô.

Sem isso, o Nav2 não sabe onde o robô está e as metas do passo 2 vão falhar.

---

## 2. Gerenciador de chamados — fila + preempção (2º terminal, fica aberto)

```bash
ros2 run hestia_robot gerenciador_chamados
```

Com Nav2 de pé (passo 1) e a pose inicial já dada, o robô deve começar a
**rondar** sozinho pelos waypoints (log `-> Nav2: ronda rumo a (...)`).

### Testar a preempção (o ponto que o professor cobra)

Em um 3º terminal, dispare chamados com o script já pronto:

```bash
# pedido comum — o robô vai, mas pode ser interrompido
bash ros2_ws/src/hestia_robot/scripts/publica_chamado.sh agua PEDIDO_COMUM 3.0 -1.0

# emergência — enquanto o anterior ainda está em curso, publique este:
bash ros2_ws/src/hestia_robot/scripts/publica_chamado.sh queda EMERGENCIA -4.5 2.0
```

No terminal do `gerenciador_chamados` deve aparecer `PREEMPCAO: queda[...]
interrompe agua[...] — cancelando meta Nav2` e o robô muda de destino na hora.
**Isso é a evidência que vale pro vídeo final.**

---

## 3. Ponte — servidor FastAPI (4º terminal, fica aberto)

```bash
cd ponte
pip install -r requirements.txt     # só na primeira vez
uvicorn servidor:app --host 0.0.0.0 --port 8000 --reload
```

Confirme que subiu:
```bash
curl localhost:8000/status
# -> {"pose":{"x":0.0,"y":0.0,"theta":0.0},"atividade":"ocioso"}
```

---

## 4. Ponte ROS→FastAPI — `no_ponte` (5º terminal, fica aberto)

```bash
ros2 run hestia_robot no_ponte
```

Com os passos 1 e 3 já de pé, confira que a pose real do robô chega na ponte:

```bash
curl localhost:8000/status
# -> o x/y/theta deve mudar conforme o robô se move no Gazebo
```

Se continuar `0.0,0.0,0.0` fixo: confirme que o AMCL está publicando em
`/amcl_pose` (`ros2 topic hz /amcl_pose`) e que a pose inicial do passo 1 foi
dada no RViz.

---

## 5. Interface Godot

O projeto Godot já existe em `interface_godot/` (Godot 4.7). A casa vem do
`casa.glb` (exportado do Blender) e o robô é um nó movido pela pose da ponte.

```powershell
# no Windows (precisa da ponte do passo 3 no ar):
godot --path interface_godot        # roda a cena
godot --path interface_godot -e     # abre no editor
```

Ele consome `GET http://127.0.0.1:8000/status` em polling e move o robô. Os
parâmetros de alinhamento pose-ROS -> casa (escala, offset, inverter_z,
offset_theta) estão no inspector do nó **Robo**. O shader autoral do robô
(`shaders/robo.gdshader`) pulsa em vermelho quando a atividade indica emergência.
Ver `AMBIENTE_PRONTO.md` para o passo a passo completo nesta máquina.

---

## 6. Pentest (fazer isolado, não durante a demo)

Ver `pentest/README.md` e `pentest/relatorio_template.md` para a ordem exata
(ataque sem token → evidência → correção → reteste). Resumo dos comandos:

```bash
nmap -sV -p 8000 localhost                 # 1. recon

cd pentest
python exploit.py                          # 2. ataque sem token -> esperado 200 (ANTES de usar o servidor.py com JWT)

# 3. troque para o servidor.py com JWT (reinicie o uvicorn do passo 3 acima)

python exploit.py                          # 4. reteste sem token -> esperado 401
curl -X POST localhost:8000/token          #    pega um token válido
python exploit.py --token <TOKEN_OBTIDO>   #    reteste com token -> esperado 200
```

---

## Ordem resumida para o dia da demo (6 terminais)

| # | Terminal | Comando | Fica aberto? |
|---|----------|---------|---------------|
| 1 | Robótica | `ros2 launch hestia_robot localizacao.launch.py` + pose inicial no RViz | sim |
| 2 | Chamados | `ros2 run hestia_robot gerenciador_chamados` | sim |
| 3 | Ponte | `uvicorn servidor:app --host 0.0.0.0 --port 8000` (dentro de `ponte/`) | sim |
| 4 | Ponte-ROS | `ros2 run hestia_robot no_ponte` | sim |
| 5 | Godot | abrir o projeto e dar play (quando existir) | sim |
| 6 | Testes | `publica_chamado.sh` para disparar chamados / `curl` para checar `/status` | usa e fecha |

**Dica:** suba na ordem 1 → 2 → 3 → 4 com uma pausa curta entre cada um
(espera o anterior terminar de inicializar). Subir tudo junto de uma vez é a
causa mais comum de "Nav2 indisponível" ou erro de conexão na ponte.
