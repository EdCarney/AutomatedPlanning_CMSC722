#! /usr/bin/env python3.10

import subprocess, os
from astropy.time import Time
from datetime import datetime

PROJ_DIR = os.environ["PROJ_DIR"]
BENCHMARKS_DIR = os.environ["BENCHMARKS_DIR"]
HTN_PLAN_FOUND = "INFO: plan found"
HTN_PLAN_NOT_FOUND = "INFO: plan not found"


def getRandSeed() -> int:
    time = Time(datetime.utcnow().isoformat())
    time.format = "gps"
    randseed = int(time.value * 10 ** 6)
    return randseed


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
        oldDir = os.getcwd()
        os.chdir(PROJ_DIR + "/satellite-generator")
        subprocess.run(subProcessArr, stdout=f)
        os.replace(
            PROJ_DIR + f"/helper-scripts/{fileName}",
            BENCHMARKS_DIR + f"/satellite/{fileName}",
        )
        os.chdir(oldDir)

    return fileName


def runHtnPlanner(fileName: str) -> bool:
    subProcessArr = [
        "./Examples/problem_ingestor/problem_ingestor.py",
        "satellite",
        BENCHMARKS_DIR + "/satellite/domain.pddl",
        BENCHMARKS_DIR + f"/satellite/{fileName}",
    ]

    oldDir = os.getcwd()
    os.chdir(PROJ_DIR + "/gt-pyhop")
    ret = subprocess.run(subProcessArr, stdout=subprocess.PIPE)
    os.chdir(oldDir)

    retText = ret.stdout.decode("utf-8")
    return retText.find(HTN_PLAN_FOUND) > 0


def main():
    numObsArr = [20, 25]
    numProbsPerSize = 10

    for numObs in numObsArr:
        successCount = 0
        while successCount < numProbsPerSize:
            fileName = generateProblemFile(numObs, successCount)
            result = runHtnPlanner(fileName)
            if result:
                successCount += 1
            else:
                print(
                    f"WARN: Failed attempt {successCount + 1} for count {numObs}, retrying..."
                )


if __name__ == "__main__":
    main()
