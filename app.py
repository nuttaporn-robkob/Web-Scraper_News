from flask import Flask, render_template, request
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from main import fetch_all_news

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect("news.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    search = request.args.get(
        "search",
        ""
    ).strip()
    category = request.args.get(
        "category",
        ""
    ).strip()
    conn = get_db_connection()

    query = """
        SELECT
            id,
            title,
            link,
            pubDate,
            category,
            description,
            image
        FROM news
        WHERE 1=1
    """
    params = []

    if search:
        query += """
            AND (
                title LIKE ?
                OR description LIKE ?
            )
        """
        search_value = f"%{search}%"
        params.append(search_value)
        params.append(search_value)

    if category:
        query += """
            AND category = ?
        """
        params.append(category)
    query += """
        ORDER BY id DESC
    """
    cursor = conn.execute(query, params)
    news_list = cursor.fetchall()
    
    categories = conn.execute("""
        SELECT DISTINCT category
        FROM news
        ORDER BY category
    """).fetchall()
    conn.close()
    return render_template(
        "index.html",
        news_list=news_list,
        categories=categories,
        search=search,
        selected_category=category
    )

scheduler = BackgroundScheduler()

scheduler.add_job(
    fetch_all_news,
    "interval",
    minutes=5,
    id="news_fetch",
    replace_existing=True
)

print("Fetching news...")
fetch_all_news()

scheduler.start()

print("News scheduler started.")
print("News will be updated every 5 minutes.")

if __name__ == "__main__":
  app.run(debug=True,use_reloader=False)

        