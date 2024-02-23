import streamlit as st
from st_supabase_connection import SupabaseConnection
from supabase import create_client, client
import openai
from openai import OpenAI
import numpy as np
import pandas as pd
import vecs
import psycopg2
from insert_functions import connect_psycopg2

conn_params = f"dbname={st.secrets["dbname"]} user={st.secrets["user"]} host={st.secrets["host"]} password={st.secrets["password"]}"


# Function to get embedding from openai for search term
def get_embedding(text, model="text-embedding-3-small"):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=model).data[0].embedding

# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

#Initialise connection
supabase = init_connection()

#Set title for page
st.title("Ironmarch semantic search")


# OpenAI API Key (ensure to use your own key securely)
openai.api_key = st.secrets["OPENAI_KEY"]

# Add input box for search term
search_term = st.text_input("Enter a search term: (e.g. facism)")
# Adding an information note to the sidebar
# Use st.sidebar.markdown with HTML for styling
# Additional section for a textbox 
st.sidebar.header("Additional Information")
st.sidebar.markdown("""
Web app designed to search for Iron March posts using cosine similarity on OpenAI vector embeddings. Implemented using Supabase and Streamlit.
                    """)

# Additional section for GitHub link in the sidebar
st.sidebar.header("GitHub Repository")
st.sidebar.markdown("""
                    Find the source code for this app on GitHub:
                    [GitHub Repository](https://github.com/smose94/ironmarch-semantic-search)
                    """)
st.sidebar.markdown(
    """
    <div style="background-color:lightblue; border-radius: 5px; padding: 10px; margin: 10px 0;">
        <strong>Note:</strong> Returns posts with cosine similarity below 0.5.
    </div>
    """,
    unsafe_allow_html=True
)
#OpenAI client
client = OpenAI(
    api_key=st.secrets["OPENAI_KEY"],
)

#Loop to compare search term embeddings with database embeddings
if search_term:
    
    # Generate an embedding for the search term using OpenAI API
    search_embedding = get_embedding(search_term, model='text-embedding-3-small')
    #Create transient vector table to store embedding in temporarily

    #Save conn and cursor to store
    conn, cursor = connect_psycopg2(conn_params)

    # Insert embedding from search term into table
    cursor.execute("INSERT INTO temp_table (embedding) VALUES (%s)", (search_embedding,))

    # Create another temporary table for storing cosine distances
    cursor.execute("""
    CREATE TEMPORARY TABLE cosine_distances (
        id bigint primary key generated always as identity,
        temp_id bigint,  
        vector_id bigint,
        distance float NOT NULL
    );
    """)

    # Step 3: Calculate cosine distance and insert into the new table
    # Using the <=> operator for distance calculation between embeddings
    cursor.execute("""
    INSERT INTO cosine_distances (temp_id, vector_id, distance)
    SELECT temp.id, vec.msg_id, temp.embedding <=> vec.ada_embedding
    FROM temp_table temp
    CROSS JOIN vector_embeddings vec;                           
    """)

    #Select distances below 0.5 similarity and return the distance and original post
    cursor.execute("""
    SELECT cd.distance, ve.msg_post
    FROM cosine_distances cd
    JOIN vector_embeddings ve ON cd.vector_id = ve.msg_id
    WHERE cd.distance < 0.5;
    """)

    # Commit the changes
    conn.commit()

    # Fetch all rows from cursor
    rows = cursor.fetchall()

    # Get the column names from the cursor description
    columns = [desc[0] for desc in cursor.description]

    # Create a DataFrame from the query results
    df = pd.DataFrame(rows, columns=columns)

    # Display the number of results with an emoji
    num_results = len(df)

    # Close the cursor and the connection
    cursor.close()
    conn.close()
    st.markdown(f"##### 🔍 {num_results} results found")
        #Write to UI
    st.dataframe(df,use_container_width=True)


else:
    st.write("Please enter a search term to find similar posts.")

