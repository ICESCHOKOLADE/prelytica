import psycopg2,psycopg2.extras

def connect_db():
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="tra74ag+",
            host="localhost",
            port="5432"
        )
        # cur = conn.cursor()
        cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        return cur
    except psycopg2.OperationalError as e:
        return None
        
    