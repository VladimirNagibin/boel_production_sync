import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from core.settings import settings
from db.postgres import Base
from models.communications import (  # noqa: F401
    CommunicationChannel,
    CommunicationChannelType,
)
from models.company_models import Company  # noqa: F401
from models.contact_models import Contact  # noqa: F401
from models.deal_documents import Billing, Contract  # noqa: F401
from models.deal_models import AdditionalInfo, Deal  # noqa: F401
from models.delivery_note_models import DeliveryNote  # noqa: F401
from models.invoice_models import Invoice  # noqa: F401
from models.lead_models import Lead  # noqa: F401
from models.references import Industry  # noqa: F401
from models.references import InvoiceStage  # noqa: F401
from models.references import LeadStatus  # noqa: F401
from models.references import MainActivity  # noqa: F401
from models.references import ShippingCompany  # noqa: F401
from models.references import Source  # noqa: F401
from models.references import Warehouse  # noqa: F401
from models.references import (  # noqa: F401
    AdditionalResponsible,
    Category,
    ContactType,
    CreationSource,
    Currency,
    DealFailureReason,
    DealStage,
    DealType,
    DefectType,
    Department,
    Emploees,
    Measure,
)
from models.timeline_comment_models import TimelineComment  # noqa: F401
from models.user_models import Manager, User  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", settings.dsn)
# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
