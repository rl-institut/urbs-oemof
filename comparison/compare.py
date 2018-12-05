import os
import sys
import pandas as pd
import numpy as np
import oemof.solph as solph
import oemof.outputlib as outputlib
import matplotlib.pyplot as plt
from datetime import datetime


def prepare_result_directory(result_name):
    """ create a time stamped directory within the result folder """
    # timestamp for result directory
    now = datetime.now().strftime('%Y%m%dT%H%M')

    # create result directory if not existent
    result_dir = os.path.join('result', '{}-{}'.format(result_name, now))
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    return result_dir


def compare_storages(urbs_model, oemof_model):
    # get oemof storage variables
    oemof_model = solph.EnergySystem()
    oemof_model.restore(dpath=None, filename=None)

    # storage dictionaries
    sto_df = {}
    sto_con_df = {}
    sto_cap_df = {}

    for sit in urbs_model.sit:
        # plot init
        iterations = []
        urbs_values = []
        oemof_values = []

        # get storage variables for all sites
        results_bel = outputlib.views.node(oemof_model.results['main'],
                                           'b_el_'+sit)
        results_con = outputlib.views.node(oemof_model.results['main'],
                                           'None')

        # charge/discharge
        sto_df[sit] = results_bel['sequences']
        sto_df[sit] = sto_df[sit].filter(like='storage')

        # content
        sto_con_df[sit] = results_con['sequences']
        sto_con_df[sit] = sto_con_df[sit].filter(like=sit)

        # capacity
        sto_cap_df[sit] = results_con['scalars']
        sto_cap_df[sit] = sto_cap_df[sit].filter(like=sit)

        # output template
        print('----------------------------------------------------')
        print('i', '\t', 'Storage', sit, '\t', '(urbs - oemof)')

        # storage capacity
        if abs(urbs_model.cap_sto_c[(sit, 'Pump storage', 'Elec')]() -
               sto_cap_df[sit][(('storage_el_'+sit, 'None'),
                               'invest')]) >= 0.1:
            print('\t', 'Storage CAP', '\t' 'Diff:',
                  urbs_model.cap_sto_c[(sit, 'Pump storage', 'Elec')]() -
                  sto_cap_df[sit][(('storage_el_'+sit, 'None'),
                                  'invest')])

        for i in range(1, len(oemof_model.timeindex)):
            # storage unit charge
            if abs(urbs_model.e_sto_in[(i, sit, 'Pump storage', 'Elec')]() -
                   sto_df[sit][(('b_el_'+sit, 'storage_el_'+sit),
                               'flow')][(i-1)]) >= 0.1:

                print(i, '\t', 'Storage IN', '\t', 'Diff:',
                      urbs_model.e_sto_in[(i, sit, 'Pump storage', 'Elec')]() -
                      sto_df[sit][(('b_el_'+sit, 'storage_el_'+sit),
                                  'flow')][(i-1)])

            # storage unit discharge
            if abs(urbs_model.e_sto_out[(i, sit, 'Pump storage', 'Elec')]() -
                   sto_df[sit][(('storage_el_'+sit, 'b_el_'+sit),
                               'flow')][(i-1)]) >= 0.1:

                print(i, '\t', 'Storage OUT', '\t', 'Diff:',
                      urbs_model.e_sto_out[(i, sit, 'Pump storage', 'Elec')]() -
                      sto_df[sit][(('storage_el_'+sit, 'b_el_'+sit),
                                  'flow')][(i-1)])
            # storage unit content
            if abs(urbs_model.e_sto_con[(i, sit, 'Pump storage', 'Elec')]() -
                   sto_con_df[sit][(('storage_el_'+sit, 'None'),
                                   'capacity')][(i-1)]) >= 0.1:

                print(i, '\t', 'Storage CON', '\t', 'Diff:',
                      urbs_model.e_sto_con[(i, sit, 'Pump storage', 'Elec')]() -
                      sto_con_df[sit][(('storage_el_'+sit, 'None'),
                                      'capacity')][(i-1)])

            # plot details
            iterations.append(i)
            urbs_values.append(urbs_model.e_sto_con[(i, sit, 'Pump storage', 'Elec')]())
            oemof_values.append(sto_con_df[sit][(('storage_el_'+sit, 'None'),
                                                'capacity')][(i-1)])

        # plot
        draw_graph(sit, iterations, urbs_values, oemof_values, 'Storage')

    return print('----------------------------------------------------')


