import os
import re
import logging
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum
import wikipedia
import openai
import json
from json.decoder import JSONDecodeError
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
load_dotenv()


class EntityType(Enum):
    PERSON = "Person"
    ORGANIZATION = "Organization"
    LOCATION = "Location"
    EVENT = "Event"
    CONCEPT = "Concept"
    DOCUMENT = "Document"


class RelationType(Enum):
    AFFILIATED_WITH = "AFFILIATED_WITH"
    BORN_IN = "BORN_IN"
    CREATED = "CREATED"
    PARTICIPATED_IN = "PARTICIPATED_IN"
    LEADS = "LEADS"
    SUCCEEDED = "SUCCEEDED"
    RELATED_TO = "RELATED_TO"
    LOCATED_IN = "LOCATED_IN"
    MEMBER_OF = "MEMBER_OF"


@dataclass
class Entity:
    name: str
    type: EntityType
    properties: Dict[str, Any]


@dataclass
class Relationship:
    source: str
    target: str
    type: RelationType
    properties: Dict[str, Any]


def try_repair_json(text: str) -> str:
    """Attempt to repair truncated JSON string by keeping only complete fragments"""
    # If dealing with an array of objects, split by "},{"
    fragments = text.split("},{")

    if len(fragments) <= 1:
        return text

    # Check each fragment for completeness
    complete_fragments = []
    for i, fragment in enumerate(fragments):
        # First fragment should end with }
        if i == 0 and not fragment.rstrip().endswith("}"):
            fragment = fragment + "}"

        # Middle fragments need both { and }
        elif 0 < i < len(fragments) - 1:
            fragment = "{" + fragment + "}"

        # Last fragment should start with {
        elif i == len(fragments) - 1:
            if not fragment.lstrip().startswith("{"):
                fragment = "{" + fragment

        try:
            # Test if fragment is valid JSON
            json.loads(fragment)
            complete_fragments.append(fragment)
        except JSONDecodeError:
            # Stop at first incomplete fragment
            break

    if not complete_fragments:
        return text

    # Reconstruct array with complete fragments
    if len(complete_fragments) == 1:
        return complete_fragments[0]

    result = ",".join(complete_fragments)
    if text.lstrip().startswith("["):
        result = "[" + result + "]"

    return result


def parse_json_response(text: str) -> dict:
    try:
        return json.loads(text)
    except JSONDecodeError:
        # Look for JSON in code blocks
        code_block_pattern = r"```(?:json)?\s*(.*?)\s*```"
        json_match = re.search(code_block_pattern, text, re.DOTALL)

        if json_match:
            try:
                json_text = json_match.group(1).strip()
                return json.loads(json_text)
            except JSONDecodeError:
                # Try repairing truncated JSON in code block
                repaired_json = try_repair_json(json_text)
                try:
                    return json.loads(repaired_json)
                except JSONDecodeError:
                    logger.error(
                        "🚫 Failed to parse JSON from code block even after repair"
                    )
                    raise

        # Try repairing the full text if no code block found
        try:
            repaired_json = try_repair_json(text)
            return json.loads(repaired_json)
        except JSONDecodeError:
            logger.error("🚫 No valid JSON found in response")
            logger.debug(f"Response: {text}")
            raise JSONDecodeError("No valid JSON found in response", text, 0)


