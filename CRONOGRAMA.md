# Cronograma — Projeto Héstia (8 semanas)

**Da inscrição (11/09) à avaliação individual (09–13/11).**

> Não há folga neste calendário. Se uma semana atrasar, corte escopo — não empurre prazo.
> A nota é **individual e oral**: cada semana tem o que a IA constrói, **o que você precisa saber explicar**, e o que provavelmente vai dar errado.

---

## Semana 1 (15–21/09) — Fundação e decisões irreversíveis

**Entrega:** ambiente rodando. Ubuntu 22.04 + ROS 2 **Humble** (decidam a distro agora e escrevam em toda prompt de IA — misturar Humble com Jazzy/Foxy é a causa nº 1 de erro fantasma). Gazebo abrindo o `turtlebot3_house`. `ARQUITETURA.md` escrito. Papéis distribuídos.

- **Saber explicar:** o que é ROS 2, nó, tópico e serviço.
- **Risco:** perder a semana instalando ROS no Windows. Usem WSL2, VM ou dual boot. Se o Gazebo não abrir até sexta, é prioridade absoluta antes de qualquer outra coisa.

## Semana 2 (22–28/09) — Mapa e localização

**Entrega:** rodar `slam_toolbox`, gerar o mapa, **salvar o `.pgm` e o `.yaml`**. Trocar para AMCL sobre o mapa salvo. A partir daqui não se depende mais do SLAM ao vivo.

- **Saber explicar:** diferença entre mapear (SLAM) e se localizar num mapa pronto (AMCL), e por que salvaram o mapa.
- **Risco:** mapa vira espaguete. Contingência embutida — salvem o melhor mapa e operem sobre ele. Gravem um vídeo do mapeamento dando certo uma vez, como evidência.

## Semana 3 (29/09–04/10) — Chamados com prioridade e preempção

**Entrega:** nó Python que faz o robô circular por waypoints (ronda de cuidado) e atender chamados por prioridade. **Ponto crítico exigido pelo professor:** ao chegar um chamado de maior prioridade (queda) durante o atendimento de um menor (água), a meta de navegação atual do Nav2 é **cancelada (preemptada)** e a nova é enviada. Não é um `if` simples — usa a API de ações (action client: `cancel_goal` + novo `send_goal`).

- **Saber explicar:** como o robô decide entre dois chamados concorrentes, o que é preempção de meta, o que o Nav2 faz por baixo (costmap, planner), e onde o Observer aparece.
- **Risco:** subestimar a preempção. Peça à IA "cancelar uma NavigateToPose action e enviar outra, ROS 2 Humble, rclpy action client" e **teste o cancelamento isolado** antes de plugar na lógica de chamados.

## Semana 4 (06–10/10) — A ponte

**Entrega:** servidor FastAPI em localhost. Um nó ROS posta a pose e o estado do robô; a API expõe `/status` e o `/stream` da câmera. **Deixem sem autenticação de propósito** — é o alvo do pentest.

- **Saber explicar:** por que existe uma ponte em vez de o Godot falar direto com o ROS; o que é um endpoint HTTP.
- **Risco:** alguém vai querer plugar o Godot direto no ROS 2 via algum bridge nativo. Não deixem — some uma semana, não acrescenta nota.

## Semana 5 (13–18/10) — Godot + Blender

**Entrega:** casa e robô modelados no Blender (exportados em glTF/`.glb`) e importados no Godot. Godot lendo `/status` e movendo o robô em tempo real, e exibindo o `/stream` da câmera ("pelos olhos do robô"). Um shader autoral (linguagem de shaders do Godot, `.gdshader`) e iluminação em tempo real. Destaque visual quando há emergência.

- **Saber explicar:** o que é um shader, o que é o pipeline de renderização (mesmo superficialmente). Se perguntarem sobre "2D disfarçada de 3D", mostre o shader, a iluminação e a pose atualizando ao vivo.
- **Risco:** polir gráfico e abandonar o resto. Timebox: fica bonita o suficiente esta semana e não se mexe mais.

## Semana 6 (20–25/10) — Pentest (localhost, sem depender de internet)

**Entrega, nesta ordem exata:** (1) `nmap` no host; (2) script Python que manda o robô atender um chamado falso **sem token** — o ataque; (3) **gravar o vídeo do ataque funcionando e salvar os logs**; (4) relatório com vetor CVSS; (5) **só então** aplicar as duas correções: JWT + validação de schema (Pydantic).

- **Saber explicar:** qual a vulnerabilidade, por que existia, como a correção fecha. Entenda o vetor CVSS, não decore a nota.
- **Risco:** corrigir antes de documentar. Aí não sobra ataque pra mostrar. A ordem não é sugestão.

## Semana 7 (27/10–01/11) — Integração e o que quebrou

**Entrega:** tudo de ponta a ponta ao mesmo tempo — Gazebo → nó → FastAPI → Godot, com pentest documentado. Semana de buffer de propósito.

- **Saber explicar:** cada integrante explica **a parte de outra pessoa**. Onde travar, é onde o professor pega.
- **Risco:** descobrir que duas partes assumiram formatos de dado diferentes. Por isso a ponte foi feita na semana 4.

## Semana 8 (03–08/11) — Congelar e ensaiar a defesa

**Entrega:** **freeze.** Nada de código novo. Gravar um vídeo de 3 minutos do sistema inteiro funcionando — é o seguro, porque Gazebo trava e a avaliação é individual e sequencial. Ensaiar a arguição cruzada.

- **Saber explicar:** é a prova oral. Não tem mais o que construir, só o que saber.
- **Risco:** demo ao vivo no Gazebo na frente do professor. Não façam. Vídeo primeiro, simulação ao lado como bônus.

---

## Dois pontos que decidem o resultado (e não estão nas semanas)

1. **Ritual de compreensão semanal.** Toda sexta, 30 min, cada integrante explica a parte de OUTRO. Se alguém não consegue em setembro, há dois meses para resolver. Se descobrem em novembro, a nota individual já era.
2. **Dependência de uma pessoa só.** Se o integrante que sabe ROS sumir na semana 5, o projeto morre? Se sim, esse é o maior risco de execução — não a tecnologia. Ninguém pode ser o único que entende uma camada.
