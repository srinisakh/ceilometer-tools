from ceilometer.openstack.common.db.sqlalchemy import migration
from ceilometer import service
from ceilometer import storage
from oslo.config import cfg
import os

VERSION_TO_DOWNGRADE=37
PATH_TO_MIGRATE_REPO='/opt/stack/ceilometer/ceilometer/storage/sqlalchemy/migrate_repo'

service.prepare_service()
conn = storage.get_connection_from_config(cfg.CONF)
engine = conn._engine_facade.get_engine()
#path to migrate_repo
migration.db_sync(engine, PATH_TO_MIGRATE_REPO, version=VERSION_TO_DOWNGRADE)

