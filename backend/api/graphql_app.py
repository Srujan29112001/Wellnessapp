"""
GraphQL API using Strawberry
"""
import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List, Optional
from datetime import datetime

from backend.api.graphql_schema import Query, Mutation


# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# Create GraphQL router
graphql_app = GraphQLRouter(
    schema,
    graphiql=True,  # Enable GraphiQL interface
    path="/",
)
