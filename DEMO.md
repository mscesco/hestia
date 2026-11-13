# DEMO — roteiro do dia (Héstia)

Guia curto para rodar o sistema na frente do professor, sem pensar. Caminho do
projeto no WSL: `/mnt/c/Users/Usuario/Documents/hestia`.

---

## 0. Antes de começar (uma vez por máquina)
```bash
cd /mnt/c/Users/Usuario/Documents/hestia
bash ros2_ws/src/hestia_robot/scripts/ajustar_laser_16m.sh      # laser 3.5->16 m (pede sudo)
cd ros2_ws && colcon build --symlink-install && source install/setup.bash && cd ..
python3 -m pip install fastapi uvicorn pydantic requests        # deps da ponte
# porta 8000 precisa estar livre (se tiver o container do task-manager: docker stop task_manager_api)
```

## 1. Subir o sistema (1 comando)
```bash
export TURTLEBOT3_MODEL=burger
bash iniciar_hestia_blender_simples.sh     # PLANO B — recomendado p/ a demo (liso)
#   alternativa "robótica de verdade" (com AMCL): bash iniciar_hestia_blender.sh
```
Espere o `HESTIA_UP ...` no fim. O RViz abre. **Marque a caixinha "RobotModel"**
no painel da esquerda para o robô aparecer.

## 2. Navegação autônoma
O robô já sai **rondando os 4 cômodos** sozinho. No RViz, a **linha** é o caminho
que o Nav2 planejou; o robô segue por ela, desviando de obstáculos.

## 3. A PREEMPÇÃO (o ponto que vale nota) — em outro terminal
```bash
cd /mnt/c/Users/Usuario/Documents/hestia && source ros2_ws/install/setup.bash

# 1) pedido comum (água) — robô vai para a cozinha
bash ros2_ws/src/hestia_robot/scripts/publica_chamado.sh agua  PEDIDO_COMUM  5.0 -1.9

# 2) com o água ainda a caminho, dispare a emergência (queda):
bash ros2_ws/src/hestia_robot/scripts/publica_chamado.sh queda EMERGENCIA  -7.9 11.45
```
Acompanhe num terminal: `tail -f /tmp/hestia_logs/gerenciador.log`
→ deve aparecer `PREEMPCAO: queda[EMERGENCIA] interrompe agua[PEDIDO_COMUM] ...`
e o caminho no RViz **muda de destino na hora**. **Grave um vídeo disto.**

## 4. Godot — a vista 3D + painel do cuidador
No Windows (com a ponte no ar): `godot --path interface_godot`.
O robô (cápsula azul) se move junto com a navegação e **pulsa vermelho** na emergência.
- Canto superior direito: **"pelos olhos do robô"** (câmera acoplada).
- Canto inferior esquerdo: **painel do cuidador** — status em texto e botões que
  fazem o pedido sem terminal: **💧 água**, **🚨 queda (emergência)**, **🛋️ sala**.
  Clicar em 🚨 com um pedido comum a caminho mostra a **preempção** na cena.
  (A UI autentica sozinha na ponte; credencial da demo: `operador` / `hestia2026`.)

## 5. Parar tudo
```bash
bash parar_hestia.sh
```

---

## O que dizer, em 1 linha por camada
- **Robótica:** ROS 2 + Nav2 navegam sozinhos; fila de prioridade **cancela
  (preempta)** a meta atual quando chega uma emergência — via API de ações do Nav2.
- **Arquitetura:** uma ponte FastAPI liga ROS ↔ Godot; o código usa OOP, estilo
  funcional no tratamento de sensores e o padrão **Observer** (tópicos do ROS).
- **Computação Gráfica:** casa modelada no **Blender**, renderizada no **Godot**
  com shader autoral e iluminação em tempo real.
- **Segurança:** pentest no endpoint `/comando` (Broken Authentication, **CVSS 8.1**),
  corrigido com **JWT** + validação de schema (Pydantic). Relatório em `pentest/relatorio.md`.

## Se perguntarem "plano A vs plano B" (localização)
- **A (AMCL):** localização "de verdade" — o robô se acha comparando o laser com o
  mapa. Em cômodos grandes e abertos às vezes fica incerto (daí as manobras de
  recuperação).
- **B:** como é simulação, usamos a posição exata que o Gazebo já conhece (um
  atalho só possível em simulação). Fica mais liso para a demo, mas não é
  localização "real" — por isso o A é o conceito importante de explicar.

## Se algo der errado
- Status da ponte: `curl localhost:8000/status` (tem que mostrar a pose, não `Not Found`).
- Logs de tudo: `ls /tmp/hestia_logs/` (ponte.log, localizacao.log, no_ponte.log, gerenciador.log).
- Recomeçar do zero: `bash parar_hestia.sh` e suba de novo.
