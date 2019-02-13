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
def comparison(u_model, o_model, threshold=0.1):
    """
    Function for comparing urbs & oemof

    Args:
        u_model: urbs model instance use create_um() to generate
        o_model: oemof model instance use create_om() to generate

    Returns:
        None
    """
    # check objective difference
    if u_model.obj() != o_model.objective():
        print('OBJECTIVE')
        print('urbs\t', u_model.obj())
        print('oemof\t', o_model.objective())
        print('Diff\t', u_model.obj() - o_model.objective())
    print('----------------------------------------------------')

    # memory info & cpu time
    with open('urbs_log.txt', 'r') as urbslog:
        urbslog = urbslog.read().replace('\n', ' ')
        mem_urbs = float(urbslog[urbslog.find('Memory used:')+12:
                                 urbslog.find('Mb')])
        cpu_urbs = float(urbslog[urbslog.find('Time used:')+10:
                                 urbslog.find('secs')])

    with open('oemof_log.txt', 'r') as oemoflog:
        oemoflog = oemoflog.read().replace('\n', ' ')
        mem_oemof = float(oemoflog[oemoflog.find('Memory used:')+12:
                                   oemoflog.find('Mb')])
        cpu_oemof = float(oemoflog[oemoflog.find('Time used:')+10:
                                   oemoflog.find('secs')])

    # check cpu time difference
    if cpu_urbs != cpu_oemof:
        print('Time Used')
        print('urbs\t', cpu_urbs, ' secs')
        print('oemof\t', cpu_oemof, ' secs')
        print('Diff\t', format(cpu_urbs - cpu_oemof, '.1f'), ' secs')
    print('----------------------------------------------------')

    # check memory difference
    if mem_urbs != mem_oemof:
        print('Memory Used')
        print('urbs\t', mem_urbs, ' Mb')
        print('oemof\t', mem_oemof, ' Mb')
        print('Diff\t', format(mem_urbs - mem_oemof, '.1f'), ' Mb')
    print('----------------------------------------------------')

    # create oemof energysytem
    o_model = solph.EnergySystem()
    o_model.restore(dpath=None, filename=None)

    # compare lp files
    u_const, o_const = comp.compare_lp_files()
    if u_const != o_const:
        print('Constraint Amount')
        print('urbs\t', u_const)
        print('oemof\t', o_const)
        print('Diff\t', u_const - o_const)
    print('----------------------------------------------------')

    # compare model variables
    if len(u_model.tm) >= 2:
        comp.compare_storages(u_model, o_model, threshold)
        comp.compare_transmission(u_model, o_model, threshold)
        comp.compare_process(u_model, o_model, threshold)
    else:
        pass
    print('----------------------------------------------------')


###############################################################################
# urbs Model
###############################################################################

# create urbs model
def create_um(input_data, timesteps):
    """
    Creates an urbs model for given input, time steps

    Args:
        input_file: input file
        timesteps: simulation timesteps

    Returns:
        model instance
    """
    # create model
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
        input_file: input file
        timesteps: simulation timesteps

    Returns:
        model instance
    """
    # create oemof energy system
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
            # setup table
            table['ubbb_'+key] = conn.setup_table('ubbb_'+key,
                                                  schema_name='sandbox',
                                                  metadata=metadata)
            # upload to OEP
            '''
            table['ubbb_'+key] = conn.upload_to_oep(data[key],
                                                    table['ubbb_'+key],
                                                    engine, metadata)
            '''
            # download from OEP
            input_data[key] = conn.get_df(engine, table['ubbb_'+key])

        # write data
        input_data = conn.write_data(input_data)

    else:
        input_data = data
        input_data = conn.write_data(input_data)

    # create models
    if benchmark:
        print('----------------------------------------------------')

        start = time.perf_counter()
        urbs_model = create_um(input_data, timesteps)
        end = time.perf_counter()

        print('CREATING urbs MODEL  [' + format(end-start, '.1f') + ' secs]')

        start = time.perf_counter()
        oemof_model = create_om(input_data, timesteps)
        end = time.perf_counter()

        print('CREATING oemof MODEL [' + format(end-start, '.1f') + ' secs]')

        print('----------------------------------------------------')

        # comparison
        comparison(urbs_model, oemof_model, threshold=0.1)
    else:
        print('----------------------------------------------------')
        print('CREATING urbs MODEL')
        urbs_model = create_um(input_data, timesteps)
        print('CREATING oemof MODEL')
        oemof_model = create_om(input_data, timesteps)
        print('----------------------------------------------------')

        # comparison
        comparison(urbs_model, oemof_model, threshold=0.1)
