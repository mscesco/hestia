# config/ — parâmetros (os "botões" do Nav2 e da ronda)

Arquivos `.yaml` que os launch files carregam. Ficam separados do código para
poder ajustar sem recompilar.

| Arquivo | O que é |
|---------|---------|
| `nav2_params.yaml` | Parâmetros do Nav2 (AMCL, planner, controller, costmaps). Base do TurtleBot3 `burger` para Humble, ajustada para a casa aberta do Blender. Usado pelo **plano A** (com AMCL). |
| `nav2_params_simples.yaml` | Igual ao anterior, mas com `amcl: tf_broadcast: false` — usado pelo **plano B** (localização por TF estática). |

> Os waypoints da ronda não ficam aqui: estão inline no `gerenciador_chamados.py`
> (lista `RONDA`, os 4 cômodos da casa do Blender).

> O `nav2_params.yaml` veio do padrão do TurtleBot3 para Humble (não foi escrito
> do zero). Reinventar esse arquivo é um poço de tempo sem retorno de nota.
