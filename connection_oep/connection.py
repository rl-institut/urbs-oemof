import getpass
import oedialect
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2.types import Geometry
import pandas as pd
import pdb

Base = declarative_base()

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


def setup_table(table_name, schema_name='sandbox',
                metadata=None):
    if table_name == 'ubbb_global_prop':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True, autoincrement=True,
                      nullable=False),
            sa.Column('Property', sa.VARCHAR(50)),
            sa.Column('value', sa.FLOAT(50)),
            schema=schema_name)

    if table_name == 'ubbb_site':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True, autoincrement=True,
                      nullable=False),
            sa.Column('Name', sa.VARCHAR(50)),
            sa.Column('area', sa.VARCHAR(50)),
            schema=schema_name)

    if table_name == 'ubbb_commodity':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True, autoincrement=True,
                      nullable=False),
            sa.Column('Site', sa.VARCHAR(50)),
            sa.Column('Commodity', sa.VARCHAR(50)),
            sa.Column('Type', sa.VARCHAR(50)),
            sa.Column('price', sa.FLOAT(50)),
            sa.Column('max', sa.FLOAT(50)),
            sa.Column('maxperhour', sa.FLOAT(50)),
            schema=schema_name)

    if table_name == 'ubbb_process':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True, autoincrement=True,
                      nullable=False),
            sa.Column('Site', sa.VARCHAR(50)),
            sa.Column('Process', sa.VARCHAR(50)),
            sa.Column('inst-cap', sa.FLOAT(50)),
            sa.Column('cap-lo', sa.FLOAT(50)),
            sa.Column('cap-up', sa.FLOAT(50)),
            sa.Column('max-grad', sa.FLOAT(50)),
            sa.Column('min-fraction', sa.FLOAT(50)),
            sa.Column('inv-cost', sa.FLOAT(50)),
            sa.Column('fix-cost', sa.FLOAT(50)),
            sa.Column('var-cost', sa.FLOAT(50)),
            sa.Column('wacc', sa.FLOAT(50)),
            sa.Column('depreciation', sa.FLOAT(50)),
            sa.Column('area-per-cap', sa.FLOAT(50)),
            schema=schema_name)
    return table


def upload_to_oep(df, Table, engine, metadata):
    table_name = Table.name
    schema_name = Table.schema

    if not engine.dialect.has_table(engine, table_name, schema_name):
        Table.create()
        print('Created table')
    else:
        print('Table already exists')

    # insert data
    try:
        df.to_sql(table_name, engine, schema='sandbox', if_exists='replace')
        print('Inserted to ' + table_name)
    except Exception as e:
        Session = sessionmaker(bind=engine)
        session = Session()
        session.rollback()
        session.close()
        raise
        print('Insert incomplete!')

    return Table


def get_df(engine, table):
    Session = sessionmaker(bind=engine)
    session = Session()
    df = pd.DataFrame(session.query(table).all())
    session.close()

    return df


"""
def get_df(engine):
    data = {}
    Session = sessionmaker(bind=engine)
    session = Session()
    session.close()

    data['global_prop'] = pd.DataFrame(
        session.query(global_prop.Property, global_prop.value).all())
    data['site'] = pd.DataFrame(
        session.query(site.Name, site.area).all())
    data['commodity'] = pd.DataFrame(
        session.query(commodity.Site, commodity.Commodity, commodity.Type,
                      commodity.price, commodity.max, commodity.maxperhour).all())
    data['process'] = 0
    data['process_commodity'] = 0
    data['transmission'] = 0
    data['storage'] = 0
    data['demand'] = 0
    data['supim'] = 0
    data['eff_factor'] = 0
    import pdb; pdb.set_trace()
    data = write_data(data)
    return data


def write_data(data):
    data['global_prop'] = data['global_prop'].set_index(['Property'])
    data['site'] = data['site'].set_index(['Name'])
    data['commodity'] = data['commodity'].set_index(
                            ['Site', 'Commodity', 'Type'])
    data['process'] = data['process'].set_index(['Site', 'Process'])
    data['process_commodity'] = data['process_commodity'].set_index(
                                    ['Process', 'Commodity', 'Direction'])
    data['transmission'] = data['transmission'].set_index(
                               ['Site In', 'Site Out',
                                'Transmission', 'Commodity'])
    data['storage'] = data['storage'].set_index(
                          ['Site', 'Storage', 'Commodity'])
    data['demand'] = data['demand'].set_index(['t'])
    data['demand'].columns = split_columns(data['demand'].columns, '.')
    data['supim'] = data['supim'].set_index(['t'])
    data['supim'].columns = split_columns(data['supim'].columns, '.')
    data['eff_factor'] = data['eff_factor'].set_index(['t'])
    data['eff_factor'].columns = split_columns(data['eff_factor'].columns, '.')

    for key in data:
        if isinstance(data[key].index, pd.core.index.MultiIndex):
            data[key].sort_index(inplace=True)
    return data


def split_columns(columns, sep='.'):
    if len(columns) == 0:
        return columns
    column_tuples = [tuple(col.split('.')) for col in columns]
    return pd.MultiIndex.from_tuples(column_tuples)
"""
