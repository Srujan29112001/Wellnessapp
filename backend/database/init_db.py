"""
Database Initialization Script

Creates all tables, indexes, and seeds initial data
"""
import asyncio
import logging
from datetime import datetime

from backend.database.postgres import init_db as init_postgres, AsyncSessionLocal
from backend.database.mongo import init_mongo
from backend.models.postgres_models import User, Dosha, Gender
from backend.models.mongo_schemas import UserContext
from backend.database.mongo import get_mongo_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_demo_user():
    """Create a demo user for testing"""
    async with AsyncSessionLocal() as session:
        # Check if demo user exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == "demo@wellness.ai")
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.info("Demo user already exists")
            return existing_user

        # Create demo user
        demo_user = User(
            email="demo@wellness.ai",
            name="Demo User",
            password_hash="$2b$12$demo_hash_not_for_production",  # Placeholder
            age=30,
            gender=Gender.NON_BINARY,
            dosha_type=Dosha.VATA_PITTA,
            health_goals=["reduce_stress", "improve_sleep", "increase_energy"],
            dietary_restrictions=["vegetarian"],
            medical_conditions=[],
            current_medications=[],
            preferences={
                "notifications": True,
                "communication_style": "empathetic",
                "preferred_language": "en"
            }
        )

        session.add(demo_user)
        await session.commit()
        await session.refresh(demo_user)

        logger.info(f"Created demo user: {demo_user.id}")

        # Create user context in MongoDB
        db = get_mongo_db()
        user_context = {
            "user_id": demo_user.id,
            "patterns": {},
            "insights": [],
            "communication_style": "empathetic",
            "preferred_interventions": ["breathing", "meditation"],
            "topics_of_interest": ["stress_management", "sleep_optimization"],
            "active_goals": [
                {
                    "goal": "reduce_stress",
                    "target": "< 30% daily average",
                    "started_at": datetime.now().isoformat()
                }
            ],
            "completed_goals": [],
            "milestones": [],
            "key_memories": [],
            "updated_at": datetime.now()
        }

        await db.user_context.insert_one(user_context)
        logger.info("Created user context in MongoDB")

        return demo_user


async def seed_knowledge_graph():
    """Seed Neo4j knowledge graph with initial data"""
    try:
        from neo4j import AsyncGraphDatabase
        from config.settings import settings
        import json

        driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

        async with driver.session() as session:
            # Clear existing data (for clean setup)
            await session.run("MATCH (n) DETACH DELETE n")
            logger.info("Cleared existing Neo4j data")

            # Load Ayurvedic doshas
            with open("knowledge_base/ayurveda/doshas.json", "r") as f:
                doshas_data = json.load(f)

            for dosha_name, dosha_info in doshas_data.items():
                # Create dosha node
                await session.run(
                    """
                    CREATE (d:Dosha {
                        name: $name,
                        description: $description,
                        characteristics: $characteristics
                    })
                    """,
                    name=dosha_name,
                    description=dosha_info.get("description", ""),
                    characteristics=json.dumps(dosha_info.get("characteristics", {}))
                )

                # Create food nodes and relationships
                for food_type in ["balancing_foods", "foods_to_reduce"]:
                    foods = dosha_info.get(food_type, [])
                    relationship = "BALANCES" if food_type == "balancing_foods" else "AGGRAVATES"

                    for food in foods:
                        await session.run(
                            f"""
                            MERGE (f:Food {{name: $food}})
                            WITH f
                            MATCH (d:Dosha {{name: $dosha}})
                            CREATE (f)-[r:{relationship}]->(d)
                            """,
                            food=food,
                            dosha=dosha_name
                        )

                # Create herb nodes and relationships
                herbs = dosha_info.get("recommended_herbs", [])
                for herb in herbs:
                    await session.run(
                        """
                        MERGE (h:Herb {name: $name, properties: $properties})
                        WITH h
                        MATCH (d:Dosha {name: $dosha})
                        CREATE (h)-[:BALANCES]->(d)
                        """,
                        name=herb.get("name", ""),
                        properties=herb.get("properties", ""),
                        dosha=dosha_name
                    )

            # Load supplements
            with open("knowledge_base/supplements/supplements_db.json", "r") as f:
                supplements_data = json.load(f)

            supplements = supplements_data.get("supplements", [])
            for supp in supplements:
                # Create supplement node
                await session.run(
                    """
                    CREATE (s:Supplement {
                        name: $name,
                        category: $category,
                        description: $description,
                        benefits: $benefits,
                        dosage: $dosage
                    })
                    """,
                    name=supp.get("name", ""),
                    category=supp.get("category", ""),
                    description=supp.get("description", ""),
                    benefits=json.dumps(supp.get("benefits", [])),
                    dosage=json.dumps(supp.get("dosage", {}))
                )

                # Create relationships for benefits
                for benefit in supp.get("benefits", []):
                    await session.run(
                        """
                        MERGE (b:Benefit {name: $benefit})
                        WITH b
                        MATCH (s:Supplement {name: $supp_name})
                        CREATE (s)-[:PROVIDES]->(b)
                        """,
                        benefit=benefit,
                        supp_name=supp.get("name", "")
                    )

                # Create contraindication nodes
                for contra in supp.get("contraindications", []):
                    await session.run(
                        """
                        MERGE (c:Contraindication {name: $contra})
                        WITH c
                        MATCH (s:Supplement {name: $supp_name})
                        CREATE (s)-[:CONTRAINDICATED_WITH]->(c)
                        """,
                        contra=contra,
                        supp_name=supp.get("name", "")
                    )

            logger.info("Seeded Neo4j knowledge graph successfully")

        await driver.close()

    except Exception as e:
        logger.error(f"Error seeding knowledge graph: {e}")
        logger.warning("Continuing without Neo4j seeding...")


async def initialize_all_databases():
    """Initialize all databases and seed initial data"""
    logger.info("=== Starting Database Initialization ===")

    # 1. Initialize PostgreSQL
    logger.info("Initializing PostgreSQL...")
    await init_postgres()

    # 2. Initialize MongoDB
    logger.info("Initializing MongoDB...")
    await init_mongo()

    # 3. Create demo user
    logger.info("Creating demo user...")
    await create_demo_user()

    # 4. Seed Neo4j knowledge graph
    logger.info("Seeding Neo4j knowledge graph...")
    await seed_knowledge_graph()

    logger.info("=== Database Initialization Complete ===")


if __name__ == "__main__":
    asyncio.run(initialize_all_databases())
