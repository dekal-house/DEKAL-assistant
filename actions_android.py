# -*- coding: utf-8 -*-
"""
actions_android.py
====================
Contient toutes les fonctions capables d'agir réellement sur le téléphone
Android : flash, applications, Bluetooth, volume, GPS, SMS, notifications.

Utilise :
- Pyjnius pour appeler directement les API Java natives d'Android
- Plyer comme couche d'abstraction multiplateforme quand c'est possible

Chaque fonction est protégée par un try/except : si le code tourne sur
desktop (hors Android) pendant le développement, un message explicatif
est affiché à la place d'un plantage.
"""

try:
    from jnius import autoclass, cast
    SUR_ANDROID = True
except Exception:
    SUR_ANDROID = False


def _obtenir_activite_courante():
    """Retourne l'activité Android courante (nécessaire pour la plupart des appels natifs)."""
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    return PythonActivity.mActivity


# ----------------------------------------------------------------------
# 1) FLASH / LAMPE TORCHE
# ----------------------------------------------------------------------
def activer_flash():
    """Allume le flash de la caméra arrière."""
    if not SUR_ANDROID:
        print("[Simulation] Flash activé 🔦")
        return True
    try:
        activite = _obtenir_activite_courante()
        Context = autoclass("android.content.Context")
        camera_manager = activite.getSystemService(Context.CAMERA_SERVICE)
        camera_id = camera_manager.getCameraIdList()[0]
        camera_manager.setTorchMode(camera_id, True)
        return True
    except Exception as erreur:
        print(f"[Erreur] Impossible d'activer le flash : {erreur}")
        return False


def desactiver_flash():
    """Éteint le flash de la caméra arrière."""
    if not SUR_ANDROID:
        print("[Simulation] Flash désactivé 🔦")
        return True
    try:
        activite = _obtenir_activite_courante()
        Context = autoclass("android.content.Context")
        camera_manager = activite.getSystemService(Context.CAMERA_SERVICE)
        camera_id = camera_manager.getCameraIdList()[0]
        camera_manager.setTorchMode(camera_id, False)
        return True
    except Exception as erreur:
        print(f"[Erreur] Impossible de désactiver le flash : {erreur}")
        return False


# ----------------------------------------------------------------------
# 2) OUVRIR UNE APPLICATION
# ----------------------------------------------------------------------
def ouvrir_application(nom_paquet):
    """
    Ouvre une application Android à partir de son nom de paquet
    (ex : "com.google.android.youtube").
    """
    if not SUR_ANDROID:
        print(f"[Simulation] Ouverture de l'application : {nom_paquet}")
        return True
    try:
        activite = _obtenir_activite_courante()
        gestionnaire_paquets = activite.getPackageManager()
        intention = gestionnaire_paquets.getLaunchIntentForPackage(nom_paquet)
        if intention:
            activite.startActivity(intention)
            return True
        print(f"[Erreur] Application non trouvée : {nom_paquet}")
        return False
    except Exception as erreur:
        print(f"[Erreur] Impossible d'ouvrir l'application : {erreur}")
        return False


# ----------------------------------------------------------------------
# 3) BLUETOOTH
# ----------------------------------------------------------------------
def activer_bluetooth():
    """Active le Bluetooth du téléphone."""
    if not SUR_ANDROID:
        print("[Simulation] Bluetooth activé 📶")
        return True
    try:
        BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
        adaptateur = BluetoothAdapter.getDefaultAdapter()
        if adaptateur and not adaptateur.isEnabled():
            adaptateur.enable()
        return True
    except Exception as erreur:
        print(f"[Erreur] Impossible d'activer le Bluetooth : {erreur}")
        return False


def desactiver_bluetooth():
    """Désactive le Bluetooth du téléphone."""
    if not SUR_ANDROID:
        print("[Simulation] Bluetooth désactivé 📶")
        return True
    try:
        BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
        adaptateur = BluetoothAdapter.getDefaultAdapter()
        if adaptateur and adaptateur.isEnabled():
            adaptateur.disable()
        return True
    except Exception as erreur:
        print(f"[Erreur] Impossible de désactiver le Bluetooth : {erreur}")
        return False


