#! /usr/bin/env python3.10

import multiprocessing
import os, re, time
from threading import Thread
from multiprocessing import Lock, Queue, Pool
from subprocess import Popen, PIPE
from enum import Enum
from typing import Tuple
from astropy.time import Time
from datetime import datetime

PROJ_DIR = os.environ["PROJ_DIR"]
BENCHMARKS_DIR = os.environ["BENCHMARKS_DIR"]
HTN_PLAN_FOUND = "INFO: plan found"
POOL_SIZE = 10
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
            printError(
                "Number of parentheses did not match when determining HTN plan length!"
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


def printWarn(msg: str) -> None:
    print(f"{datetime.utcnow().isoformat()} - WARN: {msg}")


def printInfo(msg: str) -> None:
    print(f"{datetime.utcnow().isoformat()} - INFO: {msg}")


def printError(msg: str) -> None:
    print(f"{datetime.utcnow().isoformat()} - INFO: {msg}")


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


def generatePlanData(probSize: int, successCount: int, q: Queue) -> str:
    success = False

    while not success:
        fileName = generateProblemFile(probSize, successCount)
        htnResult = runHtnPlanner(fileName, probSize)
        domIndResult = runDomIndPlanner(fileName, probSize)
        if not htnResult or htnResult.find(HTN_PLAN_FOUND) < 0:
            printWarn(
                f"Failed to find HTN solution for plan {successCount + 1} problem size {probSize}, retrying..."
            )
        elif not domIndResult:
            printWarn(
                f"Failed to find DI solution for plan {successCount + 1} problem size {probSize}, retrying..."
            )
        else:
            success = True

    htnPlan = HtnPlanData(htnResult, probSize)
    domIndPlan = DomainIndPlanData(domIndResult, probSize)

    q.put(htnPlan)
    q.put(domIndPlan)

    printInfo(
        f"Generated plan {successCount} for problem size {probSize} in {htnPlan.runTime} s (HTN) and {domIndPlan.runTime} s (DI)"
    )
    printInfo(
        f"Generated plan {successCount} for problem size {probSize} in {htnPlan.runTime} s (HTN)"
    )


def calcOptimalPoolSize(probSizeArr: list[int], numProbsPerSize: int):
    manager = multiprocessing.Manager()
    planQ: Queue = manager.Queue()
    probTuples = [
        (probSize, probNum, planQ)
        for probSize in probSizeArr
        for probNum in range(numProbsPerSize)
    ]

    poolSizes = [5, 10, 15, 20, 25, 30, 35, 40, 45]
    timesToTest = 5
    multiTimes = []

    for size in poolSizes:
        runningAvg = 0
        for i in range(timesToTest):
            multiStart = time.time()
            with Pool(size) as p:
                p.starmap(generatePlanData, probTuples)
            multiEnd = time.time()
            runningAvg += multiEnd - multiStart

        multiTimes.append((size, runningAvg / timesToTest))

    runningAvg = 0
    for i in range(timesToTest):
        seqStart = time.time()
        for prob in probTuples:
            generatePlanData(prob[0], prob[1], prob[2])
        seqEnd = time.time()
        runningAvg += seqEnd - seqStart
    seqRunTime = runningAvg / timesToTest

    for multiTime in multiTimes:
        percentImpStr = "{:.3f}".format(
            ((seqRunTime - multiTime[1]) / seqRunTime) * 100
        )
        print(f"Pool size {multiTime[0]}: {percentImpStr} % improvement")


def generateData(probSizeArr: list[int], numProbsPerSize: int) -> Queue:
    planQ: Queue[PlanData] = multiprocessing.Manager().Queue()
    probTuples = [
        (probSize, probNum, planQ)
        for probSize in probSizeArr
        for probNum in range(numProbsPerSize)
    ]

    with Pool(POOL_SIZE) as p:
        p.starmap(generatePlanData, probTuples)

    return planQ


def writePlansToFile(plans: Queue) -> None:
    timestamp = str(datetime.utcnow().timestamp()).replace(".", "")
    fileName = f"plan_data_{timestamp}.csv"
    with open(fileName, "w") as f:
        f.write("Problem Size,Run Time (s),Num Steps,Expanded Nodes,Plan Type\n")
        while not plans.empty():
            plan = plans.get()
            f.write(
                f"{plan.problemSize},{plan.runTime},{plan.numSteps},{plan.numNodesExpanded},{plan.type.value}\n"
            )


def main():
    numObsArr = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70]
    numProbsPerSize = 15
    planData = generateData(numObsArr, numProbsPerSize)
    writePlansToFile(planData)


if __name__ == "__main__":
    main()