class WikiKnowledgeGraph:
    EXTRACTION_PROMPT = """
    You are a precise knowledge graph extractor. Extract entities and relationships from the text following these rules:
    1. Only extract clearly stated facts
    2. All dates must be in YYYY-MM-DD format
    3. All relationships must use predefined types
    4. Entity names must be consistent throughout
    5. Include relevant properties and metadata
    6. Prioritize most important entities and relationships first
    
    Valid entity types: Person, Organization, Location, Event, Concept, Document
    Valid relationship types: AFFILIATED_WITH, BORN_IN, CREATED, PARTICIPATED_IN, LEADS, SUCCEEDED, RELATED_TO, LOCATED_IN, MEMBER_OF

    Format the output as valid JSON inside of a code block:
    {
      "entities": [
        {"name": "", "type": "", "properties": {"description": "", "dates": [], "aliases": []}}
      ],
      "relationships": [
        {"source": "", "target": "", "type": "", "properties": {"start_date": "", "end_date": "", "description": ""}}
      ]
    }
    """

    def __init__(self):
        self.neo4j_url = os.getenv("NEO4J_CONNECTION_URL")
        self.neo4j_user = os.getenv("NEO4J_USER")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.openai_key)
        self.driver = GraphDatabase.driver(
            self.neo4j_url, auth=(self.neo4j_user, self.neo4j_password)
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.close()

    def fetch_wikipedia_content(self, title: str) -> str:
        logger.info(f"📚 Fetching Wikipedia content for: {title}")
        try:
            page = wikipedia.page(title)
            logger.info(
                f"✅ Successfully fetched {len(page.content)} characters for {title}"
            )
            return page.content
        except Exception as e:
            logger.error(f"❌ Error fetching Wikipedia content for {title}: {e}")
            raise

    def extract_structured_data(self, content: str) -> Dict[str, Any]:
        logger.info("🤖 Starting OpenAI extraction")
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.EXTRACTION_PROMPT},
                    {"role": "user", "content": content},
                ],
                temperature=0.1,
                max_tokens=2000,
            )
            logger.info("📝 Received OpenAI response")
            data = parse_json_response(response.choices[0].message.content)
            logger.info(
                f"✨ Extracted {len(data['entities'])} entities and {len(data['relationships'])} relationships"
            )
            return data
        except Exception as e:
            logger.error(f"💥 Error in OpenAI extraction: {e}")
            raise

    def create_graph(self, data: Dict[str, Any]) -> None:
        logger.info("🗄️ Starting graph creation")
        with self.driver.session() as session:
            for entity in data["entities"]:
                logger.debug(f"📋 Creating entity: {entity['name']}")
                cypher = """
                MERGE (e:{label} {{name: $name}})
                SET e += $properties
                """.format(
                    label=entity["type"]
                )

                session.run(
                    cypher,
                    {
                        "name": entity["name"],
                        "properties": entity.get("properties", {}),
                    },
                )

            for rel in data["relationships"]:
                logger.debug(
                    f"🔗 Creating relationship: {rel['source']} -> {rel['target']}"
                )
                cypher = """
                MATCH (source) WHERE source.name = $source_name
                MATCH (target) WHERE target.name = $target_name
                MERGE (source)-[r:{rel_type}]->(target)
                SET r += $properties
                """.format(
                    rel_type=rel["type"]
                )

                session.run(
                    cypher,
                    {
                        "source_name": rel["source"],
                        "target_name": rel["target"],
                        "properties": rel["properties"],
                    },
                )
        logger.info("✅ Graph creation completed")

    def process_article(self, title: str) -> None:
        try:
            logger.info(f"🎯 Processing article: {title}")
            content = self.fetch_wikipedia_content(title)
            logger.info(f"📑 Analyzing content for {title}")

            # First attempt
            try:
                data = self.extract_structured_data(content)
            except JSONDecodeError:
                logger.warning("⚠️ First attempt failed, retrying extraction...")
                # Second attempt
                data = self.extract_structured_data(content)

            logger.info(f"💾 Saving data for {title}")
            self.create_graph(data)
            logger.info(f"🎉 Successfully processed {title}")
        except Exception as e:
            logger.error(f"💀 Failed processing {title}: {e}")
            raise


def main():
    titles = [
        "Donald Trump",
        "Joseph R. Biden",
        "Kamala Devi Harris",
        "Andrzej Duda",
        "Volodymyr Zelenskyy",
        "Vladimir Vladimirovich Putin",
        "People's Republic of China",
    ]

    wikipedia.set_lang("en")
    logger.info("🚀 Starting Wikipedia knowledge graph extraction")

    with WikiKnowledgeGraph() as graph:
        for title in titles:
            graph.process_article(title)

    logger.info("✨ Knowledge graph creation completed")


if __name__ == "__main__":
    main()
