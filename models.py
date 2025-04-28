"""
モデルの定義追加したらこのファイルを実行してテーブルを作成する
if __name__ == '__main__':の中に モデル名.create_table()を追加する
モデルを変更した時の処理はない
モデル変更したらpostgresqlで直接変更するしかない
"""
from db import BaseModel
from datetime import datetime


class UserLevels(BaseModel):
    table_name = 'user_levels'
    fields = {
        'user_id': 'BIGINT',
        'guild_id': 'BIGINT',
        'level': 'INTEGER',
        'xp': 'INTEGER',
        'last_message': 'TIMESTAMP',
    }

class Twitch(BaseModel):
    table_name = 'twitch'
    fields = {
        'twitch_username': 'TEXT',
        'channel_id': 'BIGINT',
    }

    @classmethod
    def create_table(cls):
        field_definitions = ", ".join(f"{name} {type}" for name, type in cls.fields.items())
        query = f"CREATE TABLE IF NOT EXISTS {cls.table_name} (id SERIAL PRIMARY KEY, {field_definitions}, UNIQUE(twitch_username, channel_id))"
        with cls.connect() as connect:
            with connect.cursor() as cursor:
                cursor.execute(query)
                connect.commit()


class Birthdays(BaseModel):
    table_name = 'birthdays'
    fields = {
        'user_id': 'BIGINT',
        'birthday': 'TEXT',
        'channel_id': 'BIGINT',
    }

    @classmethod
    def create_table(cls):
        field_definitions = ", ".join(f"{name} {type}" for name, type in cls.fields.items())
        query = f"CREATE TABLE IF NOT EXISTS {cls.table_name} (id SERIAL PRIMARY KEY, {field_definitions}, UNIQUE(user_id, channel_id))"
        with cls.connect() as connect:
            with connect.cursor() as cursor:
                cursor.execute(query)
                connect.commit()


class ServerLevels(BaseModel):
    table_name = 'server_levels'
    fields = {
        'guild_id': 'BIGINT',
        'channel_id': 'BIGINT',
    }

    @classmethod
    def create_table(cls):
        field_definitions = ", ".join(f"{name} {type}" for name, type in cls.fields.items())
        query = f"CREATE TABLE IF NOT EXISTS {cls.table_name} (id SERIAL PRIMARY KEY, {field_definitions}, UNIQUE(guild_id))"
        with cls.connect() as connect:
            with connect.cursor() as cursor:
                cursor.execute(query)
                connect.commit()

class Guilds(BaseModel):
    table_name = 'guild_guilds'

    @classmethod
    def create_or_update(cls, **kwargs):
        columns = ", ".join(kwargs.keys())
        placeholders = ", ".join(f"%s" for _ in kwargs)
        values = tuple(kwargs.values())

                # 一意制約のカラム（最初のキーを使う）
        conflict_key = list(kwargs.keys())[0]

        # UPDATE の SET 部分を生成（すべてのカラムを更新）
        update_clause = ", ".join([f"{key} = EXCLUDED.{key}" for key in kwargs.keys()])

        query = f"""
                INSERT INTO {cls.table_name} ({columns}) VALUES ({placeholders})
                ON CONFLICT ({conflict_key}) DO UPDATE SET {update_clause}
                """
        with cls.connect() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(query, values)
                    conn.commit()
                except Exception as e:
                    print(e)
                    return 1
                return 0


if __name__ == '__main__':
    UserLevels.create_table()
    Twitch.create_table()
    Birthdays.create_table()
    ServerLevels.create_table()