# ----------------------------------------------------------------------
# 4) VOLUME
# ----------------------------------------------------------------------
def _regler_volume(delta):
    """Modifie le volume média du téléphone (+1 ou -1 cran)."""
    if not SUR_ANDROID:
        print(f"[Simulation] Volume ajusté ({'+' if delta > 0 else ''}{delta})")
        return True
    try:
        activite = _obtenir_activite_courante()
        Context = autoclass("android.content.Context")
        AudioManager = autoclass("android.media.AudioManager")
        gestionnaire_audio = activite.getSystemService(Context.AUDIO_SERVICE)
        direction = AudioManager.ADJUST_RAISE if delta > 0 else AudioManager.ADJUST_LOWER
        gestionnaire_audio.adjustStreamVolume(
            AudioManager.STREAM_MUSIC, direction, AudioManager.FLAG_SHOW_UI
        )
        return True
    except Exception as erreur:
        print(f"[Erreur] Impossible de modifier le volume : {erreur}")
        return False


def augmenter_volume():
    return _regler_volume(1)


def diminuer_volume():
    return _regler_volume(-1)


# ----------------------------------------------------------------------
# 5) POSITION GPS (via Plyer, multiplateforme)
# ----------------------------------------------------------------------
def obtenir_position_gps(callback_succes=None, callback_erreur=None):
    """
    Démarre la localisation GPS. Les résultats arrivent de façon
    asynchrone via callback_succes(latitude, longitude, **kwargs).
    """
    try:
        from plyer import gps

        def _defaut_succes(**kwargs):
            print(f"[GPS] Position reçue : {kwargs}")

        def _defaut_erreur(message):
            print(f"[GPS] Erreur : {message}")

        gps.configure(
            on_location=callback_succes or _defaut_succes,
            on_status=lambda **kw: None,
        )
        gps.start(minTime=1000, minDistance=1)
        return True
    except Exception as erreur:
        print(f"[Erreur] GPS indisponible : {erreur}")
        if callback_erreur:
            callback_erreur(str(erreur))
        return False


# ----------------------------------------------------------------------
# 6) ENVOI DE MESSAGE (SMS)
# ----------------------------------------------------------------------
def envoyer_message(numero, texte):
    """Ouvre l'application SMS avec le message pré-rempli (nécessite SEND_SMS)."""
    if not SUR_ANDROID:
        print(f"[Simulation] Message à {numero} : {texte}")
        return True
    try:
        from plyer import sms
        sms.send(recipient=numero, message=texte)
        return True
    except Exception as erreur:
        print(f"[Erreur] Impossible d'envoyer le message : {erreur}")
        return False


# ----------------------------------------------------------------------
# 7) NOTIFICATIONS
# ----------------------------------------------------------------------
def envoyer_notification(titre, message):
    """Affiche une notification système."""
    try:
        from plyer import notification
        notification.notify(title=titre, message=message, timeout=5)
        return True
    except Exception as erreur:
        print(f"[Erreur] Impossible d'envoyer la notification : {erreur}")
        return False


# ----------------------------------------------------------------------
# TABLE DE DISPATCH : relie un code d'action (venant de analyse_commandes.py)
# à la fonction Python correspondante.
# ----------------------------------------------------------------------
def executer_action(action, parametre=None):
    """
    Point d'entrée unique utilisé par l'interface : reçoit le code
    d'action retourné par le moteur d'analyse et exécute la bonne
    fonction Android.
    """
    dispatch = {
        "ACTIVER_FLASH": lambda: activer_flash(),
        "DESACTIVER_FLASH": lambda: desactiver_flash(),
        "OUVRIR_APPLICATION": lambda: ouvrir_application(parametre),
        "ACTIVER_BLUETOOTH": lambda: activer_bluetooth(),
        "DESACTIVER_BLUETOOTH": lambda: desactiver_bluetooth(),
        "AUGMENTER_VOLUME": lambda: augmenter_volume(),
        "DIMINUER_VOLUME": lambda: diminuer_volume(),
        "POSITION_GPS": lambda: obtenir_position_gps(),
        "ENVOYER_MESSAGE": lambda: envoyer_notification(
            "Message", "Fonction à compléter avec un numéro de destinataire"
        ),
    }

    fonction = dispatch.get(action)
    if fonction is None:
        print(f"[Actions] Action inconnue ou non implémentée : {action}")
        return False
    return fonction()
