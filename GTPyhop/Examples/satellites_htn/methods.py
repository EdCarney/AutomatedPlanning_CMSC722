################################################################################
# Helper functions that are used in the methods' preconditions.


def getInstrumentsSupportingMode(state, mode: str) -> set[str]:
    return [ins for ins in state.supports if state.supports[ins] == mode]


def getSatsSupportingInstruments(state, supporting_instruments: set[str]) -> set[str]:
    return {state.on_board[x] for x in supporting_instruments}


def sortSatsByFuelCost(state, supporting_sats: set[str]) -> list[str]:
    sat_costs = {
        sat: state.slew_time[(current_dir, dir)]
        for (sat, current_dir) in state.pointing
        if sat in supporting_sats
    }
    return [sat for (sat, cost) in sorted(sat_costs.items(), key=lambda x: x[1])]


def getStatus(state, sat, dir, ins):
    cur_dir = state.pointing[sat]
    cal_dir = state.cal_target[ins]
    req_target_fuel = state.slew_time[(cur_dir, dir)]
    req_cal_fuel = state.slew_time[(cur_dir, cal_dir)]
    if state.calibrated.get(ins) and (
        state.fuel[sat] >= req_target_fuel or cur_dir == dir
    ):
        return "collect-target"
    elif state.fuel[sat] >= req_cal_fuel or cur_dir == cal_dir:
        return "calibrate-instrument"
    else:
        return "insufficient-fuel"


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
        sats_cost_sorted = sortSatsByFuelCost(state, supporting_sats)

        for sat in sats_cost_sorted:
            sat_ins = [ins for ins in supporting_ins if state.on_board[ins] == sat]
            sat_calibrated_ins = [ins for ins in sat_ins if state.calibrated.get(ins)]

            # prefer to use calibrated instruments when possible to conserve fuel
            ins = sat_calibrated_ins[0] if any(sat_calibrated_ins) else sat_ins[0]

            status = getStatus(state, sat, dir, ins)

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
    if state.calibrated.get(ins) and cur_dir != dir:
        return [("turn_to", sat, cur_dir, dir), ("collect", sat, dir, ins, mode)]

    return False


def m_collect_3(state, sat, dir, ins, mode) -> list[tuple] | bool:
    cur_dir = state.pointing[sat]
    if state.calibrated.get(ins) and cur_dir == dir:
        return [
            ("switch_on", ins, sat),
            ("take_image", sat, dir, ins, mode),
            ("switch_off", ins, sat),
        ]

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
    Calibrate instrument when satellite is pointed towards calibration
    target.
    """
    cal_dir = state.cal_target[ins]
    cur_dir = state.pointing[sat]
    if cur_dir == cal_dir:
        return [
            ("switch_on", ins, sat),
            ("calibrate", sat, ins, cal_dir),
            ("switch_off", ins, sat),
        ]

    return False
