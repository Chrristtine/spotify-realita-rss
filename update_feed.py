import os
import html
import requests
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree

ARTIST_ID = "56DyVeJDf5P6envEFo6s7X"
ARTIST_URL = f"https://open.spotify.com/artist/{ARTIST_ID}"

# Discord role Fanoušci 🔔
ROLE_ID = "1531371818772861089"
ROLE_MENTION = f"<@&{ROLE_ID}>"

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
    headers = {"Authorization": f"Bearer {token}"}
    releases = []

    url = (
        f"https://api.spotify.com/v1/artists/{ARTIST_ID}/albums"
        "?include_groups=single&market=CZ&limit=10"
    )

    while url and len(releases) < 50:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        releases.extend(data.get("items", []))
        url = data.get("next")

    unique = {item["id"]: item for item in releases}

    def release_date(item):
        parts = item.get("release_date", "1900-01-01").split("-")
        try:
            return tuple(int(x) for x in parts)
        except ValueError:
            return (1900, 1, 1)

    return sorted(unique.values(), key=release_date, reverse=True)[:20]


def parse_date(item):
    value = item.get("release_date", "")
    precision = item.get("release_date_precision", "day")

    if precision == "day":
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    if precision == "month":
        return datetime.strptime(value, "%Y-%m").replace(tzinfo=timezone.utc)

    return datetime.strptime(value, "%Y").replace(tzinfo=timezone.utc)


def make_rss(releases):
    rss = Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:atom": "http://www.w3.org/2005/Atom",
            "xmlns:content": "http://purl.org/rss/1.0/modules/content/",
        },
    )

    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = "Realita – nové releasy na Spotify"
    SubElement(channel, "link").text = ARTIST_URL
    SubElement(channel, "description").text = (
        "Nové skladby interpreta Realita na Spotify."
    )
    SubElement(channel, "language").text = "cs-CZ"
    SubElement(channel, "ttl").text = "60"

    for item in releases:
        item_el = SubElement(channel, "item")

        title = item.get("name", "Nový release")
        spotify_url = item["external_urls"]["spotify"]
        release_date = parse_date(item)

        image = ""
        if item.get("images"):
            image = item["images"][0].get("url", "")

        SubElement(item_el, "title").text = title
        SubElement(item_el, "link").text = spotify_url
        SubElement(item_el, "guid", {"isPermaLink": "false"}).text = (
            f"spotify:album:{item['id']}"
        )
        SubElement(item_el, "pubDate").text = format_datetime(release_date)

        description = (
            f'<p>🎵 <strong>Nová skladba od Realita!</strong></p>'
            f'<p><strong>{html.escape(title)}</strong></p>'
            f'<p>{ROLE_MENTION}</p>'
            f'<p><a href="{html.escape(spotify_url)}">'
            f'🎧 Poslechnout na Spotify'
            f'</a></p>'
        )

        if image:
            description = (
                f'<p><img src="{html.escape(image)}" '
                f'alt="{html.escape(title)}" /></p>'
                + description
            )

        SubElement(item_el, "description").text = description
        SubElement(item_el, "content:encoded").text = description

    ElementTree(rss).write(
        "rss.xml",
        encoding="utf-8",
        xml_declaration=True
    )


if __name__ == "__main__":
    token = get_token()
    releases = get_releases(token)
    make_rss(releases)
    print(f"Generated RSS with {len(releases)} releases.")
