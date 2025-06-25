# here is core/containers.py
from dependency_injector import containers, providers

import logging
logger = logging.getLogger(__name__)
import os


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.repositories.user_repository import UserRepository
from db.repositories.chat_repository import ChatRepository
from db.repositories.message_repository import MessageRepository
# from db.repositories.file_repository import FileRepository
from db.session import get_engine
import yaml




class Services(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Engine provider
    engine = providers.Singleton(
        create_engine,
        config.db_url,
        echo=False
    )

    # Session factory provider
    session_factory = providers.Singleton(
        sessionmaker,
        bind=engine
    )


    # UserRepository provider
    user_repository = providers.Factory(
        UserRepository,
        session=providers.Dependency()
    )

    chat_repository = providers.Factory(
        ChatRepository,
        session=providers.Dependency()
    )


    message_repository = providers.Factory(
        MessageRepository,
        session=providers.Dependency()
    )

