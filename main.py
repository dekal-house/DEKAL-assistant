# -*- coding: utf-8 -*-
"""
main.py
========
Point d'entrée de l'application "Assistant Vocal Intelligent".

Ce fichier reste volontairement minimal : toute la logique d'interface
est déléguée à interface.py (séparation des responsabilités demandée
dans le cahier des charges).

Pour lancer l'application :
    - Sur desktop (test) : python main.py
    - Sur Android : buildozer android debug deploy run
"""

from interface import AssistantVocalApp

if __name__ == "__main__":
    AssistantVocalApp().run()