def compare_transmission(urbs_model, oemof_model):

    # get oemof transmission variables
    oemof_model = solph.EnergySystem()
    oemof_model.restore(dpath=None, filename=None)

    # transmission dictionaries
    tra_df = {}
    tra_cap_df = {}

    for sit in urbs_model.sit:
        # plot init
        sit_outs = []
        urbs_values = {}
        oemof_values = {}

        # get transmission variables for all sites
        results_bel = outputlib.views.node(oemof_model.results['main'],
                                           'b_el_'+sit)

        # in/out
        tra_df[sit] = results_bel['sequences']
        tra_df[sit] = tra_df[sit].filter(like='line')

        # capacity
        tra_cap_df[sit] = results_bel['scalars']
        tra_cap_df[sit] = tra_cap_df[sit].filter(like='line')

        print('----------------------------------------------------')
        print('i', '\t', 'Transmission', sit, '\t', '(urbs - oemof)')

        # transmission capacity
        out = (sit_out for sit_out in urbs_model.sit if sit_out != sit)
        for sit_out in out:
            try:
                if abs(urbs_model.cap_tra[(sit, sit_out, 'hvac', 'Elec')]() -
                       tra_cap_df[sit][(('b_el_'+sit, 'line_'+sit+'_'+sit_out),
                                       'invest')]) >= 0.1:

                    print('\t', 'Transmission CAP', '\t', sit+'_'+sit_out, '\t' 'Diff:',
                          urbs_model.cap_tra[(sit, sit_out, 'hvac', 'Elec')]() -
                          tra_cap_df[sit][(('b_el_'+sit, 'line_'+sit+'_'+sit_out),
                                          'invest')])

            except KeyError:
                if abs(urbs_model.cap_tra[(sit, sit_out, 'hvac', 'Elec')]() -
                       tra_cap_df[sit][(('b_el_'+sit, 'line_'+sit_out+'_'+sit),
                                       'invest')]) >= 0.1:

                    print('\t', 'Transmission CAP', '\t', sit+'_'+sit_out, '\t' 'Diff:',
                          urbs_model.cap_tra[(sit, sit_out, 'hvac', 'Elec')]() -
                          tra_cap_df[sit][(('b_el_'+sit, 'line_'+sit_out+'_'+sit),
                                          'invest')])

            # plot details
            sit_outs.append(sit_out)
            urbs_values[sit_out] = urbs_model.cap_tra[(sit, sit_out, 'hvac', 'Elec')]()
            try:
                oemof_values[sit_out] = tra_cap_df[sit][(('b_el_'+sit, 'line_'+sit+'_'+sit_out),
                                                        'invest')]
            except KeyError:
                oemof_values[sit_out] = tra_cap_df[sit][(('b_el_'+sit, 'line_'+sit_out+'_'+sit),
                                                        'invest')]

        for i in range(1, len(oemof_model.timeindex)):
            for sit_out in out:
                # transmission in
                try:
                    if abs(urbs_model.e_tra_in[(i, sit, sit_out, 'hvac', 'Elec')]() -
                           tra_df[sit][(('b_el_'+sit, 'line_'+sit+'_'+sit_out),
                                       'flow')][(i-1)]) >= 0.1:

                        print(i, '\t', 'Transmission IN', '\t', sit+'_'+sit_out, '\t' 'Diff:',
                              urbs_model.e_tra_in[(i, sit, sit_out, 'hvac', 'Elec')]() -
                              tra_df[sit][(('b_el_'+sit, 'line_'+sit+'_'+sit_out),
                                          'flow')][(i-1)])

                except KeyError:
                    if abs(urbs_model.e_tra_in[(i, sit, sit_out, 'hvac', 'Elec')]() -
                           tra_df[sit][(('b_el_'+sit, 'line_'+sit_out+'_'+sit),
                                       'flow')][(i-1)]) >= 0.1:

                        print(i, '\t', 'Transmission IN', '\t', sit+'_'+sit_out, '\t' 'Diff:',
                              urbs_model.e_tra_in[(i, sit, sit_out, 'hvac', 'Elec')]() -
                              tra_df[sit][(('b_el_'+sit, 'line_'+sit_out+'_'+sit),
                                          'flow')][(i-1)])

                # transmission out
                try:
                    if abs(urbs_model.e_tra_out[(i, sit_out, sit, 'hvac', 'Elec')]() -
                           tra_df[sit][(('line_'+sit+'_'+sit_out, 'b_el_'+sit),
                                       'flow')][(i-1)]) >= 0.1:

                        print(i, '\t', 'Transmission OUT', '\t', sit_out+'_'+sit, '\t' 'Diff:',
                              urbs_model.e_tra_out[(i, sit_out, sit, 'hvac', 'Elec')]() -
                              tra_df[sit][(('line_'+sit+'_'+sit_out, 'b_el_'+sit),
                                          'flow')][(i-1)])

                except KeyError:
                    if abs(urbs_model.e_tra_out[(i, sit_out, sit, 'hvac', 'Elec')]() -
                           tra_df[sit][(('line_'+sit_out+'_'+sit, 'b_el_'+sit),
                                       'flow')][(i-1)]) >= 0.1:

                        print(i, '\t', 'Transmission OUT', '\t', sit_out+'_'+sit, '\t' 'Diff:',
                              urbs_model.e_tra_out[(i, sit_out, sit, 'hvac', 'Elec')]() -
                              tra_df[sit][(('line_'+sit_out+'_'+sit, 'b_el_'+sit),
                                          'flow')][(i-1)])

        # plot
        draw_graph(sit, sit_outs, urbs_values, oemof_values, 'Transmission')

    return print('----------------------------------------------------')


