# models.py
import weaviate

# Initialize Weaviate client
WEAVIATE_URL = "http://localhost:8080"
client = weaviate.Client(WEAVIATE_URL)

# Define Weaviate schema for User and Post
def create_weaviate_schema():
    user_class = {
        "class": "User",
        "properties": [
            {"name": "username", "dataType": ["string"]},
            {"name": "email", "dataType": ["string"]},
            {"name": "hashed_password", "dataType": ["string"]}
        ]
    }

    post_class = {
        "class": "Post",
        "properties": [
            {"name": "title", "dataType": ["string"]},
            {"name": "content", "dataType": ["string"]},
            {"name": "author", "dataType": ["string"]}
        ]
    }

    # Create schema in Weaviate
    client.schema.create_class(user_class)
    client.schema.create_class(post_class)
