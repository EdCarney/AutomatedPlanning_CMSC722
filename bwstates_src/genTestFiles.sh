#!/usr/bin/env bash

numBlocks=( 5 10 25 50 75 100 150 200 )
echo "Generating files..."
for i in "${numBlocks[@]}"
do
	./bwstates -n $i > test.$i
done
echo "Files generated"

echo "Moving files to benchmarks..."
mv test.* $BENCHMARKS/blocks-world
echo "Files moved"

echo "Translating to PDDL..."
pushd $BENCHMARKS/blocks-world
./generate-prob-pddl.py ~/benchmarks/blocks-world/
popd
echo "Files translated"
