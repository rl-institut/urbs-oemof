# Comparison of urbs & oemof

This script allows the user to get some understanding of the differences between the two energy modelling frameworks; urbs & oemof.

# Frameworks

urbs: https://github.com/tum-ens/urbs

oemof: https://github.com/oemof

# Input Data

mimo.xlsx (https://github.com/rl-institut/urbs-oemof/blob/master/mimo.xlsx) is a simpler version of the example input data (https://github.com/tum-ens/urbs/blob/master/mimo-example.xlsx) of urbs.

# Required Packages

oemof, os, sys, logging, pandas, numpy, networkx, matplotlib, datetime, pprint, getpass, oedialect, sqlalchemy, geoalchemy2

# How to Use

* After installing the above mentioned required packages, run `mimo.py` via `python3 mimo.py`.
* The script should output the differences as text on cmd.
* Under `result` folder, generated plots can be found.
