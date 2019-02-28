import oedialect
import getpass
import pandas as pd
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

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
    if table_name == 'mimo_global_prop':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('property', sa.VARCHAR(50)),
            sa.Column('value', sa.Float()),
            schema=schema_name)

    if table_name == 'mimo_site':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('name', sa.VARCHAR(50)),
            schema=schema_name)

    if table_name == 'mimo_commodity':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('site', sa.VARCHAR(50)),
            sa.Column('commodity', sa.VARCHAR(50)),
            sa.Column('type', sa.VARCHAR(50)),
            sa.Column('price', sa.Float()),
            sa.Column('max', sa.Float()),
            sa.Column('maxperhour', sa.Float()),
            schema=schema_name)

    if table_name == 'mimo_process':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('site', sa.VARCHAR(50)),
            sa.Column('process', sa.VARCHAR(50)),
            sa.Column('parameter', sa.VARCHAR(50)),
            sa.Column('value', sa.Float()),
            sa.Column('unit', sa.VARCHAR(50)),
            schema=schema_name)

    if table_name == 'mimo_process_commodity':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('process', sa.VARCHAR(50)),
            sa.Column('commodity', sa.VARCHAR(50)),
            sa.Column('direction', sa.VARCHAR(50)),
            sa.Column('ratio', sa.Float()),
            schema=schema_name)

    if table_name == 'mimo_transmission':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('site_in', sa.VARCHAR(50)),
            sa.Column('site_out', sa.VARCHAR(50)),
            sa.Column('transmission', sa.VARCHAR(50)),
            sa.Column('commodity', sa.VARCHAR(50)),
            sa.Column('parameter', sa.VARCHAR(50)),
            sa.Column('value', sa.Float()),
            sa.Column('unit', sa.VARCHAR(50)),
            schema=schema_name)

    if table_name == 'mimo_storage':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('site', sa.VARCHAR(50)),
            sa.Column('storage', sa.VARCHAR(50)),
            sa.Column('commodity', sa.VARCHAR(50)),
            sa.Column('parameter', sa.VARCHAR(50)),
            sa.Column('value', sa.Float()),
            sa.Column('unit', sa.VARCHAR(50)),
            schema=schema_name)

    if table_name == 'mimo_demand':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('t', sa.Integer),
            sa.Column('mid_elec', sa.Float()),
            sa.Column('south_elec', sa.Float()),
            sa.Column('north_elec', sa.Float()),
            schema=schema_name)

    if table_name == 'mimo_supim':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('index', sa.Integer, primary_key=True,
                      autoincrement=True, nullable=False),
            sa.Column('t', sa.Integer),
            sa.Column('mid_wind', sa.Float()),
            sa.Column('mid_solar', sa.Float()),
            sa.Column('mid_hydro', sa.Float()),
            sa.Column('south_wind', sa.Float()),
            sa.Column('south_solar', sa.Float()),
            sa.Column('south_hydro', sa.Float()),
            sa.Column('north_wind', sa.Float()),
            sa.Column('north_solar', sa.Float()),
            sa.Column('north_hydro', sa.Float()),
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

    for key in data:
        if isinstance(data[key].index, pd.core.index.MultiIndex):
            data[key].sort_index(inplace=True)
    return data


def split_columns(columns, sep='.'):
    if len(columns) == 0:
        return columns
    column_tuples = [tuple(col.split('.')) for col in columns]
    return pd.MultiIndex.from_tuples(column_tuples)


