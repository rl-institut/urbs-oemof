##########################################################################
# IMPORTS
##########################################################################

# oemof
from oemof.tools import logger
from oemof.tools import helpers
from oemof.tools import economics
from oemof.network import Node
import oemof.solph as solph
import oemof.outputlib as outputlib

# urbs
import urbs
from pyomo.opt.base import SolverFactory

# misc.
import logging
import os
import pandas as pd
import pprint as pp
import matplotlib.pyplot as plt
from datetime import datetime

##########################################################################
# Helper Functions
##########################################################################


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

##########################################################################


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
    prob = urbs.create_model(data, 1, timesteps)

    # solve model and read results
    optim = SolverFactory('glpk')
    result = optim.solve(prob, tee=False)

    return prob


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

    # Init
    solver = 'glpk'
    weight = float(8760)/(len(timesteps))
    timesteps = timesteps[-1]

    # Time Index
    date_time_index = pd.date_range('1/1/2018', periods=timesteps,
                                    freq='H')

    # Create Energy System
    energysystem = solph.EnergySystem(timeindex=date_time_index)
    Node.registry = energysystem

    # Read Input File
    data = pd.read_csv(input_file)

    ##########################################################################
    # Create oemof object
    ##########################################################################

    # Buses
    bcoal = solph.Bus(label="coal")
    blig = solph.Bus(label="lignite")
    bgas = solph.Bus(label="gas")
    bbio = solph.Bus(label="biomass")
    bel = solph.Bus(label="electricity")

    # Sources
    scoal = solph.Source(label='scoal',
                         outputs={bcoal: solph.Flow(
                            variable_costs=7*weight)})
    slig = solph.Source(label='slignite',
                        outputs={blig: solph.Flow(
                            variable_costs=4*weight)})
    sgas = solph.Source(label='sgas',
                        outputs={bgas: solph.Flow(
                            variable_costs=27*weight)})
    sbio = solph.Source(label='sbio',
                        outputs={bbio: solph.Flow(
                            variable_costs=6*weight)})

    # Sink
    demand = solph.Sink(label='demand',
                        inputs={bel: solph.Flow(
                            actual_value=data['demand'], fixed=True,
                            nominal_value=1)})

    # Transformers
    # annu() & fix costs
    acoal = economics.annuity(600000, 40, 0.07)
    alig = economics.annuity(600000, 40, 0.07)
    agas = economics.annuity(450000, 30, 0.07)
    abio = economics.annuity(875000, 25, 0.07)

    tcoal = solph.Transformer(
                label="pp_coal",
                inputs={bcoal: solph.Flow(investment=
                               solph.Investment(ep_costs=acoal,
                                                maximum=100000,
                                                existing=0),
                        variable_costs=0.6*weight)},
                outputs={bel: solph.Flow()},
                conversion_factors={bel: 0.4})

    tlig = solph.Transformer(
               label="pp_lignite",
               inputs={blig: solph.Flow(investment=
                             solph.Investment(ep_costs=alig,
                                              maximum=60000,
                                              existing=0),
                       variable_costs=0.6*weight)},
               outputs={bel: solph.Flow()},
               conversion_factors={bel: 0.4})

    tgas = solph.Transformer(
               label="pp_gas",
               inputs={bgas: solph.Flow(investment=
                             solph.Investment(ep_costs=agas,
                                              maximum=80000,
                                              existing=0),
                       variable_costs=1.6*weight)},
               outputs={bel: solph.Flow()},
               conversion_factors={bel: 0.6})

    tbio = solph.Transformer(
               label="pp_biomass",
               inputs={bbio: solph.Flow(investment=
                             solph.Investment(ep_costs=abio,
                                              maximum=5000,
                                              existing=0),
                       variable_costs=1.4*weight)},
               outputs={bel: solph.Flow()},
               conversion_factors={bel: 0.35})

    ##########################################################################
    # Optimise the energy system and plot the results
    ##########################################################################

    # initialise the operational model
    model = solph.Model(energysystem)
    model.solve(solver=solver, solve_kwargs={'tee': False})

    # write LP file
    filename = os.path.join(os.path.dirname(__file__), 'mimo_oemof.lp')
    model.write(filename, io_options={'symbolic_solver_labels': True})

    # add results to the energy system to make it possible to store them.
    energysystem.results['main'] = outputlib.processing.results(model)
    energysystem.results['meta'] = outputlib.processing.meta_results(model)

    # The default path is the '.oemof' folder in your $HOME directory.
    # The default filename is 'es_dump.oemof'.

    # store energy system with results
    energysystem.dump(dpath=None, filename=None)

    # ************************************************************************
    # ********** PART 2 - Processing the results *****************************
    # ************************************************************************
    energysystem = solph.EnergySystem()
    energysystem.restore(dpath=None, filename=None)

    # define an alias for shorter calls below (optional)
    results = energysystem.results['main']

    '''
    EXTRAS

    swind = solph.Source(label='rwind', outputs={bel: solph.Flow(
                         actual_value=data['wind_m'], nominal_value=1000000, fixed=True)}))
    spv = solph.Source(label='rpv', outputs={bel: solph.Flow(
                       actual_value=data['pv_m'], nominal_value=1000000, fixed=True)}))
    shydro = solph.Source(label='rhydro', outputs={bel: solph.Flow(
                          actual_value=data['hydro_m'], nominal_value=1000000, fixed=True)}))
    '''

    return model

if __name__ == '__main__':
    # Input Files
    input_file_urbs = 'mimo.xlsx'
    input_file_oemof = 'mimo.csv'

    # simulation timesteps
    (offset, length) = (0, 8760)  # time step selection
    timesteps = range(offset, offset + length + 1)

    # create models
    print('----------------------------------------------------')
    print('CREATING urbs MODEL')
    urbs_model = create_um(input_file_urbs, timesteps)
    print('CREATING oemof MODEL')
    oemof_model = create_om(input_file_oemof, timesteps)
    print('----------------------------------------------------')

    comparison(urbs_model, oemof_model)
