[README.md](https://github.com/user-attachments/files/32396462/README.md)
# Spotify → RSS feed pro interpreta Realita

Tento projekt vytvoří RSS feed pro nové releasy interpreta Realita na Spotify.

Spotify Artist ID:
`56DyVeJDf5P6envEFo6s7X`

Výsledný feed bude:
`https://TVUJ-GITHUB-UCET.github.io/NAZEV-REPO/rss.xml`

## Co to dělá

GitHub Actions každou hodinu:
1. přihlásí se ke Spotify Web API pomocí Client Credentials,
2. načte singly a alba interpreta,
3. vytvoří `rss.xml`,
4. nasadí ho přes GitHub Pages.

Do MEE6 pak vložíš URL `rss.xml`.

## Nastavení

### 1. Vytvoř Spotify Developer App

Otevři Spotify Developer Dashboard:
https://developer.spotify.com/dashboard

Vytvoř novou App a zkopíruj:
- Client ID
- Client Secret

Redirect URI pro tento projekt nepotřebuješ, protože používá Client Credentials.

### 2. Nahraj tento projekt na GitHub

Vytvoř nový veřejný GitHub repository, například:

`spotify-realita-rss`

Nahraj všechny soubory z tohoto projektu.

### 3. Přidej Secrets

V GitHubu otevři:

Settings → Secrets and variables → Actions → New repository secret

Vytvoř:

`SPOTIFY_CLIENT_ID`

a jako hodnotu vlož Spotify Client ID.

Potom:

`SPOTIFY_CLIENT_SECRET`

a vlož Spotify Client Secret.

Secret nikdy nedávej přímo do kódu.

### 4. Zapni GitHub Pages

GitHub:
Settings → Pages

Jako Source zvol:
`GitHub Actions`

Potom spusť workflow:
Actions → Spotify RSS → Run workflow

Po dokončení bude feed přibližně zde:

`https://TVUJ-UCET.github.io/spotify-realita-rss/rss.xml`

### 5. MEE6

V MEE6 → RSS Feeds → New RSS feed

Do `RSS Link` vlož URL:

`https://TVUJ-UCET.github.io/spotify-realita-rss/rss.xml`

A vyber Discord kanál.

## Poznámka

Feed je nastavený na singly + alba. Pokud chceš pouze jednotlivé nové skladby, změň v `update_feed.py`:

`include_groups=album,single`

na:

`include_groups=single`

Spotify API vrací metadata o vydáních; tento projekt nestahuje ani neposkytuje hudební soubory.
