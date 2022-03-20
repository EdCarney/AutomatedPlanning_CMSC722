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


class Problem:
    domain: str
    domainFile: str
    problemFile: str
    domainProblem: DomainProblem

    def __init__(self, domain: str, domainFile: str, problemFile: str) -> None:
        self.domain = domain
        self.domainFile = domainFile
        self.problemFile = problemFile
        self.domainProblem = DomainProblem(self.domainFile, self.problemFile)

    def isSatelliteDomain(self) -> bool:
        return self.domain.lower() == "satellite"

    def isBlocksDomain(self) -> bool:
        return self.domain.lower() == "blocks"


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


def generateGoalState(problem: Problem) -> gtpyhop.Multigoal:
    goalAtoms = problem.domainProblem.goals()
    state = gtpyhop.Multigoal("state_g")
    return generateState(problem, goalAtoms, state)


def generateInitialState(problem: Problem) -> gtpyhop.State:
    initialAtoms = problem.domainProblem.initialstate()
    state = gtpyhop.State("state_0")
    return generateState(problem, initialAtoms, state)


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
    return


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
