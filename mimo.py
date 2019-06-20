###############################################################################
# IMPORTS
###############################################################################
# urbs
import urbs
from pyomo.opt.base import SolverFactory

# oemof
import oemofm
import oemof.solph as solph
import oemof.outputlib as outputlib
from oemof.graph import create_nx_graph

# comparison
import comparison as comp

# connection
import connection_oep as conn

# misc.
import os
import time
import pandas as pd


###############################################################################
# Comparison & Benchmarking
###############################################################################
def benchmarking(input_data):
    """
    Function for benchmarking urbs & oemof

    Args:
        input_data: input data

    Returns:
        bench: a dictionary containing benchmarking values
    """
    # init
    bench = {}

    # [1,10,20,30,40,50,60,70,80,90,100,200,300,400,500,600,700,800,900,1000]
    for i in range(1, 1001):
        # simulation timesteps
        (offset, length) = (0, i)  # time step selection
        timesteps = range(offset, offset + length + 1)

        if i == 1:
            urbs_model, urbs_time = create_um(input_data, timesteps)
            oemof_model, oemof_time = create_om(input_data, timesteps)

            bench[i] = comparison(urbs_model, oemof_model,
                                  threshold=0.1, benchmark=True)

            # setting build time for urbs
            bench[i][0]['build'] = urbs_time
            # setting build time for oemof
            bench[i][1]['build'] = oemof_time

        elif i <= 100 and i % 10 == 0:
            urbs_model, urbs_time = create_um(input_data, timesteps)
            oemof_model, oemof_time = create_om(input_data, timesteps)

            bench[i] = comparison(urbs_model, oemof_model,
                                  threshold=0.1, benchmark=True)

            # setting build time for urbs
            bench[i][0]['build'] = urbs_time
            # setting build time for oemof
            bench[i][1]['build'] = oemof_time

        elif i > 100 and i % 100 == 0:
            urbs_model, urbs_time = create_um(input_data, timesteps)
            oemof_model, oemof_time = create_om(input_data, timesteps)

            bench[i] = comparison(urbs_model, oemof_model,
                                  threshold=0.1, benchmark=True)

            # setting build time for urbs
            bench[i][0]['build'] = urbs_time
            # setting build time for oemof
            bench[i][1]['build'] = oemof_time

        else:
            pass

    # process benchmark
    comp.process_benchmark(bench)
    return bench


def comparison(u_model, o_model, threshold=0.1, benchmark=False):
    """
    Function for comparing urbs & oemof

    Args:
        u_model: urbs model instance use create_um() to generate
        o_model: oemof model instance use create_om() to generate
        threshold: threshold value for outputting the differences
        benchmark: a parameter for activate/deactivate benchmarking

    Returns:
        urbs: a dictionary containing the specific values
        oemof:  a dictionary containing the specific values
    """
    # init
    urbs = {}
    oemof = {}

    # compare objective
    urbs['obj'] = u_model.obj()
    oemof['obj'] = o_model.objective()

    # terminal output
    print('----------------------------------------------------')
    if u_model.obj() != o_model.objective():
        print('OBJECTIVE')
        print('urbs\t', u_model.obj())
        print('oemof\t', o_model.objective())
        print('Diff\t', u_model.obj() - o_model.objective())
    print('----------------------------------------------------')

    # create oemof energysytem
    o_model = solph.EnergySystem()
    o_model.restore(dpath=None, filename=None)

    # compare cpu and memory
    urbs['cpu'], urbs['memory'], oemof['cpu'], oemof['memory'] = \
        comp.compare_cpu_and_memory()

    # compare lp files
    urbs['const'], oemof['const'] = comp.compare_lp_files()

    # compare model variables
    if len(u_model.tm) >= 2 and not benchmark:
        urbs['sto'], oemof['sto'] = \
            comp.compare_storages(u_model, o_model, threshold)
        urbs['tra'], oemof['tra'] = \
            comp.compare_transmission(u_model, o_model, threshold)
        urbs['pro'], oemof['pro'] = \
            comp.compare_process(u_model, o_model, threshold)
    else:
        pass

    return urbs, oemof


