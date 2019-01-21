import pandas as pd
import getpass
import oedialect
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2.types import Geometry

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
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('Property', sa.VARCHAR(50)),
            sa.Column('value', sa.Float()),
            schema=schema_name)

    if table_name == 'ubbb_site':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('Name', sa.VARCHAR(50)),
            sa.Column('area', sa.VARCHAR(50)),
            schema=schema_name)

    if table_name == 'ubbb_commodity':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('Site', sa.VARCHAR(50)),
            sa.Column('Commodity', sa.VARCHAR(50)),
            sa.Column('Type', sa.VARCHAR(50)),
            sa.Column('price', sa.Float()),
            sa.Column('max', sa.Float()),
            sa.Column('maxperhour', sa.Float()),
            schema=schema_name)

    if table_name == 'ubbb_process':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('Site', sa.VARCHAR(50)),
            sa.Column('Process', sa.VARCHAR(50)),
            sa.Column('inst-cap', sa.Float()),
            sa.Column('cap-lo', sa.Float()),
            sa.Column('cap-up', sa.Float()),
            sa.Column('max-grad', sa.Float()),
            sa.Column('min-fraction', sa.Float()),
            sa.Column('inv-cost', sa.Float()),
            sa.Column('fix-cost', sa.Float()),
            sa.Column('var-cost', sa.Float()),
            sa.Column('wacc', sa.Float()),
            sa.Column('depreciation', sa.Float()),
            sa.Column('area-per-cap', sa.Float()),
            schema=schema_name)

    if table_name == 'ubbb_process_commodity':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('Process', sa.VARCHAR(50)),
            sa.Column('Commodity', sa.VARCHAR(50)),
            sa.Column('Direction', sa.VARCHAR(50)),
            sa.Column('ratio', sa.Float()),
            sa.Column('ratio-min', sa.Float()),
            schema=schema_name)

    if table_name == 'ubbb_transmission':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('Site In', sa.VARCHAR(50)),
            sa.Column('Site Out', sa.VARCHAR(50)),
            sa.Column('Transmission', sa.VARCHAR(50)),
            sa.Column('Commodity', sa.VARCHAR(50)),
            sa.Column('eff', sa.Float()),
            sa.Column('inv-cost', sa.Float()),
            sa.Column('fix-cost', sa.Float()),
            sa.Column('var-cost', sa.Float()),
            sa.Column('inst-cap', sa.Float()),
            sa.Column('cap-lo', sa.Float()),
            sa.Column('cap-up', sa.Float()),
            sa.Column('wacc', sa.Float()),
            sa.Column('depreciation', sa.Float()),
            schema=schema_name)

    if table_name == 'ubbb_storage':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('Site', sa.VARCHAR(50)),
            sa.Column('Storage', sa.VARCHAR(50)),
            sa.Column('Commodity', sa.VARCHAR(50)),
            sa.Column('inst-cap-c', sa.Float()),
            sa.Column('cap-lo-c', sa.Float()),
            sa.Column('cap-up-c', sa.Float()),
            sa.Column('inst-cap-p', sa.Float()),
            sa.Column('cap-lo-p', sa.Float()),
            sa.Column('cap-up-p', sa.Float()),
            sa.Column('eff-in', sa.Float()),
            sa.Column('eff-out', sa.Float()),
            sa.Column('inv-cost-p', sa.Float()),
            sa.Column('inv-cost-c', sa.Float()),
            sa.Column('fix-cost-p', sa.Float()),
            sa.Column('fix-cost-c', sa.Float()),
            sa.Column('var-cost-p', sa.Float()),
            sa.Column('var-cost-c', sa.Float()),
            sa.Column('wacc', sa.Float()),
            sa.Column('depreciation', sa.Float()),
            sa.Column('init', sa.Float()),
            sa.Column('discharge', sa.Float()),
            sa.Column('ep-ratio', sa.Float()),
            schema=schema_name)

    if table_name == 'ubbb_demand':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('t', sa.Integer),
            sa.Column('Mid.Elec', sa.Float()),
            sa.Column('South.Elec', sa.Float()),
            sa.Column('North.Elec', sa.Float()),
            schema=schema_name)

    if table_name == 'ubbb_supim':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('t', sa.Integer),
            sa.Column('Mid.Wind', sa.Float()),
            sa.Column('Mid.Solar', sa.Float()),
            sa.Column('Mid.Hydro', sa.Float()),
            sa.Column('South.Wind', sa.Float()),
            sa.Column('South.Solar', sa.Float()),
            sa.Column('South.Hydro', sa.Float()),
            sa.Column('North.Wind', sa.Float()),
            sa.Column('North.Solar', sa.Float()),
            sa.Column('North.Hydro', sa.Float()),
            schema=schema_name)

    if table_name == 'ubbb_eff_factor':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('t', sa.Integer),
            schema=schema_name)

    return table


def upload_to_oep(df, table, engine, metadata):
    table_name = table.name
    schema_name = table.schema

    if not engine.dialect.has_table(engine, table_name, schema_name):
        table.create()
        print('Created table')
    else:
        print('Table already exists')
        table.drop(engine)
        table.create()
        print('Created table')

    # insert data
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        dtype = {key: table.columns[key].type for key in table.columns.keys()}
        df.to_sql(table_name, engine, schema=schema_name, if_exists='replace',
                  dtype=dtype)
        print('Inserted to ' + table_name)
    except Exception as e:
        session.rollback()
        session.close()
        raise
        print('Insert incomplete!')
    finally:
        session.close()

    return table


def get_df(engine, table):
    Session = sessionmaker(bind=engine)
    session = Session()
    df = pd.DataFrame(session.query(table).all())
    session.close()

    return df


def write_data(data):
    for key in data:
        try:
            data[key] = data[key].drop(columns='index')
        except KeyError:
            pass
        data[key].fillna(value=pd.np.nan, inplace=True)

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
