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
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime


###############################################################################
# Helper Functions
###############################################################################


def draw_graph(grph, edge_labels=True, node_color='#AFAFAF',
               edge_color='#CFCFCF', plot=True, node_size=2000,
               with_labels=True, arrows=True, layout='neato'):
    """
    Draw a graph. This function will be removed in future versions.

    Parameters
    ----------
    grph : networkxGraph
        A graph to draw.
    edge_labels : boolean
        Use nominal values of flow as edge label
    node_color : dict or string
        Hex color code oder matplotlib color for each node. If string, all
        colors are the same.

    edge_color : string
        Hex color code oder matplotlib color for edge color.

    plot : boolean
        Show matplotlib plot.

    node_size : integer
        Size of nodes.

    with_labels : boolean
        Draw node labels.

    arrows : boolean
        Draw arrows on directed edges. Works only if an optimization_model has
        been passed.
    layout : string
        networkx graph layout, one of: neato, dot, twopi, circo, fdp, sfdp.
    """
    if type(node_color) is dict:
        node_color = [node_color.get(g, '#AFAFAF') for g in grph.nodes()]

    # set drawing options
    options = {
     'prog': 'dot',
     'with_labels': with_labels,
     'node_color': node_color,
     'edge_color': edge_color,
     'node_size': node_size,
     'arrows': arrows
    }

    # draw graph
    pos = nx.drawing.nx_agraph.graphviz_layout(grph, prog=layout)

    nx.draw(grph, pos=pos, **options)

    # add edge labels for all edges
    if edge_labels is True and plt:
        labels = nx.get_edge_attributes(grph, 'weight')
        nx.draw_networkx_edge_labels(grph, pos=pos, edge_labels=labels)

    # show output
    if plot is True:
        plt.show()


def comparison(u_model, o_model):
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

    # memory info
    with open('urbs_log.txt', 'r') as urbslog:
        mem_urbs = urbslog.read().replace('\n', ' ')
        mem_urbs = float(mem_urbs[mem_urbs.find('Memory used:')+12:
                                  mem_urbs.find('Mb')])

    with open('oemof_log.txt', 'r') as oemoflog:
        mem_oemof = oemoflog.read().replace('\n', ' ')
        mem_oemof = float(mem_oemof[mem_oemof.find('Memory used:')+12:
                                    mem_oemof.find('Mb')])

    # check memory difference
    if mem_urbs != mem_oemof:
        print('Memory Used')
        print('urbs\t', mem_urbs, ' Mb')
        print('oemof\t', mem_oemof, ' Mb')
        print('Diff\t', mem_urbs - mem_oemof, ' Mb')

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
    comp.compare_storages(u_model, o_model)
    comp.compare_transmission(u_model, o_model)
    comp.compare_process(u_model, o_model)

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
        draw_graph(graph, plot=True, layout='neato', node_size=3000,
                   node_color={'b_0': '#cd3333',
                               'b_1': '#7EC0EE',
                               'b_2': '#eeac7e'})

    # get results
    es.results['main'] = outputlib.processing.results(model)
    es.dump(dpath=None, filename=None)

    return model


if __name__ == '__main__':
    # connection
    connection = False

    # input file
    input_file = 'mimo.xlsx'

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

    # simulation timesteps
    (offset, length) = (0, 10)  # time step selection
    timesteps = range(offset, offset + length + 1)

    # create models
    print('----------------------------------------------------')
    print('CREATING urbs MODEL')
    urbs_model = create_um(input_data, timesteps)
    print('CREATING oemof MODEL')
    oemof_model = create_om(input_data, timesteps)
    print('----------------------------------------------------')

    # comparison
    comparison(urbs_model, oemof_model)
