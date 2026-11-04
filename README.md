# dcoff

Tweak iOS (roothide) qui **neutralise Apple DeviceCheck** au niveau du daemon `devicecheckd`, hors du process de l'app cible.

> made with ❤️ by notaudren

## Pourquoi hors-process

Tout dylib injecté *dans* Snapchat est détectable (LC_ID_DYLIB / infoArray / scan mémoire → SS03). `dcoff` ne touche donc jamais l'app : il hooke `-[DCClientHandler fetchOpaqueBlobWithCompletion:]` **dans `devicecheckd`** et renvoie une erreur. L'app reçoit `(nil, error)` via XPC → bascule App Attest → le token DeviceCheck banni n'est jamais produit (pas de SS06), et le process de l'app reste 100 % propre.

- Filtre : `Executables = ("devicecheckd")` — injecté uniquement dans le daemon.
- Dépend d'`ellekit`. iPhone 8 / roothide, slice arm64e (fat arm64+arm64e).

## Repo Sileo

`docs/` est un repo APT prêt à héberger (GitHub Pages ou tout serveur HTTPS).

Ajouter dans Sileo : `https://<user>.github.io/dcoff/`

## Rebuild

- **Renommer / repack depuis le .deb existant** (sans device) : `python3 repack_deb.py`
- **Régénérer les métadonnées du repo** : `python3 build_repo.py`
- **Build from source on-device** (Theos) : `src/` + `deploy.py`

## Install / maintenance device

Après install Sileo, recharger le hook :

```
launchctl kickstart -k system/com.apple.devicecheckd
```

Règle : toujours laisser `dcoff` actif, DeviceCheck banni ou pas.
