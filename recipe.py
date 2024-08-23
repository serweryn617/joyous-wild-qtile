# Cooking recipe, checkout Cook at https://github.com/serweryn617/cook

from pathlib import Path
base_path = Path(__file__).parent.resolve()

default_build_server = 'local'
default_project = 'install'

projects = {}

projects['install'] = (
    f'ln -s {base_path}/qtile ~/.config/qtile',
)