###############################################################################
# urbs Model
###############################################################################

# create urbs model
def create_um(input_data, timesteps):
    """
    Creates an urbs model for given input, time steps

    Args:
        input_data: input data
        timesteps: simulation timesteps

    Returns:
        model: a model instance
    """
    # create model
    print('CREATING urbs MODEL')
    start = time.perf_counter()
    model = urbs.create_model(input_data, 1, timesteps)
    end = time.perf_counter()

    # solve model and read results
    optim = SolverFactory('glpk')
    result = optim.solve(model, logfile='urbs_log.txt', tee=False)

    # write LP file
    filename = os.path.join(os.path.dirname(__file__), 'mimo_urbs.lp')
    model.write(filename, io_options={'symbolic_solver_labels': True})

    return model, end - start


###############################################################################
# oemof Model
###############################################################################

# create oemof model
def create_om(input_data, timesteps):
    """
    Creates an oemof model for given input, time steps

    Args:
        input_data: input data
        timesteps: simulation timesteps

    Returns:
        model: a model instance
    """
    # create oemof energy system
    print('CREATING oemof MODEL')
    start = time.perf_counter()
    es, model = oemofm.create_model(input_data, timesteps)
    end = time.perf_counter()

    # solve model and read results
    model.solve(solver='glpk',
                solve_kwargs={'logfile': 'oemof_log.txt', 'tee': False})

    # write LP file
    filename = os.path.join(os.path.dirname(__file__), 'mimo_oemof.lp')
    model.write(filename, io_options={'symbolic_solver_labels': True})

    # draw graph
    graph = False
    if graph:
        graph = create_nx_graph(es, model)
        oemofm.draw_graph(graph, plot=True, layout='neato', node_size=3000,
                          node_color={'b_0': '#cd3333',
                                      'b_1': '#7EC0EE',
                                      'b_2': '#eeac7e'})

    # get results
    es.results['main'] = outputlib.processing.results(model)
    es.dump(dpath=None, filename=None)

    return model, end - start


