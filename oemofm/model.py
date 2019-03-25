from oemof.tools import economics
from oemof.network import Node
from itertools import combinations
import matplotlib.pyplot as plt
import oemof.solph as solph
import networkx as nx
import pandas as pd
import math


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
        for s in self.source:
            source['s_'+s+'_'+self.name] = solph.Source(
                label='s_'+s+'_'+self.name,
                outputs={bus['b_'+s+'_'+self.name]:
                         solph.Flow(
                             variable_costs=self.source[s]*self.weight)})

        # create renewable sources
        for rs in self.rsource:
            rsource['rs_'+rs+'_'+self.name] = solph.Source(
                label='rs_'+rs+'_'+self.name,
                outputs={bus['b_Elec'+'_'+self.name]:
                         solph.Flow(
                             actual_value=self.rsource[rs][0],
                             fixed=True,
                             investment=solph.Investment(
                                 ep_costs=self.rsource[rs][1],
                                 maximum=self.rsource[rs][2],
                                 existing=self.rsource[rs][3]))})

        # create transformer (output: elec only)
        for t in self.transformer:
            transformer['t_'+t+'_'+self.name] = solph.Transformer(
                label='pp_'+t+'_'+self.name,
                inputs={bus['b_'+t+'_'+self.name]:
                        solph.Flow(
                            investment=solph.Investment(
                                ep_costs=self.transformer[t][0],
                                maximum=self.transformer[t][1],
                                existing=self.transformer[t][2]),
                            variable_costs=self.transformer[t][3]*self.weight,
                            emission=self.transformer[t][4]*self.weight)},
                outputs={bus['b_Elec'+'_'+self.name]: solph.Flow()},
                conversion_factors={bus['b_'+t+'_'+self.name]:
                                    self.transformer[t][5],
                                    bus['b_Elec'+'_'+self.name]:
                                    self.transformer[t][6]})

        # create sink (input: elec only)
        for sn in self.sink:
            sink[sn+'_'+self.name] = solph.Sink(
                label=sn+'_'+self.name,
                inputs={bus['b_Elec'+'_'+self.name]:
                        solph.Flow(
                            actual_value=self.sink[sn],
                            fixed=True, nominal_value=1)})

        # create storage
        for st in self.storage:
            storage['storage_'+st+'_'+self.name] = solph.components.GenericStorage(
                label='storage_'+st+'_'+self.name,
                inputs={bus['b_Elec'+'_'+self.name]:
                        solph.Flow(
                            investment=solph.Investment(
                                ep_costs=self.storage[st][0],
                                maximum=self.storage[st][1],
                                existing=self.storage[st][2]),
                            variable_costs=self.storage[st][3]*self.weight)},
                outputs={bus['b_Elec'+'_'+self.name]:
                         solph.Flow(
                             investment=solph.Investment(
                                 ep_costs=0,
                                 maximum=self.storage[st][1],
                                 existing=self.storage[st][2]),
                             variable_costs=self.storage[st][3]*self.weight)},
                investment=solph.Investment(
                    ep_costs=self.storage[st][4],
                    maximum=self.storage[st][5],
                    existing=self.storage[st][6]),
                variable_costs=self.storage[st][7]*self.weight,
                initial_capacity=self.storage[st][8],
                inflow_conversion_factor=self.storage[st][9],
                outflow_conversion_factor=self.storage[st][10],
                capacity_loss=self.storage[st][11])

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
                        self.site_1[1]['b_Elec'+'_'+self.site_1[0]]):
                        self.specs[4],
                       (self.site_1[1]['b_Elec'+'_'+self.site_1[0]],
                        self.site_0[1]['b_Elec'+'_'+self.site_0[0]]):
                        self.specs[4]})
        """
        line = {}
        line['line_'+self.site_0[0]+'_'+self.site_1[0]] = solph.Transformer(
            label='line_'+self.site_0[0]+'_'+self.site_1[0],
            inputs={self.site_0[1]['b_Elec'+'_'+self.site_0[0]]:
                    solph.Flow(
                        investment=solph.Investment(
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
                    solph.Flow(
                        investment=solph.Investment(
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
    """
    Creates an oemof model for given input, time steps

    Args:
        data: input data
        timesteps: simulation timesteps

    Returns:
        es: an oemof energy system
        model: an oemof model instance
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
         rsource={components: (data, annuity, max-cap, existing-cap)},
         transformer={components: (annuity, max-cap, existing-cap, var-cost,
                                   conversion_factor, )},
         sink={components: data}
         storage={components: (annuity, max-cap-p, existing-cap-p, var-cost-p,
                               annuity, max-cap-c, existing-cap-c, var-cost-c,
                               initial-cap, eff-in, eff-out, discharge)}
        )
    """
    sites = dict.fromkeys(data['site'].index)

    for site in sites:
        # Create Lists and Dicts for Sites
        df1 = data['commodity'].index.get_level_values('Site') == site
        df2 = data['commodity'].index.get_level_values('Type') == 'Stock'
        df3 = data['commodity'].index.get_level_values('Type') == 'Demand'
        df4 = data['commodity'].index.get_level_values('Type') == 'SupIm'
        df5 = data['storage'].index.get_level_values('Storage').unique()

        # Bus List
        bus_df1 = data['commodity'][df1 & df2].index.remove_unused_levels() \
            .get_level_values('Commodity')
        bus_df2 = data['commodity'][df1 & df3].index.remove_unused_levels() \
            .get_level_values('Commodity')
        bus_list = bus_df1.append(bus_df2).tolist()

        # Source Dict
        source_dict = {}
        for item in bus_df1:
            source_dict[item] = data['commodity']['price'][site][item]['Stock']

        # RSource List & Dict
        r_df = data['commodity'][df1 & df4].index.remove_unused_levels() \
            .get_level_values('Commodity')
        rsource_list = r_df.tolist()
        rsource_dict = {}
        for item in rsource_list:
            rsource_dict[item] = (
                data['supim'][site][item],
                economics.annuity(
                    data['process']['inv-cost'][site].filter(like=item).values[0],
                    data['process']['depreciation'][site].filter(like=item).values[0],
                    data['process']['wacc'][site].filter(like=item).values[0]),
                data['process']['cap-up'][site].filter(like=item).values[0],
                data['process']['inst-cap'][site].filter(like=item).values[0])

        # Transformer Dict
        transformer_dict = {}
        for item in bus_df1:
            transformer_dict[item] = (
                economics.annuity(data['process']['inv-cost'][site].filter(like=item).values[0],
                                  data['process']['depreciation'][site].filter(like=item).values[0],
                                  data['process']['wacc'][site].filter(like=item).values[0]),
                data['process']['cap-up'][site].filter(like=item).values[0],
                data['process']['inst-cap'][site].filter(like=item).values[0],
                data['process']['var-cost'][site].filter(like=item).values[0],
                data['process_commodity']['ratio'].filter(like=item).filter(like='CO2').values[0],
                data['process_commodity']['ratio'].filter(like=item).filter(like='In').values[0],
                data['process_commodity']['ratio'].filter(like=item).filter(like='Elec').values[0])

        # Sink Dict
        sink_dict = {}
        for item in bus_df2:
            sink_dict[item] = data['demand'][site][item]

        # Storage Tuple
        storage_dict = {}
        for item in df5:
            storage_dict[item] = (
                economics.annuity(data['storage']['inv-cost-p'][site].filter(like=item).values[0],
                                  data['storage']['depreciation'][site].filter(like=item).values[0],
                                  data['storage']['wacc'][site].filter(like=item).values[0]),
                data['storage']['cap-up-p'][site].filter(like=item).values[0],
                data['storage']['inst-cap-p'][site].filter(like=item).values[0],
                data['storage']['var-cost-p'][site].filter(like=item).values[0],
                economics.annuity(data['storage']['inv-cost-c'][site].filter(like=item).values[0],
                                  data['storage']['depreciation'][site].filter(like=item).values[0],
                                  data['storage']['wacc'][site].filter(like=item).values[0]),
                data['storage']['cap-up-c'][site].filter(like=item).values[0],
                data['storage']['inst-cap-c'][site].filter(like=item).values[0],
                data['storage']['var-cost-c'][site].filter(like=item).values[0],
                data['storage']['init'][site].filter(like=item).values[0],
                data['storage']['eff-in'][site].filter(like=item).values[0],
                data['storage']['eff-out'][site].filter(like=item).values[0],
                data['storage']['discharge'][site].filter(like=item).values[0])

        # Site Creation
        sites[site] = Site(site, data, weight,
                           bus=bus_list,
                           source=source_dict,
                           rsource=rsource_dict,
                           transformer=transformer_dict,
                           sink=sink_dict,
                           storage=storage_dict)

        sites[site] = sites[site]._create_components()

    # Create Transmission Lines
    """Syntax

    Line(site_0, site_1, weight,
         specs=[(annuity, max-cap, existing-cap, var-cost, eff)]
        )
    """
    lines_list = list(data['transmission'].reset_index(level=[2, 3]).index.values)
    lines_list = (set(tuple(sorted(line)) for line in lines_list))
    lines = dict.fromkeys(lines_list)

    for line in lines:
        lines[line] = Line(sites[line[0]], sites[line[1]], weight, specs=[
            economics.annuity(data['transmission']['inv-cost'][line][0],
                              data['transmission']['depreciation'][line][0],
                              data['transmission']['wacc'][line][0]),
            data['transmission']['cap-up'][line][0],
            data['transmission']['inst-cap'][line][0],
            data['transmission']['var-cost'][line][0],
            data['transmission']['eff'][line][0]])

        lines[line] = lines[line]._create_lines()

    # create model
    model = solph.Model(es)
    model.name = 'oemof APP'

    # add storage investment symmetry constraint
    for site in sites:
        el = es.groups['b_Elec_'+sites[site][0]]
        sto = es.groups['storage_Pump_'+sites[site][0]]

        solph.constraints.equate_variables(
            model,
            model.InvestmentFlow.invest[el, sto],
            model.InvestmentFlow.invest[sto, el])

    # add storage power/capacity ratio constraint
    for site in sites:
        if math.isnan(data['storage']['ep-ratio'][site].filter(like='Pump').values[0]):
            continue
        else:
            pwr = es.groups['storage_Pump_'+sites[site][0]]
            el = es.groups['b_Elec_'+sites[site][0]]
            cap = es.groups['storage_Pump_'+sites[site][0]]

            solph.constraints.equate_variables(
                model,
                model.GenericInvestmentStorageBlock.invest[pwr],
                model.InvestmentFlow.invest[el, cap],
                factor1=data['storage']['ep-ratio'][site].filter(like='Pump').values[0])

    # add transmission lines symmetry constraint
    lines_sym = []
    for key in es.groups.keys():
        if isinstance(key, str) and 'line' in key:
            lines_sym.append(key)
    lines_sym = [i for i in combinations(lines_sym, 2)
                 if i[0].split('_')[1:] == i[1].split('_')[1:][::-1]]

    for line in lines_sym:
        l0 = es.groups[line[0]]
        l1 = es.groups[line[1]]
        b0 = es.groups['b_Elec_'+line[0].split('_')[1:][0]]
        b1 = es.groups['b_Elec_'+line[1].split('_')[1:][0]]

        solph.constraints.equate_variables(
            model,
            model.InvestmentFlow.invest[b0, l0],
            model.InvestmentFlow.invest[b1, l1])

    # add emission constraint
    if not math.isinf(data['global_prop']['value']['CO2 limit']):
        limit = data['global_prop']['value']['CO2 limit']
        solph.constraints.emission_limit(model, limit=limit)

    return es, model


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
