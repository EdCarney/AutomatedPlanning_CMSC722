#! python3

import gtpyhop
import sys

domain_name = __name__
domain = gtpyhop.Domain(domain_name)

state0 = gtpyhop.State("s_0")

# states
state0.calibrated = {}
state0.data_stored = 0
state0.fuel = {"satellite0": 146}
state0.fuel_used = 0
state0.have_image = {}
state0.pointing = {"satellite0": "GroundStation0"}
state0.power_avail = {"satellite0": True}
state0.power_on = {}

# rigid relations
state0.cal_target = {"instrument0": "GroundStation0"}
state0.direction = {"Star1": True, "GroundStation0": True}
state0.data = {("Star1", "infrared0"): 123}
state0.data_capacity = {"satellite0": 1000}
state0.instrument = {"instrument0": True}
state0.mode = {"infrared0": True}
state0.on_board = {"instrument0": "satellite0"}
state0.satellite = {"satellite0": True}
state0.slew_time = {
    ("Star1", "GroundStation0"): 30.11,
    ("GroundStation0", "Star1"): 30.11,
}
state0.supports = {"instrument0": "infrared0"}

# goal
goal = gtpyhop.Multigoal("s_g")
goal.have_image = {"Star1": "infrared0"}
