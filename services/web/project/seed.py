#!/usr/bin/env python3
"""
Seed script: loads tweets from geoTwitter zip files into the database.
Run from the project root with:
    docker compose exec web python /usr/src/app/project/seed.py
"""

import psycopg2
import zipfile
import json
import os
import glob
from datetime import datetime

CONN = {
    "dbname": os.getenv("POSTGRES_DB", "twitter_dev"),
    "user": os.getenv("POSTGRES_USER", "twitter"),
    "password": os.getenv("POSTGRES_PASSWORD", "twitter"),
    "host": os.getenv("SQL_HOST", "db"),
    "port": os.getenv("SQL_PORT", "5432"),
}

TWEETS_DIR = "/data/tweets_corona"
MAX_FILES = 25        # increase this once you've confirmed it works
MAX_PER_FILE = 50000 # tweets to read per zip file

def parse_created_at(s):
    return datetime.strptime(s, "%a %b %d %H:%M:%S +0000 %Y")

def main():
    conn = psycopg2.connect(**CONN)
    conn.autocommit = False
    cur = conn.cursor()

    zip_files = sorted(glob.glob(f"{TWEETS_DIR}/*.zip"))[:MAX_FILES]
    print(f"Processing {len(zip_files)} zip files...")

    users = {}      # username -> user_id
    tweet_count = 0

    for zip_path in zip_files:
        print(f"  Loading {os.path.basename(zip_path)}...")
        try:
            with zipfile.ZipFile(zip_path) as z:
                with z.open(z.namelist()[0]) as f:
                    for i, line in enumerate(f):
                        if i >= MAX_PER_FILE:
                            break
                        try:
                            tweet = json.loads(line)
                            username = tweet['user']['screen_name']
                            text = tweet.get('text', '')
                            created_at = parse_created_at(tweet['created_at'])

                            if not text or not username:
                                continue

                            # insert user if we haven't seen them
                            if username not in users:
                                cur.execute("""
                                    INSERT INTO users (username)
                                    VALUES (%s)
                                    ON CONFLICT (username) DO NOTHING
                                    RETURNING id
                                """, (username,))
                                row = cur.fetchone()
                                if row is None:
                                    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                                    row = cur.fetchone()
                                users[username] = row[0]

                                # insert a dummy credential for each user
                                cur.execute("""
                                    INSERT INTO credentials (user_id, password_hash)
                                    VALUES (%s, %s)
                                    ON CONFLICT DO NOTHING
                                """, (users[username], 'seed_data_no_password'))

                            # insert tweet
                            cur.execute("""
                                INSERT INTO tweets (user_id, message, created_at)
                                VALUES (%s, %s, %s)
                            """, (users[username], text, created_at))
                            tweet_count += 1

                        except (KeyError, ValueError):
                            continue

        except zipfile.BadZipFile:
            print(f"  Skipping bad zip: {zip_path}")
            continue

        conn.commit()
        print(f"  Committed. Total tweets so far: {tweet_count}")

    print(f"Done! Inserted {tweet_count} tweets and {len(users)} users.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
