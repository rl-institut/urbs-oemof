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


def _file_len(filename):
    with open(filename) as f:
        for i, l in enumerate(f):
            pass
    return i


def compare_cpu_and_memory():
    # memory info & cpu time
    with open('urbs_log.txt', 'r') as urbslog:
        urbslog = urbslog.read().replace('\n', ' ')
        mem_urbs = float(urbslog[urbslog.find('Memory used:')+12:
                                 urbslog.find('Mb')])
        cpu_urbs = float(urbslog[urbslog.find('Time used:')+10:
                                 urbslog.find('secs')])

    with open('oemof_log.txt', 'r') as oemoflog:
        oemoflog = oemoflog.read().replace('\n', ' ')
        mem_oemof = float(oemoflog[oemoflog.find('Memory used:')+12:
                                   oemoflog.find('Mb')])
        cpu_oemof = float(oemoflog[oemoflog.find('Time used:')+10:
                                   oemoflog.find('secs')])

    # Terminal Output CPU
    print('Time Used')
    print('urbs\t', cpu_urbs, ' secs')
    print('oemof\t', cpu_oemof, ' secs')
    print('Diff\t', format(cpu_urbs - cpu_oemof, '.1f'), ' secs')
    print('----------------------------------------------------')

    # Terminal Output Memory
    print('Memory Used')
    print('urbs\t', mem_urbs, ' Mb')
    print('oemof\t', mem_oemof, ' Mb')
    print('Diff\t', format(mem_urbs - mem_oemof, '.1f'), ' Mb')
    print('----------------------------------------------------')

    return cpu_urbs, mem_urbs, cpu_oemof, mem_oemof


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

    u_const_amount = _file_len('constraints_urbs.txt')
    o_const_amount = _file_len('constraints_oemof.txt')

    # Terminal Output
    print('Constraint Amount')
    print('urbs\t', u_const_amount)
    print('oemof\t', o_const_amount)
    print('Diff\t', u_const_amount - o_const_amount)
    print('----------------------------------------------------')

    return u_const_amount, o_const_amount


def compare_storages(urbs_model, oemof_model, threshold):
    # restore oemof energysytem results
    oemof_model = solph.EnergySystem()
    oemof_model.restore(dpath=None, filename=None)

    # storage dictionaries
    sto_df = {}
    sto_con_df = {}
    sto_pwr_df = {}
    sto_cap_df = {}

    for sit in urbs_model.sit:
        # plot init
        iterations = []
        urbs_values = []
        oemof_values = []

        # get storage variable values
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

        # power
        sto_pwr_df[sit] = results_bel['scalars']
        sto_pwr_df[sit] = sto_pwr_df[sit].filter(like=sit)

        # capacity
        sto_cap_df[sit] = results_con['scalars']
        sto_cap_df[sit] = sto_cap_df[sit].filter(like=sit)

        # output template
        print('----------------------------------------------------')
        print('i', '\t', 'Storage', sit, '\t', '(urbs - oemof)')

        # storage power
        if abs(urbs_model.cap_sto_p_new[(sit, 'Pump', 'Elec')]() -
               sto_pwr_df[sit][(('b_Elec_'+sit, 'storage_Pump_'+sit),
                               'invest')]) >= threshold:
            print('\t', 'Storage PWR', '\t', 'Diff:',
                  urbs_model.cap_sto_p_new[(sit, 'Pump', 'Elec')]() -
                  sto_pwr_df[sit][(('b_Elec_'+sit, 'storage_Pump_'+sit),
                                  'invest')])

        # storage capacity
        if abs(urbs_model.cap_sto_c_new[(sit, 'Pump', 'Elec')]() -
               sto_cap_df[sit][(('storage_Pump_'+sit, 'None'),
                               'invest')]) >= threshold:
            print('\t', 'Storage CAP', '\t', 'Diff:',
                  urbs_model.cap_sto_c_new[(sit, 'Pump', 'Elec')]() -
                  sto_cap_df[sit][(('storage_Pump_'+sit, 'None'),
                                  'invest')])

        for i in range(1, len(oemof_model.timeindex)):
            # storage unit charge
            if abs(urbs_model.e_sto_in[(i, sit, 'Pump', 'Elec')]() -
                   sto_df[sit][(('b_Elec_'+sit, 'storage_Pump_'+sit),
                               'flow')][(i-1)]) >= threshold:

                print(i, '\t', 'Storage IN', '\t', 'Diff:',
                      urbs_model.e_sto_in[(i, sit, 'Pump', 'Elec')]() -
                      sto_df[sit][(('b_Elec_'+sit, 'storage_Pump_'+sit),
                                  'flow')][(i-1)])

            # storage unit discharge
            if abs(urbs_model.e_sto_out[(i, sit, 'Pump', 'Elec')]() -
                   sto_df[sit][(('storage_Pump_'+sit, 'b_Elec_'+sit),
                               'flow')][(i-1)]) >= threshold:

                print(i, '\t', 'Storage OUT', '\t', 'Diff:',
                      urbs_model.e_sto_out[(i, sit, 'Pump', 'Elec')]() -
                      sto_df[sit][(('storage_Pump_'+sit, 'b_Elec_'+sit),
                                  'flow')][(i-1)])
            # storage unit content
            if abs(urbs_model.e_sto_con[(i, sit, 'Pump', 'Elec')]() -
                   sto_con_df[sit][(('storage_Pump_'+sit, 'None'),
                                   'capacity')][(i-1)]) >= threshold:

                print(i, '\t', 'Storage CON', '\t', 'Diff:',
                      urbs_model.e_sto_con[(i, sit, 'Pump', 'Elec')]() -
                      sto_con_df[sit][(('storage_Pump_'+sit, 'None'),
                                      'capacity')][(i-1)])

            # plot details
            iterations.append(i)
            urbs_values.append(urbs_model.e_sto_con[(i, sit, 'Pump', 'Elec')]())
            oemof_values.append(sto_con_df[sit][(('storage_Pump_'+sit, 'None'),
                                                'capacity')][(i-1)])

        # plot
        draw_graph(sit, iterations, urbs_values, oemof_values, 'Storage')

    return print('----------------------------------------------------')


