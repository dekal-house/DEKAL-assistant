# 🤖 Assistant Vocal Intelligent

Application Android développée en **Python + Kivy**, capable d'écouter la voix
de l'utilisateur, de comprendre ses commandes et d'exécuter des actions
directement sur le téléphone — **entièrement hors ligne**.

---

## 🎯 Fonctionnement (v1 — version fonctionnelle de base)

```
Microphone → Reconnaissance vocale (Vosk) → Analyse de la commande → Action (flash ON/OFF)
```

Exemple :

```
Utilisateur : "Allume la lampe"
→ commande = "allume la lampe"
→ action    = ACTIVER_FLASH
→ réponse   = "Lampe activée ✅"
```

Cette première version couvre le flux complet demandé : capter la voix,
la transcrire, comprendre l'intention, puis agir (allumer/éteindre la
lampe torche). Les fonctionnalités suivantes (Bluetooth, applications,
volume, GPS, SMS...) sont déjà codées dans `actions_android.py` et
`base_commandes.json`, prêtes à être activées/étendues.

---

## 📁 Structure du projet

```
AssistantVocal/
│
├── main.py                   # Point d'entrée de l'application
├── interface.py               # Interface graphique Kivy
├── reconnaissance_vocale.py   # Capture micro + voix → texte (Vosk / Whisper)
├── analyse_commandes.py       # Moteur de compréhension (texte → intention)
├── actions_android.py         # Exécution réelle des actions (Pyjnius/Plyer)
├── base_commandes.json        # Base de phrases ↔ actions, personnalisable
├── requirements.txt           # Dépendances Python
├── buildozer.spec             # Configuration de compilation Android (APK)
└── README.md
```

---

## 🧠 Fonctionnalités

| Domaine | Détail |
|---|---|
| Écoute vocale | Demande la permission micro, capture l'audio, transcrit hors ligne avec Vosk (repli Whisper si besoin) |
| Compréhension | Reconnaît une intention à partir du texte (correspondance directe + similarité floue) |
| Actions téléphone | Flash, ouverture d'applications, Bluetooth, volume, GPS, SMS, notifications |
| Interface | Bouton "🎤 Écouter", zone commande détectée, zone réponse, indicateur micro actif/inactif |
| Personnalisation | Ajout de nouvelles phrases → action via `MoteurCommandes.ajouter_commande()` |
| Confidentialité | Tout le traitement vocal est local ; aucune donnée envoyée sur Internet |

---

## ⚙️ Installation (développement desktop)

```bash
pip install -r requirements.txt
```

Téléchargez un modèle Vosk français léger (ex. `vosk-model-small-fr-0.22`)
sur https://alphacephei.com/vosk/models, décompressez-le, puis renommez
le dossier obtenu en `modele_vosk/` à la racine du projet.

Lancez ensuite :

```bash
python main.py
```

> Sur desktop, les actions Android (flash, Bluetooth...) sont simulées
> par de simples messages dans la console — c'est normal, ces API
> n'existent que sur un vrai téléphone.

---

## 📱 Compilation en APK Android

Le projet est prêt pour [Buildozer](https://buildozer.readthedocs.io/) :

```bash
pip install buildozer cython
buildozer android debug
```

L'APK généré se trouve ensuite dans `bin/`. Pensez à :
1. Placer le dossier `modele_vosk/` dans le projet avant de compiler.
2. Décommenter la ligne `source.include_patterns = modele_vosk/*`
   dans `buildozer.spec` pour l'inclure dans l'APK.
3. Ajouter une icône `icon.png` à la racine du projet.

---

## ➕ Ajouter une commande personnalisée

```python
from analyse_commandes import MoteurCommandes

moteur = MoteurCommandes()
moteur.ajouter_commande(
    phrase="mets de la musique",
    action="OUVRIR_APPLICATION",
    parametre="com.spotify.music",
    reponse="Ouverture de Spotify 🎵",
)
```

La nouvelle phrase est aussitôt sauvegardée dans `base_commandes.json`
et reconnue lors des prochaines écoutes.

---

## 🗺️ Feuille de route (améliorations progressives)

- [x] v1 : Micro → Vosk → Analyse → Flash ON/OFF
- [x] v2 : Ouverture d'applications, Bluetooth, volume
- [x] v3 : GPS, envoi de message, notifications
- [ ] v4 : Apprentissage de nouvelles commandes directement depuis l'interface (sans passer par le code)
- [ ] v5 : Intégration OpenCV / TensorFlow Lite pour des fonctions intelligentes (reconnaissance d'objets, etc.)
- [ ] v6 : Synthèse vocale (réponse parlée de l'assistant, hors ligne)

---

## 🔒 Confidentialité & sécurité

- Reconnaissance vocale **100 % locale** (Vosk / Whisper embarqués).
- Aucune commande ni conversation n'est envoyée sur un serveur.
- Toutes les permissions Android (micro, caméra, Bluetooth, position,
  SMS) sont demandées explicitement à l'utilisateur avant utilisation.

---

## 🛠️ Technologies utilisées

- **Python 3**
- **Kivy** — interface graphique
- **Pyjnius** — appels aux API Java/Android natives
- **Plyer** — accès multiplateforme au matériel du téléphone
- **Vosk** — reconnaissance vocale hors ligne (moteur principal)
- **Whisper** — reconnaissance vocale alternative (secours, plus précise)
- **Buildozer** — compilation du projet Python en APK Android
