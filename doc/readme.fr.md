# mupl - MangaDex Bulk Uploader
Upload de masse de dossiers et d'archives (.zip/.cbz) sur Mangadex rapidement et facilement.

README original:
[English](doc/readme.md)


## Table des matières
- [Guide d'utilisation](#guide-d'utilisation)
  - [Arguments de ligne de commande](#arguments-de-ligne-de-commande)
- [Format de nom des fichiers à upload](#format-de-nom-des-fichiers-à-upload)
  - [Format](#format)
  - [Paramètres du format](#paramètres-du-format)
  - [Formats d'image acceptés](#formats-d'image-acceptés)
- [Configuration](#configuration)
  - [Options](#options)
  - [Authentifiants MangaDex](#authentifiants-mangadex)
  - [Chemins d'accès](#chemins-d'accès)
- [Fichier associatif nom-ID](#fichier-associatif-nom-id)
  - [Exemples d'association](#exemples)
- [Contribution](#contribution)
- [Traduction](#traduction)


## Guide d'utilisation
Téléchargez la [dernière version](https://github.com/ArdaxHz/mupl/releases/latest) (le zip du code source), décompressez l'archive dans un dossier et ouvrez un terminal dans celui-ci.

Dans le terminal (bash, powershell, cmd) tapez `python mupl.py` pour lancer l'uploader.
Assurez vous d'avoir Python 3.9+ d'installé. Utilisez `python` pour Windows et `python3` pour Mac et Linux.

### Arguments de ligne de commande
Des arguments peuvent être ajoutés après la commande principale pour modifier le comportement du programme, exemple: `python mupl.py -u`.

##### Options:
- `--update` `-u` Désactive la recherche de mise à jour au lancement.
- `--verbose` `-v` Rend les messages et logs plus verbeux.
- `--threaded` `-t` Lance l'uploader en mode multithread. *Par défaut: False*

## Format de nom des fichiers à upload
#### Format
`manga_title [lang] - cXXX (vYY) (chapter_title) {publish_date} [group]`

#### Paramètres du format
- `manga_title` Titre du manga (identique à la clef dans `name_id_map.json`) ou l'ID MangaDex.
- `[lang]` Langue au format code ISO. *Omis pour l'anglais.*
- `cXXX` Numéro du chapitre. *Retirez le préfixe pour les oneshots, e.g. `cXXX` > `XXX`.*
- `(vYY)` Volume du chapitre. *Optionnel.*
- `(chapter_title)` Titre du chapitre. Remplacez chaque `?` présent dans le titre par `{question_mark}`. *Optionnel.*
- `{publish_date}` Date de publication ultérieure du chapitre du côté de MangaDex. ***DOIT** être au format `YYYY-MM-DDTHH-MM-SS` si inclus.* *Optionnel.*
- `[group]` Liste des noms ou des IDs des groupes. Utiliser le nom des groupes requiert de les associer à leur ID respectif dans `name_id_map.json`. *Chaque groupe doit être séparé par `+`.* *Optionnel.*

#### Formats d'image acceptés
- `png`
- `jpg`/`jpeg`
- `gif`
- `webp` *Sera converti soit en `png`, `jpg`, ou `gif` au cours de l'upload.*

## Configuration
Les options de configuration disponibles peuvent être modifiées dans le fichier `config.json`. C'est également l'endroit où indiquer vos authentifiants MangaDex (***obligatoires***).
Copiez le fichier `config.json.example` et retirez le suffixe `.example` pour en faire usage.

*Note: les valeurs JSON ne peuvent pas être vides. Utilisez (`null`) lorsqu'une valeur est censée être vide, une chaîne de caractères (`"username"`) pour les valeurs textuelles, et un nombre (`1`) pour les valeurs numériques.*


#### Options
- `number_of_images_upload` Nombre d'images à upload à la fois. *Par défaut: 10*
- `upload_retry` Nombre maximal de tentatives d'upload par chapitre et image. *Par défaut: 3*
- `ratelimit_time` Temps d'attente (en secondes) après chaque appel API. *Par défaut: 2*
- `max_log_days` Nombre de jours de conservation des logs. *Par défaut: 30*
- `group_fallback_id` ID de groupe subsidiaire si l'ID est absent du nom du fichier et de `name_id_map.json`. Laissez `null` pour n'indiquer aucun groupe. *Par défaut: null*
- `number_threads`: Nombre de threads pour l'upload d'images simultané. **Peut vous faire dépasser la fréquence limite de requêtes d'upload.** Minimum-maximum : 1-3. *Par défaut: 3*
- `language`: Langue utilisée pour les messages affichés sur le terminal. *Par défaut: null*

#### Authentifiants MangaDex
***Ces valeurs sont nécessaires pour utiliser l'uploader.***
- `mangadex_username` Nom d'utilisateur MangaDex.
- `mangadex_password` Mot de passe MangaDex.
- `client_id` ID du client pour l'API MangaDex.
- `client_secret` Secret du client pour l'API MangaDex.

#### Chemins d'accès
*Ces options peuvent être laissées telles quelles.*
- `name_id_map_file` Nom du fichier associatif nom-ID. *Par défaut: name_id_map.json*
- `uploads_folder` Dossier des chapitres à upload. *Par défaut: to_upload*
- `uploaded_files` Dossier où sont déplacés les chapitres uploadés. *Par défaut: uploaded*
- `mangadex_api_url` URL de l'API MangaDex. *Par défaut: https://api.mangadex.org*
- `mangadex_auth_url` URL d'authentification MangaDex. *Par défaut: https://auth.mangadex.org/realms/mangadex/protocol/openid-connect*
- `mdauth_path` Fichier dans lequel est conservé le token de session MangaDex. *Par défaut: .mdauth*

<details>
  <summary>Création d'un client API MangaDex</summary>

  ![Screenshot du mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_1.png?raw=true)
  ![Screenshot du mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_2.png?raw=true)
</details>
<br />


## Fichier associatif nom-ID
`name_id_map.json` a le format suivant:
```json
{
    "manga": {
        "hyakkano": "efb4278c-a761-406b-9d69-19603c5e4c8b"
    },
    "group": {
        "XuN": "b6d57ade-cab7-4be7-b2b8-be68484b3ad3"
    }
}
```
`manga` et `group` contiennent respectivement l'association des noms aux ID des manga et des groupes auxquels les chapitres à upload appartiennent. Ces noms doivent correspondre à ceux trouvés dans les noms des fichiers. Utilisez des noms en minuscules et sans espace pour éviter tout problème durant l'upload.

Chaque paire nom-ID doit être séparée d'une virgule en fin de ligne (sauf pour la dernière paire) et de deux points (`:`) entre le nom et l'ID.

#### Exemples

Prenons `hyakkano - c025 (v04) [XuN].cbz` comme chapitre à upload. Dans mon fichier `name_id_map.json`, j'aurai alors besoin de la clef `hyakkano` avec pour valeur `efb4278c-a761-406b-9d69-19603c5e4c8b`, qui est l'ID MangaDex du manga auquel appartient mon chapitre. J'aurai également la clef `XuN` dans la partie "group" avec la valeur `b6d57ade-cab7-4be7-b2b8-be68484b3ad3`, ID MangaDex du groupe en question.

Le programme cherchera par la suite dans ce fichier les clefs `hyakkano` et `XuN` et récupérera les IDs assignés.

Pour un fichier nommé `efb4278c-a761-406b-9d69-19603c5e4c8b [es] - 000 (Momi-san) [XuN+00e03853-1b96-4f41-9542-c71b8692033b]` : le programme utiliserait directement l'ID du manga présent dans le nom du fichier, la langue du chapitre serait l'espagnol avec le code `es`, le numéro du chapitre nul car il s'agit d'un oneshot (préfixe absent), de même pour le volume non indiqué, le titre `Momi-san`, et enfin le chapitre serait upload sous le groupe `XuN` avec pour ID `00e03853-1b96-4f41-9542-c71b8692033b`, récupéré du fichier `name_id_map.json`.



## Contribution
- Assurez vous qu'une issue similaire n'existe pas déjà avant d'en ouvrir une nouvelle.
- Vous êtes libre d'ouvrir une pull request si besoin mais formatez votre code avec Python Black (options par défaut) au préalable.

### Traduction
Deux fichiers sont à traduire : ce README et [mupl/loc/en.json](mupl/loc/en.json).

- Le README traduit doit être placé sous [doc](doc/) au format `readme.<>.md` avec la langue au format code ISO entre les points, exemple : `readme.pt-br.md`.
- Le fichier json traduit doit avoir la langue au format code ISO comme nom de fichier et être placé dans le dossier [mupl/loc/](mupl/loc/), par exemple : `pt-br.json`.

Mettez à jour le README original avec un lien vers celui-ci puis ouvrez une pull request avec vos changements.
