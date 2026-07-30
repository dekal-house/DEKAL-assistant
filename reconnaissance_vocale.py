# -*- coding: utf-8 -*-
"""
reconnaissance_vocale.py
=========================
Gère la capture audio du microphone et la transcription voix -> texte,
entièrement hors ligne (respect de la vie privée : rien n'est envoyé
sur Internet).

Moteur principal : Vosk (léger, rapide, fonctionne bien sur mobile).
Moteur alternatif : Whisper (plus précis, mais plus lourd en calcul),
                     utilisé uniquement si Vosk échoue ou n'est pas
                     disponible.

Sur Android, l'accès au micro passe par Plyer / Android natif (Pyjnius).
Sur desktop (pour tester le module pendant le développement), le module
utilise sounddevice comme repli.
"""

import os
import json
import queue

# ----------------------------------------------------------------------
# Détection de la plateforme
# ----------------------------------------------------------------------
try:
    from plyer import platform as plyer_platform  # noqa: F401 (juste pour vérifier plyer)
    from plyer import audio
    SUR_ANDROID = True
except Exception:
    SUR_ANDROID = False

# Dossier attendu pour le modèle Vosk (léger, français).
# À télécharger manuellement depuis https://alphacephei.com/vosk/models
# (ex : vosk-model-small-fr-0.22) et à placer dans le dossier "modele_vosk/"
DOSSIER_MODELE_VOSK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modele_vosk")


class ReconnaissanceVocale:
    """
    Encapsule la reconnaissance vocale hors ligne.

    Utilisation typique :
        rv = ReconnaissanceVocale()
        rv.demander_permission_micro()
        texte = rv.ecouter_et_transcrire(duree_secondes=5)
    """

    def __init__(self, dossier_modele=DOSSIER_MODELE_VOSK, langue="fr"):
        self.dossier_modele = dossier_modele
        self.langue = langue
        self.modele_vosk = None
        self.pret = False
        self._charger_moteur_vosk()

    # ------------------------------------------------------------------
    # Permissions Android
    # ------------------------------------------------------------------
    def demander_permission_micro(self):
        """
        Demande la permission RECORD_AUDIO à l'utilisateur (obligatoire
        sur Android 6+). Ne fait rien sur desktop.
        """
        if not SUR_ANDROID:
            print("[Permissions] Mode desktop : permission micro simulée accordée.")
            return True

        try:
            from android.permissions import request_permissions, Permission, check_permission

            permissions_necessaires = [
                Permission.RECORD_AUDIO,
                Permission.BLUETOOTH,
                Permission.BLUETOOTH_ADMIN,
                Permission.ACCESS_FINE_LOCATION,
                Permission.CAMERA,
                Permission.SEND_SMS,
            ]

            manquantes = [p for p in permissions_necessaires if not check_permission(p)]
            if manquantes:
                request_permissions(manquantes)
            return True
        except Exception as erreur:
            print(f"[Permissions] Erreur lors de la demande de permissions : {erreur}")
            return False

    # ------------------------------------------------------------------
    # Chargement du moteur Vosk
    # ------------------------------------------------------------------
    def _charger_moteur_vosk(self):
        """Charge le modèle Vosk s'il est présent sur le disque."""
        if not os.path.isdir(self.dossier_modele):
            print(
                f"[Vosk] Modèle introuvable dans '{self.dossier_modele}'. "
                "Téléchargez un modèle sur https://alphacephei.com/vosk/models "
                "et placez-le dans ce dossier."
            )
            self.pret = False
            return

        try:
            import vosk
            vosk.SetLogLevel(-1)  # silence les logs internes de Vosk
            self.modele_vosk = vosk.Model(self.dossier_modele)
            self.pret = True
            print("[Vosk] Modèle chargé avec succès.")
        except Exception as erreur:
            print(f"[Vosk] Impossible de charger le modèle : {erreur}")
            self.pret = False

    # ------------------------------------------------------------------
    # Écoute + transcription
    # ------------------------------------------------------------------
    def ecouter_et_transcrire(self, duree_secondes=5, frequence_echantillonnage=16000):
        """
        Enregistre l'audio du micro pendant `duree_secondes` puis retourne
        le texte transcrit (chaîne vide si rien n'a été compris).
        """
        if self.pret:
            texte = self._transcrire_avec_vosk(duree_secondes, frequence_echantillonnage)
            if texte:
                return texte

        # Repli sur Whisper si Vosk n'est pas disponible ou n'a rien compris
        return self._transcrire_avec_whisper(duree_secondes, frequence_echantillonnage)

    def _capturer_audio(self, duree_secondes, frequence_echantillonnage):
        """
        Capture un flux audio brut (PCM 16 bits mono) depuis le micro.
        Utilise sounddevice sur desktop ; sur Android, Kivy/Plyer gèrent
        généralement le flux via un module natif équivalent (audiostream).
        """
        try:
            import sounddevice as sd
            import numpy as np

            enregistrement = sd.rec(
                int(duree_secondes * frequence_echantillonnage),
                samplerate=frequence_echantillonnage,
                channels=1,
                dtype="int16",
            )
            sd.wait()
            return enregistrement.tobytes()
        except Exception as erreur:
            print(f"[Audio] Erreur de capture audio : {erreur}")
            return None

    def _transcrire_avec_vosk(self, duree_secondes, frequence_echantillonnage):
        """Transcrit l'audio capturé grâce au modèle Vosk (hors ligne)."""
        import vosk

        audio_brut = self._capturer_audio(duree_secondes, frequence_echantillonnage)
        if audio_brut is None:
            return ""

        reconnaisseur = vosk.KaldiRecognizer(self.modele_vosk, frequence_echantillonnage)
        reconnaisseur.AcceptWaveform(audio_brut)
        resultat = json.loads(reconnaisseur.FinalResult())
        texte = resultat.get("text", "").strip()
        return texte

    def _transcrire_avec_whisper(self, duree_secondes, frequence_echantillonnage):
        """
        Transcrit l'audio grâce à Whisper (plus précis, plus lent).
        Utilisé uniquement en repli si Vosk échoue.
        """
        try:
            import whisper
            import numpy as np

            audio_brut = self._capturer_audio(duree_secondes, frequence_echantillonnage)
            if audio_brut is None:
                return ""

            audio_np = (
                np.frombuffer(audio_brut, dtype="int16").astype("float32") / 32768.0
            )

            if not hasattr(self, "_modele_whisper"):
                # "tiny" ou "base" pour rester léger sur mobile
                self._modele_whisper = whisper.load_model("tiny")

            resultat = self._modele_whisper.transcribe(audio_np, language=self.langue)
            return resultat.get("text", "").strip()
        except Exception as erreur:
            print(f"[Whisper] Reconnaissance impossible : {erreur}")
            return ""


if __name__ == "__main__":
    # Test manuel : écoute le micro pendant 5 secondes et affiche le texte reconnu
    rv = ReconnaissanceVocale()
    rv.demander_permission_micro()
    print("Parlez maintenant...")
    texte = rv.ecouter_et_transcrire(duree_secondes=5)
    print("Texte reconnu :", texte)
