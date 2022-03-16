#!/usr/bin/env bash

numSats=( 5 10 25 50 75 100 150 200 )
echo "Generating files..."
for i in "${numSats[@]}"
do
	./satgen -u 777 3 2 2 $i 2 > test.$i.pddl
done
echo "Files generated"

echo "Moving files to benchmarks..."
mv test.* $BENCHMARKS/satellite
echo "Files moved"
