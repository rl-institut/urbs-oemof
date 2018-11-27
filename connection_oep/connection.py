import getpass
import oedialect
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2.types import Geometry
import pandas as pd
import pdb

Base = declarative_base()

class global_prop(Base):
    __tablename__ = 'ubbb_global_prop'
    __table_args__ = {'schema': 'model_draft'}

    id = sa.Column(sa.Integer, primary_key=True, nullable=False,
                   server_default=sa.text("nextval('model_draft.ubbb_global_prop_id_seq'::regclass)"))
    Property = sa.Column(sa.String())
    value = sa.Column(sa.Float())


class site(Base):
    __tablename__ = 'ubbb_site'
    __table_args__ = {'schema': 'model_draft'}

    id = sa.Column(sa.Integer, primary_key=True, nullable=False,
                   server_default=sa.text("nextval('model_draft.ubbb_site_id_seq'::regclass)"))
    Name = sa.Column(sa.String())
    area = sa.Column(sa.String())


class commodity(Base):
    __tablename__ = 'ubbb_commodity'
    __table_args__ = {'schema': 'model_draft'}

    id = sa.Column(sa.Integer, primary_key=True, nullable=False,
                   server_default=sa.text("nextval('model_draft.ubbb_commodity_id_seq'::regclass)"))
    Site = sa.Column(sa.String())
    Commodity = sa.Column(sa.String())
    Type = sa.Column(sa.String())
    price = sa.Column(sa.Float())
    max = sa.Column(sa.Float())
    maxperhour = sa.Column(sa.Float())


def send_df(input_file):
    # Read Data
    data = read_data(input_file)

    # Login Details
    engine, metadata = connect_oep('Okan Akca',
                                   'd7b3e9ab325abc843e4b54ac37dad544d8345ca1')

    for i in data:
        if i is 'global_prop' or i is 'site' or i is 'commodity':
            # Setup Table in OEP
            table = setup_table(table_name='ubbb_'+i, schema_name='model_draft',
                                metadata=metadata)

            # Create Table in OEP
            if not engine.dialect.has_table(engine, 'ubbb_'+i, 'model_draft'):
                #table.drop(engine)
                table.create()
                data[i].to_sql('ubbb_'+i, engine, schema='model_draft',
                               if_exists='append', index=None)
            else:
                table.drop(engine)
                table.create()
                data[i].to_sql('ubbb_'+i, engine, schema='model_draft',
                               if_exists='append', index=None)
        else:
            print(i)

    return engine

    # Remove Table from OEP
    #table.drop(engine)


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
                metadata=None):
    if table_name == 'ubbb_global_prop':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True,
                      nullable=False),
            sa.Column('Property', sa.String()),
            sa.Column('value', sa.Float()),
            schema=schema_name)

    if table_name == 'ubbb_site':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True,
                      nullable=False),
            sa.Column('Name', sa.String(50)),
            sa.Column('area', sa.String(50)),
            schema=schema_name)

    if table_name == 'ubbb_commodity':
        table = sa.Table(
            table_name,
            metadata,
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True,
                      nullable=False),
            sa.Column('Site', sa.String(50)),
            sa.Column('Commodity', sa.String(50)),
            sa.Column('Type', sa.String(50)),
            sa.Column('price', sa.Float(10)),
            sa.Column('max', sa.Float(10)),
            sa.Column('maxperhour', sa.Float(10)),
            schema=schema_name)
    return table
