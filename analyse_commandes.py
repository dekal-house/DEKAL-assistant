# -*- coding: utf-8 -*-
"""
analyse_commandes.py
=====================
Moteur d'analyse des commandes vocales.

Rôle :
- Charger la base de commandes (base_commandes.json)
- Comparer le texte reconnu par la reconnaissance vocale
  avec les phrases connues
- Retourner l'action correspondante (+ paramètre éventuel)
- Permettre d'ajouter de nouvelles phrases personnalisées à chaud

Le moteur utilise une comparaison "floue" simple (mots-clés + similarité)
afin de tolérer les petites variations de langage, sans dépendre
d'une connexion Internet.
"""

import json
import os
import difflib

# Chemin du fichier de base de commandes (à côté de ce script)
CHEMIN_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "base_commandes.json")


class MoteurCommandes:
    """
    Charge et interroge la base de commandes vocales.
    Chaque entrée de la base contient :
      - "phrases"   : liste de phrases déclenchant l'action
      - "action"    : code de l'action à exécuter (ex: ACTIVER_FLASH)
      - "parametre" : (optionnel) donnée supplémentaire (ex: nom de paquet Android)
      - "reponse"   : texte affiché/énoncé après exécution
    """

    def __init__(self, chemin_base=CHEMIN_BASE):
        self.chemin_base = chemin_base
        self.commandes = []
        self.charger_base()

    def charger_base(self):
        """Charge le fichier JSON contenant les commandes connues."""
        try:
            with open(self.chemin_base, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.commandes = data.get("commandes", [])
        except FileNotFoundError:
            # Si le fichier n'existe pas encore, on part d'une base vide
            self.commandes = []
            self.sauvegarder_base()
        except json.JSONDecodeError:
            print("[MoteurCommandes] Erreur : base_commandes.json est corrompu.")
            self.commandes = []

    def sauvegarder_base(self):
        """Réécrit le fichier JSON avec l'état actuel des commandes."""
        with open(self.chemin_base, "w", encoding="utf-8") as f:
            json.dump({"commandes": self.commandes}, f, ensure_ascii=False, indent=2)

    @staticmethod
    def normaliser(texte):
        """Met le texte en minuscules et retire les espaces superflus/accents simples."""
        texte = texte.strip().lower()
        remplacements = {
            "é": "e", "è": "e", "ê": "e", "ë": "e",
            "à": "a", "â": "a",
            "î": "i", "ï": "i",
            "ô": "o",
            "û": "u", "ù": "u",
            "ç": "c",
        }
        for accent, lettre in remplacements.items():
            texte = texte.replace(accent, lettre)
        return texte

    def analyser(self, texte_utilisateur):
        """
        Analyse le texte prononcé par l'utilisateur et retourne un dictionnaire :
        {
            "action": "ACTIVER_FLASH" | None,
            "parametre": ... | None,
            "reponse": "texte de confirmation",
            "phrase_reconnue": texte original
        }
        Si aucune commande ne correspond, action = "INCONNUE".
        """
        texte_norm = self.normaliser(texte_utilisateur)
        meilleure_correspondance = None
        meilleur_score = 0.0

        for commande in self.commandes:
            for phrase in commande.get("phrases", []):
                phrase_norm = self.normaliser(phrase)

                # 1) Correspondance directe (la phrase est contenue dans le texte dit)
                if phrase_norm in texte_norm or texte_norm in phrase_norm:
                    return {
                        "action": commande["action"],
                        "parametre": commande.get("parametre"),
                        "reponse": commande.get("reponse", "Action exécutée ✅"),
                        "phrase_reconnue": texte_utilisateur,
                    }

                # 2) Similarité approximative (tolère les fautes de reconnaissance vocale)
                score = difflib.SequenceMatcher(None, texte_norm, phrase_norm).ratio()
                if score > meilleur_score:
                    meilleur_score = score
                    meilleure_correspondance = commande

        # Seuil de tolérance : au-delà de 0.6, on considère que c'est probablement la bonne commande
        if meilleure_correspondance and meilleur_score >= 0.6:
            return {
                "action": meilleure_correspondance["action"],
                "parametre": meilleure_correspondance.get("parametre"),
                "reponse": meilleure_correspondance.get("reponse", "Action exécutée ✅"),
                "phrase_reconnue": texte_utilisateur,
            }

        # Aucune commande reconnue
        return {
            "action": "INCONNUE",
            "parametre": None,
            "reponse": "Je n'ai pas compris cette commande ❓",
            "phrase_reconnue": texte_utilisateur,
        }

    def ajouter_commande(self, phrase, action, parametre=None, reponse=None):
        """
        Permet à l'utilisateur d'ajouter une nouvelle commande personnalisée.
        Si l'action existe déjà dans la base, la phrase est ajoutée à cette action.
        Sinon, une nouvelle entrée est créée.
        """
        phrase = phrase.strip().lower()

        for commande in self.commandes:
            if commande["action"] == action:
                if phrase not in commande["phrases"]:
                    commande["phrases"].append(phrase)
                self.sauvegarder_base()
                return

        nouvelle_commande = {
            "phrases": [phrase],
            "action": action,
            "reponse": reponse or "Action exécutée ✅",
        }
        if parametre:
            nouvelle_commande["parametre"] = parametre

        self.commandes.append(nouvelle_commande)
        self.sauvegarder_base()

    def liste_actions_disponibles(self):
        """Retourne la liste des codes d'action actuellement connus."""
        return sorted({c["action"] for c in self.commandes})


if __name__ == "__main__":
    # Petit test manuel en ligne de commande
    moteur = MoteurCommandes()
    print("Actions disponibles :", moteur.liste_actions_disponibles())
    resultat = moteur.analyser("il fait sombre")
    print(resultat)