if __name__ == '__main__':
    # connection to OEP
    connection = False

    # benchmarking
    benchmark = False

    # input file
    input_file = 'mimo.xlsx'

    # simulation timesteps
    (offset, length) = (0, 10)  # time step selection
    timesteps = range(offset, offset + length + 1)

    # load data
    data = conn.read_data(input_file)

    # establish connection to OEP
    if connection:
        # config for OEP
        username, token = open("config.ini", "r").readlines()

        # create engine
        engine, metadata = conn.connect_oep(username, token)
        print('OEP Connection established')

        # create table
        table = {}
        input_data = {}
        for key in data:
            # normalize data for database
            data[key] = conn.normalize(data[key], key)

            # setup table
            table['mimo_'+key] = conn.setup_table('mimo_'+key,
                                                  schema_name='sandbox',
                                                  metadata=metadata)
            """
            # upload to OEP
            table['mimo_'+key] = conn.upload_to_oep(data[key],
                                                    table['mimo_'+key],
                                                    engine, metadata)
            """
            # download from OEP
            input_data[key] = conn.get_df(engine, table['mimo_'+key])

            # denormalize data for models
            input_data[key] = conn.denormalize(input_data[key], key)

        # write data
        input_data = conn.write_data(input_data)

    else:
        # write data
        input_data = data
        input_data = conn.write_data(input_data)

    # benchmarking
    if benchmark:
        print('BENCHMARKING----------------------------------------')
        benchmarking(input_data)
        print('BENCHMARKING-COMPLETED------------------------------')

    # comparing
    else:
        print('COMPARING-------------------------------------------')
        urbs_model, urbs_time = create_um(input_data, timesteps)
        oemof_model, oemof_time = create_om(input_data, timesteps)
        urbs, oemof = comparison(urbs_model, oemof_model, threshold=0.1)
        print('COMPARING-COMPLETED---------------------------------')

        # send results to OEP
        if connection:
            output = {'urbs': 
                         {'storage_capacity_mid': urbs['sto']['Mid'][0],
                          'storage_capacity_south': urbs['sto']['South'][0],
                          'storage_capacity_north': urbs['sto']['North'][0],
                          'storage_power_mid': urbs['sto']['Mid'][0],
                          'storage_power_south': urbs['sto']['South'][0],
                          'storage_power_north': urbs['sto']['North'][0],
                          'transmission_capacity_mid_south': urbs['tra']['MidSouth'],
                          'transmission_capacity_mid_north': urbs['tra']['MidNorth'],
                          'transmission_capacity_south_mid': urbs['tra']['SouthMid'],
                          'transmission_capacity_south_north': urbs['tra']['SouthNorth'],
                          'transmission_capacity_north_south': urbs['tra']['NorthSouth'],
                          'transmission_capacity_north_mid': urbs['tra']['NorthMid'],
                          'process_capacity_mid_biomass': urbs['pro']['MidBiomass'],
                          'process_capacity_mid_coal': urbs['pro']['MidCoal'],
                          'process_capacity_mid_gas': urbs['pro']['MidGas'],
                          'process_capacity_mid_lignite': urbs['pro']['MidLignite'],
                          'process_capacity_mid_hydro': urbs['pro']['MidHydro'],
                          'process_capacity_mid_solar': urbs['pro']['MidSolar'],
                          'process_capacity_mid_wind': urbs['pro']['MidWind'],
                          'process_capacity_south_biomass': urbs['pro']['SouthBiomass'],
                          'process_capacity_south_coal': urbs['pro']['SouthCoal'],
                          'process_capacity_south_gas': urbs['pro']['SouthGas'],
                          'process_capacity_south_lignite': urbs['pro']['SouthLignite'],
                          'process_capacity_south_hydro': urbs['pro']['SouthHydro'],
                          'process_capacity_south_solar': urbs['pro']['SouthSolar'],
                          'process_capacity_south_wind': urbs['pro']['SouthWind'],
                          'process_capacity_north_biomass': urbs['pro']['NorthBiomass'],
                          'process_capacity_north_coal': urbs['pro']['NorthCoal'],
                          'process_capacity_north_gas': urbs['pro']['NorthGas'],
                          'process_capacity_north_lignite': urbs['pro']['NorthLignite'],
                          'process_capacity_north_hydro': urbs['pro']['NorthHydro'],
                          'process_capacity_north_solar': urbs['pro']['NorthSolar'],
                          'process_capacity_north_wind': urbs['pro']['NorthWind']
                         },
                      'oemof': 
                         {'storage_capacity_mid': oemof['sto']['Mid'][0],
                          'storage_capacity_south': oemof['sto']['South'][0],
                          'storage_capacity_north': oemof['sto']['North'][0],
                          'storage_power_mid': oemof['sto']['Mid'][0],
                          'storage_power_south': oemof['sto']['South'][0],
                          'storage_power_north': oemof['sto']['North'][0],
                          'transmission_capacity_mid_south': oemof['tra']['MidSouth'],
                          'transmission_capacity_mid_north': oemof['tra']['MidNorth'],
                          'transmission_capacity_south_mid': oemof['tra']['SouthMid'],
                          'transmission_capacity_south_north': oemof['tra']['SouthNorth'],
                          'transmission_capacity_north_south': oemof['tra']['NorthSouth'],
                          'transmission_capacity_north_mid': oemof['tra']['NorthMid'],
                          'process_capacity_mid_biomass': oemof['pro']['MidBiomass'],
                          'process_capacity_mid_coal': oemof['pro']['MidCoal'],
                          'process_capacity_mid_gas': oemof['pro']['MidGas'],
                          'process_capacity_mid_lignite': oemof['pro']['MidLignite'],
                          'process_capacity_mid_hydro': oemof['pro']['MidHydro'],
                          'process_capacity_mid_solar': oemof['pro']['MidSolar'],
                          'process_capacity_mid_wind': oemof['pro']['MidWind'],
                          'process_capacity_south_biomass': oemof['pro']['SouthBiomass'],
                          'process_capacity_south_coal': oemof['pro']['SouthCoal'],
                          'process_capacity_south_gas': oemof['pro']['SouthGas'],
                          'process_capacity_south_lignite': oemof['pro']['SouthLignite'],
                          'process_capacity_south_hydro': oemof['pro']['SouthHydro'],
                          'process_capacity_south_solar': oemof['pro']['SouthSolar'],
                          'process_capacity_south_wind': oemof['pro']['SouthWind'],
                          'process_capacity_north_biomass': oemof['pro']['NorthBiomass'],
                          'process_capacity_north_coal': oemof['pro']['NorthCoal'],
                          'process_capacity_north_gas': oemof['pro']['NorthGas'],
                          'process_capacity_north_lignite': oemof['pro']['NorthLignite'],
                          'process_capacity_north_hydro': oemof['pro']['NorthHydro'],
                          'process_capacity_north_solar': oemof['pro']['NorthSolar'],
                          'process_capacity_north_wind': oemof['pro']['NorthWind']
                         }
                     }

            output_df = pd.DataFrame(output)
            output_df = (output_df.assign(variable=output_df.index)
                                  .assign(unit='')
                                  .assign(version='v0.1')
                                  .assign(aggregation=False)
                                  .assign(updated=pd.Timestamp.now())
                                  .rename(columns={'urbs': 'urbs_value', 'oemof': 'oemof_value'})
                                  .reset_index(drop=True))
            unit = {'storage_capacity_mid': 'MWh',
                    'storage_capacity_south': 'MWh',
                    'storage_capacity_north': 'MWh',
                    'storage_power_mid': 'MW',
                    'storage_power_south': 'MW',
                    'storage_power_north': 'MW',
                    'transmission_capacity_mid_south': 'MW',
                    'transmission_capacity_mid_north': 'MW',
                    'transmission_capacity_south_mid': 'MW',
                    'transmission_capacity_south_north': 'MW',
                    'transmission_capacity_north_south': 'MW',
                    'transmission_capacity_north_mid': 'MW',
                    'process_capacity_mid_biomass': 'MW',
                    'process_capacity_mid_coal': 'MW',
                    'process_capacity_mid_gas': 'MW',
                    'process_capacity_mid_lignite': 'MW',
                    'process_capacity_mid_hydro': 'MW',
                    'process_capacity_mid_solar': 'MW',
                    'process_capacity_mid_wind': 'MW',
                    'process_capacity_south_biomass': 'MW',
                    'process_capacity_south_coal': 'MW',
                    'process_capacity_south_gas': 'MW',
                    'process_capacity_south_lignite': 'MW',
                    'process_capacity_south_hydro': 'MW',
                    'process_capacity_south_solar': 'MW',
                    'process_capacity_south_wind': 'MW',
                    'process_capacity_north_biomass': 'MW',
                    'process_capacity_north_coal': 'MW',
                    'process_capacity_north_gas': 'MW',
                    'process_capacity_north_lignite': 'MW',
                    'process_capacity_north_hydro': 'MW',
                    'process_capacity_north_solar': 'MW',
                    'process_capacity_north_wind': 'MW'}
            output_df['unit'] = output_df['variable'].map(unit)
            output_df = output_df[['version', 'variable', 'urbs_value', 'oemof_value',
                                   'unit', 'aggregation', 'updated']]

            # upload to OEP
            out_table = conn.setup_table('mimo_result', schema_name='sandbox',
                                     metadata=metadata)
            out_table = conn.upload_to_oep(output_df, out_table, engine, metadata)
            
        else:
            pass
