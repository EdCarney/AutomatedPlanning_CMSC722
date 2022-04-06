#! /usr/bin/env python3

from os import listdir
from os.path import exists, isdir, isfile, basename, join
from posixpath import dirname
import sys
import re

FILE_START = "(define"
FILE_END = ")"
LEVEL_1_INDENT = "\t"
LEVEL_2_INDENT = "\t\t"
LEVEL_3_INDENT = "\t\t\t"


def generateObjects():
    return


def getProbFiles(fileDir: str) -> list[str]:
    probRe = re.compile("^test\.[0-9]*$")
    allFiles = [f for f in listdir(fileDir) if isfile(join(fileDir, f))]
    probFiles = [f for f in allFiles if re.match(probRe, f)]
    print(f"INFO: Problem files found: {probFiles}")
    return probFiles


def generatePddlFiles(fileDir: str, probFiles: list[str]) -> None:
    for probFile in probFiles:
        print(f"INFO: Generating PDDL for {probFile}...")
        generatePddlFile(fileDir, probFile)


def generatePddlFile(fileDir: str, probFile: str) -> None:
    with open(join(fileDir, probFile)) as f:
        lines = f.readlines()

    if fileFormatIsInvalid(lines):
        print("ERROR: File definition not correct, skipping")
        return

    pddlLines = translateToPddl(probFile, lines)

    with open(join(fileDir, probFile) + ".pddl", "w") as f:
        f.writelines(pddlLines)


def fileFormatIsInvalid(lines: list[str]) -> bool:
    blocksWorldRe = [
        re.compile("^\s([0-9]*)$"),
        re.compile("^(\s[0-9]*)+$"),
        re.compile("^\s([0-9]*)$"),
        re.compile("^(\s[0-9]*)+$"),
        re.compile("0"),
    ]

    if len(lines) != 5:
        return True

    for i in range(len(lines)):
        if not re.match(blocksWorldRe[i], lines[i]):
            return True

    return False


def translateToPddl(probFileName: str, lines: list[str]) -> list[str]:
    pddlLines = []
    pddlLines.append(FILE_START)
    pddlLines.append(generateProblemElement(probFileName))
    pddlLines.append(generateDomainElement())
    pddlLines.append(generateObjectsElement(lines))
    pddlLines += generateInitElement(lines)
    pddlLines += generateGoalElement(lines)
    pddlLines.append(FILE_END)
    return pddlLines


def generateProblemElement(fileName: str) -> str:
    nameWithDashes = fileName
    nameWithDashes = nameWithDashes.replace(" ", "-")
    nameWithDashes = nameWithDashes.replace(".", "-")
    nameWithDashes = nameWithDashes.replace("(", "-")
    nameWithDashes = nameWithDashes.replace(")", "-")

    return f"(problem blocks-{nameWithDashes})"


def generateDomainElement() -> str:
    return "(:domain blocks)"


def generateObjectsElement(lines: list[str]) -> str:
    numBlocks = int(lines[0].strip())
    blocksText = " ".join([f"b{i+1}" for i in range(numBlocks)])
    return f"(:objects {blocksText})"


def generateInitElement(lines: list[str]) -> list[str]:
    initStr = lines[1].strip()
    initStates = initStr.split(" ")
    initLines = []

    initLines.append("(:init")
    initLines += getStateElementLines(initStates)
    initLines.append(")")

    return initLines


def generateGoalElement(lines: list[str]) -> str:
    goalStr = lines[3].strip()
    goalStates = goalStr.split(" ")
    goalLines = []

    goalLines.append("(:goal (and")
    goalLines += getStateElementLines(goalStates)
    goalLines.append("))")

    return goalLines


def getStateElementLines(states: list[str]) -> list[str]:
    states = [int(x) for x in states]
    stateElementLines = []

    for i in range(len(states)):
        blockNum = i + 1
        onBlock = states[i]

        if onBlock == 0:
            stateElementLines.append(f"(ontable b{blockNum})")
        else:
            stateElementLines.append(f"(on b{blockNum} b{onBlock})")

        if not blockNum in states:
            stateElementLines.append(f"(clear b{blockNum})")

    stateElementLines.append("(handempty)")

    return stateElementLines


def main():
    if len(sys.argv) != 2:
        print("ERROR: Script requires exactly one argument for the directory or file")
        return

    fileOrDir = sys.argv[1]
    if exists(fileOrDir) and isfile(fileOrDir):
        generatePddlFiles(dirname(fileOrDir), [basename(fileOrDir)])
    elif exists(fileOrDir) and isdir(fileOrDir):
        files = getProbFiles(fileOrDir)
        generatePddlFiles(fileOrDir, files)


if __name__ == "__main__":
    main()
