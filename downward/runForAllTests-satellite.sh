#!/usr/bin/env bash

runTests=0

while getopts r flag
do
    case "${flag}" in
        r) runTests=1;;
    esac
done

randseed=$(date +%s)
numSats=3
numMaxIntsPerSat=2
numModes=2
numTargets=20
numObsArr=( 5 10 15 20 25 50 75 100 125 150 175 200 225 250 )
echo "Generating files..."
pushd ~/Projects/School/cmsc722/project-1/satellite-generator
rm test.*
for numObs in "${numObsArr[@]}"
do
	./satgen -c -n -u $randseed $numSats $numMaxIntsPerSat $numModes $numTargets $numObs > test.$numObs.pddl
done
popd
echo "Files generated"

echo "Moving files to benchmarks..."
pushd ~/Projects/School/cmsc722/project-1/satellite-generator
rm $BENCHMARKS/satellite/test.*
mv test.* $BENCHMARKS/satellite
popd
echo "Files moved"

if [ $runTests -eq 1 ]
then
	benchmarks=($(ls $BENCHMARKS/satellite/test.*))
	echo $benchmarks
	for i in "${benchmarks[@]}"
	do
		echo "Running for $i target case..."
		./fast-downward.py $BENCHMARKS/satellite/domain.pddl $i --search "astar(lmcut())" | grep "Total time:"
	done
fi