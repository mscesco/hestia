# Héstia — Robô de Assistência para Smart Home 2050

**Projeto NEXUS · ExpoTech 2026.2 · 6º Semestre — Ciência da Computação**

Robô autônomo de assistência a idosos em uma casa inteligente. O robô navega
pela casa de forma autônoma, faz uma ronda de cuidado e atende chamados da
pessoa assistida, priorizando emergências (queda) sobre pedidos comuns (água).
O sistema é monitorado por uma interface imersiva 3D e tem sua própria
segurança testada pela equipe.

A arquitetura é um fluxo único de informação e controle que vai do robô até o
cuidador. Cada disciplina do semestre governa uma camada desse fluxo.

---

## Começando (Semana 1)

1. Monte o ambiente seguindo **`INSTALL_WSL2.md`** (guia do zero, para Windows/WSL2).
2. Rode **`bash verifica_ambiente.sh`** para conferir a instalação.
3. Siga o checklist em **`SEMANA_01.md`** até o portão de saída (o Gazebo abrir
   o `turtlebot3_house`).
4. Leia **`ARQUITETURA.md`** e **`CRONOGRAMA.md`**.

---

## 1. Robótica (Navegação Autônoma)

- **Plataforma:** ROS 2 Humble, simulação no Gazebo (mundo `turtlebot3_house`).
- **Navegação em malha fechada:** localização contínua por sensor, sem execução em malha aberta.
- **Mapeamento:** mapa da casa gerado previamente por SLAM (`slam_toolbox`) e salvo (`.pgm` + `.yaml`).
- **Localização:** AMCL (localização de Monte Carlo adaptativa) sobre o mapa salvo.
- **Planejamento:** Nav2 — planner global para a rota e controlador local para desvio de obstáculos dinâmicos.
- **Lógica de prioridade com preempção:** os chamados entram em uma fila com
  prioridade. Ao chegar um chamado de maior prioridade (queda) durante o
  atendimento de um de menor prioridade (água), a meta de navegação atual do
  Nav2 é **cancelada (preemptada)** e a nova meta é enviada imediatamente. O
  robô não conclui a tarefa em andamento antes de reagir à emergência.

## 2. Computação Gráfica (Interface Imersiva)

- **Modelagem:** casa e robô modelados no Blender.
- **Renderização:** Godot (shader autoral na linguagem de shaders do Godot e
  iluminação em tempo real, comprovando uso real do pipeline gráfico).
- **Ponte de comunicação:** um servidor HTTP (FastAPI) atua como ponte entre o
  ROS 2 e o Godot. Um nó ROS publica no servidor:
  - **pose do robô** (posição e orientação em tempo real);
  - **stream da câmera** do robô (visão "pelos olhos do robô").

  O Godot consome esses dados do servidor e atualiza a cena 3D em tempo real.

## 3. Segurança (Pentest)

- **Alvo:** o servidor-ponte (FastAPI) que expõe o controle do robô.
- **Vetor de ataque exato:** o endpoint de comando de movimento/atendimento
  aceita requisições **sem autenticação**, acessível na rede local. Um atacante
  consegue enviar comandos de controle ao robô sem qualquer credencial
  (Broken Authentication — OWASP API Security).
- **Ciclo documentado no relatório:**
  1. Reconhecimento (`nmap` no host do servidor);
  2. Exploração (script que envia comando de controle sem token) — com
     evidência (log + vídeo) capturada **antes** da correção;
  3. Classificação da severidade (vetor e nota CVSS).
- **Correções técnicas aplicadas:**
  1. Autenticação por token (JWT) no endpoint de comando;
  2. Validação de schema do payload (Pydantic), rejeitando comandos malformados ou injetados.

## 4. Paradigmas e Arquitetura

Ver `ARQUITETURA.md` para a justificativa completa.

- **Paradigma 1 — Orientado a Objetos (OOP):** modela os componentes do robô
  (robô, sensores, atuadores) — entidades com identidade e estado mutável.
- **Paradigma 2 — Funcional:** pipeline de processamento das leituras de
  sensor, como uma cadeia de funções puras, sem estado compartilhado.
- **Padrão de projeto — Observer:** adotado na comunicação por eventos. O modelo
  publish/subscribe de tópicos do ROS 2 é uma aplicação direta do Observer.

---

## Estrutura do repositório

```
hestia/
├── README.md                 # este arquivo
├── CRONOGRAMA.md             # plano de 8 semanas
├── ARQUITETURA.md            # justificativa de paradigmas e padrão de projeto
├── ros2_ws/                  # workspace ROS 2 (robótica)
│   └── src/hestia_robot/
│       ├── hestia_robot/     # código Python (nós, modelos, pipeline)
│       ├── launch/           # bringup: SLAM (Sem.2), AMCL+Nav2 (Sem.3), sistema (Sem.7)
│       ├── config/           # nav2_params.yaml, waypoints da ronda
│       ├── maps/             # mapa salvo pelo SLAM (casa.pgm + casa.yaml)
│       └── rviz/             # layouts do RViz2 para ver a navegação
├── ponte/                    # servidor FastAPI (ponte ROS <-> Godot, alvo do pentest)
├── interface_godot/          # projeto Godot (usa models/casa.glb exportada do Blender)
├── modelagem/                # fonte Blender da casa (ExpoProjectHouse.blend) — FORA do projeto Godot
└── pentest/                  # recon, exploit, relatório e correções
```

## Equipe

| Integrante                     | RA     | Responsabilidade principal |
|---------------------------------|--------|----------------------------|
| Camila Cesco Ferreira            | 134666 | (definir)                  |
| Leandro Laurindo Soares          | 82263  | (definir)                  |
| Marcelo Luna Ieradi              | 95121  | (definir)                  |

> A responsabilidade principal indica quem liderou cada camada — **não** exime
> ninguém de saber explicar as demais. A avaliação é individual.

## Stack

ROS 2 Humble · Gazebo · slam_toolbox · Nav2 · AMCL · FastAPI · Blender ·
Godot · Python · nmap
