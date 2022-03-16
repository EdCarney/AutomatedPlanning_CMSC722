#! python3

import gtpyhop
import sys

domain_name = __name__
domain = gtpyhop.Domain(domain_name)

# states and rigid relations

state0 = gtpyhop.State("s0")
