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
            start = time.perf_counter()
            urbs_model = create_um(input_data, timesteps)
            mid = time.perf_counter()
            oemof_model = create_om(input_data, timesteps)
            end = time.perf_counter()

            bench[i] = comparison(urbs_model, oemof_model,
                                  threshold=0.1, benchmark=True)

            # setting build time for urbs
            bench[i][0]['build'] = mid - start
            # setting build time for oemof
            bench[i][1]['build'] = end - mid

        elif i <= 100 and i % 10 == 0:
            start = time.perf_counter()
            urbs_model = create_um(input_data, timesteps)
            mid = time.perf_counter()
            oemof_model = create_om(input_data, timesteps)
            end = time.perf_counter()

            bench[i] = comparison(urbs_model, oemof_model,
                                  threshold=0.1, benchmark=True)

            # setting build time for urbs
            bench[i][0]['build'] = mid - start
            # setting build time for oemof
            bench[i][1]['build'] = end - mid

        elif i > 100 and i % 100 == 0:
            start = time.perf_counter()
            urbs_model = create_um(input_data, timesteps)
            mid = time.perf_counter()
            oemof_model = create_om(input_data, timesteps)
            end = time.perf_counter()

            bench[i] = comparison(urbs_model, oemof_model,
                                  threshold=0.1, benchmark=True)

            # setting build time for urbs
            bench[i][0]['build'] = mid - start
            # setting build time for oemof
            bench[i][1]['build'] = end - mid

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
        sto = comp.compare_storages(u_model, o_model, threshold)
        tra = comp.compare_transmission(u_model, o_model, threshold)
        pro = comp.compare_process(u_model, o_model, threshold)
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
    model = urbs.create_model(input_data, 1, timesteps)

    # solve model and read results
    optim = SolverFactory('glpk')
    result = optim.solve(model, logfile='urbs_log.txt', tee=False)

    # write LP file
    filename = os.path.join(os.path.dirname(__file__), 'mimo_urbs.lp')
    model.write(filename, io_options={'symbolic_solver_labels': True})

    return model


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
    es, model = oemofm.create_model(input_data, timesteps)

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

    return model


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
            """
            # setup table
            table['mimo_'+key] = conn.setup_table('mimo_'+key,
                                                  schema_name='sandbox',
                                                  metadata=metadata)
            """
            # upload to OEP
            table['mimo_'+key] = conn.upload_to_oep(data[key],
                                                    table['mimo_'+key],
                                                    engine, metadata)

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
        urbs_model = create_um(input_data, timesteps)
        oemof_model = create_om(input_data, timesteps)
        comparison(urbs_model, oemof_model, threshold=0.1)
        print('COMPARING-COMPLETED---------------------------------')