def compare_transmission(urbs_model, oemof_model, threshold):
    # restore oemof energysytem results
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

        # get transmission variable values
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
        out = []
        for sit_out in urbs_model.sit:
            if sit_out is not sit:
                try:
                    urbs_model.cap_tra_new[(sit, sit_out, 'hvac', 'Elec')]
                    out.append(sit_out)
                except KeyError:
                    pass

        for sit_out in out:
            if abs(urbs_model.cap_tra_new[(sit, sit_out, 'hvac', 'Elec')]() -
                   tra_cap_df[sit][(('b_Elec_'+sit, 'line_'+sit+'_'+sit_out),
                                    'invest')]) >= threshold:

                print('\t', 'Transmission CAP', '\t', sit+'_'+sit_out, '\t', 'Diff:',
                      urbs_model.cap_tra_new[(sit, sit_out, 'hvac', 'Elec')]() -
                      tra_cap_df[sit][(('b_Elec_'+sit, 'line_'+sit+'_'+sit_out),
                                       'invest')])

            # plot details
            sit_outs.append(sit_out)
            urbs_values[sit_out] = urbs_model.cap_tra_new[(sit, sit_out, 'hvac', 'Elec')]()
            oemof_values[sit_out] = tra_cap_df[sit][(('b_Elec_'+sit, 'line_'+sit+'_'+sit_out),
                                                    'invest')]

        for i in range(1, len(oemof_model.timeindex)):
            for sit_out in out:
                # transmission in
                if abs(urbs_model.e_tra_in[(i, sit, sit_out, 'hvac', 'Elec')]() -
                       tra_df[sit][(('b_Elec_'+sit, 'line_'+sit+'_'+sit_out),
                                   'flow')][(i-1)]) >= threshold:

                    print(i, '\t', 'Transmission IN', '\t', sit+'_'+sit_out, '\t', 'Diff:',
                          urbs_model.e_tra_in[(i, sit, sit_out, 'hvac', 'Elec')]() -
                          tra_df[sit][(('b_Elec_'+sit, 'line_'+sit+'_'+sit_out),
                                      'flow')][(i-1)])

                # transmission out
                if abs(urbs_model.e_tra_out[(i, sit_out, sit, 'hvac', 'Elec')]() -
                       tra_df[sit][(('line_'+sit_out+'_'+sit, 'b_Elec_'+sit),
                                   'flow')][(i-1)]) >= threshold:

                    print(i, '\t', 'Transmission OUT', '\t', sit+'_'+sit_out, '\t', 'Diff:',
                          urbs_model.e_tra_out[(i, sit_out, sit, 'hvac', 'Elec')]() -
                          tra_df[sit][(('line_'+sit_out+'_'+sit, 'b_Elec_'+sit),
                                      'flow')][(i-1)])

        # plot
        draw_graph(sit, sit_outs, urbs_values, oemof_values, 'Transmission')

    return print('----------------------------------------------------')


