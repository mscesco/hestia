from glob import glob

from setuptools import setup

package_name = "hestia_robot"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        # Pastas de recursos instaladas junto do pacote (globs vazios agora, OK).
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/maps", glob("maps/*.pgm") + glob("maps/*.yaml")),
        ("share/" + package_name + "/rviz", glob("rviz/*.rviz")),
        # scripts/ precisa ser instalado: o launch do plano B roda o
        # pose_tf_bridge.py pelo caminho instalado (share/.../scripts/).
        ("share/" + package_name + "/scripts",
         glob("scripts/*.py") + glob("scripts/*.sh")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Equipe Héstia",
    description="Robô de assistência Héstia",
    license="MIT",
    entry_points={
        "console_scripts": [
            "gerenciador_chamados = hestia_robot.gerenciador_chamados:main",
            "no_ponte = hestia_robot.no_ponte:main",
        ],
    },
)
