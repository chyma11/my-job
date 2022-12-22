import sqlalchemy
import psycopg2


DSN = 'postgresql://postgres:12345@localhost:5432/diplom2'
engine = sqlalchemy.create_engine(DSN)
connection = engine.connect()


def create_db():
    initial_connection = psycopg2.connect(
        database="diplom2",
        user='postgres',
        password='12345',
        host='localhost',
        port='5432'
    )
    initial_connection.close()


def create_tables():
    connection.execute('''
    CREATE TABLE IF NOT EXISTS seen_users (
    id integer PRIMARY KEY,
    first_name varchar(40) NOT NULL,
    last_name varchar(40) NOT NULL,
    photo1 integer NOT NULL,
    photo2 integer NOT NULL,
    photo3 integer NOT NULL
    );
    ''')


def insert_users(user, photo_data):
    if not connection.execute(f"SELECT id FROM seen_users WHERE id = {user['id']};").fetchone():
        connection.execute(f"INSERT INTO seen_users (id, first_name, last_name, photo1, photo2, photo3)"
                           f"VALUES ({user['id']}, \'{user['first_name']}\',"
                           f"\'{user['last_name']}\', {photo_data['photo_ids'][0]},"
                           f"{photo_data['photo_ids'][1]}, {photo_data['photo_ids'][2]});")
        
def check_users(user):
    if connection.execute(f"SELECT id FROM seen_users WHERE id = {user['id']};").fetchone():
        return False
    return True
