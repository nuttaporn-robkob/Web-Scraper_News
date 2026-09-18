import requests
import xml.etree.ElementTree as ET
import sqlite3
import re
from html import unescape
from bs4 import BeautifulSoup

rss_urls = [
    {
        "url": "https://www.investing.com/rss/news.rss",
        "category": "Finance"
    },
    {
        "url": "https://feeds.bbci.co.uk/news/rss.xml",
        "category": "General News"
    },
    {
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "category": "World News"
    },
    {
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "category": "World News"
    },
    {
        "url": "https://www.theguardian.com/world/rss",
        "category": "World News"
    },
    {
        "url": "https://feeds.npr.org/1001/rss.xml",
        "category": "General News"
    },
    {
        "url": "https://www.france24.com/en/rss",
        "category": "World News"
    },
    {
        "url": "https://rss.dw.com/xml/rss-en-all",
        "category": "World News"
    }
]

def clean_html(text):
    if not text:
        return ""
    text = unescape(text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def get_image_from_item(item):

    media_content = item.find("{http://search.yahoo.com/mrss/}content")
    if media_content is not None:
        image_url = media_content.get("url")
        if image_url:
            return image_url

    media_thumbnail = item.find("{http://search.yahoo.com/mrss/}thumbnail")
    if media_thumbnail is not None:
        image_url = media_thumbnail.get("url")
        if image_url:
            return image_url
        
    enclosure = item.find("enclosure")
    if enclosure is not None:
        image_url = enclosure.get("url")
        media_type = enclosure.get("type", "")
        if image_url and media_type.startswith("image"):
            return image_url

    description_element = item.find("description")
    if description_element is not None:
        description = description_element.text or ""
        match = re.search(
            r'<img[^>]+src=["\']([^"\']+)["\']',
            description,
            re.IGNORECASE
        )
        if match:
            return match.group(1)
    return None

def get_image_from_article_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        og_image = soup.find(
            "meta",
            property="og:image"
        )

        if og_image and og_image.get("content"):
            return og_image["content"].strip()
        twitter_image = soup.find(
            "meta",
            attrs={"name": "twitter:image"}
        )
        if twitter_image and twitter_image.get("content"):
            return twitter_image["content"].strip()
        return ""
    except Exception as e:
        print(f"Cannot get image from article: {url}")
        print(f"Error: {e}")
        return ""

def fetch_news_from_rss(url, category):
    print("\n--------------------------------")
    print("กำลังดึงข่าวจาก:")
    print(url)
    print("--------------------------------")

    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},timeout=15)
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except Exception as e:
        print("เกิดข้อผิดพลาด:", e)
        return []

    items = root.findall(".//item")
    print("จำนวน item ที่เจอ:",len(items))

    news_list = []
    for item in items[:10]:
        title_element = item.find("title")
        link_element = item.find("link")
        pubdate_element = item.find("pubDate")
        description_element = item.find("description")

        if (title_element is None
            or link_element is None
        ):
            continue
        title = title_element.text or ""
        link = link_element.text or ""

        pub_date = ""
        if pubdate_element is not None:
            pub_date = (
                pubdate_element.text
                or ""
            )

        description = ""
        if description_element is not None:
            description = clean_html(
                description_element.text
                or ""
            )

        image = get_image_from_item(item)
        if not image and link:
            image = get_image_from_article_url(link)

        news_item = {
            "title": title.strip(),
            "link": link.strip(),
            "pubDate": pub_date.strip(),
            "category": category,
            "description": description,
            "image": image
        }
        news_list.append(news_item)
    return news_list

def create_database():
    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT UNIQUE,
            pubDate TEXT,
            category TEXT,
            description TEXT,
            image TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_news_to_db(news_list):
    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()
    for news_item in news_list:
        cursor.execute("""
            INSERT OR IGNORE INTO news
            (
                title,
                link,
                pubDate,
                category,
                description,
                image
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            news_item["title"],
            news_item["link"],
            news_item["pubDate"],
            news_item["category"],
            news_item["description"],
            news_item["image"]
        ))
    conn.commit()
    print(f"บันทึกข่าว {len(news_list)} รายการ")
    conn.close()

def fetch_all_news():
    print("\n")
    print("================================")
    print("       START FETCHING NEWS")
    print("================================")
    create_database()
    for rss in rss_urls:
        url = rss["url"]
        category = rss["category"]
        news_list = fetch_news_from_rss(url, category)
        save_news_to_db(news_list)
    print("\n================================")
    print("       FETCH COMPLETE")
    print("================================")

if __name__ == "__main__":
    fetch_all_news()

