import sqlite3
from patangoma.base import BaseModel
from patangoma.track import TrackInfo


class FileStorage(BaseModel):
    """ Class to handle database operations. """

    def __init__(self, database_path, track_metadata: dict):
        """ Initialize the database connection and create the table. """
        self.conn = sqlite3.connect(database_path)
        self.create_tables(track_metadata)

    def create_tables(self, track_metadata):
        """ Create the database tables. """
        cursor = self.conn.cursor()

        # Create the SQL table dynamically based on metadata attributes
        table_creation_sql = f'''
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY,
                {', '.join([f"{key} {self.get_sqlite_type(value)}"
                for key, value in track_metadata.items()])}
            )
        '''

        cursor.execute(table_creation_sql)
        self.conn.commit()

    def get_sqlite_type(self, value):
        """
        Map Python data types to SQLite data types.
        """
        if isinstance(value, int):
            return 'INTEGER'
        elif isinstance(value, float):
            return 'REAL'
        else:
            return 'TEXT'

    def add_track_metadata(self, track_metadata):
        """ Add track metadata to the database. """

        cursor = self.conn.cursor()
        keys = [
            key for key in track_metadata.keys()
            if key != 'images' or 'art' in key
        ]
        placeholders = ', '.join(['?' for _ in keys])

        # Create the SQL INSERT statement with dynamic columns and placeholders
        sql = f'''
            INSERT INTO tracks ({', '.join(keys)})
            VALUES ({placeholders})
        '''

        # Serialize list-like values to JSON strings before insertion
        values = [
            json.dumps(track_metadata[key]) if isinstance(
                track_metadata[key], list) else track_metadata[key]
            for key in keys
        ]

        cursor.execute(sql, values)

        self.conn.commit()

    def get_track_metadata(self, track_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tracks WHERE id = ?', (track_id, ))
        return cursor.fetchone()

    def export_library_metadata(self, export_format):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tracks')
        metadata_list = cursor.fetchall()

        if export_format == 'json':
            with open('libmeta.json', 'w') as json_file:
                json.dump(metadata_list, json_file, indent=4)
        elif export_format == 'yaml':
            with open('libmeta.yaml', 'w') as yaml_file:
                yaml.dump(metadata_list, yaml_file, indent=4)
        elif export_format == 'csv':
            with open('libmeta.csv', 'w') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow([i[0] for i in cursor.description])
                csv_writer.writerows(metadata_list)

    def close(self):
        """Close the database connection."""
        self.conn.close


if __name__ == '__main__':
    import json
    import yaml
    import csv
    from tags import TrackInfo
    # Add track metadata
    t = TrackInfo('../audio.mp3')
    # print(t.as_dict().keys())
    db = FileStorage('test_lib.db', track_metadata=t.as_dict())

    # # print(t.as_dict())

    db.add_track_metadata(track_metadata=t.as_dict())
    # # # Get track metadata
    metadata = db.get_track_metadata(1)
    # print(metadata)

    # Export library metadata
    export = db.export_library_metadata('yaml')
    # print(export)

    db.close()
