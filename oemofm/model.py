from oemof.tools import logger
from oemof.tools import helpers
from oemof.tools import economics
from oemof.network import Node
import oemof.solph as solph
import pandas as pd
import pprint as pp


class Site:
    """Energy model for a site

    Attributes:
        weight: A float number
        bus: A list of buses
        source: A dict of sources
        rsource: A dict of renewable sources
        transformer: A dict of transformers
        sink: A dict of sinks
    """

    def __init__(self, name, data, weight, **kwargs):
        self.name = name
        self.data = data
        self.weight = weight
        self.bus = kwargs['bus']
        self.source = kwargs['source']
        self.rsource = kwargs['rsource']
        self.transformer = kwargs['transformer']
        self.sink = kwargs['sink']

    def _create_components(self):
        # create empty dictionaries
        bus = {}
        source = {}
        rsource = {}
        transformer = {}
        sink = {}

        # create buses
        for b in self.bus:
            bus['b_'+b+self.name] = solph.Bus(label='b_'+b+self.name)

        # create sources
        for s in self.source.keys():
            source['s_'+s+self.name] = solph.Source(
                            label='s_'+s+self.name,
                            outputs={bus['b_'+s+self.name]:
                                solph.Flow(
                                    variable_costs=self.source[s]*self.weight)})

        # create renewable sources
        for rs in self.rsource.keys():
            rsource['rs_'+rs+self.name] = solph.Source(
                            label='rs_'+rs+self.name,
                            outputs={bus['b_el'+self.name]:
                                solph.Flow(
                                    actual_value=self.data[rs+self.name],
                                    fixed=True,
                                    investment=solph.Investment(
                                        ep_costs=self.rsource[rs][0],
                                        maximum=self.rsource[rs][1],
                                        existing=self.rsource[rs][2]))})

        # create transformer (output: elec only)
        for t in self.transformer.keys():
            transformer['t_'+t+self.name] = solph.Transformer(
                            label="pp_"+t+self.name,
                            inputs={bus['b_'+t+self.name]:
                                solph.Flow(
                                    investment=solph.Investment(
                                        ep_costs=self.transformer[t][0],
                                        maximum=self.transformer[t][1],
                                        existing=self.transformer[t][2]),
                                    variable_costs=self.transformer[t][3]*self.weight)},
                            outputs={bus['b_el'+self.name]: solph.Flow()},
                            conversion_factors={bus['b_el'+self.name]:
                                                    self.transformer[t][4]})

        # create sink (input: elec only)
        for sn in self.sink.keys():
            sink[sn+self.name] = solph.Sink(
                            label=sn+self.name,
                            inputs={bus['b_el'+self.name]:
                                solph.Flow(
                                    actual_value=self.data[sn+self.name],
                                    fixed=True, nominal_value=self.sink[sn])})

        return bus, source, rsource, transformer, sink