def compare_process(urbs_model, oemof_model, threshold):
    # restore oemof energysytem results
    oemof_model = solph.EnergySystem()
    oemof_model.restore(dpath=None, filename=None)

    # non-f process dictionaries
    pro_df = {}
    pro_cap_df = {}

    # f process dictionaries
    pro_r_df = {}
    pro_cap_r_df = {}

    for sit in urbs_model.sit:
        # nf process list
        p1 = urbs_model.commodity.index.get_level_values('Site') == sit
        p2 = urbs_model.commodity.index.get_level_values('Type') == 'Stock'
        pro_list = urbs_model.commodity[p1 & p2].index.remove_unused_levels() \
            .get_level_values('Commodity')

        # f process list
        r1 = urbs_model.commodity.index.get_level_values('Type') == 'SupIm'
        ren_list = urbs_model.commodity[p1 & r1].index.remove_unused_levels() \
            .get_level_values('Commodity')

        # plot init
        iterations = [i for i in range(1, len(oemof_model.timeindex))]
        urbs_values = dict([(key, []) for key in pro_list])
        oemof_values = dict([(key, []) for key in pro_list])

        # get process unit variable values
        results_bel = outputlib.views.node(oemof_model.results['main'],
                                           'b_Elec_'+sit)

        # nf process unit
        pro_df[sit] = results_bel['sequences']
        pro_df[sit] = pro_df[sit].filter(like='pp')

        # f process unit
        pro_r_df[sit] = results_bel['sequences']
        pro_r_df[sit] = pro_r_df[sit].filter(like='rs')

        # f process capacity
        pro_cap_r_df[sit] = results_bel['scalars']
        pro_cap_r_df[sit] = pro_cap_r_df[sit].filter(like='rs')

        print('----------------------------------------------------')
        print('i', '\t', 'Process', sit, '\t', '(urbs - oemof)')

        # get nf process capacity variable values
        for pro in pro_list:
            results_con = outputlib.views.node(oemof_model.results['main'], 'pp_'+pro+'_'+sit)

            # nf process capacity
            pro_cap_df[sit] = results_con['scalars']

            if abs(urbs_model.cap_pro_new[(sit, pro+' plant')]() -
                   pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                   'invest')]) >= threshold:

                print('\t', 'CAP', '\t', pro, '\t', 'Diff:',
                      urbs_model.cap_pro_new[(sit, pro+' plant')]() -
                      pro_cap_df[sit][(('b_'+pro+'_'+sit, 'pp_'+pro+'_'+sit),
                                      'invest')])

            for i in range(1, len(oemof_model.timeindex)):
                # plot details
                urbs_values[pro].append(urbs_model.e_pro_out[(i, sit, pro+' plant', 'Elec')]())
                oemof_values[pro].append(pro_df[sit][(('pp_'+pro+'_'+sit, 'b_Elec_'+sit),
                                                     'flow')][(i-1)])
                # nf process unit
                if abs(urbs_model.e_pro_out[(i, sit, pro+' plant', 'Elec')]() -
                       pro_df[sit][(('pp_'+pro+'_'+sit, 'b_Elec_'+sit),
                                   'flow')][(i-1)]) >= threshold:

                    print(i, '\t', 'UNIT', '\t', pro, '\t', 'Diff:',
                          urbs_model.e_pro_out[(i, sit, pro+' plant', 'Elec')]() -
                          pro_df[sit][(('pp_'+pro+'_'+sit, 'b_Elec_'+sit),
                                       'flow')][(i-1)])

        # plot
        draw_graph(sit, iterations, urbs_values, oemof_values, 'Process (PP)')

        # plot init
        urbs_values = dict([(key, []) for key in ren_list])
        oemof_values = dict([(key, []) for key in ren_list])

        # get f process capacity variable values
        for ren in ren_list:
            # f process capacity
            if abs(urbs_model.cap_pro_new[(sit, ren+' plant')]() -
                   pro_cap_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                     'invest')]) >= threshold:

                print('\t', 'CAP', '\t', ren, '\t', 'Diff:',
                      urbs_model.cap_pro_new[(sit, ren+' plant')]() -
                      pro_cap_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                        'invest')])

            for i in range(1, len(oemof_model.timeindex)):
                # plot details
                urbs_values[ren].append(urbs_model.e_pro_out[(i, sit, ren+' plant', 'Elec')]())
                oemof_values[ren].append(pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                                       'flow')][(i-1)])
                # f process unit
                if abs(urbs_model.e_pro_out[(i, sit, ren+' plant', 'Elec')]() -
                       pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                     'flow')][(i-1)]) >= threshold:

                    print(i, '\t', 'UNIT', '\t', ren, '\t', 'Diff:',
                          urbs_model.e_pro_out[(i, sit, ren+' plant', 'Elec')]() -
                          pro_r_df[sit][(('rs_'+ren+'_'+sit, 'b_Elec_'+sit),
                                        'flow')][(i-1)])

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
        plt.close(fig)

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
        x_ticks = list(map((' to ').__add__, list(u.keys())))
        x_ticks_new = [ticks.replace('-', '-\n') for ticks in x_ticks]
        plt.xticks(i_pos, x_ticks_new, fontsize=6)

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
        plt.close(fig)

    elif 'Process' in name:
        # init
        u = {}
        o = {}

        # create figure
        fig = plt.figure()

        # x-Axis (timesteps)
        i = np.array(i)

        for key in urbs_values:
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
        plt.title(site+' '+name, y=1.02)
        plt.grid(True)
        plt.tight_layout(rect=[0,0,0.72,1])
        plt.legend(bbox_to_anchor=(1.025, 1), loc=2, borderaxespad=0)
        # plt.show()

        # save plot
        fig.savefig(os.path.join(result_dir, 'comp_'+name+'_'+site+'.png'), dpi=300)
        plt.close(fig)


