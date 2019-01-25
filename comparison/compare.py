import os
import sys
import re as r
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


def compare_lp_files():
    # open urbs lp file
    with open('mimo_urbs.lp', 'r') as urbslp:

        # create constraint file
        const = open('constraints_urbs.txt', 'w+')

        for line in urbslp:

            # find constraints
            ce = r.match(r'c_e_(.*)\_', line)
            cu = r.match(r'c_u_(.*)\_', line)
            re = r.match(r'r_e_(.*)\_', line)
            rl = r.match(r'r_l_(.*)\_', line)

            # write constraints
            if ce:
                const.write(ce.group(1))
                const.write('\n')

            if cu:
                const.write(cu.group(1))
                const.write('\n')

            if re:
                const.write(re.group(1))
                const.write('\n')

            if rl:
                const.write(rl.group(1))
                const.write('\n')

        const.close()

    # open oemof lp file
    with open('mimo_oemof.lp', 'r') as oemoflp:

        # create constraint file
        const = open('constraints_oemof.txt', 'w+')

        for line in oemoflp:

            # find constraints
            ce = r.match(r'c_e_(.*)\_', line)
            cu = r.match(r'c_u_(.*)\_', line)

            # write constraints
            if ce:
                const.write(ce.group(1))
                const.write('\n')
            if cu:
                const.write(cu.group(1))
                const.write('\n')

        
        const.close()

    return None


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
                                           'b_Elec_'+sit)
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
               sto_cap_df[sit][(('storage_Elec_'+sit, 'None'),
                               'invest')]) >= 0.01:
            print('\t', 'Storage CAP', '\t' 'Diff:',
                  urbs_model.cap_sto_c[(sit, 'Pump storage', 'Elec')]() -
                  sto_cap_df[sit][(('storage_Elec_'+sit, 'None'),
                                  'invest')])

        for i in range(1, len(oemof_model.timeindex)):
            # storage unit charge
            if abs(urbs_model.e_sto_in[(i, sit, 'Pump storage', 'Elec')]() -
                   sto_df[sit][(('b_Elec_'+sit, 'storage_Elec_'+sit),
                               'flow')][(i-1)]) >= 0.01:

                print(i, '\t', 'Storage IN', '\t', 'Diff:',
                      urbs_model.e_sto_in[(i, sit, 'Pump storage', 'Elec')]() -
                      sto_df[sit][(('b_Elec_'+sit, 'storage_Elec_'+sit),
                                  'flow')][(i-1)])

            # storage unit discharge
            if abs(urbs_model.e_sto_out[(i, sit, 'Pump storage', 'Elec')]() -
                   sto_df[sit][(('storage_Elec_'+sit, 'b_Elec_'+sit),
                               'flow')][(i-1)]) >= 0.01:

                print(i, '\t', 'Storage OUT', '\t', 'Diff:',
                      urbs_model.e_sto_out[(i, sit, 'Pump storage', 'Elec')]() -
                      sto_df[sit][(('storage_Elec_'+sit, 'b_Elec_'+sit),
                                  'flow')][(i-1)])
            # storage unit content
            if abs(urbs_model.e_sto_con[(i, sit, 'Pump storage', 'Elec')]() -
                   sto_con_df[sit][(('storage_Elec_'+sit, 'None'),
                                   'capacity')][(i-1)]) >= 0.01:

                print(i, '\t', 'Storage CON', '\t', 'Diff:',
                      urbs_model.e_sto_con[(i, sit, 'Pump storage', 'Elec')]() -
                      sto_con_df[sit][(('storage_Elec_'+sit, 'None'),
                                      'capacity')][(i-1)])

            # plot details
            iterations.append(i)
            urbs_values.append(urbs_model.e_sto_con[(i, sit, 'Pump storage', 'Elec')]())
            oemof_values.append(sto_con_df[sit][(('storage_Elec_'+sit, 'None'),
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
                                           'b_Elec_'+sit)

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
            if abs(urbs_model.cap_tra[(sit, sit_out, 'hvac', 'Elec')]() -
                   tra_cap_df[sit][(('b_Elec_'+sit, 'line_'+sit+'_'+sit_out),
                                    'invest')]) >= 0.01:

                print('\t', 'Transmission CAP', '\t', sit+'_'+sit_out, '\t' 'Diff:',
                      urbs_model.cap_tra[(sit, sit_out, 'hvac', 'Elec')]() -
                      tra_cap_df[sit][(('b_Elec_'+sit, 'line_'+sit+'_'+sit_out),
                                       'invest')])

            # plot details
            sit_outs.append(sit_out)
            urbs_values[sit_out] = urbs_model.cap_tra[(sit, sit_out, 'hvac', 'Elec')]()
            oemof_values[sit_out] = tra_cap_df[sit][(('b_Elec_'+sit, 'line_'+sit+'_'+sit_out),
                                                    'invest')]

        out = (sit_out for sit_out in urbs_model.sit if sit_out != sit)
        for i in range(1, len(oemof_model.timeindex)):
            for sit_out in out:
                # transmission in
                if abs(urbs_model.e_tra_in[(i, sit, sit_out, 'hvac', 'Elec')]() -
                       tra_df[sit][(('b_Elec_'+sit, 'line_'+sit+'_'+sit_out),
                                   'flow')][(i-1)]) >= 0.01:

                    print(i, '\t', 'Transmission IN', '\t', sit+'_'+sit_out, '\t' 'Diff:',
                          urbs_model.e_tra_in[(i, sit, sit_out, 'hvac', 'Elec')]() -
                          tra_df[sit][(('b_Elec_'+sit, 'line_'+sit+'_'+sit_out),
                                      'flow')][(i-1)])

                # transmission out
                if abs(urbs_model.e_tra_out[(i, sit_out, sit, 'hvac', 'Elec')]() -
                       tra_df[sit][(('line_'+sit_out+'_'+sit, 'b_Elec_'+sit),
                                   'flow')][(i-1)]) >= 0.01:

                    print(i, '\t', 'Transmission OUT', '\t', sit+'_'+sit_out, '\t' 'Diff:',
                          urbs_model.e_tra_out[(i, sit_out, sit, 'hvac', 'Elec')]() -
                          tra_df[sit][(('line_'+sit_out+'_'+sit, 'b_Elec_'+sit),
                                      'flow')][(i-1)])

        # plot
        draw_graph(sit, sit_outs, urbs_values, oemof_values, 'Transmission')

    return print('----------------------------------------------------')


def compare_process(urbs_model, oemof_model):

    # get oemof process variables
    oemof_model = solph.EnergySystem()
    oemof_model.restore(dpath=None, filename=None)

    # nRE process list
    pro_list = ['Biomass', 'Coal', 'Gas', 'Lignite']

    # Re process list
    ren_list = ['Wind', 'Solar', 'Hydro']

    # nRE process dictionaries
    pro_df = {}
    pro_cap_df = {}

    # Re process dictionaries
    pro_r_df = {}
    pro_cap_r_df = {}

    for sit in urbs_model.sit:
        # plot init
        iterations = []
        urbs_values = dict([(key, []) for key in pro_list])
        oemof_values = dict([(key, []) for key in pro_list])

        # get process unit variables for all sites
        results_bel = outputlib.views.node(oemof_model.results['main'],
                                           'b_Elec_'+sit)

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

            if pro is 'Coal':
                if abs(urbs_model.cap_pro[(sit, 'Coal plant')]() -
                       pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                       'invest')]) >= 0.01:

                    print('\t', 'CAP', '\t', pro, '\t', 'Diff:',
                          urbs_model.cap_pro[(sit, 'Coal plant')]() -
                          pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                          'invest')])

                for i in range(1, len(oemof_model.timeindex)):
                    # plot details
                    iterations.append(i)
                    urbs_values[pro].append(urbs_model.e_pro_out[(i, sit, 'Coal plant', 'Elec')]())
                    oemof_values[pro].append(pro_df[sit][(('pp_'+pro+'_'+sit, 'b_Elec_'+sit),
                                                         'flow')][(i-1)])

                    if abs(urbs_model.e_pro_out[(i, sit, 'Coal plant', 'Elec')]() -
                           pro_df[sit][(('pp_'+pro+'_'+sit, 'b_Elec_'+sit),
                                       'flow')][(i-1)]) >= 0.01:

                        print(i, '\t', 'UNIT', '\t', pro, '\t', 'Diff:',
                              urbs_model.e_pro_out[(i, sit, 'Coal plant', 'Elec')]() -
                              pro_df[sit][(('pp_'+pro+'_'+sit, 'b_Elec_'+sit),
                                           'flow')][(i-1)])

            elif pro is 'Lignite':
                if abs(urbs_model.cap_pro[(sit, 'Lignite plant')]() -
                       pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                       'invest')]) >= 0.01:

                    print('\t', 'CAP', '\t', pro, '\t', 'Diff:',
                          urbs_model.cap_pro[(sit, 'Lignite plant')]() -
                          pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                          'invest')])

                for i in range(1, len(oemof_model.timeindex)):
                    # plot details
                    urbs_values[pro].append(urbs_model.e_pro_out[(i, sit, 'Lignite plant', 'Elec')]())
                    oemof_values[pro].append(pro_df[sit][(('pp_'+pro+'_'+sit, 'b_Elec_'+sit),
                                                         'flow')][(i-1)])

                    if abs(urbs_model.e_pro_out[(i, sit, 'Lignite plant', 'Elec')]() -
                           pro_df[sit][(('pp_'+pro+'_'+sit, 'b_Elec_'+sit),
                                       'flow')][(i-1)]) >= 0.01:

                        print(i, '\t', 'UNIT', '\t', pro, '\t', 'Diff:',
                              urbs_model.e_pro_out[(i, sit, 'Lignite plant', 'Elec')]() -
                              pro_df[sit][(('pp_'+pro+'_'+sit, 'b_Elec_'+sit),
                                           'flow')][(i-1)])

            elif pro is 'Gas':
                if abs(urbs_model.cap_pro[(sit, 'Gas plant')]() -
                       pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                       'invest')]) >= 0.01:

                    print('\t', 'CAP', '\t', pro, '\t', 'Diff:',
                          urbs_model.cap_pro[(sit, 'Gas plant')]() -
                          pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                          'invest')])

                for i in range(1, len(oemof_model.timeindex)):
                    # plot details
                    urbs_values[pro].append(urbs_model.e_pro_out[(i, sit, 'Gas plant', 'Elec')]())
                    oemof_values[pro].append(pro_df[sit][(('pp_'+pro+'_'+sit, 'b_Elec_'+sit),
                                                         'flow')][(i-1)])

                    if abs(urbs_model.e_pro_out[(i, sit, 'Gas plant', 'Elec')]() -
                           pro_df[sit][(('pp_'+pro+'_'+sit, 'b_Elec_'+sit),
                                       'flow')][(i-1)]) >= 0.01:

                        print(i, '\t', 'UNIT', '\t', pro, '\t', 'Diff:',
                              urbs_model.e_pro_out[(i, sit, 'Gas plant', 'Elec')]() -
                              pro_df[sit][(('pp_'+pro+'_'+sit, 'b_Elec_'+sit),
                                           'flow')][(i-1)])

            elif pro is 'Biomass':
                if abs(urbs_model.cap_pro[(sit, 'Biomass plant')]() -
                       pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                       'invest')]) >= 0.01:

                    print('\t', 'CAP', '\t', pro, '\t', 'Diff:',
                          urbs_model.cap_pro[(sit, 'Biomass plant')]() -
                          pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                          'invest')])

                for i in range(1, len(oemof_model.timeindex)):
                    # plot details
                    urbs_values[pro].append(urbs_model.e_pro_out[(i, sit, 'Biomass plant', 'Elec')]())
                    oemof_values[pro].append(pro_df[sit][(('pp_'+pro+'_'+sit, 'b_Elec_'+sit),
                                                         'flow')][(i-1)])

                    if abs(urbs_model.e_pro_out[(i, sit, 'Biomass plant', 'Elec')]() -
                           pro_df[sit][(('pp_'+pro+'_'+sit, 'b_Elec_'+sit),
                                       'flow')][(i-1)]) >= 0.01:

                        print(i, '\t', 'UNIT', '\t', pro, '\t', 'Diff:',
                              urbs_model.e_pro_out[(i, sit, 'Biomass plant', 'Elec')]() -
                              pro_df[sit][(('pp_'+pro+'_'+sit, 'b_Elec_'+sit),
                                          'flow')][(i-1)])

            else:
                raise TypeError('NON Recognised Value for PRO-LOOP')

        # plot
        draw_graph(sit, iterations, urbs_values, oemof_values, 'Process (PP)')

        # plot init
        urbs_values = dict([(key, []) for key in ren_list])
        oemof_values = dict([(key, []) for key in ren_list])

        for ren in ren_list:
            if ren is 'Wind':
                if abs(urbs_model.cap_pro[(sit, 'Wind park')]() -
                       pro_cap_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                         'invest')]) >= 0.01:

                    print('\t', 'CAP', '\t', ren, '\t', 'Diff:',
                          urbs_model.cap_pro[(sit, 'Wind park')]() -
                          pro_cap_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                            'invest')])

                for i in range(1, len(oemof_model.timeindex)):
                    # plot details
                    urbs_values[ren].append(urbs_model.e_pro_out[(i, sit, 'Wind park', 'Elec')]())
                    oemof_values[ren].append(pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                                           'flow')][(i-1)])

                    if abs(urbs_model.e_pro_out[(i, sit, 'Wind park', 'Elec')]() -
                           pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                         'flow')][(i-1)]) >= 0.01:

                        print(i, '\t', 'UNIT', '\t', ren, '\t', 'Diff:',
                              urbs_model.e_pro_out[(i, sit, 'Wind park', 'Elec')]() -
                              pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                            'flow')][(i-1)])

            elif ren is 'Solar':
                if abs(urbs_model.cap_pro[(sit, 'Solar plant')]() -
                       pro_cap_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                         'invest')]) >= 0.01:

                    print('\t', 'CAP', '\t', ren, '\t', 'Diff:',
                          urbs_model.cap_pro[(sit, 'Solar plant')]() -
                          pro_cap_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                            'invest')])

                for i in range(1, len(oemof_model.timeindex)):
                    # plot details
                    urbs_values[ren].append(urbs_model.e_pro_out[(i, sit, 'Solar plant', 'Elec')]())
                    oemof_values[ren].append(pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                                           'flow')][(i-1)])

                    if abs(urbs_model.e_pro_out[(i, sit, 'Solar plant', 'Elec')]() -
                           pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                         'flow')][(i-1)]) >= 0.01:

                        print(i, '\t', 'UNIT', '\t', ren, '\t', 'Diff:',
                              urbs_model.e_pro_out[(i, sit, 'Solar plant', 'Elec')]() -
                              pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                            'flow')][(i-1)])

            elif ren is 'Hydro':
                if abs(urbs_model.cap_pro[(sit, 'Hydro plant')]() -
                       pro_cap_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                         'invest')]) >= 0.01:

                    print('\t', 'CAP', '\t', ren, '\t', 'Diff:',
                          urbs_model.cap_pro[(sit, 'Hydro plant')]() -
                          pro_cap_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                            'invest')])

                for i in range(1, len(oemof_model.timeindex)):
                    # plot details
                    urbs_values[ren].append(urbs_model.e_pro_out[(i, sit, 'Hydro plant', 'Elec')]())
                    oemof_values[ren].append(pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                                           'flow')][(i-1)])

                    if abs(urbs_model.e_pro_out[(i, sit, 'Hydro plant', 'Elec')]() -
                           pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                         'flow')][(i-1)]) >= 0.01:

                        print(i, '\t', 'UNIT', '\t', ren, '\t', 'Diff:',
                              urbs_model.e_pro_out[(i, sit, 'Hydro plant', 'Elec')]() -
                              pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                            'flow')][(i-1)])

            else:
                raise TypeError('NON Recognised Value for PRO-RE-LOOP')

        # plot
        draw_graph(sit, iterations, urbs_values, oemof_values, 'Process (fPP)')

    return print('----------------------------------------------------')


