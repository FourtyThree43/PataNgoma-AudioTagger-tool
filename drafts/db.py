import sqlite3

class Database:
    def __init__(self, db_name):
        self.db_name = db_name

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        self.create_tables()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                artist TEXT,
                album TEXT,
                duration REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS albums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                artist TEXT
            )
        ''')

    def insert_track(self, track_info):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO tracks (title, artist, album, duration)
            VALUES (?, ?, ?, ?)
        ''', (track_info.title, track_info.artist, track_info.album, track_info.duration))

    def insert_album(self, album_info):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO albums (name, artist)
            VALUES (?, ?)
        ''', (album_info.album_name, album_info.artist_name))
        album_id = cursor.lastrowid

        # Insert tracks associated with the album in a batch
        track_records = [(track.title, track.artist, album_info.album_name, track.duration) for track in album_info.tracks]
        cursor.executemany('''
            INSERT INTO tracks (title, artist, album, duration)
            VALUES (?, ?, ?, ?)
        ''', track_records)
