#! /usr/bin/env python3.10

import multiprocessing
import os, re, time
import sys
import statistics
from threading import Thread
from multiprocessing import Queue, Pool
from subprocess import Popen, PIPE
from enum import Enum
from astropy.time import Time
from datetime import datetime

PROJ_DIR = os.environ["PROJ_DIR"]
BENCHMARKS_DIR = os.environ["BENCHMARKS_DIR"]
HTN_PLAN_FOUND = "INFO: plan found"
USE_MULTITHREADING = True
POOL_SIZE = 20
TIMEOUT = 30
VERBOSITY = 0

global DOMAIN


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
            if "error" in retVal:
                retVal = False

        os.chdir(oldDir)
        return retVal


class DomainType(Enum):
    SATELLITE = "satellite"
    BLOCKS = "blocks"


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

    def tryParse(self, parseFunc) -> str:
        try:
            return parseFunc()
        except:
            if VERBOSITY > 0:
                printError(
                    f"Exception in func {parseFunc.__name__} parsing {self.type.value} Plan {self.problemSize}.{self.successCount} : {self.data}"
                )
            return None


class HtnPlanData(PlanData):
    def __init__(self, data: str, probSize: int, successCount: int) -> None:
        self.data = data
        self.type = PlanType.HTN
        self.problemSize = probSize
        self.successCount = successCount
        self.runTime = super().tryParse(self.__extractRunTime)
        self.numSteps = super().tryParse(self.__extractNumSteps)
        self.numNodesExpanded = super().tryParse(self.__extractNumNodesExpanded)

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
    def __init__(self, data: str, probSize: int, successCount: int) -> None:
        self.data = data
        self.type = PlanType.DOM_IND
        self.problemSize = probSize
        self.successCount = successCount
        self.runTime = super().tryParse(self.__extractRunTime)
        self.numSteps = super().tryParse(self.__extractNumSteps)
        self.numNodesExpanded = super().tryParse(self.__extractNumNodesExpanded)

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
    print(f"{datetime.utcnow().isoformat()} - ERROR: {msg}")


def generateProblemFile(probSize: int, domain: DomainType, successCount: int) -> str:
    if domain == DomainType.SATELLITE:
        return generateSatelliteProblemFile(probSize, successCount)
    elif domain == DomainType.BLOCKS:
        return generateBlocksProblemFile(probSize, successCount)
    else:
        printError("Unknown domain")
        exit()


def generateSatelliteProblemFile(numTargets: int, successCount: int) -> str:
    randseed = getRandSeed()
    numSats = 10
    numMaxIntsPerSat = 5
    numModes = 5
    numObs = 5

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

    fileName = f"test.{numTargets}.{successCount}.pddl"

    with open(fileName, "w") as f:
        RunCmd(
            subProcessArr, f"{PROJ_DIR}/satellite-generator", TIMEOUT, stdoutOpt=f
        ).Run()

    os.replace(
        f"{PROJ_DIR}/helper-scripts/{fileName}",
        f"{BENCHMARKS_DIR}/satellite/{fileName}",
    )

    return fileName


def generateBlocksProblemFile(numBlocks: int, successCount: int) -> str:
    randseed = getRandSeed()

    fileName = f"test.{numBlocks}.{successCount}"
    subProcessArr = ["./bwstates", "-r", str(randseed), "-n", str(numBlocks)]
    with open(fileName, "w") as f:
        RunCmd(subProcessArr, f"{PROJ_DIR}/bwstates-src", TIMEOUT, stdoutOpt=f).Run()

    os.replace(
        f"{PROJ_DIR}/helper-scripts/{fileName}",
        f"{BENCHMARKS_DIR}/blocks/{fileName}",
    )

    subProcessArr = ["./generate-prob-pddl.py", f"{BENCHMARKS_DIR}/blocks/{fileName}"]
    RunCmd(subProcessArr, f"{PROJ_DIR}/helper-scripts", TIMEOUT).Run()

    return f"{fileName}.pddl"


def runHtnPlanner(fileName: str, domain: DomainType) -> str:
    subProcessArr = [
        "./problem_ingestor.py",
        domain.value,
        f"{BENCHMARKS_DIR}/{domain.value}/domain.pddl",
        f"{BENCHMARKS_DIR}/{domain.value}/{fileName}",
    ]

    return RunCmd(
        subProcessArr, f"{PROJ_DIR}/helper-scripts/problem_ingestor", TIMEOUT
    ).Run()


def runDomIndPlanner(fileName: str, domain: DomainType) -> str:
    subProcessArr = [
        "./ff",
        "-o",
        f"{BENCHMARKS_DIR}/{domain.value}/domain.pddl",
        "-f",
        f"{BENCHMARKS_DIR}/{domain.value}/{fileName}",
    ]

    return RunCmd(subProcessArr, f"{PROJ_DIR}/metric-ff", TIMEOUT).Run()