def draw_graph(site, i, urbs_values, oemof_values, name):
    # result directory
    result_dir = prepare_result_directory('plots')

    if name is 'Storage':
        # create figure
        fig = plt.figure()

        # x-Axis (timesteps)
        i = np.array(i)

        # y-Axis (values)
        u = np.array(urbs_values)
        o = np.array(oemof_values)

        # draw plots
        plt.plot(i, u, label='urbs', linestyle='None', marker='x')
        plt.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        plt.plot(i, o, label='oemof', linestyle='None', marker='.')
        plt.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))

        # plot specs
        plt.xlabel('Timesteps [h]')
        plt.ylabel('Content [MWh]')
        plt.title(site+' '+name)
        plt.grid(True)
        plt.legend()
        # plt.show()

        # save plot
        fig.savefig(os.path.join(result_dir, 'comp_'+name+'_'+site+'.png'), dpi=300)

    elif name is 'Transmission':
        # create figure
        fig = plt.figure()

        # x-Axis (sites)
        i = np.array(i)
        i_pos = np.arange(len(i))

        # y-Axis (values)
        u = urbs_values
        o = oemof_values

        plt.bar(i_pos-0.15, list(u.values()), label='urbs', align='center', alpha=0.75, width=0.2)
        plt.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        plt.bar(i_pos+0.15, list(o.values()), label='oemof', align='center', alpha=0.75, width=0.2)
        plt.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))

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

    elif 'Process' in name:
        # init
        u = {}
        o = {}

        # create figure
        fig = plt.figure()

        # x-Axis (timesteps)
        i = np.array(i)

        for key in urbs_values.keys():
            # y-Axis (values)
            u[key] = np.array(urbs_values[key])
            o[key] = np.array(oemof_values[key])

            # draw plots
            plt.plot(i, u[key], label='urbs_'+str(key), linestyle='None', marker='x')
            plt.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
            plt.plot(i, o[key], label='oemof_'+str(key), linestyle='None', marker='.')
            plt.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))

        # plot specs
        plt.xlabel('Timesteps [h]')
        plt.ylabel('Flow [MWh]')
        plt.title(site+' '+name)
        plt.grid(True)
        plt.legend()
        # plt.show()

        # save plot
        fig.savefig(os.path.join(result_dir, 'comp_'+name+'_'+site+'.png'), dpi=300)
