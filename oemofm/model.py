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
        storage: A dict of storages
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
        self.storage = kwargs['storage']

        # fix data
        self.data['demand'] = self.data['demand'].shift(-1)
        self.data['demand'] = self.data['demand'][:-1]
        self.data['supim'] = self.data['supim'].shift(-1)
        self.data['supim'] = self.data['supim'][:-1]

    def _create_components(self):
        # create empty dictionaries
        bus = {}
        source = {}
        rsource = {}
        transformer = {}
        sink = {}
        storage = {}

        # create buses
        for b in self.bus:
            bus['b_'+b+'_'+self.name] = solph.Bus(label='b_'+b+'_'+self.name)

        # create sources
        for s in self.source.keys():
            source['s_'+s+'_'+self.name] = solph.Source(
                            label='s_'+s+'_'+self.name,
                            outputs={bus['b_'+s+'_'+self.name]:
                                solph.Flow(
                                    variable_costs=self.source[s]*self.weight)})

        # create renewable sources
        for rs in self.rsource.keys():
            rsource['rs_'+rs+'_'+self.name] = solph.Source(
                            label='rs_'+rs+'_'+self.name,
                            outputs={bus['b_el'+'_'+self.name]:
                                solph.Flow(
                                    actual_value=self.data['supim'][self.name][rs],
                                    fixed=True,
                                    investment=solph.Investment(
                                        ep_costs=self.rsource[rs][0],
                                        maximum=self.rsource[rs][1],
                                        existing=self.rsource[rs][2]))})

        # create transformer (output: elec only)
        for t in self.transformer.keys():
            transformer['t_'+t+'_'+self.name] = solph.Transformer(
                            label="pp_"+t+'_'+self.name,
                            inputs={bus['b_'+t+'_'+self.name]:
                                solph.Flow(
                                    investment=solph.Investment(
                                        ep_costs=self.transformer[t][0],
                                        maximum=self.transformer[t][1],
                                        existing=self.transformer[t][2]),
                                    variable_costs=self.transformer[t][3]*self.weight)},
                            outputs={bus['b_el'+'_'+self.name]: solph.Flow()},
                            conversion_factors={bus['b_el'+'_'+self.name]:
                                                    self.transformer[t][4]})

        # create sink (input: elec only)
        for sn in self.sink.keys():
            sink[sn+'_'+self.name] = solph.Sink(
                            label=sn+self.name,
                            inputs={bus['b_el'+'_'+self.name]:
                                solph.Flow(
                                    actual_value=self.data[sn][self.name]['Elec'],
                                    fixed=True, nominal_value=self.sink[sn])})

        # create storage
        for st in self.storage.keys():
            storage['storage_'+st+'_'+self.name] = solph.components.GenericStorage(
                            label='storage_'+st+'_'+self.name,
                            inputs={
                                bus['b_el'+'_'+self.name]: solph.Flow(
                                    variable_costs=self.storage[st][3]*self.weight)},
                            outputs={
                                bus['b_el'+'_'+self.name]: solph.Flow(
                                    variable_costs=self.storage[st][3]*self.weight)},
                            inflow_conversion_factor=1, outflow_conversion_factor=1,
                            initial_capacity=0,
                            investment=solph.Investment(
                                            ep_costs=self.storage[st][0],
                                            maximum=self.storage[st][1],
                                            existing=self.storage[st][2]),
                            variable_costs=self.storage[st][3]*self.weight)

        return self.name, bus, source, rsource, transformer, sink, storage


class Line:
    """Transmission line between sites

    Attributes:
        site_0: A Site object
        site_1: A Site object
        weight: A float number
        specs: Specifications of the storage
    """

    def __init__(self, site_0, site_1, weight, **kwargs):
        self.site_0 = site_0
        self.site_1 = site_1
        self.weight = weight
        self.specs = kwargs['specs']

    def _create_lines(self):
        # create transmission lines
        line = solph.custom.Link(
                    label="line"+'_'+self.site_0[0]+'_'+self.site_1[0],
                    inputs={
                       self.site_0[1]['b_el'+'_'+self.site_0[0]]:
                           solph.Flow(investment=solph.Investment(
                               ep_costs=self.specs[0],
                               maximum=self.specs[1],
                               existing=self.specs[2]),
                           variable_costs=self.specs[3]*self.weight),
                       self.site_1[1]['b_el'+'_'+self.site_1[0]]:
                           solph.Flow(investment=solph.Investment(
                               ep_costs=self.specs[0],
                               maximum=self.specs[1],
                               existing=self.specs[2]),
                           variable_costs=self.specs[3]*self.weight)},
                    outputs={
                       self.site_1[1]['b_el'+'_'+self.site_1[0]]:
                           solph.Flow(),
                       self.site_0[1]['b_el'+'_'+self.site_0[0]]:
                           solph.Flow()},
                    conversion_factors={
                       (self.site_0[1]['b_el'+'_'+self.site_0[0]],
                        self.site_1[1]['b_el'+'_'+self.site_1[0]]): self.specs[4],
                       (self.site_1[1]['b_el'+'_'+self.site_1[0]],
                        self.site_0[1]['b_el'+'_'+self.site_0[0]]): self.specs[4]})

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

    # Create Sites
    """Syntax

    Site(site_name, site_data, weight,
         bus=[components],
         source={components: variable_cost},
         rsource={components: (ep_costs, max_capacity, existing_capacity)},
         transformer={components: (ep_costs, max_capacity, existing_capacity,
                                   variable_cost, conversion_factor)},
         sink={components: nominal_value}
         storage={components: (ep_costs, max_capacity, existing_capacity,
                               variable_costs)
        )
    """
    sites = data['site'].to_dict()['area']

    for site in sites:
        sites[site] = Site(site, data, weight,
                           bus=['coal', 'lig', 'gas', 'bio', 'el'],
                           source={'coal': 7, 'lig': 4, 'gas': 27, 'bio': 6},
                           rsource={'Wind': (economics.annuity(1500000, 25, 0.07), 13000, 0),
                                    'Solar': (economics.annuity(600000, 25, 0.07), 160000, 0),
                                    'Hydro': (economics.annuity(1600000, 50, 0.07), 1400, 0)},
                           transformer={'coal': (economics.annuity(600000, 40, 0.07), 100000, 0, 0.6, 0.4),
                                        'lig': (economics.annuity(600000, 40, 0.07), 60000, 0, 0.6, 0.4),
                                        'gas': (economics.annuity(450000, 30, 0.07), 80000, 0, 1.6, 0.6),
                                        'bio': (economics.annuity(875000, 25, 0.07), 5000, 0, 1.4, 0.35)},
                           sink={'demand': 1},
                           storage={'el': (economics.annuity(100000, 50, 0.07), float('inf'), 0, 0.02)}
                          )
        sites[site] = sites[site]._create_components()

    # Create Transmission Lines
    """Syntax

    Line(site_0, site_1, weight,
         specs=[(ep_costs, max_capacity, existing_capacity, variable_cost,
                 conversion_factor]
        )
    """
    lines = {('Mid', 'North'): None,
             ('South', 'Mid'): None,
             ('South', 'North'): None,
            }

    for line in lines:
        lines[line] = Line(sites[line[0]], sites[line[1]], weight,
                           specs = [economics.annuity(1650000, 40, 0.07), float('inf'), 0, 0, 0.90]
                          )
        lines[line] = lines[line]._create_lines()

    return m
