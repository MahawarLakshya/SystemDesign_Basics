import os
import time
import threading

from typing import Optional
from urllib.parse import urlsplit

import psycopg
import redis

from psycopg.errors import UniqueViolation
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
EPOCH_MS = 946742245000
#Make thte longer url into ID for encod62 then generate the shortUSR using this encoding

#encode62
def encode(number):
    if number<0:
        raise ValueError("ID must be nonnegative")
    if number==0:
        return "0"
    code="" 
    while number:
        rem=number%62
        number=number//62
        code=ALPHABET[rem]+code
    return code

#check whether the given value is url or not

from urllib.parse import urlsplit

def validate_url(url):
    url = url.strip()
    parsed = urlsplit(url)

    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Invalid HTTP/HTTPS URL")

    return url

#Generate the snowflake ID-> timestamp+machine_code+sequence

class Snowflake:
    def __init__(self, worker_id: int):
        if not 0 <= worker_id < 1024:
            raise ValueError("WORKER_ID must be in 0..1023")
        self.worker_id = worker_id
        self.last_ms = -1
        self.sequence = 0
        self.lock = threading.Lock()

    def generate(self):
        with self.lock:
            now=time.time_ns() // 1_000_000  #converts nano seconds into mili seconds
           
            if now < self.last_ms:
                raise RuntimeError("Clock moved backwards")
            if now==self.last_ms:
                self.sequence=(self.sequence+1)%4096
                if self.sequence==0:
                        while now<=self.last_ms:
                            time.sleep(0.0001)
                            now=time.time_ns() // 1_000_000 #converts nano seconds into mili seconds
                            
            else:
                self.sequence = 0
            elapsed = now - EPOCH_MS
            if not 0 <= elapsed < (1 << 41):
                raise RuntimeError("Snowflake timestamp out of range")
            self.last_ms = now
            return (elapsed << 22) | (self.worker_id << 12) | self.sequence  


class URLShortener:
    def __init__(self):
        self.generator = Snowflake(int(os.environ.get("WORKER_ID", "1")))
        self.base_url = os.environ.get("BASE_URL", "https://sho.rt").rstrip("/")
        #establish the db connection
        self.db = psycopg.connect(os.environ.get("DATABASE_URL", "postgresql://urluser:urlpass@localhost:5432/urls"), autocommit=True)
        self.db.execute("""CREATE TABLE IF NOT EXISTS urls (
            short_code VARCHAR(16) PRIMARY KEY,
            long_url TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""")
        #establish redis cache connection
        self.cache = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True, socket_connect_timeout=0.5, socket_timeout=0.5)

    def shorten(self, long_url: str) :
        long_url = validate_url(long_url)
        for _ in range(3):
            code = encode(self.generator.generate())
            try:
                self.db.execute("INSERT INTO urls (short_code, long_url) VALUES (%s, %s)", (code, long_url))
                break
            except UniqueViolation:
                continue
        else:
            raise RuntimeError("Failed to allocate unique short code")
        try:
            self.cache.setex(f"url:{code}", 3600, long_url)
        except redis.RedisError as exc:
            print(f"[Cache unavailable; saved in PostgreSQL: {exc}]")
        return f"{self.base_url}/{code}"

    def resolve(self, code: str) :
        code = code.removeprefix(self.base_url + "/")
        try:
            cached = self.cache.get(f"url:{code}")
            if cached is not None:
                print("[Redis cache HIT]")
                return cached
            
        except redis.RedisError:
            print("[Redis unavailable; querying PostgreSQL]")
        print("[PostgreSQL lookup]")
        row = self.db.execute("SELECT long_url FROM urls WHERE short_code = %s", (code,)).fetchone()
        if row is None:
            return None
        try:
            self.cache.setex(f"url:{code}", 3600, row[0])
        except redis.RedisError:
            pass
        return row[0]

    def close(self):
        self.db.close()
        self.cache.close()


def main():
    shortener = URLShortener()
    try:
        while True:
            print("\n1. Shorten URL  2. Resolve short code  3. Exit")
            choice = input("Choose: ").strip()
            try:
                if choice == "1":
                    print("Short URL:", shortener.shorten(input("Enter Long URL: ").strip()))
                elif choice == "2":
                    original = shortener.resolve(input("Enter short code or short URL: ").strip())
                    print("Original URL:", original or "Not found")
                elif choice == "3":
                    break
                else:
                    print("Invalid choice")
            except (ValueError, RuntimeError, psycopg.Error) as exc:
                print("Error:", exc)
    finally:
        shortener.close()


if __name__ == "__main__":
    main()

                     