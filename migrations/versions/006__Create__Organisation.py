from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    t = Table(
        "organisation",
        meta,
        Column("id", Integer, primary_key=True),
        Column("name", NVARCHAR(255)),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("organisation", meta, autoload=True)
    t.drop()