class Line:
    """Transmission line between sites

    Attributes:
        bus: A list of buses
        source: A dict of sources
        rsource: A dict of renewable sources
        transformer: A dict of transformers
        sink: A dict of sinks
    """

    def __init__(self, name_0, name_1, site_0, site_1, weight, **kwargs):
        self.name_0 = name_0
        self.name_1 = name_1
        self.site_0 = site_0
        self.site_1 = site_1
        self.weight = weight
        self.specs = kwargs['specs']

    def _create_lines(self):
        # create transmission lines
        line = solph.custom.Link(
                    label="line"+self.name_0+self.name_1,
                    inputs={
                       self.site_0[0]['b_el'+self.name_0]:
                           solph.Flow(investment=solph.Investment(
                               ep_costs=self.specs[0],
                               maximum=self.specs[1],
                               existing=self.specs[2]),
                           variable_costs=self.specs[3]*self.weight),
                       self.site_1[0]['b_el'+self.name_1]:
                           solph.Flow(investment=solph.Investment(
                               ep_costs=self.specs[0],
                               maximum=self.specs[1],
                               existing=self.specs[2]),
                           variable_costs=self.specs[3]*self.weight)},
                    outputs={
                       self.site_1[0]['b_el'+self.name_1]:
                           solph.Flow(),
                       self.site_0[0]['b_el'+self.name_0]:
                           solph.Flow()},
                    conversion_factors={
                       (self.site_0[0]['b_el'+self.name_0],
                        self.site_1[0]['b_el'+self.name_1]): self.specs[4],
                       (self.site_1[0]['b_el'+self.name_1],
                        self.site_0[0]['b_el'+self.name_0]): self.specs[4]})

        return line


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
    m = solph.EnergySystem(timeindex=date_time_index)
    Node.registry = m

    # Create oemof object (sites)
    """Syntax

    site_name = Site(site_name, site_data, weight,
                     bus=[components],
                     source={components: variable_cost},
                     rsource={components: (ep_costs, max_capacity, existing_capacity)},
                     transformer={components: (ep_costs, max_capacity, existing_capacity,
                                               variable_cost, conversion_factor)},
                     sink={components: nominal_value})
    """
    # Site input 'mid'
    mid = Site('_mid', data.filter(like='_mid'), weight,
               bus=['coal', 'lig', 'gas', 'bio', 'el'],
               source={'coal': 7, 'lig': 4, 'gas': 27, 'bio': 6},
               rsource={'wind': (economics.annuity(1500000, 25, 0.07), 13000, 0),
                        'pv': (economics.annuity(600000, 25, 0.07), 160000, 0),
                        'hydro': (economics.annuity(1600000, 50, 0.07), 1400, 0)},
               transformer={'coal': (economics.annuity(600000, 40, 0.07), 100000, 0, 0.6, 0.4),
                            'lig': (economics.annuity(600000, 40, 0.07), 60000, 0, 0.6, 0.4),
                            'gas': (economics.annuity(450000, 30, 0.07), 80000, 0, 1.6, 0.6),
                            'bio': (economics.annuity(875000, 25, 0.07), 5000, 0, 1.4, 0.35)},
               sink={'demand': 1})

    # Site input 'south'
    south = Site('_south', data.filter(like='_south'), weight,
                 bus=['coal', 'lig', 'gas', 'bio', 'el'],
                 source={'coal': 7, 'lig': 4, 'gas': 27, 'bio': 6},
                 rsource={'wind': (economics.annuity(1500000, 25, 0.07), 13000, 0),
                          'pv': (economics.annuity(600000, 25, 0.07), 160000, 0),
                          'hydro': (economics.annuity(1600000, 50, 0.07), 1400, 0)},
                 transformer={'coal': (economics.annuity(600000, 40, 0.07), 100000, 0, 0.6, 0.4),
                              'lig': (economics.annuity(600000, 40, 0.07), 60000, 0, 0.6, 0.4),
                              'gas': (economics.annuity(450000, 30, 0.07), 80000, 0, 1.6, 0.6),
                              'bio': (economics.annuity(875000, 25, 0.07), 5000, 0, 1.4, 0.35)},
                 sink={'demand': 1})

    # Site input 'north'
    north = Site('_north', data.filter(like='_north'), weight,
                 bus=['coal', 'lig', 'gas', 'bio', 'el'],
                 source={'coal': 7, 'lig': 4, 'gas': 27, 'bio': 6},
                 rsource={'wind': (economics.annuity(1500000, 25, 0.07), 13000, 0),
                          'pv': (economics.annuity(600000, 25, 0.07), 160000, 0),
                          'hydro': (economics.annuity(1600000, 50, 0.07), 1400, 0)},
                 transformer={'coal': (economics.annuity(600000, 40, 0.07), 100000, 0, 0.6, 0.4),
                              'lig': (economics.annuity(600000, 40, 0.07), 60000, 0, 0.6, 0.4),
                              'gas': (economics.annuity(450000, 30, 0.07), 80000, 0, 1.6, 0.6),
                              'bio': (economics.annuity(875000, 25, 0.07), 5000, 0, 1.4, 0.35)},
                 sink={'demand': 1})

    # Sites
    site = {}
    site['mid'] = mid._create_components()
    site['south'] = south._create_components()
    site['north'] = north._create_components()

    # Create transmission lines between sites
    transmission = []
    transmission.append(Line('_mid', '_north', site['mid'], site['north'], weight,
                        specs = [economics.annuity(1650000, 40, 0.07), float('inf'), 0, 0, 0.90]))
    transmission.append(Line('_south', '_mid', site['south'], site['mid'], weight,
                        specs = [economics.annuity(1650000, 40, 0.07), float('inf'), 0, 0, 0.90]))
    transmission.append(Line('_south', '_north', site['south'], site['north'], weight,
                        specs = [economics.annuity(3000000, 40, 0.07), float('inf'), 0, 0, 0.85]))

    lines = {}
    for i in range(0, len(transmission)):
        lines[i] = transmission[i]._create_lines()

    return m
