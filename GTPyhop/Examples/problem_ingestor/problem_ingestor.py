#! /usr/bin/env python3

from enum import Enum
import gtpyhop
from pddlpy import DomainProblem
from pddlpy.pddl import Atom
import sys


class BlocksPredicate(Enum):
    ON = "on"
    ONTABLE = "ontable"
    CLEAR = "clear"
    HANDEMPTY = "handempty"


class SatellitePredicate(Enum):
    CALIBRATED = "calibrated"
    CALIBRATION_TARGET = "calibration_target"
    DIRECTION = "direction"
    HAVE_IMAGE = "have_image"
    INSTRUMENT = "instrument"
    MODE = "mode"
    ON_BOARD = "on_board"
    POINTING = "pointing"
    POWER_AVAIL = "power_avail"
    POWER_ON = "power_on"
    SATELLITE = "satellite"
    SUPPORTS = "supports"


class SatelliteFunctions(Enum):
    DATA_CAPACITY = "data_capacity"
    DATA = "data"
    SLEW_TIME = "slew_time"
    DATA_STORED = "data-stored"
    FUEL = "fuel"
    FUEL_USED = "fuel-used"


class Problem:
    domain: str
    goalAtoms: set[Atom] | list[Atom]
    initialAtoms: set[Atom] | list[Atom]

    __INIT_START: str = "(:init"
    __INIT_END: str = ")"
    __GOAL_START: str = "(:goal (and"
    __GOAL_END: str = "))"

    def __init__(self, domain: str, domainFile: str, problemFile: str) -> None:
        self.domain = domain
        if self.isBlocksDomain():
            domainProblem = DomainProblem(domainFile, problemFile)
            self.goalAtoms = domainProblem.goals()
            self.initialAtoms = domainProblem.initialstate()
        elif self.isSatelliteDomain():
            self.goalAtoms = self.__generateGoalSatAtoms(problemFile)
            self.initialAtoms = self.__generateInitialSatAtoms(problemFile)

    def isSatelliteDomain(self) -> bool:
        return self.domain.lower() == "satellite"

    def isBlocksDomain(self) -> bool:
        return self.domain.lower() == "blocks"

    def __generateGoalSatAtoms(self, problemFile: str) -> list[Atom]:
        with open(problemFile) as f:
            lines = f.readlines()

        return self.__extractPredicates(lines, self.__GOAL_START, self.__GOAL_END)

    def __generateInitialSatAtoms(self, problemFile: str) -> list[Atom]:
        with open(problemFile) as f:
            lines = f.readlines()

        return self.__extractPredicates(lines, self.__INIT_START, self.__INIT_END)

    def __extractPredicates(self, lines: list[str], start: str, end: str) -> list[Atom]:
        atoms = []
        index = 0
        while lines[index].strip() != start:
            index += 1

        index += 1

        while lines[index].strip() != end:
            line = lines[index]
            predicate = (
                line.replace("(", "")
                .replace(")", "")
                .replace("=", "")
                .strip()
                .split(" ")
            )
            atoms.append(Atom(predicate))
            index += 1

        return atoms


def runPlanner(problem: Problem) -> None:
    initializeForDomain(problem)
    state_0 = generateInitialState(problem)
    state_g = generateGoalState(problem)
    gtpyhop.find_plan(state_0, [("achieve", state_g)])


def initializeForDomain(problem: Problem) -> None:
    gtpyhop.current_domain = gtpyhop.Domain(problem.domain)

    if problem.isBlocksDomain():
        from Examples.problem_ingestor.blocks_htn import actions
        from Examples.problem_ingestor.blocks_htn import methods

        gtpyhop.declare_actions(
            actions.pickup, actions.unstack, actions.putdown, actions.stack
        )
        gtpyhop.declare_task_methods("achieve", methods.m_moveblocks)
        gtpyhop.declare_task_methods("take", methods.m_take)
        gtpyhop.declare_task_methods("put", methods.m_put)

    elif problem.isSatelliteDomain():
        from Examples.problem_ingestor.satellites_htn import actions
        from Examples.problem_ingestor.satellites_htn import methods

        gtpyhop.declare_actions(
            actions.turn_to,
            actions.switch_on,
            actions.switch_off,
            actions.calibrate,
            actions.take_image,
        )

        gtpyhop.declare_task_methods("achieve", methods.m_collect_all)
        gtpyhop.declare_task_methods(
            "collect", methods.m_collect_1, methods.m_collect_2, methods.m_collect_3
        )
        gtpyhop.declare_task_methods(
            "calibrate_instrument",
            methods.m_calibrate_instrument_1,
            methods.m_calibrate_instrument_2,
            methods.m_calibrate_instrument_3,
        )


