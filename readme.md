# criar ambiente windows
python -m venv .venv

# ativar ambiente
.venv\Scripts\activate

# exportar libs do projeto
pipreqs . --ignore .venv --force

# instalar libs do projeto
pip install -r requirements.txt