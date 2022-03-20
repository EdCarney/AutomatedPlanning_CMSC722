#! python3

import gtpyhop
import sys

domain_name = __name__
domain = gtpyhop.Domain(domain_name)

# states and rigid relations

state0 = gtpyhop.State("s0")
state0.calibrated = {}
state0.cal_target = {}
state0.power_on = {}
state0.power_avail = {}
state0.fuel = {}
state0.fuel_used = 0
state0.data_capacity = {}
state0.data = {}
state0.data_stored = 0
state0.have_image = {}
state0.pointing = {}
state0.on_board = {}
state0.supports = {}