def compare_process(urbs_model, oemof_model):

    # get oemof process variables
    oemof_model = solph.EnergySystem()
    oemof_model.restore(dpath=None, filename=None)

    # nRE process list
    pro_list = ['coal', 'lig', 'gas', 'bio']

    # Re process list
    ren_list = ['wind', 'pv', 'hydro']

    # nRE process dictionaries
    pro_df = {}
    pro_cap_df = {}

    # Re process dictionaries
    pro_r_df = {}
    pro_cap_r_df = {}

    for sit in urbs_model.sit:
        # get process unit variables for all sites
        results_bel = outputlib.views.node(oemof_model.results['main'],
                                           'b_el_'+sit)

        # nRE process unit
        pro_df[sit] = results_bel['sequences']
        pro_df[sit] = pro_df[sit].filter(like='pp')

        # RE process unit
        pro_r_df[sit] = results_bel['sequences']
        pro_r_df[sit] = pro_r_df[sit].filter(like='rs')

        # RE process capacity
        pro_cap_r_df[sit] = results_bel['scalars']
        pro_cap_r_df[sit] = pro_cap_r_df[sit].filter(like='rs')

        print('----------------------------------------------------')
        print('i', '\t', 'Process', sit, '\t', '(urbs - oemof)')

        # get nRE process capacity variables for all sites
        for pro in pro_list:
            results_con = outputlib.views.node(oemof_model.results['main'], 'pp_'+pro+'_'+sit)

            # nRE process capacity
            pro_cap_df[sit] = results_con['scalars']

            if pro is 'coal':
                if abs(urbs_model.cap_pro[(sit, 'Coal plant')]() -
                       pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                       'invest')]) >= 0.1:

                    print('\t', 'CAP', '\t', pro, '\t', 'Diff:',
                          urbs_model.cap_pro[(sit, 'Coal plant')]() -
                          pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                          'invest')])

                for i in range(1, len(oemof_model.timeindex)):
                    if abs(urbs_model.e_pro_out[(i, sit, 'Coal plant', 'Elec')]() -
                           pro_df[sit][(('pp_'+pro+'_'+sit, 'b_el_'+sit),
                                       'flow')][(i-1)]) >= 0.1:

                        print(i, '\t', 'UNIT', '\t', pro, '\t', 'Diff:',
                              urbs_model.e_pro_out[(i, sit, 'Coal plant', 'Elec')]() -
                              pro_df[sit][(('pp_'+pro+'_'+sit, 'b_el_'+sit),
                                           'flow')][(i-1)])

            elif pro is 'lig':
                if abs(urbs_model.cap_pro[(sit, 'Lignite plant')]() -
                       pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                       'invest')]) >= 0.1:

                    print('\t', 'CAP', '\t', pro, '\t', 'Diff:',
                          urbs_model.cap_pro[(sit, 'Lignite plant')]() -
                          pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                          'invest')])

                for i in range(1, len(oemof_model.timeindex)):
                    if abs(urbs_model.e_pro_out[(i, sit, 'Lignite plant', 'Elec')]() -
                           pro_df[sit][(('pp_'+pro+'_'+sit, 'b_el_'+sit),
                                       'flow')][(i-1)]) >= 0.1:

                        print(i, '\t', 'UNIT', '\t', pro, '\t', 'Diff:',
                              urbs_model.e_pro_out[(i, sit, 'Lignite plant', 'Elec')]() -
                              pro_df[sit][(('pp_'+pro+'_'+sit, 'b_el_'+sit),
                                           'flow')][(i-1)])

            elif pro is 'gas':
                if abs(urbs_model.cap_pro[(sit, 'Gas plant')]() -
                       pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                       'invest')]) >= 0.1:

                    print('\t', 'CAP', '\t', pro, '\t', 'Diff:',
                          urbs_model.cap_pro[(sit, 'Gas plant')]() -
                          pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                          'invest')])

                for i in range(1, len(oemof_model.timeindex)):
                    if abs(urbs_model.e_pro_out[(i, sit, 'Gas plant', 'Elec')]() -
                           pro_df[sit][(('pp_'+pro+'_'+sit, 'b_el_'+sit),
                                       'flow')][(i-1)]) >= 0.1:

                        print(i, '\t', 'UNIT', '\t', pro, '\t', 'Diff:',
                              urbs_model.e_pro_out[(i, sit, 'Gas plant', 'Elec')]() -
                              pro_df[sit][(('pp_'+pro+'_'+sit, 'b_el_'+sit),
                                           'flow')][(i-1)])

            elif pro is 'bio':
                if abs(urbs_model.cap_pro[(sit, 'Biomass plant')]() -
                       pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                       'invest')]) >= 0.1:

                    print('\t', 'CAP', '\t', pro, '\t', 'Diff:',
                          urbs_model.cap_pro[(sit, 'Biomass plant')]() -
                          pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                          'invest')])

                for i in range(1, len(oemof_model.timeindex)):
                    if abs(urbs_model.e_pro_out[(i, sit, 'Biomass plant', 'Elec')]() -
                           pro_df[sit][(('pp_'+pro+'_'+sit, 'b_el_'+sit),
                                       'flow')][(i-1)]) >= 0.1:

                        print(i, '\t', 'UNIT', '\t', pro, '\t', 'Diff:',
                              urbs_model.e_pro_out[(i, sit, 'Biomass plant', 'Elec')]() -
                              pro_df[sit][(('pp_'+pro+'_'+sit, 'b_el_'+sit),
                                          'flow')][(i-1)])

            else:
                raise TypeError('NON Recognised Value for PRO-LOOP')

        for ren in ren_list:
            if ren is 'wind':
                if abs(urbs_model.cap_pro[(sit, 'Wind park')]() -
                       pro_cap_r_df[sit][(('rs_'+ren+'_'+sit, 'b_el_'+sit),
                                         'invest')]) >= 0.1:

                    print('\t', 'CAP', '\t', ren, '\t', 'Diff:',
                          urbs_model.cap_pro[(sit, 'Wind park')]() -
                          pro_cap_r_df[sit][(('rs_'+ren+'_'+sit, 'b_el_'+sit),
                                            'invest')])

                for i in range(1, len(oemof_model.timeindex)):
                    if abs(urbs_model.e_pro_out[(i, sit, 'Wind park', 'Elec')]() -
                           pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_el_'+sit),
                                         'flow')][(i-1)]) >= 0.1:

                        print(i, '\t', 'UNIT', '\t', ren, '\t', 'Diff:',
                              urbs_model.e_pro_out[(i, sit, 'Wind park', 'Elec')]() -
                              pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_el_'+sit),
                                            'flow')][(i-1)])

            elif ren is 'pv':
                if abs(urbs_model.cap_pro[(sit, 'Photovoltaics')]() -
                       pro_cap_r_df[sit][(('rs_'+ren+'_'+sit, 'b_el_'+sit),
                                         'invest')]) >= 0.1:

                    print('\t', 'CAP', '\t', ren, '\t', 'Diff:',
                          urbs_model.cap_pro[(sit, 'Photovoltaics')]() -
                          pro_cap_r_df[sit][(('rs_'+ren+'_'+sit, 'b_el_'+sit),
                                            'invest')])

                for i in range(1, len(oemof_model.timeindex)):
                    if abs(urbs_model.e_pro_out[(i, sit, 'Photovoltaics', 'Elec')]() -
                           pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_el_'+sit),
                                         'flow')][(i-1)]) >= 0.1:

                        print(i, '\t', 'UNIT', '\t', ren, '\t', 'Diff:',
                              urbs_model.e_pro_out[(i, sit, 'Photovoltaics', 'Elec')]() -
                              pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_el_'+sit),
                                            'flow')][(i-1)])

            elif ren is 'hydro':
                if abs(urbs_model.cap_pro[(sit, 'Hydro plant')]() -
                       pro_cap_r_df[sit][(('rs_'+ren+'_'+sit, 'b_el_'+sit),
                                         'invest')]) >= 0.1:

                    print('\t', 'CAP', '\t', ren, '\t', 'Diff:',
                          urbs_model.cap_pro[(sit, 'Hydro plant')]() -
                          pro_cap_r_df[sit][(('rs_'+ren+'_'+sit, 'b_el_'+sit),
                                            'invest')])

                for i in range(1, len(oemof_model.timeindex)):
                    if abs(urbs_model.e_pro_out[(i, sit, 'Hydro plant', 'Elec')]() -
                           pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_el_'+sit),
                                         'flow')][(i-1)]) >= 0.1:

                        print(i, '\t', 'UNIT', '\t', ren, '\t', 'Diff:',
                              urbs_model.e_pro_out[(i, sit, 'Hydro plant', 'Elec')]() -
                              pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_el_'+sit),
                                            'flow')][(i-1)])

            else:
                raise TypeError('NON Recognised Value for PRO-RE-LOOP')

    return print('----------------------------------------------------')


