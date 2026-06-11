# PoC — Vol de jeton de session via deep link (Android)

> **Démonstration éducative.** L'entreprise « Formae », ses utilisateurs et ses
> données sont entièrement fictifs. Le jeton manipulé est un faux et l'application
> est une app de test, sans aucune cible réelle. Ce dépôt illustre une classe de
> vulnérabilité à des fins pédagogiques et de sensibilisation, à n'utiliser que
> dans un cadre autorisé.

Démonstration jouable de la faille décrite dans [un article du blog HDW Sec](https://hdwsec.fr/fr/blog/) :
un simple lien suffit à exfiltrer le jeton de session d'un utilisateur.

C'est une **ressource technique pour les curieux**, pas un produit. Tout est
factice : application de démonstration, jeton factice, aucune cible réelle.

## Lancer la démo (parcours guidé)

Une seule commande côté machine, tout le reste se passe **sur le téléphone**.

1. **Une fois**, construire l'APK (il faut Docker, voir plus bas) :
   ```bash
   ./build-apk.sh
   ```
2. Lancer le serveur :
   ```bash
   uv run receiver-server.py
   ```
   Il affiche l'URL à ouvrir (ex. `http://192.168.1.21:8000/`).
3. Sur un téléphone **Android**, sur le **même wifi**, ouvrir cette URL dans
   **Chrome** et se laisser guider :
   - télécharger puis installer l'app de démo (autoriser les sources inconnues),
   - confirmer « J'ai installé l'app »,
   - sur la fausse boîte mail, taper **« Voir mon certificat »**.

   > Ouvrez bien dans **Chrome**. Le lien piégé est un lien `intent://` : Samsung
   > Internet ne le lance pas, et Firefox renvoie vers le Play Store. Hors Chrome,
   > le bouton « Voir mon certificat » ne déclenchera rien.

L'app s'ouvre, déroule la chaîne, et le jeton est exfiltré sur le serveur. La
page mail bascule toute seule en **« Jeton exfiltré »**, et le terminal logue la
requête avec l'en-tête `Authorization: Bearer ...`. Un bouton « Relancer la
démo » réarme un nouveau passage sans relancer le serveur.

**Si la page ne charge pas sur le téléphone**, deux blocages classiques alors
que le wifi est pourtant le bon. Le pare-feu macOS peut demander d'autoriser
Python à accepter les connexions entrantes au premier lancement (cliquer
« Autoriser », et comme on passe par `uv`, c'est l'interpréteur de uv qu'il faut
autoriser, pas le Python système). Et certains réseaux, surtout les wifi
« invité », activent l'isolation client qui coupe la communication entre
appareils du même réseau : dans ce cas, utiliser un wifi domestique ou un
partage de connexion.

## Ce que ça reproduit

La même chaîne que celle décrite dans l'article, en trois temps :

1. **Redirection ouverte** — la route `/api/track/click` renvoie le paramètre
   `url` sans valider le domaine (`VulnerableRouter.resolveOpenRedirect`).
2. **Route de téléchargement** — elle reconstruit l'URL de l'API mais en
   recyclant le domaine d'entrée, devenu celui de l'attaquant
   (`VulnerableRouter.resolveCertificateDownload`).
3. **Couche réseau** — elle attache `Authorization: Bearer <jeton>` à **toutes**
   les requêtes sortantes, y compris celle qui part chez l'attaquant
   (`ApiClient.download`). Le correctif (allowlist de domaine) est en commentaire
   juste au-dessus du code vulnérable.

> Le lien piégé utilise un scheme maison `formae-demo://` (via une URL
> `intent://`, la façon fiable de lancer une app depuis Chrome Android). L'article
> décrit le même mécanisme avec un Universal Link `https://`. La faille démontrée
> est identique, on évite juste d'avoir à héberger un fichier de vérification.

## Construire l'APK (sans Android Studio)

`./build-apk.sh` fait tout dans Docker (JDK + cmdline-tools Android + Gradle) et
sort `formae-poc.apk`. Le build est forcé en `linux/amd64` : l'outil `aapt2`
n'existe qu'en x86_64 et ne tourne pas sur une image arm64 (Mac Apple Silicon).

<details>
<summary>Sans Docker (alternative)</summary>

Installer les `cmdline-tools` Android + Gradle, puis `gradle assembleDebug`.
L'APK sort dans `app/build/outputs/apk/debug/app-debug.apk`. Juste un JDK 17, pas
d'Android Studio.
</details>

## Fichiers

| Fichier | Rôle |
| --- | --- |
| `receiver-server.py` | Serveur guidé : onboarding, téléchargement de l'APK, fausse boîte mail, réception et affichage du jeton exfiltré |
| `app/src/main/java/.../VulnerableRouter.kt` | Les 2 défauts enchaînés (open redirect + recyclage du domaine) |
| `app/src/main/java/.../ApiClient.kt` | La couche réseau qui attache le Bearer partout (+ le correctif en commentaire) |
| `app/src/main/java/.../MainActivity.kt` | Reçoit le deep link, déroule la chaîne, affiche tout |
| `app/src/main/AndroidManifest.xml` | Déclare le deep link `formae-demo://` |
| `Dockerfile` / `build-apk.sh` | Build de l'APK sans Android Studio |
