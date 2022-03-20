import gtpyhop

################################################################################
# Helper functions that are used in the methods' preconditions.


def getFuelCost(state, cur_dir: str, req_dir: str) -> float:
    return state.slew_time.get((cur_dir, req_dir), 0)


def instrumentReadyToCollect(state, ins) -> bool:
    return state.calibrated.get(ins) and state.power_on.get(ins)


def satHasResources(state, sat, dir, mode) -> bool:
    return satHasSufficientFuel(state, sat, dir) and satHasSufficientData(
        state, sat, dir, mode
    )


def satHasSufficientFuel(state, sat, target_dir) -> bool:
    cur_dir = state.pointing[sat]
    fuel_cost = getFuelCost(state, cur_dir, target_dir)
    return state.fuel[sat] >= fuel_cost or cur_dir == target_dir


def satHasSufficientData(state, sat, dir, mode):
    req_data = state.data[(dir, mode)]
    return state.data_capacity[sat] >= req_data


def getInstrumentsSupportingMode(state, mode: str) -> set[str]:
    return [ins for ins in state.supports if state.supports[ins] == mode]


def getSatsSupportingInstruments(state, supporting_instruments: set[str]) -> set[str]:
    return {state.on_board[x] for x in supporting_instruments}


def getActiveInstrumentForSat(state, sat) -> list[str]:
    active_int = [int for int in state.power_on if state.on_board[int] == sat]
    return active_int[0] if any(active_int) else None


def getStatus(state, sat, dir, ins, mode):
    cal_dir = state.cal_target[ins]

    if instrumentReadyToCollect(state, ins) and satHasResources(state, sat, dir, mode):
        return "collect-target"
    elif satHasResources(state, sat, dir, mode):
        return "calibrate-instrument"
    else:
        return "insufficient-resources"


def sortSatInsByCost(state, sats: set[str], ints: set[str], dir: str) -> list[tuple]:
    """
    Returns a sorted list of satellite-instrument pairs to point to the provided direction.
    The list is sorted in ascending order by the total fuel cost. If an instrument is
    calibrated and powered on, the cost is the fuel to slew to the desired direction.
    Otherwise, the cost is the fuel to slew from the current direction to the calibration
    target plus the fuel to slew from the calibration target to the desired direction.
    """

    costs = {}

    for sat in sats:
        cur_dir = state.pointing[sat]
        sat_ints = [int for int in ints if state.on_board[int] == sat]
        for sat_int in sat_ints:
            if state.calibrated.get(sat_int) and state.power_on.get(sat_int):
                cost = getFuelCost(state, cur_dir, dir)
            else:
                cal_dir = state.cal_target[sat_int]
                cost = getFuelCost(state, cur_dir, cal_dir) + getFuelCost(
                    state, cal_dir, dir
                )
            costs[(sat, sat_int)] = cost

    return [sat for (sat, _) in sorted(costs.items(), key=lambda x: x[1])]


################################################################################
# Methods for the task of collecting all desired images


def m_collect_all(state, goal):
    """
    Method to collect all desired images.
    """

    desired_images: dict = goal.have_image

    for dir, mode in desired_images.items():
        if state.have_image.get(dir) == mode:
            continue

        supporting_ins = getInstrumentsSupportingMode(state, mode)
        supporting_sats = getSatsSupportingInstruments(state, supporting_ins)
        sat_ins_cost_sorted = sortSatInsByCost(
            state, supporting_sats, supporting_ins, dir
        )

        for (sat, ins) in sat_ins_cost_sorted:
            status = getStatus(state, sat, dir, ins, mode)

            if status == "collect-target":
                return [
                    ("collect", sat, dir, ins, mode),
                    ("achieve", goal),
                ]
            elif status == "calibrate-instrument":
                return [
                    ("calibrate_instrument", sat, ins),
                    ("achieve", goal),
                ]

    return []


def m_collect_1(state, sat, dir, ins, mode) -> list[tuple] | bool:
    """
    Collect image when satellite instrument is not yet calibrated.
    """
    if not state.calibrated.get(ins):
        return [("calibrate_instrument", sat, ins), ("collect", sat, dir, ins, mode)]

    return False


def m_collect_2(state, sat, dir, ins, mode) -> list[tuple] | bool:
    """
    Collect image when satellite not pointing at desired target and
    instrument is already calibrated. We do not want to turn to target
    direction if instrument still needs to be calibrated at calibration
    target.
    """
    cur_dir = state.pointing[sat]
    if cur_dir != dir:
        return [("turn_to", sat, cur_dir, dir), ("collect", sat, dir, ins, mode)]

    return False


def m_collect_3(state, sat, dir, ins, mode) -> list[tuple] | bool:
    cur_dir = state.pointing[sat]
    if state.calibrated.get(ins) and cur_dir == dir:
        return [("take_image", sat, dir, ins, mode)]

    return False


def m_calibrate_instrument_1(state, sat, ins) -> list[tuple] | bool:
    """
    Calibrate instrument when satellite not already pointed towards
    calibration target.
    """
    cal_dir = state.cal_target[ins]
    cur_dir = state.pointing[sat]
    if cur_dir != cal_dir:
        return [("turn_to", sat, cur_dir, cal_dir), ("calibrate_instrument", sat, ins)]

    return False


def m_calibrate_instrument_2(state, sat, ins) -> list[tuple] | bool:
    """
    Calibrate instrument when satellite does not have power available.
    """
    if not state.power_avail[sat]:
        active_ins = getActiveInstrumentForSat(state, sat)
        return [("switch_off", active_ins, sat), ("calibrate_instrument", sat, ins)]


def m_calibrate_instrument_3(state, sat, ins) -> list[tuple] | bool:
    """
    Calibrate instrument when satellite is pointed towards calibration
    target and the satellite has available power.
    """
    cal_dir = state.cal_target[ins]
    cur_dir = state.pointing[sat]
    if cur_dir == cal_dir and state.power_avail[sat]:
        return [("switch_on", ins, sat), ("calibrate", sat, ins, cal_dir)]

    return False