def draw_graph(site, i, urbs_values, oemof_values, name):
    # result directory
    result_dir = prepare_result_directory('plots')

    if name is 'Storage':
        # x-Axis (timesteps)
        i = np.array(i)

        # y-Axis (values)
        u = np.array(urbs_values)
        o = np.array(oemof_values)

        # create figure
        fig = plt.figure()

        # draw plots
        plt.plot(i, u, label='urbs', linestyle='--', dashes=(5, 5), marker='x')
        plt.ticklabel_format(axis='y', style='sci',scilimits=(1,5))
        plt.plot(i, o, label='oemof', linestyle='--', dashes=(5, 5), marker='.')
        plt.ticklabel_format(axis='y', style='sci',scilimits=(1,5))

        # plot specs
        plt.xlabel('Timesteps')
        plt.ylabel('Value')
        plt.title(site+' '+name)
        plt.grid(True)
        plt.legend()
        # plt.show()

        # save plot
        fig.savefig(os.path.join(result_dir, 'comp_'+name+'_'+site+'.png'), dpi=300)

    elif name is 'Transmission':
         # x-Axis (timesteps)
        i = np.array(i)
        i_pos = np.arange(len(i))

        # y-Axis (values)
        u = urbs_values
        o = oemof_values

        # create figure
        fig = plt.figure()

        plt.bar(i_pos-0.15, list(u.values()), label='urbs', align='center', alpha=0.75, width=0.2)
        plt.ticklabel_format(axis='y', style='sci',scilimits=(1,5))
        plt.bar(i_pos+0.15, list(o.values()), label='oemof', align='center', alpha=0.75, width=0.2)
        plt.ticklabel_format(axis='y', style='sci',scilimits=(1,5))

        # tick names
        plt.xticks(i_pos, list(map((site+' to ').__add__, list(u.keys()))))

        # plot specs
        plt.xlabel('Lines')
        plt.ylabel('Capacity [MW]')
        plt.title(site+' '+name)
        plt.grid(True)
        plt.legend()
        plt.ticklabel_format(style='sci', axis='y')
        # plt.show()

        # save plot
        fig.savefig(os.path.join(result_dir, 'comp_'+name+'_'+site+'.png'), dpi=300)
