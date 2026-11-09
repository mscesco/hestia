# Handoff — Casa do Blender integrada ao ROS (para a Camila)

> Escrito para a Camila continuar a robótica. Feito na máquina do Leandro
> (WSL2 + ROS 2 Humble). Data: 2026-11-09.

## O que mudou (resumo)

O problema que a gente tinha: o robô navegava na **casa do TurtleBot3**, mas o
Godot mostrava a **casa do Blender** — casas diferentes, não batia. Agora a
**casa do Blender é a mesma em todo lugar**: Gazebo, mapa e Godot.

Como: exportei a casa do `ExpoProjectHouse.blend` para um mesh, montei um mundo
Gazebo com ela, gerei um mapa de ocupação dela e apontei o Nav2 pra esse
conjunto. Como o mundo está nas coordenadas nativas do Blender, o Godot (que
vem do mesmo `.blend`) **alinha sozinho** (escala=1, offset=0).

## Arquivos novos/alterados

| Arquivo | O que é |
|---|---|
| `ros2_ws/.../worlds/casa_blender/casa_blender.obj` (+ `.mtl`) | A casa exportada do Blender (24 objetos, metros). Colisão+visual do mundo. |
| `ros2_ws/.../worlds/casa_blender.world` | Mundo Gazebo com a casa como modelo estático. |
| `ros2_ws/.../maps/casa_blender.pgm` (+ `.yaml`) | Mapa de ocupação da casa do Blender (fatiado do mesh na altura do laser, z=0.18 m; origin [-9.6,-3.6], res 0.05). **Já alinhado ao mundo.** |
| `ros2_ws/.../launch/localizacao_blender.launch.py` | Sobe Gazebo(casa_blender) + spawn do burger em (0,6) + Nav2 (map_server+AMCL) com o mapa novo. |
| `ros2_ws/.../hestia_robot/gerenciador_chamados.py` | `RONDA` agora passa pelos 4 cômodos da casa do Blender: `[(-7.9,-1.8) Sala, (-7.9,11.45) Quarto, (5.85,9.7) Banheiro, (5.0,-1.9) Cozinha]`. |
| `ros2_ws/.../config/nav2_params.yaml` | Adicionado `set_initial_pose: true` + `initial_pose (0,6)` no AMCL (nasce localizado, sem depender de /initialpose na hora). |
| `ros2_ws/.../scripts/ajustar_laser_16m.sh` | Estende o laser do burger de 3.5 m → 16 m (ver abaixo). |
| `iniciar_hestia_blender.sh` | Igual ao `iniciar_hestia.sh`, mas na casa do Blender (launch novo + pose inicial (0,6)). |

> Os arquivos originais (turtlebot3_house) continuam intactos — nada foi
> apagado. `localizacao.launch.py` e `iniciar_hestia.sh` ainda rodam a casa do TB3.

## Como rodar na sua máquina (uma vez o setup)

Pré-requisitos: WSL2 Ubuntu 22.04 + ROS 2 Humble + Nav2 + TurtleBot3 + Gazebo
(o `INSTALL_WSL2.md` monta tudo).

```bash
# 1) ajustar o laser (uma vez só, depois de instalar o turtlebot3_gazebo)
bash ros2_ws/src/hestia_robot/scripts/ajustar_laser_16m.sh

# 2) buildar
cd ros2_ws && colcon build && source install/setup.bash && cd ..

# 3) subir o stack na casa do Blender
export TURTLEBOT3_MODEL=burger
bash iniciar_hestia_blender.sh
```

Depois abre o Godot (`interface_godot/`) e dá Play — o robô aparece na casa.

## ⚠️ Ponto que FALTA afinar (o "restante") — localização do AMCL

**Status honesto:** o mundo carrega, o robô spawna, o laser vê as paredes (16 m),
e a **pose real flui pro Godot** (testei: Gazebo→ponte→Godot, alinhado). O que
**ainda não ficou 100%** é a **localização do AMCL** nessa casa grande/aberta:

- O robô *físico* no Gazebo fica certo (dá pra conferir com `gz model -m burger -p`).
- Mas a *estimativa* do AMCL às vezes diverge (pula de posição) quando o robô
  está longe de paredes. Quando isso acontece, o Nav2 aborta metas (`status=6`)
  e o robô trava.

**Por que:** fiz tudo **sem RViz** (render por software no WSL do Leandro travava
a janela). Sem RViz não dá pra dar o "2D Pose Estimate" visual nem ver as
partículas convergindo. Já ataquei as duas causas principais:
1. Laser de 3.5 m → **16 m** (vê as paredes opostas).
2. Pose inicial fixa no AMCL (`set_initial_pose`).

**O que você pode fazer (você tem RViz funcionando):**
- Suba com `ros2 launch hestia_robot localizacao_blender.launch.py` (ele NÃO mata
  o RViz; dá pra incluir o RViz do Nav2). Dê **"2D Pose Estimate"** na posição
  real do robô — o AMCL converge e a nuvem de partículas fecha.
- Se ainda divergir no centro dos cômodos, dá pra: aumentar `max_beams` (60→120)
  e `laser_likelihood_max_dist` (2.0→4.0) no `nav2_params.yaml`, ou subir
  `max_particles`.
- Alternativa (se quiser garantir a demo visual independente do AMCL): publicar
  um `map→odom` estático e confiar na odometria do Gazebo (localização
  "perfeita" de simulação) — aí o robô navega liso e o Godot mostra certo, sem
  depender do AMCL casar scan. Posso preparar esse modo se preferir.

## Arquitetura (pra lembrar na prova)

```
Gazebo (casa_blender, física+laser) → AMCL (localiza no casa_blender.pgm)
   → Nav2 (planeja/desvia, preempção no gerenciador_chamados)
   → /amcl_pose → no_ponte → POST /pose,/atividade → ponte FastAPI → Godot
```

Frame do Gazebo = frame do Blender → Godot alinha sem offset (o `Robo.gd` já faz
o flip Y↔Z: Godot Z = -ROS y).
