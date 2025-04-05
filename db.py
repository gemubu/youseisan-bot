import psycopg2
import config
from psycopg2.extras import DictCursor

class BaseModel:
    table_name = ''
    fields = {}

    @classmethod
    def connect(cls):
        return psycopg2.connect(dbname=config.DBNAME,
                                user=config.USER,
                                password=config.PASSWORD,
                                host=config.HOST)

    @classmethod
    def create_table(cls):
        field_definitions = ", ".join(f"{name} {type}" for name, type in cls.fields.items())
        query = f"CREATE TABLE IF NOT EXISTS {cls.table_name} (id SERIAL PRIMARY KEY, {field_definitions})"
        with cls.connect() as connect:
            with connect.cursor() as cursor:
                cursor.execute(query)
                connect.commit()

    @classmethod
    def create(cls, **kwargs):
        columns = ", ".join(kwargs.keys())
        placeholders = ", ".join(f"%s" for _ in kwargs)
        values = tuple(kwargs.values())
        query = f"INSERT INTO {cls.table_name} ({columns}) VALUES ({placeholders}) RETURNING id"
        with cls.connect() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(query, values)
                    conn.commit()
                except Exception as e:
                    return 1
                return 0

    @classmethod
    def all(cls):
        query = f"SELECT * FROM {cls.table_name}"
        with cls.connect() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

    @classmethod
    def filter(cls, **kwargs):
        conditions = " AND ".join(f"{key} = %s" for key in kwargs)
        values = tuple(kwargs.values())
        query = f"SELECT * FROM {cls.table_name} WHERE {conditions}"
        with cls.connect() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, values)
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

    @classmethod
    def get(cls, **kwargs):
        conditions = " AND ".join(f"{key} = %s" for key in kwargs)
        values = tuple(kwargs.values())
        query = f"SELECT * FROM {cls.table_name} WHERE {conditions}"
        with cls.connect() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, values)
                row = cursor.fetchone()
        return dict(row) if row else None

    @classmethod
    def update(cls, **kwargs):
        query = f"UPDATE {cls.table_name} SET {', '.join(f'{key} = %s' for key in kwargs)} WHERE id = %s"
        with cls.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, tuple(kwargs.values()) + (kwargs['id'],))
                conn.commit()

    @classmethod
    def delete(cls, **kwargs):
        conditions = " AND ".join([f"{key} = %s" for key in kwargs.keys()])
        values = tuple(kwargs.values())
        query = f"DELETE FROM {cls.table_name} WHERE {conditions}"
        with cls.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                conn.commit()
                if cursor.rowcount == 0:
                    return 1
                return 0

if __name__ == '':
    #モデル作成の例
    class User(BaseModel):
        table_name = 'users'
        fields = {
            'name': 'TEXT',
            'email': 'TEXT',
        }

    User.create_table()
    User.create(name='Alice',email='aaa@a.a')