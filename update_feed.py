import os
import html
import requests
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree

ARTIST_ID = "56DyVeJDf5P6envEFo6s7X"
ARTIST_URL = f"https://open.spotify.com/artist/{ARTIST_ID}"

CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]

# =========================
# NASTAVENÍ
# =========================

LOOKBACK_HOURS = 48

# Nech TRUE pro jednorázový test Afterlife.
# Po úspěšném testu změň na FALSE.
TEST_MODE = True

TEST_SONG = "afterlife"

ROLE_MENTION = "<@&1531371818772861089>"

# Verze GUID – díky tomu se test a následná ostrá verze
# nepošlou MEE6 dvakrát.
GUID_VERSION = "v2"


def get_token():
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_releases(token):
    headers = {"Authorization": f"Bearer {token}"}

    releases = []

    url = (
        f"https://api.spotify.com/v1/artists/{ARTIST_ID}/albums"
        "?include_groups=single&market=CZ&limit=50"
    )

    while url and len(releases) < 50:
        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        releases.extend(data.get("items", []))
        url = data.get("next")

    unique = {}

    for item in releases:
        unique[item["id"]] = item

    return list(unique.values())


def parse_date(item):
    value = item.get("release_date", "")
    precision = item.get("release_date_precision", "day")

    try:
        if precision == "day":
            return datetime.strptime(
                value,
                "%Y-%m-%d",
            ).replace(tzinfo=timezone.utc)

        if precision == "month":
            return datetime.strptime(
                value,
                "%Y-%m",
            ).replace(tzinfo=timezone.utc)

        return datetime.strptime(
            value,
            "%Y",
        ).replace(tzinfo=timezone.utc)

    except ValueError:
        return datetime(1900, 1, 1, tzinfo=timezone.utc)


def get_track_from_single(token, album_id):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = (
        f"https://api.spotify.com/v1/albums/"
        f"{album_id}/tracks?market=CZ&limit=1"
    )

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    items = response.json().get("items", [])

    if not items:
        return None

    return items[0]


def make_rss(token, releases):

    now = datetime.now(timezone.utc)

    rss = Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:atom": "http://www.w3.org/2005/Atom",
            "xmlns:content": "http://purl.org/rss/1.0/modules/content/",
            "xmlns:media": "http://search.yahoo.com/mrss/",
        },
    )

    channel = SubElement(rss, "channel")

    SubElement(
        channel,
        "title",
    ).text = "Realita – nové skladby na Spotify"

    SubElement(
        channel,
        "link",
    ).text = ARTIST_URL

    SubElement(
        channel,
        "description",
    ).text = (
        "Nové skladby interpreta Realita na Spotify."
    )

    SubElement(
        channel,
        "language",
    ).text = "cs-CZ"

    SubElement(
        channel,
        "ttl",
    ).text = "60"

    found_test_song = False
    items = []

    # ---------------------------------
    # Běžné releasy za posledních 48 hodin
    # ---------------------------------

    for release in releases:

        release_date = parse_date(release)

        age_hours = (
            now - release_date
        ).total_seconds() / 3600

        if age_hours <= LOOKBACK_HOURS:

            track = get_track_from_single(
                token,
                release["id"],
            )

            if track:
                items.append(
                    (
                        release,
                        track,
                    )
                )

                if (
                    track["name"].lower()
                    == TEST_SONG.lower()
                ):
                    found_test_song = True

    # ---------------------------------
    # TEST AFTERLIFE
    # ---------------------------------

    if TEST_MODE and not found_test_song:

        for release in releases:

            track = get_track_from_single(
                token,
                release["id"],
            )

            if not track:
                continue

            if (
                track["name"].lower()
                == TEST_SONG.lower()
            ):

                items.append(
                    (
                        release,
                        track,
                    )
                )

                break

    # ---------------------------------
    # Vytvoření RSS položek
    # ---------------------------------

    for release, track in items:

        title = track.get(
            "name",
            release.get(
                "name",
                "Nový release",
            ),
        )

        track_id = track["id"]

        # ---------------------------------
        # DŮLEŽITÉ:
        # Tohle už NENÍ Spotify URL.
        # Díky tomu by se neměl načítat Joe Rogan preview.
        # ---------------------------------

        go_url = (
            "https://chrristtine.github.io/"
            "spotify-realita-rss/go.html"
            f"?track={track_id}"
        )

        # GUID zůstává stejný v testu i po vypnutí TEST_MODE
        guid = (
            f"spotify:track:{track_id}:"
            f"{GUID_VERSION}"
        )

        item_el = SubElement(
            channel,
            "item",
        )

        # Ping + hype přímo v TITLE
        SubElement(
            item_el,
            "title",
        ).text = (
            f"{ROLE_MENTION} "
            f"🔥 REALITA NAHRÁLA NOVÝ BANGER! "
            f"🎵 {title}"
        )

        # Už NENÍ Spotify URL
        SubElement(
            item_el,
            "link",
        ).text = go_url

        SubElement(
            item_el,
            "guid",
            {
                "isPermaLink": "false"
            },
        ).text = guid

        SubElement(
            item_el,
            "pubDate",
        ).text = format_datetime(
            parse_date(release)
        )

        # ---------------------------------
        # COVER
        # ---------------------------------

        image = ""

        if release.get("images"):
            image = release["images"][0].get(
                "url",
                ""
            )

        # ---------------------------------
        # TEXT
        # ---------------------------------

        description = (
            f'<p><strong>'
            f'🔥 REALITA NAHRÁLA NOVÝ BANGER!'
            f'</strong></p>'

            f'<p>🎵 <strong>'
            f'{html.escape(title)}'
            f'</strong></p>'

            f'<p>🏃💨 Utíkej si ho poslechnout!</p>'

            f'<p>'
            f'<a href="{html.escape(go_url)}">'
            f'🎧 Poslechnout na Spotify'
            f'</a>'
            f'</p>'
        )

        # Cover přidáme jako obrázek do RSS
        if image:

            description = (
                f'<p>'
                f'<img src="{html.escape(image)}" '
                f'alt="{html.escape(title)}" />'
                f'</p>'
                + description
            )

        SubElement(
            item_el,
            "description",
        ).text = description

        SubElement(
            item_el,
            "content:encoded",
        ).text = description

        # RSS media image
        if image:

            SubElement(
                item_el,
                "media:content",
                {
                    "url": image,
                    "type": "image/jpeg",
                    "medium": "image",
                    "width": "640",
                    "height": "640",
                },
            )

    tree = ElementTree(rss)

    tree.write(
        "rss.xml",
        encoding="utf-8",
        xml_declaration=True,
    )


if __name__ == "__main__":

    token = get_token()

    releases = get_releases(token)

    make_rss(
        token,
        releases,
    )

    print(
        "RSS successfully generated."
    )
