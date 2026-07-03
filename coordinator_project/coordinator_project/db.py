import os

from mongoengine import connect, disconnect


def connect_db():
    host = os.environ.get("MONGODB_HOST", "localhost")
    port = int(os.environ.get("MONGODB_PORT", "27017"))
    db = os.environ.get("MONGODB_NAME", "coordinator_db")
    disconnect()
    connect(db=db, host=host, port=port)
