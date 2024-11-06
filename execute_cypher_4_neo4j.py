import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

neo4j_url = os.getenv("NEO4J_CONNECTION_URL")
neo4j_user = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")
gds = GraphDatabase.driver(neo4j_url, auth=(neo4j_user, neo4j_password))

# Path to the directory containing the Cypher query files
path = "sw-sn-project/data/Donald_Trump"

def execute_cypher_query(path):
    # Open a single session for all queries
    with gds.session() as session:
        for file in os.listdir(path):
            if file.endswith("_cypher.txt"):
                file_path = os.path.join(path, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    queries = f.read()
                    # Split the queries by semicolon and strip whitespace
                    query_list = [q.strip() for q in queries.split(';') if q.strip()]
                    for query in query_list:
                        try:
                            session.run(query)
                        except Exception as e:
                            print(f"Failed to execute query: {query}")
                            print(f"From file: {file}")
                            print(f"Error: {e}")

if __name__ == "__main__":
    execute_cypher_query(path)
    gds.close()