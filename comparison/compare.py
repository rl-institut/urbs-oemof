import pandas as pd
import oemof.solph as solph
import oemof.outputlib as outputlib


def compare_storages(urbs_model, oemof_model):

    # get oemof storage variables
    oemof_model = solph.EnergySystem()
    oemof_model.restore(dpath=None, filename=None)

    # storage dictionaries
    storage_df = {}
    sto_con_df = {}

    for sit in urbs_model.sit:
        # get storage variables for all sites
        results_bel = outputlib.views.node(oemof_model.results['main'], 'b_el_'+sit)
        results_con = outputlib.views.node(oemof_model.results['main'], 'None')

        # charge/discharge
        storage_df[sit] = results_bel['sequences']
        storage_df[sit] = storage_df[sit].filter(like='storage')

        # content
        sto_con_df[sit] = results_con['sequences']
        sto_con_df[sit] = sto_con_df[sit].filter(like=sit)

        print('\n', sit, '\t', '(urbs - oemof)')

        for i in range(1, len(oemof_model.timeindex)):
            # charge storage
            if abs(urbs_model.e_sto_in[(i, sit, 'Pump storage', 'Elec')]() -
                   storage_df[sit][(('b_el_'+sit, 'storage_el_'+sit), 'flow')][(i-1)]) >= 0.1:

                print(i, 'Storage_in_'+sit, 'Diff:',
                      (urbs_model.e_sto_in[(i, sit, 'Pump storage', 'Elec')]() -
                       storage_df[sit][(('b_el_'+sit, 'storage_el_'+sit), 'flow')][(i-1)]))

            # discharge storage
            if abs(urbs_model.e_sto_out[(i, sit, 'Pump storage', 'Elec')]() -
                   storage_df[sit][(('storage_el_'+sit, 'b_el_'+sit), 'flow')][(i-1)]) >= 0.1:

                print(i, 'Storage_out_'+sit, 'Diff:',
                      (urbs_model.e_sto_out[(i, sit, 'Pump storage', 'Elec')]() -
                       storage_df[sit][(('storage_el_'+sit, 'b_el_'+sit), 'flow')][(i-1)]))

            if abs(urbs_model.e_sto_con[(i, sit, 'Pump storage', 'Elec')]() -
                   sto_con_df[sit][(('storage_el_'+sit, 'None'), 'capacity')][(i-1)]) >= 0.1:

                print(i, 'Storage_con_'+sit, 'Diff:',
                      (urbs_model.e_sto_con[(i, sit, 'Pump storage', 'Elec')]() -
                       sto_con_df[sit][(('storage_el_'+sit, 'None'), 'capacity')][(i-1)]))
