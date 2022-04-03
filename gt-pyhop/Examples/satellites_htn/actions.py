import gtpyhop


def fuel_required(state, dir_new, dir_old) -> int:
    return state.slew_time[(dir_old, dir_new)]


def data_required(state, dir, mode) -> int:
    return state.data[(dir, mode)]


def turn_to(state, sat, dir_old, dir_new):
    req_fuel = fuel_required(state, dir_new, dir_old)
    if not (
        state.pointing[sat] == dir_old
        and dir_new != dir_old
        and state.fuel[sat] >= req_fuel
    ):
        return

    state.pointing[sat] = dir_new
    state.fuel[sat] -= req_fuel
    state.fuel_used += req_fuel
    return state


def switch_on(state, int, sat):
    if not (state.on_board[int] == sat and state.power_avail[sat]):
        return

    state.power_on[int] = True
    state.calibrated[int] = False
    state.power_avail[sat] = False
    return state


def switch_off(state, int, sat):
    if not (state.on_board[int] == sat and state.power_on[int]):
        return

    state.power_on[int] = False
    state.power_avail[sat] = True
    return state


def calibrate(state, sat, int, dir):
    if not (
        state.on_board[int] == sat
        and state.cal_target[int] == dir
        and state.pointing[sat] == dir
        and state.power_on[int]
    ):
        return

    state.calibrated[int] = True
    return state


def take_image(state, sat, dir, int, mode):
    req_data = data_required(state, dir, mode)
    if not (
        state.calibrated[int]
        and state.on_board[int] == sat
        and state.supports[int] == mode
        and state.power_on[int]
        and state.pointing[sat] == dir
        and state.data_capacity[sat] >= req_data
    ):
        return

    state.data_capacity[sat] -= req_data
    state.have_image[dir] = mode
    state.data_stored += req_data
    return state


gtpyhop.declare_actions(turn_to, switch_on, switch_off, calibrate, take_image)
