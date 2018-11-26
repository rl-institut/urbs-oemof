import getpass
import oedialect
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2.types import Geometry
import pandas as pd


Base = declarative_base()

class site(Base):
    __tablename__ = 'site_example'
    __table_args__ = {'schema': 'sandbox'}

    id = sa.Column(sa.Integer, primary_key=True, nullable=False,
                   server_default=sa.text("nextval('model_draft.site_example_id_seq'::regclass)"))
    Name = sa.Column(sa.String())
    area = sa.Column(sa.String())


def read_data(filename):
    with pd.ExcelFile(filename) as xls:

        sheetnames = xls.sheet_names

        site = xls.parse('Site')
        commodity = xls.parse('Commodity')
        process = xls.parse('Process')
        process_commodity = xls.parse('Process-Commodity')
        transmission = xls.parse('Transmission')
        storage = xls.parse('Storage')
        demand = xls.parse('Demand')
        supim = xls.parse('SupIm')
        global_prop = xls.parse('Global')
        eff_factor = xls.parse('TimeVarEff')

    data = {
        'global_prop': global_prop,
        'site': site,
        'commodity': commodity,
        'process': process,
        'process_commodity': process_commodity,
        'transmission': transmission,
        'storage': storage,
        'demand': demand,
        'supim': supim,
        'eff_factor': eff_factor
        }

    return data


def connect_oep(user=None, token=None):
    if user is None or token is None:
        user = input('Enter OEP-username:')
        token = getpass.getpass('Token:')

    # Create Engine:
    OEP_URL = 'openenergy-platform.org'
    OED_STRING = f'postgresql+oedialect://{user}:{token}@{OEP_URL}'

    engine = sa.create_engine(OED_STRING)
    metadata = sa.MetaData(bind=engine)
    engine = engine.connect()

    return engine, metadata


def setup_table(table_name, schema_name='model_draft',
                metadata=None, data=None):

    table = sa.Table(
        table_name,
        metadata,
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True, nullable=False),
        sa.Column('Name', sa.String(50)),
        sa.Column('area', sa.String(50)),
        schema=schema_name)

    return table
