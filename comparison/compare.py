import pandas as pd
import oemof.solph as solph
import oemof.outputlib as outputlib


def compare_storages(urbs_model, oemof_model):

    # get oemof storage variables
    oemof_model = solph.EnergySystem()
    oemof_model.restore(dpath=None, filename=None)

    # storage dictionaries
    sto_df = {}
    sto_con_df = {}

    for sit in urbs_model.sit:
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

        print('----------------------------------------------------')
        print('i', '\t', 'Storage', sit, '\t', '(urbs - oemof)')

        for i in range(1, len(oemof_model.timeindex)):
            # charge storage
            if abs(urbs_model.e_sto_in[(i, sit, 'Pump storage', 'Elec')]() -
                   sto_df[sit][(('b_el_'+sit, 'storage_el_'+sit),
                               'flow')][(i-1)]) >= 0.1:

                print(i, '\t', 'Storage IN', '\t', sit, '\t', 'Diff:',
                      (urbs_model.e_sto_in[(i, sit, 'Pump storage', 'Elec')]() -
                       sto_df[sit][(('b_el_'+sit, 'storage_el_'+sit),
                                   'flow')][(i-1)]))

            # discharge storage
            if abs(urbs_model.e_sto_out[(i, sit, 'Pump storage', 'Elec')]() -
                   sto_df[sit][(('storage_el_'+sit, 'b_el_'+sit),
                               'flow')][(i-1)]) >= 0.1:

                print(i, '\t', 'Storage OUT', '\t', sit, '\t', 'Diff:',
                      (urbs_model.e_sto_out[(i, sit, 'Pump storage', 'Elec')]() -
                       sto_df[sit][(('storage_el_'+sit, 'b_el_'+sit),
                                   'flow')][(i-1)]))
            # content storage
            if abs(urbs_model.e_sto_con[(i, sit, 'Pump storage', 'Elec')]() -
                   sto_con_df[sit][(('storage_el_'+sit, 'None'),
                                   'capacity')][(i-1)]) >= 0.1:

                print(i, '\t', 'Storage CON', '\t', sit, '\t', 'Diff:',
                      (urbs_model.e_sto_con[(i, sit, 'Pump storage', 'Elec')]() -
                       sto_con_df[sit][(('storage_el_'+sit, 'None'),
                                       'capacity')][(i-1)]))
    return print('----------------------------------------------------')


def compare_transmission(urbs_model, oemof_model):

    # get oemof transmission variables
    oemof_model = solph.EnergySystem()
    oemof_model.restore(dpath=None, filename=None)

    # transmission dictionaries
    tra_df = {}
    tra_cap_df = {}

    for sit in urbs_model.sit:
        # get transmission variables for all sites
        results_bel = outputlib.views.node(oemof_model.results['main'],
                                           'b_el_'+sit)

        # transmission in/out
        tra_df[sit] = results_bel['sequences']
        tra_df[sit] = tra_df[sit].filter(like='line')

        # transmission cap
        tra_cap_df[sit] = results_bel['scalars']
        tra_cap_df[sit] = tra_cap_df[sit].filter(like='line')

        print('----------------------------------------------------')
        print('i', '\t', 'Transmission', sit, '\t', '(urbs - oemof)')

        # transmission cap
        out = (sit_out for sit_out in urbs_model.sit if sit_out != sit)
        for sit_out in out:
            try:
                if abs(urbs_model.cap_tra[(sit, sit_out, 'hvac', 'Elec')]() -
                       tra_cap_df[sit][(('b_el_'+sit, 'line_'+sit+'_'+sit_out),
                                       'invest')]) >= 0.1:

                    print('\t', 'Transmission CAP', '\t', sit+'_'+sit_out, '\t' 'Diff:',
                          (urbs_model.cap_tra[(sit, sit_out, 'hvac', 'Elec')]() -
                           tra_cap_df[sit][(('b_el_'+sit, 'line_'+sit+'_'+sit_out),
                                           'invest')]))

            except KeyError:
                if abs(urbs_model.cap_tra[(sit, sit_out, 'hvac', 'Elec')]() -
                       tra_cap_df[sit][(('b_el_'+sit, 'line_'+sit_out+'_'+sit),
                                       'invest')]) >= 0.1:

                    print('\t', 'Transmission CAP', '\t', sit+'_'+sit_out, '\t' 'Diff:',
                          (urbs_model.cap_tra[(sit, sit_out, 'hvac', 'Elec')]() -
                           tra_cap_df[sit][(('b_el_'+sit, 'line_'+sit_out+'_'+sit),
                                           'invest')]))

        for i in range(1, len(oemof_model.timeindex)):
            for sit_out in out:
                # transmission in
                try:
                    if abs(urbs_model.e_tra_in[(i, sit, sit_out, 'hvac', 'Elec')]() -
                           tra_df[sit][(('b_el_'+sit, 'line_'+sit+'_'+sit_out),
                                       'flow')][(i-1)]) >= 0.1:

                        print(i, '\t', 'Transmission IN', '\t', sit+'_'+sit_out, '\t' 'Diff:',
                              (urbs_model.e_tra_in[(i, sit, sit_out, 'hvac', 'Elec')]() -
                               tra_df[sit][(('b_el_'+sit, 'line_'+sit+'_'+sit_out),
                                           'flow')][(i-1)]))

                except KeyError:
                    if abs(urbs_model.e_tra_in[(i, sit, sit_out, 'hvac', 'Elec')]() -
                           tra_df[sit][(('b_el_'+sit, 'line_'+sit_out+'_'+sit),
                                       'flow')][(i-1)]) >= 0.1:

                        print(i, '\t', 'Transmission IN', '\t', sit+'_'+sit_out, '\t' 'Diff:',
                              (urbs_model.e_tra_in[(i, sit, sit_out, 'hvac', 'Elec')]() -
                               tra_df[sit][(('b_el_'+sit, 'line_'+sit_out+'_'+sit),
                                           'flow')][(i-1)]))

                # transmission out
                try:
                    if abs(urbs_model.e_tra_out[(i, sit_out, sit, 'hvac', 'Elec')]() -
                           tra_df[sit][(('line_'+sit+'_'+sit_out, 'b_el_'+sit),
                                       'flow')][(i-1)]) >= 0.1:

                        print(i, '\t', 'Transmission OUT', '\t', sit_out+'_'+sit, '\t' 'Diff:',
                              (urbs_model.e_tra_out[(i, sit_out, sit, 'hvac', 'Elec')]() -
                               tra_df[sit][(('line_'+sit+'_'+sit_out, 'b_el_'+sit),
                                           'flow')][(i-1)]))

                except KeyError:
                    if abs(urbs_model.e_tra_out[(i, sit_out, sit, 'hvac', 'Elec')]() -
                           tra_df[sit][(('line_'+sit_out+'_'+sit, 'b_el_'+sit),
                                       'flow')][(i-1)]) >= 0.1:

                        print(i, '\t', 'Transmission OUT', '\t', sit_out+'_'+sit, '\t' 'Diff:',
                              (urbs_model.e_tra_out[(i, sit_out, sit, 'hvac', 'Elec')]() -
                               tra_df[sit][(('line_'+sit_out+'_'+sit, 'b_el_'+sit),
                                           'flow')][(i-1)]))
    return print('----------------------------------------------------')
