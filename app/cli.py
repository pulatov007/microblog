import os
import click
from app import app


@app.cli.group()
def translate():
    """Commandes de traduction et localisation."""
    pass


@translate.command()
def update():
    """Mettre à jour toutes les langues."""
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        raise RuntimeError('La commande extract a échoué')
    if os.system('pybabel update -i messages.pot -d app/translations'):
        raise RuntimeError('La commande update a échoué')
    os.remove('messages.pot')


@translate.command()
def compile():
    """Compiler toutes les langues."""
    if os.system('pybabel compile -d app/translations'):
        raise RuntimeError('La commande compile a échoué')


@translate.command()
@click.argument('lang')
def init(lang):
    """Initialiser une nouvelle langue."""
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        raise RuntimeError('La commande extract a échoué')
    if os.system('pybabel init -i messages.pot -d app/translations -l ' + lang):
        raise RuntimeError('La commande init a échoué')
    os.remove('messages.pot')
