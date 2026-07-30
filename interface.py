# -*- coding: utf-8 -*-
"""
interface.py
=============
Interface graphique Kivy de l'"Assistant Vocal Intelligent".

Éléments affichés :
- Bouton "🎤 Écouter"
- Zone affichant la phrase détectée (commande)
- Zone affichant l'action exécutée (réponse)
- Indicateur d'état du microphone (actif / inactif)

L'interface reste volontairement simple et légère pour économiser
la batterie et rester fluide sur des téléphones d'entrée de gamme.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse
from kivy.clock import Clock, mainthread
from kivy.core.window import Window

from reconnaissance_vocale import ReconnaissanceVocale
from analyse_commandes import MoteurCommandes
import actions_android


COULEUR_FOND = (0.07, 0.09, 0.13, 1)
COULEUR_ACCENT = (0.20, 0.60, 0.95, 1)
COULEUR_ACTIF = (0.20, 0.80, 0.45, 1)
COULEUR_INACTIF = (0.55, 0.55, 0.55, 1)


class IndicateurMicro(Widget):
    """Petit rond coloré indiquant si le micro écoute actuellement."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.actif = False
        self.size_hint = (None, None)
        self.size = (24, 24)
        with self.canvas:
            self.couleur = Color(*COULEUR_INACTIF)
            self.forme = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._maj, size=self._maj)

    def _maj(self, *args):
        self.forme.pos = self.pos
        self.forme.size = self.size

    def definir_actif(self, actif):
        self.actif = actif
        self.couleur.rgba = COULEUR_ACTIF if actif else COULEUR_INACTIF


class AssistantVocalUI(BoxLayout):
    """Widget racine de l'application : construit et gère toute l'interface."""

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=24, spacing=16, **kwargs)

        Window.clearcolor = COULEUR_FOND

        # Modules métier
        self.reconnaissance = ReconnaissanceVocale()
        self.moteur = MoteurCommandes()
        self.reconnaissance.demander_permission_micro()

        # ---- Titre ----
        self.add_widget(Label(
            text="🤖 Assistant Vocal Intelligent",
            font_size=24,
            bold=True,
            size_hint=(1, 0.12),
        ))

        # ---- Ligne indicateur micro ----
        ligne_statut = BoxLayout(orientation="horizontal", size_hint=(1, 0.08), spacing=8)
        self.indicateur = IndicateurMicro()
        ligne_statut.add_widget(self.indicateur)
        self.label_statut = Label(text="Microphone inactif", font_size=14, color=COULEUR_INACTIF)
        ligne_statut.add_widget(self.label_statut)
        self.add_widget(ligne_statut)

        # ---- Zone : commande détectée ----
        self.add_widget(Label(text="Commande détectée :", font_size=14, size_hint=(1, 0.06)))
        self.label_commande = Label(
            text="—",
            font_size=18,
            size_hint=(1, 0.18),
            color=(1, 1, 1, 1),
        )
        self.add_widget(self.label_commande)

        # ---- Zone : réponse / action exécutée ----
        self.add_widget(Label(text="Réponse :", font_size=14, size_hint=(1, 0.06)))
        self.label_reponse = Label(
            text="—",
            font_size=18,
            size_hint=(1, 0.18),
            color=COULEUR_ACTIF,
        )
        self.add_widget(self.label_reponse)

        # ---- Bouton principal ----
        self.bouton_ecouter = Button(
            text="🎤 Écouter",
            font_size=20,
            size_hint=(1, 0.18),
            background_normal="",
            background_color=COULEUR_ACCENT,
        )
        self.bouton_ecouter.bind(on_press=self.declencher_ecoute)
        self.add_widget(self.bouton_ecouter)

    # --------------------------------------------------------------
    # Gestion de l'écoute (asynchrone pour ne pas geler l'interface)
    # --------------------------------------------------------------
    def declencher_ecoute(self, instance):
        """Appelé quand l'utilisateur appuie sur le bouton Écouter."""
        self.bouton_ecouter.disabled = True
        self._definir_micro_actif(True)
        self.label_commande.text = "🎧 Écoute en cours..."
        self.label_reponse.text = "—"

        # On planifie le traitement (bloquant) sur un thread séparé
        # pour ne pas bloquer l'interface graphique de Kivy.
        Clock.schedule_once(lambda dt: self._ecouter_en_arriere_plan(), 0.1)

    def _ecouter_en_arriere_plan(self):
        import threading
        thread = threading.Thread(target=self._processus_ecoute, daemon=True)
        thread.start()

    def _processus_ecoute(self):
        """Exécuté dans un thread séparé : capture, transcrit, analyse, agit."""
        try:
            texte = self.reconnaissance.ecouter_et_transcrire(duree_secondes=5)
        except Exception as erreur:
            texte = ""
            print(f"[Interface] Erreur pendant l'écoute : {erreur}")

        self._traiter_resultat(texte)

    @mainthread
    def _traiter_resultat(self, texte):
        """Revient sur le thread principal Kivy pour mettre à jour l'UI et agir."""
        self._definir_micro_actif(False)
        self.bouton_ecouter.disabled = False

        if not texte:
            self.label_commande.text = "Aucune parole détectée"
            self.label_reponse.text = "Réessayez ❓"
            return

        self.label_commande.text = f'"{texte}"'

        resultat = self.moteur.analyser(texte)
        action = resultat["action"]

        if action == "INCONNUE":
            self.label_reponse.text = resultat["reponse"]
            return

        succes = actions_android.executer_action(action, resultat.get("parametre"))
        self.label_reponse.text = resultat["reponse"] if succes else "Échec de l'action ⚠️"

    def _definir_micro_actif(self, actif):
        self.indicateur.definir_actif(actif)
        self.label_statut.text = "Microphone actif 🎤" if actif else "Microphone inactif"
        self.label_statut.color = COULEUR_ACTIF if actif else COULEUR_INACTIF


class AssistantVocalApp(App):
    """Classe principale de l'application Kivy."""

    title = "Assistant Vocal Intelligent"

    def build(self):
        return AssistantVocalUI()
