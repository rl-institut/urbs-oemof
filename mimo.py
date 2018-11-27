##########################################################################
# IMPORTS
##########################################################################

# oemof
import oemofm
import oemof.solph as solph
import oemof.outputlib as outputlib
from oemof.graph import create_nx_graph

# urbs
import urbs
from pyomo.opt.base import SolverFactory

# misc.
import logging
import os
import pandas as pd
from datetime import datetime
import networkx as nx
import matplotlib.pyplot as plt

##########################################################################
# Helper Functions
##########################################################################
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
        print('urbs\t', u_model.obj())
        print('oemof\t', o_model.objective())
        print('Diff\t', u_model.obj() - o_model.objective())

    # to check flows with cap_pro/tra/sto
    o_model = solph.EnergySystem()
    o_model.restore(dpath=None, filename=None)
    string_results = outputlib.views.convert_keys_to_strings(o_model.results['main'])
    print(string_results.keys())
    node_results_bel = outputlib.views.node(o_model.results['main'], 'b_el_mid')
    df = node_results_bel['sequences']
    df.head()
    print(df)


##########################################################################
# urbs Model
##########################################################################

# create urbs model
def create_um(input_file, timesteps):
    """
    Creates an urbs model for given input, time steps

    Args:
        input_file: input file
        timesteps: simulation timesteps

    Returns:
        model instance
    """

    # scenario name, read and modify data for scenario
    data = urbs.read_excel(input_file)

    # create model
    model = urbs.create_model(data, 1, timesteps)

    # solve model and read results
    optim = SolverFactory('glpk')
    result = optim.solve(model, tee=False)

    # write LP file
    filename = os.path.join(os.path.dirname(__file__), 'mimo_urbs.lp')
    model.write(filename, io_options={'symbolic_solver_labels': True})

    return model


##########################################################################
# oemof Model
##########################################################################

# create oemof model
def create_om(input_file, timesteps):
    """
    Creates an oemof model for given input, time steps

    Args:
        input_file: input file
        timesteps: simulation timesteps

    Returns:
        model instance
    """

    # read input file
    data = pd.read_csv(input_file)

    # create oemof energy system
    es = oemofm.create_model(data, timesteps)

    # solve model and read results
    model = solph.Model(es)
    model.name = 'oemof APP'
    model.solve(solver='glpk', solve_kwargs={'tee': False})

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
    # Input Files
    input_file_urbs = 'mimo.xlsx'
    input_file_oemof = 'mimo.csv'

    # simulation timesteps
    (offset, length) = (0, 10)  # time step selection
    timesteps = range(offset, offset + length + 1)

    # create models
    print('----------------------------------------------------')
    print('CREATING urbs MODEL')
    urbs_model = create_um(input_file_urbs, timesteps)
    print('CREATING oemof MODEL')
    oemof_model = create_om(input_file_oemof, timesteps)
    print('----------------------------------------------------')

    comparison(urbs_model, oemof_model)
