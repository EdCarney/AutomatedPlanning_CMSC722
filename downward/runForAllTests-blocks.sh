#!/usr/bin/env bash

# GENERATE

numBlocks=( 5 10 15 20 25 30 35 40 45 50 55 60 65 70 )
randseed=$(date +%s)
echo "Generating files..."
pushd ~/Projects/School/cmsc722/project-1/bwstates_src
rm test.*
for i in "${numBlocks[@]}"
do
	./bwstates -r $randseed -n $i > test.$i
done
popd
echo "Files generated"

# MOVE

echo "Moving files to benchmarks..."
pushd ~/Projects/School/cmsc722/project-1/bwstates_src
rm $BENCHMARKS/blocks-world/test.*
mv test.* $BENCHMARKS/blocks-world
popd
echo "Files moved"

# TRANSLATE

echo "Translating to PDDL..."
pushd $BENCHMARKS/blocks-world
./generate-prob-pddl.py ~/benchmarks/blocks-world/
popd
echo "Files translated"

# RUN PLANNER

benchmarks=($(ls $BENCHMARKS/blocks-world/test.*.pddl))
echo "Running planner..."
for i in "${benchmarks[@]}"
do
	echo "Running for $i target case..."
	./fast-downward.py $BENCHMARKS/blocks-world/domain.pddl $i --evaluator "hff=ff()" --search "lazy_greedy([hff], preferred=[hff])" | grep "Total time:"
done
echo "Planner run completed"
