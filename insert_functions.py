# Function to calculate cosine similarity
import psycopg2
# Database connection parameters
conn_params = "dbname='postgres' user='postgres.noxicvyjsaxffcmfptjp' host='aws-0-eu-west-2.pooler.supabase.com' password='Ukkpekluk1!'"

def connect_psycopg2(conn_params):
    conn = psycopg2.connect(conn_params)
    cursor = conn.cursor()

    #Create a temporary table on startup - this will store the OpenAI embeddings
    cursor.execute("""
                   CREATE TEMPORARY TABLE temp_table (
                   id bigint primary key generated always as identity,
                   embedding VECTOR (1536) NOT NULL
                   );
                   """)
    return conn, cursor