def generatePlanData(
    probSize: int, successCount: int, domain: DomainType, q: Queue
) -> str:
    success = False

    while not success:
        fileName = generateProblemFile(probSize, domain, successCount)
        htnResult = runHtnPlanner(fileName, domain)
        domIndResult = runDomIndPlanner(fileName, domain)
        if not htnResult or htnResult.find(HTN_PLAN_FOUND) < 0:
            printWarn(
                f"Failed to find HTN solution for plan {successCount} problem size {probSize}, retrying..."
            )
        elif not domIndResult:
            printWarn(
                f"Failed to find DI solution for plan {successCount} problem size {probSize}, retrying..."
            )
        else:
            htnPlan = HtnPlanData(htnResult, probSize, successCount)
            domIndPlan = DomainIndPlanData(domIndResult, probSize, successCount)
            if htnPlan.runTime == None or domIndPlan.runTime == None:
                printWarn(
                    f"Failed parsing for plan {successCount} problem size {probSize}, retrying..."
                )
            else:
                success = True

    q.put(htnPlan)
    q.put(domIndPlan)

    printInfo(
        f"Generated plan {successCount} for problem size {probSize} in {htnPlan.runTime} s (HTN) and {domIndPlan.runTime} s (DI)"
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
        (probSize, probNum, DOMAIN, planQ)
        for probSize in probSizeArr
        for probNum in range(numProbsPerSize)
    ]

    if USE_MULTITHREADING:
        with Pool(POOL_SIZE) as p:
            p.starmap(generatePlanData, probTuples)
    else:
        for (probSize, probNum, domain, planQ) in probTuples:
            generatePlanData(probSize, probNum, domain, planQ)

    return planQ


def writePlansToFile(plans: Queue) -> None:
    timestamp = str(datetime.utcnow().timestamp()).replace(".", "")
    metricFileName = f"{DOMAIN.value}_metrics_{timestamp}.csv"
    planFileName = f"{DOMAIN.value}_plan_data_{timestamp}.csv"

    planDict: dict[str : dict[int:PlanData]] = {
        PlanType.HTN.value: {},
        PlanType.DOM_IND.value: {},
    }

    while not plans.empty():
        plan = plans.get()
        if plan.problemSize in planDict[plan.type.value].keys():
            planDict[plan.type.value][plan.problemSize].append(plan)
        else:
            planDict[plan.type.value][plan.problemSize] = [plan]

    with open(metricFileName, "w") as f:
        f.write(
            "Problem Size,Run Time Avg (s),Run Time StdDev (s),Num Steps Avg,Num Steps StdDev,Expanded Nodes Avg,Expanded Nodes StdDev,Plan Type\n"
        )

        for plannerType, plannerPlanDict in planDict.items():
            for probSize, planList in plannerPlanDict.items():
                runTimeAvg = statistics.mean([float(plan.runTime) for plan in planList])
                runTimeStdDev = statistics.stdev(
                    [float(plan.runTime) for plan in planList]
                )
                numStepsAvg = statistics.mean(
                    [float(plan.numSteps) for plan in planList]
                )
                numStepsStdDev = statistics.stdev(
                    [float(plan.numSteps) for plan in planList]
                )
                numNodesExpandedAvg = statistics.mean(
                    [float(plan.numNodesExpanded) for plan in planList]
                )
                numNodesExpandedStdDev = statistics.stdev(
                    [float(plan.numNodesExpanded) for plan in planList]
                )
                f.write(
                    f"{probSize},{runTimeAvg},{runTimeStdDev},{numStepsAvg},{numStepsStdDev},{numNodesExpandedAvg},{numNodesExpandedStdDev},{plannerType}\n"
                )

    with open(planFileName, "w") as f:
        f.write("Problem Size,Run Time (s),Num Steps,Expanded Nodes,Plan Type\n")

        for plannerType, plannerPlanDict in planDict.items():
            for probSize, planList in plannerPlanDict.items():
                for plan in planList:
                    f.write(
                        f"{plan.problemSize},{plan.runTime},{plan.numSteps},{plan.numNodesExpanded},{plan.type.value}\n"
                    )


def main():
    numTargetsArr = [
        5,
        10,
        15,
        20,
        25,
        30,
        35,
        40,
        45,
        50,
        55,
        60,
        65,
        70,
        75,
        80,
        85,
        90,
    ]
    numBlocksArr = [
        5,
        10,
        15,
        20,
        25,
        30,
        35,
        40,
        45,
        50,
        55,
        60,
        65,
        70,
        75,
        80,
        85,
    ]
    numProbsPerSize = 15

    if DOMAIN == DomainType.SATELLITE:
        probSizeArr = numTargetsArr
    elif DOMAIN == DomainType.BLOCKS:
        probSizeArr = numBlocksArr

    planData = generateData(probSizeArr, numProbsPerSize)
    writePlansToFile(planData)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1].upper() not in ("SATELLITE", "BLOCKS"):
        printError("Please specify domain when calling script (SATELLITE or BLOCKS)")
    else:
        DOMAIN = DomainType(sys.argv[1].lower())
        main()
