import os
from dotenv import load_dotenv
import openai
import json

# Load environment variables
load_dotenv()

neo4j_url = os.getenv("NEO4J_CONNECTION_URL")
neo4j_user = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")

api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()

if api_key:
    print("OpenAI API key found\n")
    openai.api_key = api_key
else:
    print("OpenAI API key not found\n")
    exit()

# Base content for the system prompt
base_content = """
You are generating structured data for a Neo4j knowledge graph focused on parties and countries.
Please output entities and relationships in JSON format, using the following schema:

- **Entities**: List of objects with 'name' and 'type'.
- 'type' should be either 'Person', 'Party', 'Country' or 'Institution'.
- **Relationships**: List of objects with 'type', 'from', and 'to'.
- Only include 'MEMBER_OF' for party membership and 'ASSOCIATED_WITH' for country/state.

Output only the JSON object.
"""

directories = ["sw-sn-project/data/Donald_Trump"]

# loop for generating JSON files for each text file in the directories
for dir_path in directories:
    # Get all .txt files in the directory
    txt_files = [f for f in os.listdir(dir_path) if f.endswith('.txt')]
    
    for txt_file in txt_files:
        file_path = os.path.join(dir_path, txt_file)
        
        # Read the content of the text file
        with open(file_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        # Construct the user prompt by combining the base content and the text content
        user_prompt = text_content
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": base_content
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0,
        )
        
        # Extract the assistant's reply (the JSON output)
        json_output = response.choices[0].message.content
        print("JSON output:\n", json_output)
        
        # Save the JSON output to a file
        json_file_name = os.path.splitext(txt_file)[0] + '.json'
        json_file_path = os.path.join(dir_path, json_file_name)
        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json_file.write(json_output)
        
        print(f"Generated JSON file saved to: {json_file_path}")


# loop for generating CYPHER statements for each JSON file in the directories

for dir_path in directories:
    # Get all .json files in the directory
    json_files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
    
    for json_file in json_files:
        json_file_path = os.path.join(dir_path, json_file)
        
        # Read the JSON data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cypher_statements = []
        
        # Generate Cypher statements for entities
        entities = data.get('entities', [])
        for entity in entities:
            name = entity['name'].replace("'", "\\'")
            type_ = entity['type']
            cypher = f"MERGE (n:{type_} {{name: '{name}'}});"
            cypher_statements.append(cypher)
        
        # Generate Cypher statements for relationships
        relationships = data.get('relationships', [])
        for rel in relationships:
            rel_type = rel['type']
            from_name = rel['from'].replace("'", "\\'")
            to_name = rel['to'].replace("'", "\\'")
            # Adjust labels based on entity types if necessary
            cypher = (
                f"MATCH (a:Person {{name: '{from_name}'}}), "
                f"(b:Party {{name: '{to_name}'}}) "
                f"MERGE (a)-[:{rel_type}]->(b);"
            )
            cypher_statements.append(cypher)
        
        # Save Cypher statements to a file
        cypher_file_name = os.path.splitext(json_file)[0] + '_cypher.txt'
        cypher_file_path = os.path.join(dir_path, cypher_file_name)
        
        with open(cypher_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(cypher_statements))
        
        print(f"Generated Cypher statements saved to: {cypher_file_path}")
        