from oemof.tools import logger
from oemof.tools import helpers
from oemof.tools import economics
from oemof.network import Node
import oemof.solph as solph
import pandas as pd
import pprint as pp
import matplotlib.pyplot as plt

def create_model(data, timesteps=None):
    """Creates an oemof model for given input, time steps

    Args:
        input_file: input file
        timesteps: simulation timesteps

    Returns:
        model instance
    """
    # Parameters
    weight = float(8760)/(len(timesteps))
    timesteps = timesteps[-1]

    # Time Index
    date_time_index = pd.date_range('1/1/2018', periods=timesteps,
                                    freq='H')

    # Create Energy System
    energysystem = solph.EnergySystem(timeindex=date_time_index)
    Node.registry = energysystem

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

    return energysystem
"""
    swind = solph.Source(label='rwind', outputs={bel: solph.Flow(
                         actual_value=data['wind_m'], nominal_value=1000000, fixed=True)}))
    spv = solph.Source(label='rpv', outputs={bel: solph.Flow(
                       actual_value=data['pv_m'], nominal_value=1000000, fixed=True)}))
    shydro = solph.Source(label='rhydro', outputs={bel: solph.Flow(
                          actual_value=data['hydro_m'], nominal_value=1000000, fixed=True)}))
"""

