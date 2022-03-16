#!/usr/bin/env bash

numSats=( 5 10 15 20 25 50 75 100 125 150 175 200 225 250 )
randseed=$(date +%s)
echo "Generating files..."
pushd ~/Projects/School/cmsc722/project-1/satellite-generator
rm test.*
for i in "${numSats[@]}"
do
	./satgen -u $randseed 3 2 2 $i 2 > test.$i.pddl
done
popd
echo "Files generated"

echo "Moving files to benchmarks..."
pushd ~/Projects/School/cmsc722/project-1/satellite-generator
rm $BENCHMARKS/satellite/test.*
mv test.* $BENCHMARKS/satellite
popd
echo "Files moved"

benchmarks=($(ls $BENCHMARKS/satellite/test.*))
echo $benchmarks
for i in "${benchmarks[@]}"
do
	echo "Running for $i target case..."
	./fast-downward.py $BENCHMARKS/satellite/domain.pddl $i --search "astar(lmcut())" | grep "Total time:"
done
