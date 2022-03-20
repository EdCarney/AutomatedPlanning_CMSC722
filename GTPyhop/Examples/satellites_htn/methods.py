################################################################################
# Helper functions that are used in the methods' preconditions.


def getSatsSupportingMode(state, mode: str) -> set[str]:
    supporting_instruments = [x for x in state.supports if state.supports[x] == mode]
    return {state.on_board[x] for x in supporting_instruments}


def getCheapestSatForCollection(state, supporting_sats: set[str], dir: str) -> str:
    sat_costs = {
        sat: state.slew_time[(current_dir, dir)]
        for (sat, current_dir) in state.pointing
        if sat in supporting_sats
    }
    min_cost = min(sat_costs.values())
    sats_with_min_cost = [sat for sat in sat_costs if sat_costs[sat] == min_cost]
    return sats_with_min_cost[0]


################################################################################
# Methods for the task of collecting all desired images


def m_collect_all(state, goal):
    """
    Method to collect all desired images.
    """

    desired_images: dict = goal.have_image

    for direction, mode in desired_images.items():
        if state.have_image.get(direction) == mode:
            continue

        supporting_sats = getSatsSupportingMode(state, mode)
        cheapest_sat = getCheapestSatForCollection(state, supporting_sats, direction)
        return [("collect", cheapest_sat, direction, mode), ("achieve", goal)]


def m_collect_1(state, sat, dir, mode) -> list[tuple] | bool:
    """
    Collect image when satellite not pointing at desired target and
    instrument not already calibrated
    """


def m_calibrate_1(state, int) -> list[tuple] | bool:
    """
    Calibrate
    """
