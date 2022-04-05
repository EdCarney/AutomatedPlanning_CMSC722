#! /usr/bin/env python3.10

import subprocess, os
from astropy.time import Time
from datetime import datetime

PROJ_DIR = os.environ["PROJ_DIR"]
BENCHMARKS_DIR = os.environ["BENCHMARKS_DIR"]
HTN_PLAN_FOUND = "INFO: plan found"


class PlanData:
    problemSize: int
    runTime: float
    numSteps: int
    numNodesExpanded: int


class HtnPlanData(PlanData):
    def __init__(self, data: str) -> None:
        return


class DomainIndPlanData(PlanData):
    def __init__(self, data: str) -> None:
        return


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
    numProbsPerSize = 10

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
                print(result)
                successCount += 1


if __name__ == "__main__":
    main()
