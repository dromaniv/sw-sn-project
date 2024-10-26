import os
import json
import re
from neo4j import GraphDatabase
from groq import Groq

class PoliticalKGApp:
    def __init__(self, uri, user, password, groq_api_key):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.client = Groq(api_key=groq_api_key)

    def close(self):
        self.driver.close()

    def create_node(self, label, properties):
        # Directly use label and properties as provided by the LLM's output
        with self.driver.session() as session:
            session.execute_write(self._create_node, label, properties)

    @staticmethod
    def _create_node(tx, label, properties):
        query = f"MERGE (n:{label} " + "{ " + ", ".join(f"{k}: ${k}" for k in properties.keys()) + " })"
        tx.run(query, **properties)

    def create_relationship(self, entity1, label1, entity2, label2, relationship):
        with self.driver.session() as session:
            session.execute_write(self._create_relationship, entity1, label1, entity2, label2, relationship)

    @staticmethod
    def _create_relationship(tx, entity1, label1, entity2, label2, relationship):
        query = (
            f"MATCH (a:{label1} {{name: $entity1}}), (b:{label2} {{name: $entity2}}) "
            f"MERGE (a)-[:{relationship}]->(b)"
        )
        tx.run(query, entity1=entity1, entity2=entity2)

    def extract_entities_and_relationships(self, text):
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content":
                            "You are generating structured data for a Neo4j knowledge graph focused on parties and countries."
                            " Please output entities and relationships in JSON format, using the following schema:"
                            "\n\n"
                            "- **Entities**: List of objects with 'name' and 'type'.\n"
                            "  - 'type' should be either 'Person', 'Party', or 'Country'.\n"
                            "- **Relationships**: List of objects with 'type', 'from', and 'to'.\n"
                            "  - Only include 'MEMBER_OF' for party membership and 'ASSOCIATED_WITH' for country/state.\n"
                            "\n\n"
                            "Output only the JSON object."
                    },
                    {"role": "user", "content": text}
                ],
                model="llama-3.1-8b-instant",
            )
            
            # Directly parse the JSON response
            structured_data = chat_completion.choices[0].message.content
            print("RAW RESPONSE FROM GROQ:", structured_data)

            # Try parsing directly without regex
            return self.parse_structured_data(structured_data)

        except Exception as e:
            print(f"Error during GROQ API call or response parsing: {e}")
            return [], []

    @staticmethod
    def parse_structured_data(data):
        try:
            data = json.loads(data)
            entities = [(entity["name"], entity["type"]) for entity in data.get("entities", [])]
            relationships = [(relationship["type"], relationship["from"], relationship["to"]) for relationship in data.get("relationships", [])]
            return entities, relationships
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            return [], []

    def build_kg_from_text(self, text):
        entities, relationships = self.extract_entities_and_relationships(text)

        # Add entities to the Neo4j database
        for name, label in entities:
            self.create_node(label, {"name": name})

        # Add relationships to the Neo4j database
        for rel_type, from_entity, to_entity in relationships:
            self.create_relationship(from_entity, "Person", to_entity, "Party" if "Party" in to_entity else "Country", rel_type)

        # Display the nodes and relationships in the graph
        self.print_all_nodes()
        self.print_all_relationships()

    def print_all_nodes(self):
        with self.driver.session() as session:
            result = session.run("MATCH (n) RETURN n")
            print("\nNodes in the graph:")
            for record in result:
                print(record["n"])

    def print_all_relationships(self):
        with self.driver.session() as session:
            result = session.run("MATCH (a)-[r]->(b) RETURN a.name AS from, type(r) AS relationship, b.name AS to")
            print("\nRelationships in the graph:")
            for record in result:
                print(f"{record['from']} -[:{record['relationship']}]-> {record['to']}")

# Example Usage
if __name__ == "__main__":
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "password" # Change this to your password
    groq_api_key = "groq_api_key" # Change this to your API key

    app = PoliticalKGApp(uri, user, password, groq_api_key)

    text = """
    Joe Biden is a member of the Democratic Party and is the 46th President of the United States.
    Donald Trump, a Republican, served as the 45th President before Biden.
    """

    app.build_kg_from_text(text)
    app.close()
