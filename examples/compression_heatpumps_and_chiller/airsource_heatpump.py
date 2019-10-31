"""
Example on how to use the 'calc_cops' function to get the
COPs of an exemplary air-source heat pump (ASHP).

We use the ambient air as low temperature heat reservoir.
"""

import os
import oemof.thermal.compression_heatpumps_and_chillers as cmpr_hp_chiller
import oemof.solph as solph
import oemof.outputlib as outputlib
import pandas as pd
import matplotlib.pyplot as plt

solver = 'cbc'
debug = False
number_of_time_steps = 24
periods = number_of_time_steps
solver_verbose = False

date_time_index = pd.date_range('1/1/2012', periods=number_of_time_steps,
                                freq='H')

energysystem = solph.EnergySystem(timeindex=date_time_index)

# Read data file
filename = os.path.join(os.path.dirname(__file__), 'data/ASHP_example.csv')
data = pd.read_csv(filename)

b_el = solph.Bus(label="electricity")

b_heat = solph.Bus(label="heat")

energysystem.add(b_el, b_heat)

energysystem.add(solph.Source(
    label='el_grid',
    outputs={b_el: solph.Flow(variable_costs=10)}))

energysystem.add(solph.Source(
    label='backup_heating',
    outputs={b_heat: solph.Flow(variable_costs=10)}))

energysystem.add(solph.Sink(
    label='demand',
    inputs={b_heat: solph.Flow(actual_value=data['demand_heat'],
                               fixed=True,
                               nominal_value=1)}))

# Pre-Calculate COPs
cops_ASHP = cmpr_hp_chiller.calc_cops(
    t_high=[40],
    t_low=data['ambient_temperature'],
    quality_grade=0.4,
    mode='heat_pump',
    consider_icing=True,
    factor_icing=0.8)

# Air-Source Heat Pump
energysystem.add(solph.Transformer(
    label="ASHP",
    inputs={b_el: solph.Flow()},
    outputs={b_heat: solph.Flow(nominal_value=25, variable_costs=5)},
    conversion_factors={b_heat: cops_ASHP}))

model = solph.Model(energysystem)

model.solve(solver=solver, solve_kwargs={'tee': solver_verbose})

energysystem.results['main'] = outputlib.processing.results(model)
energysystem.results['meta'] = outputlib.processing.meta_results(model)

energysystem.dump(dpath=None, filename=None)

# ****************************************************************************
# ********** PART 2 - Processing the results *********************************
# ****************************************************************************

energysystem = solph.EnergySystem()
energysystem.restore(dpath=None, filename=None)

results = energysystem.results['main']

electricity_bus = outputlib.views.node(results, 'electricity')
heat_bus = outputlib.views.node(results, 'heat')

string_results = outputlib.views.convert_keys_to_strings(
    energysystem.results['main'])
ASHP_output = string_results[
    'ASHP', 'heat']['sequences'].values
demand_h = string_results[
    'heat', 'demand']['sequences'].values
ASHP_input = string_results[
    'electricity', 'ASHP']['sequences'].values

fig2, axs = plt.subplots(3, 1, figsize=(8, 5), sharex=True)
axs[0].plot(ASHP_output, label='heat output')
axs[0].plot(demand_h, linestyle='--', label='heat demand')
axs[1].plot(cops_ASHP, linestyle='-.')
axs[2].plot(data['ambient_temperature'])
axs[0].set_title('Heat Output and Demand')
axs[1].set_title('Coefficient of Performance')
axs[2].set_title('Source Temperature (Ambient)')
axs[0].legend()

axs[0].grid()
axs[1].grid()
axs[2].grid()
axs[0].set_ylabel('Heat flow in kW')
axs[1].set_ylabel('COP')
axs[2].set_ylabel('Temperature in $°$C')
axs[2].set_xlabel('Time in h')
plt.tight_layout()
plt.show()

print('********* Main results *********')
print(electricity_bus['sequences'].sum(axis=0))
print(heat_bus['sequences'].sum(axis=0))

## Display calculated COPs
# print("")
# print("Coefficients of Performance (COP): ", *cops_ASHP, sep='\n')
# print("")