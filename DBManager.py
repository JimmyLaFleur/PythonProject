import psycopg2
from config import host, user, password, db_name

def connect():
    try:
        connection = psycopg2.connect(
            database=db_name,
            user=user,
            password=password,
            host=host)
        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute('SELECT version();')
            print(f"Server version: {cursor.fetchone()}")
        return connection
    except Exception as e:
        print("[INFO] Error while working with PostgreSQL:", e)
def drop_tables(connection):
    with connection.cursor() as cursor:
        cursor.execute('''
        DROP TABLE IF EXISTS spendings;
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS telegram_profiles;
        DROP TABLE IF EXISTS categories;''')
        print("[INFO] Tables dropped")
def create_tables(connection):
    with connection.cursor() as cursor:
        cursor.execute('''
        CREATE TABLE telegram_profiles (
        id SERIAL PRIMARY KEY UNIQUE,
        user_id BIGINT NOT NULL UNIQUE
        );
        
        CREATE TABLE categories (
        id SERIAL PRIMARY KEY UNIQUE,
        title varchar(30) NOT NULL UNIQUE
        );
        
        CREATE TABLE users (
        id SERIAL PRIMARY KEY UNIQUE,
        telegram_id INT REFERENCES telegram_profiles(id) NOT NULL UNIQUE
        );
        
        CREATE TABLE spendings (
        id SERIAL PRIMARY KEY UNIQUE,
        user_id INT REFERENCES users(id) NOT NULL,
        price INT NOT NULL,
        title varchar(50) NOT NULL,
        category_id INT REFERENCES categories(id),
        date TIMESTAMP NOT NULL,
        rate INT
        );''')
        print("[INFO] Tables created")
def add_spending(connection, dict):
    with connection.cursor() as cursor:
        print(dict)
        tg_pk = execute_query_with_return(connection, f'SELECT id FROM telegram_profiles WHERE user_id={dict['user_id']}')[0][0]
        user_pk = execute_query_with_return(connection, f'SELECT id FROM users WHERE telegram_id={tg_pk}')[0][0]
        cursor.execute(f'''INSERT INTO spendings(user_id, price, title, category_id, date) VALUES (
        {user_pk}, 
        {dict['price']}, 
        '{dict['title']}', 
        {0}, 
        TO_TIMESTAMP('{dict['date']+" 00:00:00"}', 'YYYY-MM-DD HH24:MI:SS'))''')
        print("[INFO] Spending added")
def close_connection(connection):
    connection.close()
    print("[INFO] PostgreSQL connection is closed")
def execute_query(connection, query):
    with connection.cursor() as cursor:
        cursor.execute(query)
    print("[INFO] Query executed")

def execute_query_with_return(connection, query):
    with connection.cursor() as cursor:
        cursor.execute(query)
        response = cursor.fetchall()
    print("[INFO] Query executed. Response: ", response )
    return response
def add_user(connection, user_id):
    execute_query(connection, f"INSERT INTO telegram_profiles (user_id) VALUES ({user_id}) ON CONFLICT DO NOTHING")
    telegram_id = execute_query_with_return(connection, f'SELECT id FROM telegram_profiles WHERE user_id={user_id}')[0][0]
    execute_query(connection, f"INSERT INTO users (telegram_id) VALUES ({telegram_id}) ON CONFLICT DO NOTHING")

if __name__ == '__main__':
    create_tables(connect())