def r_graph(benchmark_data, solver_name):
    # create figure
    fig, ax = plt.subplots()

    # x-Axis (timesteps)
    ts = np.array([1,10,20,30,40,50,60,70,80,90,100,
                   200,300,400,500,600,700,800,900,1000,
                   2190,4380,6570,8760])

    # y-Axis (values)
    r = []
    average = 0
    for i in benchmark_data:
        r.append(benchmark_data[i])
        average += benchmark_data[i]

    average = average / 24

    avg = []
    for i in benchmark_data:
        avg.append(average)

    r_array = np.array(r)
    avg_array = np.array(avg)

    # draw plots
    plt.plot(ts, r_array, label='Parameter r', linestyle='None', marker='x')
    plt.ticklabel_format(axis='y')
    plt.plot(ts, avg_array, label='Avg Parameter r', linestyle='-', marker='None')
    plt.ticklabel_format(axis='y')

    # plot specs
    plt.xlabel('Timesteps [h]')
    plt.ylabel('Parameter r')
    plt.xscale('log')

    log = [1,10,20,50,100,200,500,1000,2190,4380,8760]
    ax.set_xticks(log)
    ax.set_xticklabels(log)

    if solver_name == 'gurobi':
        plt.title('urbs/oemof [Gurobi]')
    elif solver_name == 'glpk':
        plt.title('urbs/oemof [GLPK]')

    plt.grid(True)
    plt.legend()
    plt.show()
    plt.close(fig)


def ratio_graph(benchmark_data):
    # create figure
    fig, ax = plt.subplots()

    # x-Axis (timesteps)
    ts = np.array([1,10,20,30,40,50,60,70,80,90,100,
                   200,300,400,500,600,700,800,900,1000,
                   2190,4380,6570,8760])

    # y-Axis (values)
    ratio_urbs = []
    ratio_oemof = []
    for i in benchmark_data['ratio_urbs']:
        ratio_urbs.append(benchmark_data['ratio_urbs'][i])
        ratio_oemof.append(benchmark_data['ratio_oemof'][i])

    ru_array = np.array(ratio_urbs)
    ro_array = np.array(ratio_oemof)
    ones = np.array([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                     1,1,1,1])



    # draw plots
    plt.plot(ts, ru_array, label='urbs', linestyle='None', marker='x')
    plt.ticklabel_format(axis='y')
    plt.plot(ts, ro_array, label='oemof', linestyle='None', marker='.')
    plt.ticklabel_format(axis='y')
    plt.plot(ts, ones, label='Ratio = 1', linestyle='-', marker='None')
    plt.ticklabel_format(axis='y')

    # plot specs
    plt.xlabel('Timesteps [h]')
    plt.ylabel('Ratio')
    plt.xscale('log')
    plt.title('Gurobi/GLPK')

    log = [1,10,20,50,100,200,500,1000,2190,4380,8760]
    ax.set_xticks(log)
    ax.set_xticklabels(log)

    plt.grid(True)
    plt.legend()
    plt.show()
    plt.close(fig)
