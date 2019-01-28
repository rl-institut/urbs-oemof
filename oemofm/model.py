from oemof.tools import helpers
from oemof.tools import economics
from oemof.network import Node
import oemof.solph as solph
import pandas as pd
import pprint as pp
from itertools import combinations


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
                            outputs={bus['b_Elec'+'_'+self.name]:
                                solph.Flow(
                                    actual_value=self.rsource[rs][0],
                                    fixed=True,
                                    investment=solph.Investment(
                                        ep_costs=self.rsource[rs][1],
                                        maximum=self.rsource[rs][2],
                                        existing=self.rsource[rs][3],
                                        minimum=self.rsource[rs][4]))})

        # create transformer (output: elec only)
        for t in self.transformer.keys():
            transformer['t_'+t+'_'+self.name] = solph.Transformer(
                            label='pp_'+t+'_'+self.name,
                            inputs={bus['b_'+t+'_'+self.name]:
                                solph.Flow(
                                    investment=solph.Investment(
                                        ep_costs=self.transformer[t][0],
                                        maximum=self.transformer[t][1],
                                        existing=self.transformer[t][2],
                                        minimum=self.transformer[t][3]),
                                    variable_costs=self.transformer[t][4]*self.weight)},
                            outputs={bus['b_Elec'+'_'+self.name]: solph.Flow()},
                            conversion_factors={bus['b_Elec'+'_'+self.name]:
                                                    self.transformer[t][5]})

        # create sink (input: elec only)
        for sn in self.sink.keys():
            sink[sn+'_'+self.name] = solph.Sink(
                            label=sn+'_'+self.name,
                            inputs={bus['b_Elec'+'_'+self.name]:
                                solph.Flow(
                                    actual_value=self.sink[sn],
                                    fixed=True, nominal_value=1)})

        # create storage
        for st in self.storage.keys():
            storage['storage_'+st+'_'+self.name] = solph.components.GenericStorage(
                            label='storage_'+st+'_'+self.name,
                            inputs={bus['b_Elec'+'_'+self.name]: solph.Flow(
                                variable_costs=self.storage[st][4]*self.weight)},
                            outputs={bus['b_Elec'+'_'+self.name]: solph.Flow(
                                variable_costs=self.storage[st][4]*self.weight)},
                            investment=solph.Investment(
                                ep_costs=self.storage[st][0],
                                maximum=self.storage[st][1],
                                existing=self.storage[st][2],
                                minimum=self.storage[st][3]),
                            initial_capacity=self.storage[st][5],
                            inflow_conversion_factor=self.storage[st][6],
                            outflow_conversion_factor=self.storage[st][7],
                            capacity_loss=self.storage[st][8])

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
        """
        line = solph.custom.Link(
                    label='line'+'_'+self.site_0[0]+'_'+self.site_1[0],
                    inputs={
                       self.site_0[1]['b_Elec'+'_'+self.site_0[0]]:
                           solph.Flow(investment=solph.Investment(
                               ep_costs=self.specs[0],
                               maximum=self.specs[1],
                               existing=self.specs[2]),
                           variable_costs=self.specs[3]*self.weight),
                       self.site_1[1]['b_Elec'+'_'+self.site_1[0]]:
                           solph.Flow(investment=solph.Investment(
                               ep_costs=self.specs[0],
                               maximum=self.specs[1],
                               existing=self.specs[2]),
                           variable_costs=self.specs[3]*self.weight)},
                    outputs={
                       self.site_1[1]['b_Elec'+'_'+self.site_1[0]]:
                           solph.Flow(),
                       self.site_0[1]['b_Elec'+'_'+self.site_0[0]]:
                           solph.Flow()},
                    conversion_factors={
                       (self.site_0[1]['b_Elec'+'_'+self.site_0[0]],
                        self.site_1[1]['b_Elec'+'_'+self.site_1[0]]): self.specs[4],
                       (self.site_1[1]['b_Elec'+'_'+self.site_1[0]],
                        self.site_0[1]['b_Elec'+'_'+self.site_0[0]]): self.specs[4]})
        """
        line = {}
        line['line_'+self.site_0[0]+'_'+self.site_1[0]] = solph.Transformer(
                            label='line_'+self.site_0[0]+'_'+self.site_1[0],
                            inputs={self.site_0[1]['b_Elec'+'_'+self.site_0[0]]:
                                        solph.Flow(investment=solph.Investment(
                                            ep_costs=self.specs[0],
                                            maximum=self.specs[1],
                                            existing=self.specs[2]),
                                        variable_costs=self.specs[3]*self.weight)},
                            outputs={self.site_1[1]['b_Elec'+'_'+self.site_1[0]]:
                                        solph.Flow()},
                            conversion_factors={self.site_1[1]['b_Elec'+'_'+self.site_1[0]]:
                                                    self.specs[4]})

        line['line_'+self.site_1[0]+'_'+self.site_0[0]] = solph.Transformer(
                            label='line_'+self.site_1[0]+'_'+self.site_0[0],
                            inputs={self.site_1[1]['b_Elec'+'_'+self.site_1[0]]:
                                        solph.Flow(investment=solph.Investment(
                                            ep_costs=self.specs[0],
                                            maximum=self.specs[1],
                                            existing=self.specs[2]),
                                        variable_costs=self.specs[3]*self.weight)},
                            outputs={self.site_0[1]['b_Elec'+'_'+self.site_0[0]]:
                                        solph.Flow()},
                            conversion_factors={self.site_0[1]['b_Elec'+'_'+self.site_0[0]]:
                                                    self.specs[4]})

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
    es = solph.EnergySystem(timeindex=date_time_index)
    Node.registry = es

    # Fix Data
    data['demand'] = data['demand'].shift(-1)
    data['demand'] = data['demand'][:-1]
    data['supim'] = data['supim'].shift(-1)
    data['supim'] = data['supim'][:-1]

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
        # Create Lists and Dicts for Sites
        b_df1 = data['commodity'].index.get_level_values('Site') == site
        b_df2 = data['commodity'].index.get_level_values('Type') == 'Stock'
        b_df3 = data['commodity'].index.get_level_values('Type') == 'Demand'
        b_df4 = data['commodity'].index.get_level_values('Type') == 'SupIm'

        # Bus List
        bus_df1 = data['commodity'][b_df1 & b_df2].index.remove_unused_levels().get_level_values('Commodity')
        bus_df2 = data['commodity'][b_df1 & b_df3].index.remove_unused_levels().get_level_values('Commodity')
        bus_list = bus_df1.append(bus_df2).tolist()

        # Source Dict
        source_dict = {}
        for item in bus_df1:
            source_dict[item] = data['commodity']['price'][site][item]['Stock']

        # RSource List & Dict
        r_df = data['commodity'][b_df1 & b_df4].index.remove_unused_levels().get_level_values('Commodity')
        rsource_list = r_df.tolist()
        rsource_dict = {}
        for item in rsource_list:
            rsource_dict[item] = (data['supim'][site][item],
                                  economics.annuity(data['process']['inv-cost'][site].filter(like=item).values[0],
                                                    data['process']['depreciation'][site].filter(like=item).values[0],
                                                    data['process']['wacc'][site].filter(like=item).values[0]),
                                  data['process']['cap-up'][site].filter(like=item).values[0],
                                  data['process']['inst-cap'][site].filter(like=item).values[0],
                                  data['process']['cap-lo'][site].filter(like=item).values[0])

        # Transformer Dict
        transformer_dict = {}
        for item in bus_df1:
            transformer_dict[item] = (economics.annuity(data['process']['inv-cost'][site].filter(like=item).values[0],
                                                        data['process']['depreciation'][site].filter(like=item).values[0],
                                                        data['process']['wacc'][site].filter(like=item).values[0]),
                                      data['process']['cap-up'][site].filter(like=item).values[0],
                                      data['process']['inst-cap'][site].filter(like=item).values[0],
                                      data['process']['cap-lo'][site].filter(like=item).values[0],
                                      data['process']['var-cost'][site].filter(like=item).values[0],
                                      data['process_commodity']['ratio'].filter(like=item).filter(like='Elec').values[0])

        # Sink Dict
        sink_dict = {}
        for item in bus_df2:
            sink_dict[item] = data['demand'][site][item]

        # Storage Tuple
        storage_tup = (economics.annuity(data['storage']['inv-cost-p'][site].filter(like='Pump').values[0],
                                         data['storage']['depreciation'][site].filter(like='Pump').values[0],
                                         data['storage']['wacc'][site].filter(like='Pump').values[0]),
                       data['storage']['cap-up-p'][site].filter(like='Pump').values[0],
                       data['storage']['inst-cap-p'][site].filter(like='Pump').values[0],
                       data['storage']['cap-lo-p'][site].filter(like='Pump').values[0],
                       data['storage']['var-cost-p'][site].filter(like='Pump').values[0],
                       data['storage']['init'][site].filter(like='Pump').values[0],
                       data['storage']['eff-in'][site].filter(like='Pump').values[0],
                       data['storage']['eff-out'][site].filter(like='Pump').values[0],
                       data['storage']['discharge'][site].filter(like='Pump').values[0])

        # Site Creation
        sites[site] = Site(site, data, weight,
                           bus=bus_list,
                           source=source_dict,
                           rsource=rsource_dict,
                           transformer=transformer_dict,
                           sink=sink_dict,
                           storage={'Elec': storage_tup})

        sites[site] = sites[site]._create_components()

    # Create Transmission Lines
    """Syntax

    Line(site_0, site_1, weight,
         specs=[(ep_costs, max_capacity, existing_capacity, variable_cost,
                 conversion_factor]
        )
    """
    lines_list = list(data['transmission'].reset_index(level=[2, 3]).index.values)
    lines_list = (set(tuple(sorted(line)) for line in lines_list))
    lines = dict.fromkeys(lines_list)

    for line in lines:
        lines[line] = Line(sites[line[0]], sites[line[1]], weight,
                           specs=[economics.annuity(data['transmission']['inv-cost'][line][0],
                                                    data['transmission']['depreciation'][line][0],
                                                    data['transmission']['wacc'][line][0]),
                           data['transmission']['cap-up'][line][0],
                           data['transmission']['inst-cap'][line][0],
                           data['transmission']['var-cost'][line][0],
                           data['transmission']['eff'][line][0]])

        lines[line] = lines[line]._create_lines()

    # transmission symmetry constraint
    lines_sym = []
    for key in es.groups.keys():
        if isinstance(key, str) and 'line' in key:
            lines_sym.append(key)
    lines_sym = [i for i in combinations(lines_sym, 2) if i[0].split('_')[1:] == i[1].split('_')[1:][::-1]]

    # create model
    model = solph.Model(es)
    model.name = 'oemof APP'

    # add lines symmetry constraint
    for line in lines_sym:
        l0 = es.groups[line[0]]
        l1 = es.groups[line[1]]
        b0 = es.groups['b_Elec_'+line[0].split('_')[1:][0]]
        b1 = es.groups['b_Elec_'+line[1].split('_')[1:][0]]

        solph.constraints.equate_variables(model,
                                           model.InvestmentFlow.invest[b0, l0],
                                           model.InvestmentFlow.invest[b1, l1])

    return es, model
