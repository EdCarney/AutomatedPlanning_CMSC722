def fuel_required(dir_new, dir_old) -> int:
    return


def data_required(dir, mode) -> int:
    return


def turn_to(state, sat, dir_new, dir_old):
    req_fuel = fuel_required(dir_new, dir_old)
    if not (
        state.pointing[sat] == dir_old
        and dir_new != dir_old
        and state.fuel[sat] >= req_fuel
    ):
        return

    state.pointing[sat] = dir_new
    state.fuel[sat] -= req_fuel
    state.fuel_used += req_fuel


def switch_on(state, int, sat):
    if not (state.on_board[int] == sat and state.power_avail[sat]):
        return

    state.power_on[int] = True
    state.calibrated[int] = False
    state.power_avail[sat] = False


def switch_off(state, int, sat):
    if not (state.on_board[int] == sat and state.power_on[int]):
        return

    state.power_on[int] = False
    state.power_avail[sat] = True


def calibrate(state, sat, int, dir):
    if not (
        state.on_board[int] == sat
        and state.cal_target[int] == dir
        and state.pointing[sat] == dir
        and state.power_on[int]
    ):
        return

    state.calibrated[int] = True


def take_image(state, sat, dir, int, mode):
    req_data = data_required(dir, mode)

    if not (
        state.calibrated[int]
        and state.on_board[int] == sat
        and state.supports[int] == mode
        and state.power_on[int]
        and state.pointing[sat] == dir
        and state.data_capacity[sat] <= req_data
    ):
        return

    state.data_capacity[sat] -= req_data
    state.have_image[dir] = mode
    state.data_stored += req_data