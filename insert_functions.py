import streamlit as st
import psycopg2
# Database connection parameters

db_secrets = st.secrets["database"]
conn_params = f"dbname='{db_secrets['dbname']}' user='{db_secrets['user']}' host='{db_secrets['host']}' password='{db_secrets['password']}'"

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