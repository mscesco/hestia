# SEMANA 1 — Fundação (pronta para executar)

Objetivo da semana: **ambiente de pé + documentos de arquitetura escritos.**
Nada de robótica ainda. Se o Gazebo não abrir a casa até o fim da semana, essa
é a única prioridade — não avance para a Semana 2.

## Checklist

- [ ] **Ambiente instalado** seguindo `INSTALL_WSL2.md` (Etapas 1 a 6).
- [ ] **Teste talker/listener** passou (Etapa 5).
- [ ] **`bash verifica_ambiente.sh`** sem falhas.
- [ ] **Portão de saída:** `turtlebot3_house` abre no Gazebo com o robô (Etapa 7).
- [ ] **`ARQUITETURA.md` lido e entendido** (os dois paradigmas + o padrão Observer).
- [ ] **Distro e modelo confirmados com a sala** (Humble? qual TURTLEBOT3_MODEL? qual Gazebo?).
- [ ] **Papéis distribuídos** e preenchidos na tabela do `README.md`.

## O portão de saída (o que prova que a semana fechou)

```bash
bash verifica_ambiente.sh
ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py
```

Janela do Gazebo abriu com a casa e o robô = Semana 1 concluída.

## O que você tem que saber explicar no fim da semana

- O que é ROS 2, e o que são **nó**, **tópico** e **serviço** (o vocabulário base).
- Por que o ROS precisa de Linux, e o que o WSL2 resolve.
- O que é "sourcing" e por que está no `.bashrc`.
- Onde, na arquitetura, estão os dois paradigmas e o padrão Observer
  (ver `ARQUITETURA.md`) — mesmo sem ter escrito o código ainda.

## Risco da semana

Perder dias na parte gráfica do WSL2 (Gazebo não abre). Se acontecer, use a
seção de troubleshooting do `INSTALL_WSL2.md` e não deixe isso arrastar: é o
gargalo clássico da Semana 1.

## Nota sobre a divisão de trabalho

Hoje "tudo é sua camada". Quando o grupo se dividir, quem pegar robótica precisa
repetir este SETUP na própria máquina — o `verifica_ambiente.sh` existe
justamente para cada pessoa confirmar que está no mesmo ambiente. Ambiente
diferente por pessoa é o que quebra a integração lá na Semana 7.