def normalize(data, key):
    if key == 'global_prop':
        data = data.rename(columns={'Property': 'property'})

    elif key == 'site':
        data = data.rename(columns={'Name': 'name'})

    elif key == 'commodity':
        data = data.rename(columns={'Site': 'site',
                                    'Commodity': 'commodity',
                                    'Type': 'type'})

    elif key == 'process':
        data = data.melt(['Site', 'Process']).assign(unit='')\
            .sort_values(['Site', 'Process']).reset_index(drop=True)

        data = data.rename(columns={'Site': 'site',
                                    'Process': 'process',
                                    'variable': 'parameter'})

        unit = {'inst-cap': 'MW', 'cap-lo': 'MW', 'cap-up': 'MW',
                'inv-cost': '€/MW', 'fix-cost': '€/MW/a', 'var-cost': '€/MWh',
                'wacc': None, 'depreciation': 'a'}
        data['unit'] = data['parameter'].map(unit)

    elif key == 'process_commodity':
        data = data.rename(columns={'Process': 'process',
                                    'Commodity': 'commodity',
                                    'Direction': 'direction'})

    elif key == 'transmission':
        data = data.melt(['Site In', 'Site Out', 'Transmission', 'Commodity'])\
            .assign(unit='')\
            .sort_values(['Site In', 'Site Out', 'Transmission', 'Commodity'])\
            .reset_index(drop=True)

        data = data.rename(columns={'Site In': 'site_in',
                                    'Site Out': 'site_out',
                                    'Transmission': 'transmission',
                                    'Commodity': 'commodity',
                                    'variable': 'parameter'})

        unit = {'eff': None, 'inv-cost': '€/MW', 'fix-cost': '€/MW/a',
                'var-cost': '€/MWh', 'inst-cap': 'MW', 'cap-lo': 'MW',
                'cap-up': 'MW', 'wacc': None, 'depreciation': 'a'}
        data['unit'] = data['parameter'].map(unit)

    elif key == 'storage':
        data = data.melt(['Site', 'Storage', 'Commodity']).assign(unit='')\
            .sort_values(['Site', 'Storage', 'Commodity'])\
            .reset_index(drop=True)

        data = data.rename(columns={'Site': 'site',
                                    'Storage': 'storage',
                                    'Commodity': 'commodity',
                                    'variable': 'parameter'})

        unit = {'inst-cap-c': 'MWh', 'cap-lo-c': 'MWh', 'cap-up-c': 'MWh',
                'inst-cap-p': 'MW', 'cap-lo-p': 'MW', 'cap-up-p': 'MW',
                'eff-in': None, 'eff-out': None, 'inv-cost-p': '€/MW',
                'inv-cost-c': '€/MWh', 'fix-cost-p': '€/MW/a',
                'fix-cost-c': '€/MWh/a', 'var-cost-p': '€/MWh',
                'var-cost-c': '€/MWh', 'wacc': None, 'depreciation': 'a',
                'init': None, 'discharge': None, 'ep-ratio': None}
        data['unit'] = data['parameter'].map(unit)

    elif key == 'demand':
        data = data.rename(columns={'Mid.Elec': 'mid_elec',
                                    'South.Elec': 'south_elec',
                                    'North.Elec': 'north_elec'})

    elif key == 'supim':
        data = data.rename(columns={'Mid.Wind': 'mid_wind',
                                    'Mid.Solar': 'mid_solar',
                                    'Mid.Hydro': 'mid_hydro',
                                    'South.Wind': 'south_wind',
                                    'South.Solar': 'south_solar',
                                    'South.Hydro': 'south_hydro',
                                    'North.Wind': 'north_wind',
                                    'North.Solar': 'north_solar',
                                    'North.Hydro': 'north_hydro'})

    else:
        pass

    return data


def denormalize(data, key):
    try:
        data = data.drop(columns=['index', 'unit'])
    except KeyError:
        pass

    if key == 'global_prop':
        data = data.rename(columns={'property': 'Property'})

    elif key == 'site':
        data = data.rename(columns={'name': 'Name'})

    elif key == 'commodity':
        data = data.rename(columns={'site': 'Site',
                                    'commodity': 'Commodity',
                                    'type': 'Type'})

    elif key == 'process':
        data = data.rename(columns={'site': 'Site',
                                    'process': 'Process'})

        data = data.pivot_table(values='value',
                                index=['Site', 'Process'],
                                columns='parameter',
                                dropna=False).reset_index()
        data = data.rename_axis(None, axis=1)

    elif key == 'process_commodity':
        data = data.rename(columns={'process': 'Process',
                                    'commodity': 'Commodity',
                                    'direction': 'Direction'})

    elif key == 'transmission':
        data = data.rename(columns={'site_in': 'Site In',
                                    'site_out': 'Site Out',
                                    'transmission': 'Transmission',
                                    'commodity': 'Commodity'})

        data = data.pivot_table(values='value',
                                index=['Site In', 'Site Out',
                                       'Transmission', 'Commodity'],
                                columns='parameter',
                                dropna=False).reset_index()
        data = data.rename_axis(None, axis=1)

    elif key == 'storage':
        data = data.rename(columns={'site': 'Site',
                                    'storage': 'Storage',
                                    'commodity': 'Commodity'})

        data = data.pivot_table(values='value',
                                index=['Site', 'Storage', 'Commodity'],
                                columns='parameter',
                                dropna=False).reset_index()
        data = data.rename_axis(None, axis=1)

    elif key == 'demand':
        data = data.rename(columns={'mid_elec': 'Mid.Elec',
                                    'south_elec': 'South.Elec',
                                    'north_elec': 'North.Elec'})

    elif key == 'supim':
        data = data.rename(columns={'mid_wind': 'Mid.Wind',
                                    'mid_solar': 'Mid.Solar',
                                    'mid_hydro': 'Mid.Hydro',
                                    'south_wind': 'South.Wind',
                                    'south_solar': 'South.Solar',
                                    'south_hydro': 'South.Hydro',
                                    'north_wind': 'North.Wind',
                                    'north_solar': 'North.Solar',
                                    'north_hydro': 'North.Hydro'})

    else:
        pass

    return data