def generateGoalState(problem: Problem) -> gtpyhop.Multigoal:
    state = gtpyhop.Multigoal("state_g")
    return generateState(problem, problem.goalAtoms, state)


def generateInitialState(problem: Problem) -> gtpyhop.State:
    state = gtpyhop.State("state_0")
    return generateState(problem, problem.initialAtoms, state)


def generateState(
    problem: Problem,
    atoms: (set[Atom] | list[Atom]),
    state: (gtpyhop.State | gtpyhop.Multigoal),
) -> (gtpyhop.State | gtpyhop.Multigoal):
    if problem.isSatelliteDomain():
        return generateSatelliteState(atoms, state)
    elif problem.isBlocksDomain():
        return generateBlocksState(atoms, state)

    return


def generateSatelliteState(
    atoms: (set[Atom] | list[Atom]), state: (gtpyhop.State | gtpyhop.Multigoal)
) -> gtpyhop.State:
    state.cal_target = {}
    state.calibrated = {}
    state.data = {}
    state.data_capacity = {}
    state.data_stored = 0
    state.direction = {}
    state.fuel = {}
    state.fuel_used = 0
    state.have_image = {}
    state.instrument = {}
    state.mode = {}
    state.on_board = {}
    state.pointing = {}
    state.power_avail = {}
    state.power_on = {}
    state.satellite = {}
    state.slew_time = {}
    state.supports = {}

    for atom in atoms:
        predicate: list[str] = atom.predicate
        predName = predicate[0]

        # check for predicates
        if predName == SatellitePredicate.CALIBRATED.value:
            state.calibrated[predicate[1]] = True
        elif predName == SatellitePredicate.CALIBRATION_TARGET.value:
            state.cal_target[predicate[1]] = predicate[2]
        elif predName == SatellitePredicate.DIRECTION.value:
            state.direction[predicate[1]] = True
        elif predName == SatellitePredicate.HAVE_IMAGE.value:
            state.have_image[predicate[1]] = predicate[2]
        elif predName == SatellitePredicate.INSTRUMENT.value:
            state.instrument[predicate[1]] = True
        elif predName == SatellitePredicate.MODE.value:
            state.mode[predicate[1]] = True
        elif predName == SatellitePredicate.ON_BOARD.value:
            state.on_board[predicate[1]] = predicate[2]
        elif predName == SatellitePredicate.POINTING.value:
            state.pointing[predicate[1]] = predicate[2]
        elif predName == SatellitePredicate.POWER_AVAIL.value:
            state.power_avail[predicate[1]] = True
        elif predName == SatellitePredicate.POWER_ON.value:
            state.power_on[predicate[1]] = True
        elif predName == SatellitePredicate.SATELLITE.value:
            state.satellite[predicate[1]] = True
        elif predName == SatellitePredicate.SUPPORTS.value:
            state.supports[predicate[1]] = predicate[2]

        # check for functions
        elif predName == SatelliteFunctions.DATA.value:
            state.data[(predicate[1], predicate[2])] = float(predicate[3])
        elif predName == SatelliteFunctions.DATA_CAPACITY.value:
            state.data_capacity[predicate[1]] = float(predicate[2])
        elif predName == SatelliteFunctions.DATA_STORED.value:
            state.data_stored = float(predicate[1])
        elif predName == SatelliteFunctions.FUEL.value:
            state.fuel[predicate[1]] = float(predicate[2])
        elif predName == SatelliteFunctions.FUEL_USED.value:
            state.fuel_used = float(predicate[1])
        elif predName == SatelliteFunctions.SLEW_TIME.value:
            state.slew_time[(predicate[1], predicate[2])] = float(predicate[3])

    state.display()
    return state


def generateBlocksState(
    atoms: (set[Atom] | list[Atom]), state: (gtpyhop.State | gtpyhop.Multigoal)
) -> (gtpyhop.State | gtpyhop.Multigoal):
    state.pos = {}
    state.clear = {}
    state.holding = {}

    for atom in atoms:
        predicate: list[str] = atom.predicate
        predName = predicate[0]
        if predName == BlocksPredicate.CLEAR.value:
            state.clear[predicate[1]] = True
        elif predName == BlocksPredicate.HANDEMPTY.value:
            state.holding["hand"] = False
        elif predName == BlocksPredicate.ON.value:
            state.pos[predicate[1]] = predicate[2]
        elif predName == BlocksPredicate.ONTABLE.value:
            state.pos[predicate[1]] = "table"

    state.display()
    return state


def main():
    if len(sys.argv) != 4:
        print(f"ERROR: Incorrect number of arguments: {len(sys.argv)}")
        return

    domain = sys.argv[1]
    domainFile = sys.argv[2]
    problemFile = sys.argv[3]
    problem = Problem(domain, domainFile, problemFile)

    runPlanner(problem)


if __name__ == "__main__":
    main()
