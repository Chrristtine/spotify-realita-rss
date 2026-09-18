import os
import html
import requests
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree


ARTIST_ID = "56DyVeJDf5P6envEFo6s7X"
ARTIST_URL = f"https://open.spotify.com/artist/{ARTIST_ID}"

# Discord role Fanoušci 🔔
ROLE_ID = "1531371818772861089"
ROLE_MENTION = f"<@&{ROLE_ID}>"

# Kontrola posledních 48 hodin
LOOKBACK_HOURS = 48

# 🧪 DOČASNÝ TEST
TEST_MODE = True
TEST_SONG = "afterlife"

CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]


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
    headers = {
        "Authorization": f"Bearer {token}"
    }

    releases = []

    # Pouze singly
    url = (
        f"https://api.spotify.com/v1/artists/{ARTIST_ID}/albums"
        "?include_groups=single&market=CZ&limit=10"
    )

    while url and len(releases) < 50:

        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        releases.extend(
            data.get("items", [])
        )

        url = data.get("next")


    # Odstranění duplicit
    unique = {
        item["id"]: item
        for item in releases
    }

    return sorted(
        unique.values(),
        key=lambda item: item.get(
            "release_date",
            "1900-01-01"
        ),
        reverse=True
    )


def parse_release_date(item):

    value = item.get(
        "release_date",
        ""
    )

    precision = item.get(
        "release_date_precision",
        "day"
    )

    try:

        if precision == "day":

            return datetime.strptime(
                value,
                "%Y-%m-%d"
            ).replace(
                tzinfo=timezone.utc
            )


        if precision == "month":

            return datetime.strptime(
                value,
                "%Y-%m"
            ).replace(
                tzinfo=timezone.utc
            )


        return datetime.strptime(
            value,
            "%Y"
        ).replace(
            tzinfo=timezone.utc
        )


    except ValueError:

        return datetime(
            1900,
            1,
            1,
            tzinfo=timezone.utc
        )


def get_recent_releases(releases):

    now = datetime.now(
        timezone.utc
    )

    cutoff = (
        now -
        timedelta(
            hours=LOOKBACK_HOURS
        )
    )

    recent = []

    for item in releases:

        release_date = parse_release_date(
            item
        )

        if release_date >= cutoff:

            recent.append(item)

    return recent


def get_track_from_single(
    token,
    album_id
):

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = (
        f"https://api.spotify.com/v1/albums/"
        f"{album_id}/tracks"
        "?market=CZ&limit=1"
    )

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    tracks = response.json().get(
        "items",
        []
    )

    if tracks:

        return tracks[0]

    return None


def make_rss(
    releases,
    token
):

    rss = Element(
        "rss",
        {
            "version": "2.0",

            "xmlns:atom":
                "http://www.w3.org/2005/Atom",

            "xmlns:content":
                "http://purl.org/rss/1.0/modules/content/",

            "xmlns:media":
                "http://search.yahoo.com/mrss/",
        },
    )


    channel = SubElement(
        rss,
        "channel"
    )


    SubElement(
        channel,
        "title"
    ).text = (
        "Realita – nové skladby na Spotify"
    )


    SubElement(
        channel,
        "link"
    ).text = ARTIST_URL


    SubElement(
        channel,
        "description"
    ).text = (
        "Nové skladby interpreta Realita na Spotify."
    )


    SubElement(
        channel,
        "language"
    ).text = "cs-CZ"


    SubElement(
        channel,
        "ttl"
    ).text = "60"


    for item in releases:

        item_el = SubElement(
            channel,
            "item"
        )


        title = item.get(
            "name",
            "Nová skladba"
        )


        release_date = parse_release_date(
            item
        )


        # Cover ze Spotify
        image = ""

        if item.get("images"):

            image = item["images"][0].get(
                "url",
                ""
            )


        # Najdeme konkrétní skladbu
        track = get_track_from_single(
            token,
            item["id"]
        )


        if track:

            spotify_url = track[
                "external_urls"
            ]["spotify"]


            title = track.get(
                "name",
                title
            )


            track_album = track.get(
                "album",
                {}
            )


            # Cover konkrétní skladby
            if track_album.get("images"):

                image = track_album[
                    "images"
                ][0].get(
                    "url",
                    image
                )


            # 🧪 TEST GUID
            guid = (
                f"spotify:track:"
                f"{track['id']}:TEST"
            )


        else:

            spotify_url = item[
                "external_urls"
            ]["spotify"]


            guid = (
                f"spotify:album:"
                f"{item['id']}:TEST"
            )


        # Název
        SubElement(
            item_el,
            "title"
        ).text = title


        # Přímý odkaz na skladbu
        SubElement(
            item_el,
            "link"
        ).text = spotify_url


        # Jedinečné ID
        SubElement(
            item_el,
            "guid",
            {
                "isPermaLink": "false"
            }
        ).text = guid


        # Datum vydání
        SubElement(
            item_el,
            "pubDate"
        ).text = format_datetime(
            release_date
        )


        # Obsah pro MEE6
        description = (

            f'<p>'
            f'🎵 <strong>'
            f'Nová skladba od Realita!'
            f'</strong>'
            f'</p>'

            f'<p>'
            f'<strong>'
            f'{html.escape(title)}'
            f'</strong>'
            f'</p>'

            f'<p>'
            f'{ROLE_MENTION}'
            f'</p>'

            f'<p>'
            f'<a href="{html.escape(spotify_url)}">'
            f'🎧 Poslechnout na Spotify'
            f'</a>'
            f'</p>'
        )


        # Cover
        if image:

            description = (

                f'<p>'
                f'<img src="{html.escape(image)}" '
                f'alt="{html.escape(title)}" />'
                f'</p>'

                +

                description
            )


        SubElement(
            item_el,
            "description"
        ).text = description


        SubElement(
            item_el,
            "content:encoded"
        ).text = description


        # Media obrázek
        if image:

            media_content = SubElement(
                item_el,
                "media:content",
                {
                    "url": image,
                    "type": "image/jpeg",
                    "medium": "image",
                },
            )

            media_content.set(
                "width",
                "640"
            )

            media_content.set(
                "height",
                "640"
            )


    ElementTree(
        rss
    ).write(
        "rss.xml",
        encoding="utf-8",
        xml_declaration=True
    )


if __name__ == "__main__":

    token = get_token()


    # Všechny singly
    all_releases = get_releases(
        token
    )


    # Normální 48h výběr
    recent_releases = get_recent_releases(
        all_releases
    )


    # 🧪 TEST:
    # Vynutíme afterlife v RSS,
    # i když už není v posledních 48 hodinách.
    if TEST_MODE:

        for release in all_releases:

            if (
                release.get("name", "").lower()
                == TEST_SONG.lower()
            ):

                if release not in recent_releases:

                    recent_releases.insert(
                        0,
                        release
                    )

                break


    print(
        f"Spotify obsahuje "
        f"{len(all_releases)} release(s)."
    )


    print(
        f"Za posledních "
        f"{LOOKBACK_HOURS} hodin: "
        f"{len(recent_releases)} release(s)."
    )


    if TEST_MODE:

        print(
            f"🧪 TEST MODE: "
            f"{TEST_SONG}"
        )


    make_rss(
        recent_releases,
        token
    )
