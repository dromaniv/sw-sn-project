# Political Knowledge Graph Builder

This project leverages Neo4j and GROQ's Large Language Model (LLM) capabilities to build a simplified knowledge graph based on political figures, their party affiliations, and associated countries or states. By using structured JSON data extracted by GROQ from unstructured text, we dynamically populate a Neo4j database with nodes and relationships that represent this information.

## Project Overview

The primary objective of this project is to:
1. **Extract political entities** from unstructured text using GROQ's LLM.
2. **Standardize data** to focus only on party affiliations and country/state associations.
3. **Populate a Neo4j knowledge graph** with entities (nodes) and relationships to represent these associations in a structured format.

The project aims to make it easy to build a knowledge graph with minimal setup and prompt engineering, without the need for extensive data cleaning or manual label adjustments.

## Requirements

- **Python 3.8+**
- **Neo4j Database** (Community or Enterprise Edition)
- **GROQ API Key** (access to GROQ's Large Language Model)
- **Python Libraries**:
  - `neo4j` (for connecting to Neo4j)
  - `groq` (GROQ client)
  - `re` and `json` (Python standard libraries)

## Installation

1. Clone this repository:
    ```bash
    [git clone https://github.com/your-username/political-knowledge-graph.git](https://github.com/dromaniv/sw-sn-project.git)
    cd political-knowledge-graph
    ```

2. Install the required libraries:
    ```bash
    pip install neo4j groq
    ```

3. Ensure Neo4j is running locally (or on the specified URI) and accessible on `bolt://localhost:7687`.

## Usage

1. **Prepare Text Input**:
   - Prepare a text input about political figures that includes information on their party and country/state affiliations. For example:
     ```
     Joe Biden is a member of the Democratic Party and is the 46th President of the United States.
     Donald Trump, a Republican, served as the 45th President before Biden.
     ```

2. **Run the Script**:
   - Run the main script to extract information and populate the Neo4j graph.
   - Example command:
     ```bash
     python from_neo4j_import_GraphDatabase.py
     ```

3. **View the Graph**:
   - After running the script, the Neo4j database will have nodes representing political figures, their parties, and their associated countries. Relationships will indicate `MEMBER_OF` for party affiliations and `ASSOCIATED_WITH` for country/state associations.

## Code Structure

- **PoliticalKGApp**: The main class responsible for managing the Neo4j database and interacting with GROQ’s API to extract and structure knowledge graph data.
  - `__init__`: Initializes Neo4j and GROQ connections.
  - `extract_entities_and_relationships`: Sends the text to GROQ for analysis and extracts structured JSON data.
  - `build_kg_from_text`: Builds the knowledge graph from extracted data, creating nodes and relationships.
  - `print_all_nodes` and `print_all_relationships`: Helper methods to display nodes and relationships for verification.

## Example Output

After running the script with the example text, you should see output like:

### Nodes:
Nodes in the graph:
```
<Node element_id='' labels=frozenset({'Person'}) properties={'name': 'Joe Biden'}>
<Node element_id='' labels=frozenset({'Person'}) properties={'name': 'Donald Trump'}>
<Node element_id='' labels=frozenset({'Party'}) properties={'name': 'Democratic Party'}>
<Node element_id='' labels=frozenset({'Party'}) properties={'name': 'Republican Party'}>
<Node element_id='' labels=frozenset({'Country'}) properties={'name': 'United States'}>

Relationships in the graph:
Joe Biden -[:MEMBER_OF]-> Democratic Party
Joe Biden -[:ASSOCIATED_WITH]-> United States
Donald Trump -[:MEMBER_OF]-> Republican Party
Donald Trump -[:ASSOCIATED_WITH]-> United States
```

## Troubleshooting

1. **No JSON content found in the response**:
   - Ensure that GROQ is correctly configured and accessible. The prompt may need adjustment if unexpected data is returned.

2. **Neo4j connection errors**:
   - Verify that Neo4j is running and accessible at `bolt://localhost:7687`. Check that your credentials are correct.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
