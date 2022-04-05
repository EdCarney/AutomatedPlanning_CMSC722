#! /usr/bin/env python3.10

import subprocess, os, re
from enum import Enum
from astropy.time import Time
from datetime import datetime

PROJ_DIR = os.environ["PROJ_DIR"]
BENCHMARKS_DIR = os.environ["BENCHMARKS_DIR"]
HTN_PLAN_FOUND = "INFO: plan found"


class PlanType(Enum):
    HTN = "htn"
    DOM_IND = "domain_independent"


class PlanData:
    type: PlanType
    problemSize: int
    runTime: float
    numSteps: int
    numNodesExpanded: int
    data: str

    def display(self) -> None:
        print("----- Plan Details -----")
        print(f"Plan Type: {self.type}")
        print(f"Problem Size: {self.problemSize}")
        print(f"Run Time: {self.runTime}")
        print(f"Num Steps: {self.numSteps}")
        print(f"Num Nodes Expanded: {self.numNodesExpanded}")


class HtnPlanData(PlanData):
    def __init__(self, data: str, probSize: int) -> None:
        self.data = data
        self.type = PlanType.HTN
        self.problemSize = probSize
        self.runTime = self.__extractRunTime()
        self.numSteps = self.__extractNumSteps()
        self.numNodesExpanded = self.__extractNumNodesExpanded()

    def __extractRunTime(self):
        runTimeRegex = "FP> runtime = (\d+.\d+)"
        return re.findall(runTimeRegex, self.data, re.M)[-1]

    def __extractNumSteps(self):
        numStepsRegex = "FP> result = (\[\(.*\)\])"
        result = re.findall(numStepsRegex, self.data, re.M)[-1]

        # get ready for some hacky business
        numLParens = result.count("(")
        numRParens = result.count(")")
        if numLParens == numRParens:
            return numLParens
        else:
            print(
                "ERROR: Number of parenthesis did not match when determining HTN plan length!"
            )
            exit()

    def __extractNumNodesExpanded(self):
        numStepsExpandedRegex = "depth (\d+) todo_list"
        return re.findall(numStepsExpandedRegex, self.data, re.M)[-1]


class DomainIndPlanData(PlanData):
    def __init__(self, data: str, probSize: int) -> None:
        self.data = data
        self.type = PlanType.DOM_IND
        self.problemSize = probSize
        self.runTime = self.__extractRunTime()
        self.numSteps = self.__extractNumSteps()
        self.numNodesExpanded = self.__extractNumNodesExpanded()

    def __extractRunTime(self):
        runTimeRegex = "\s+(\d+.\d+) seconds total time"
        return re.findall(runTimeRegex, self.data, re.M)[-1]

    def __extractNumSteps(self):
        numStepsRegex = "\s+(\d+):\s"
        return re.findall(numStepsRegex, self.data, re.M)[-1]

    def __extractNumNodesExpanded(self):
        numStepsExpandedRegex = "evaluating (\d+) states"
        return re.findall(numStepsExpandedRegex, self.data, re.M)[-1] + 1


def getRandSeed() -> int:
    time = Time(datetime.utcnow().isoformat())
    time.format = "gps"
    randseed = int(time.value * 10 ** 6)
    return randseed


def runCmdInDir(
    subProcessArr: list[str], runDir: str, stdOpt=subprocess.PIPE
) -> str | None:
    oldDir = os.getcwd()
    os.chdir(runDir)
    ret = subprocess.run(subProcessArr, stdout=stdOpt)
    os.chdir(oldDir)

    # we only have a value to return when using PIPE
    if stdOpt == subprocess.PIPE:
        return ret.stdout.decode()


def generateProblemFile(numObs: int, successCount: int) -> str:
    randseed = getRandSeed()
    numSats = 3
    numMaxIntsPerSat = 2
    numModes = 2
    numTargets = 20

    subProcessArr = [
        "./satgen",
        "-c",
        "-n",
        "-u",
        str(randseed),
        str(numSats),
        str(numMaxIntsPerSat),
        str(numModes),
        str(numTargets),
        str(numObs),
    ]

    fileName = f"test.{numObs}.{successCount}.pddl"

    with open(fileName, "w") as f:
        runCmdInDir(subProcessArr, PROJ_DIR + "/satellite-generator", stdOpt=f)

    os.replace(
        PROJ_DIR + f"/helper-scripts/{fileName}",
        BENCHMARKS_DIR + f"/satellite/{fileName}",
    )

    return fileName


def runHtnPlanner(fileName: str) -> str:
    subProcessArr = [
        "./Examples/problem_ingestor/problem_ingestor.py",
        "satellite",
        BENCHMARKS_DIR + "/satellite/domain.pddl",
        BENCHMARKS_DIR + f"/satellite/{fileName}",
    ]
    return runCmdInDir(subProcessArr, PROJ_DIR + "/gt-pyhop")


def runDomIndPlanner(fileName: str) -> str:
    subProcessArr = [
        "./ff",
        "-o",
        BENCHMARKS_DIR + "/satellite/domain.pddl",
        "-f",
        BENCHMARKS_DIR + f"/satellite/{fileName}",
    ]

    return runCmdInDir(subProcessArr, PROJ_DIR + "/metric-ff")


def main():
    numObsArr = [20, 25]
    numProbsPerSize = 1

    for numObs in numObsArr:
        successCount = 0
        while successCount < numProbsPerSize:
            fileName = generateProblemFile(numObs, successCount)
            result = runHtnPlanner(fileName)
            if result.find(HTN_PLAN_FOUND) < 0:
                print(
                    f"WARN: Failed attempt {successCount + 1} for count {numObs}, retrying..."
                )
            else:
                plan = HtnPlanData(result, numObs)
                plan.display()
                successCount += 1


if __name__ == "__main__":
    main()
