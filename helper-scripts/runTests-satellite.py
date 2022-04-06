#! /usr/bin/env python3.10

import os, re
from threading import Thread
from subprocess import run, Popen, PIPE
from enum import Enum
from typing import Tuple
from astropy.time import Time
from datetime import datetime

PROJ_DIR = os.environ["PROJ_DIR"]
BENCHMARKS_DIR = os.environ["BENCHMARKS_DIR"]
HTN_PLAN_FOUND = "INFO: plan found"
TIMEOUT = 10


class RunCmd(Thread):
    cmdArr: list[str]
    runDir: str
    timeout: int

    def __init__(self, cmdArr: list[str], runDir: str, timeout: int, stdoutOpt=PIPE):
        Thread.__init__(self)
        self.cmdArr = cmdArr
        self.runDir = runDir
        self.timeout = timeout
        self.stdoutOpt = stdoutOpt

    def run(self):
        self.p = Popen(self.cmdArr, stdout=self.stdoutOpt)
        self.p.wait()

    def Run(self) -> str | bool:
        retVal = False
        oldDir = os.getcwd()

        os.chdir(self.runDir)
        self.start()
        self.join(self.timeout)

        if self.is_alive():
            self.p.terminate()
            self.join()
        elif self.stdoutOpt == PIPE:
            retVal = self.p.communicate()[0].decode()

        os.chdir(oldDir)
        return retVal


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
        print(f"Plan Type: {self.type.value}")
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

    def __extractRunTime(self) -> str:
        runTimeRegex = "FP> runtime = (\d+.\d+)"
        return re.findall(runTimeRegex, self.data, re.M)[-1]

    def __extractNumSteps(self) -> str:
        numStepsRegex = "FP> result = (\[\(.*\)\])"
        result = re.findall(numStepsRegex, self.data, re.M)[-1]

        # get ready for some hacky business
        numLParens = result.count("(")
        numRParens = result.count(")")
        if numLParens == numRParens:
            return str(numLParens)
        else:
            print(
                "ERROR: Number of parenthesis did not match when determining HTN plan length!"
            )
            exit()

    def __extractNumNodesExpanded(self) -> str:
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

    def __extractRunTime(self) -> str:
        runTimeRegex = "\s+(\d+.\d+) seconds total time"
        return re.findall(runTimeRegex, self.data, re.M)[-1]

    def __extractNumSteps(self) -> str:
        numStepsRegex = "\s+(\d+):\s"
        return re.findall(numStepsRegex, self.data, re.M)[-1]

    def __extractNumNodesExpanded(self) -> str:
        numStepsExpandedRegex = "evaluating (\d+) states"
        return str(int(re.findall(numStepsExpandedRegex, self.data, re.M)[-1]) + 1)


def getRandSeed() -> int:
    time = Time(datetime.utcnow().isoformat())
    time.format = "gps"
    randseed = int(time.value * 10 ** 6)
    return randseed


def runCmd(
    subProcessArr: list[str], runDir: str, stdOpt=PIPE, timeout: int = -1
) -> str | None:
    oldDir = os.getcwd()
    os.chdir(runDir)
    ret = run(subProcessArr, stdout=stdOpt)
    os.chdir(oldDir)

    # we only have a value to return when using PIPE
    if stdOpt == PIPE:
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
        RunCmd(
            subProcessArr, PROJ_DIR + "/satellite-generator", TIMEOUT, stdoutOpt=f
        ).Run()

    os.replace(
        PROJ_DIR + f"/helper-scripts/{fileName}",
        BENCHMARKS_DIR + f"/satellite/{fileName}",
    )

    return fileName


def runHtnPlanner(fileName: str, probSize: int) -> str:
    subProcessArr = [
        "./Examples/problem_ingestor/problem_ingestor.py",
        "satellite",
        BENCHMARKS_DIR + "/satellite/domain.pddl",
        BENCHMARKS_DIR + f"/satellite/{fileName}",
    ]
    return RunCmd(subProcessArr, PROJ_DIR + "/gt-pyhop", TIMEOUT * probSize).Run()


def runDomIndPlanner(fileName: str, probSize: int) -> str:
    subProcessArr = [
        "./ff",
        "-o",
        BENCHMARKS_DIR + "/satellite/domain.pddl",
        "-f",
        BENCHMARKS_DIR + f"/satellite/{fileName}",
    ]

    return RunCmd(subProcessArr, PROJ_DIR + "/metric-ff", TIMEOUT * probSize).Run()


def generatePlanData(probSizeArr: list[int], numProbsPerSize: int) -> list[PlanData]:
    plans: list[PlanData] = []

    for probSize in probSizeArr:
        successCount = 0
        while successCount < numProbsPerSize:
            fileName = generateProblemFile(probSize, successCount)
            htnResult = runHtnPlanner(fileName, probSize)
            domIndResult = runDomIndPlanner(fileName, probSize)
            if not htnResult or not domIndResult or htnResult.find(HTN_PLAN_FOUND) < 0:
                print(
                    f"WARN: Failed attempt {successCount + 1} for count {probSize}, retrying..."
                )
            else:
                plans.append(HtnPlanData(htnResult, probSize))
                plans.append(DomainIndPlanData(domIndResult, probSize))
                successCount += 1
                print(f"Generated plan {successCount} for problem size {probSize}")

    return plans


def writePlansToFile(plans: list[PlanData]) -> None:
    timestamp = str(datetime.utcnow().timestamp()).replace(".", "")
    fileName = f"plan_data_{timestamp}.csv"
    with open(fileName, "w") as f:
        f.write("Problem Size,Run Time (s),Num Steps,Expanded Nodes,Plan Type\n")
        for plan in plans:
            f.write(
                f"{plan.problemSize},{plan.runTime},{plan.numSteps},{plan.numNodesExpanded},{plan.type.value}\n"
            )


def main():
    numObsArr = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70]
    numProbsPerSize = 10
    planData = generatePlanData(numObsArr, numProbsPerSize)
    writePlansToFile(planData)


if __name__ == "__main__":
    main()
