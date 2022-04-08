# Layout

This repo is composed of several source directories, a directory for generated PDDL problem files and domain PDDL definitions, and a directory of helper scripts that drive everything.

    bwstates-src: source code to generate block domain problems
    satellite-generator: source code to generate satellite domain problems
    metric-ff: source code for metric ff planner
    benchmarks
        |-blocks: blocks domain and problem PDDL files
        |-satellite: satellite domain and problem PDDL files
    helper-scripts
        |-problem_ingestor
            |-blocks_htn
                |-actions.py: HTN actions for blocks domain
                |-methods.py: HTN methods for blocks domain
            |-satellite_htn
                |-actions.py: HTN actions for satellite domain
                |-methods.py: HTN methods for satellite domain
            |-gtpyhop.py: slightly modified version of GTPyhop
            |-problem_ingestor.py: script for translating PDDL files to HTN problem definitions
        |-generate-prop-pddl.py: script for translating blocks problems to PDDL definitions
        |-runTests.py: main driver script for data generation; calls other scripts

# Building and Running Docker Image

Ensure docker is running, then execute

```
docker build -t cmsc722 .
```

This will build the Docker image named cmsc722 locally.

# Setup

Note that these scripts can be run locally or via the Docker container. As the versions of the specific software needed can be very specific, it is recommended to use the Docker image. The image can either be built locally, or obtained from this [DockerHub repo](https://hub.docker.com/repository/docker/edcarney/cmsc722) (most recommended).

If you want to run the scripts locally you will need to compile the source for **bwstates-src**, **satellite-generator**, and **metric-ff**, and set several local environment variables.

## Via DockerHub Image (Recommended)

Ensure Docker is installed on your machine, then execute the following command to pull the image from DockerHen and spin up a container named **cmsc722**.

```
docker run -di --name cmsc722 edcarney/cmsc722
```

Now, execute the following command to open a shell in the home directory of the container.

```
docker exec -ti cmsc722 bash
```

The directory you enter by default will have the all of the same folders, but with compiled binaries. All environment variables will also be set and data will be ready to generate.

## Via Locally Built Docker Image

Execute the following to build a local Docker image named **cmsc722**.

```
docker build -t cmsc722 .
```

Now run the following to spin up a local container instance named **cmsc722**.

```
docker run -di --name cmsc722 cmsc722
```

Finally, run the following to open a shell in the home directory of the container.

```
docker exec -ti cmsc722 bash
```

The directory you enter by default will have the all of the same folders, but with compiled binaries. All environment variables will also be set and data will be ready to generate.

## Via Local Setup (Not Recommended)

Local setup first requires compiling source in **bwstates-src**, **satellite-generator**, and **metric-ff** directories. All of these directories contain Makefiles. So execute the following from the repo root directory.

```
cd ./bwstates-src && make && cd ../satellite-generator && make && cd ../metric-ff && make
```

NOTE: metric-ff does not appear to compile on MacOS, so far it has only compiled on certain versions on Ubuntu (and likely other Linux distros); again, running from the DockerHub image is recommended for stability.

The python driver scripts require several environment variables to be set prior to first running, specifcally:

- **PROJ_DIR**: this should point to the root directory of whereever this repo is cloned
- **BENCHMARKS_DIR**: this should point to the parent directory of the PDDL domain and problem files; for this repo it should point to the **benchmarks** folder

# Generating Data

Once setup is complete, you can generate data. This is done by running the **runTests.py** helper script.

```
cd ./helper-scripts
./runTests.py <DOMAIN>
```

\<DOMAIN\> here can either be SATELLITE or BLOCKS. This will kick off data generation, which includes:

- Generating problem definitions either with **bwstates** or **satgen**
- Translating problem definitions into PDDL format (for blocks domain only)
- Translating PDDL into HTN definitions
- Running HTN and domain independent (DI) planners
- Outputting results

You should get something like the following if data generation starts successfully

```
22-04-08T03:13:24.172217 - WARN: Failed parsing for plan 8 problem size 5, retrying...
2022-04-08T03:13:24.179375 - WARN: Failed parsing for plan 9 problem size 10, retrying...
2022-04-08T03:13:24.195845 - INFO: Generated plan 0 for problem size 5 in 0.021317720413208008 s (HTN) and 0.1372 s (DI)
2022-04-08T03:13:24.243987 - INFO: Generated plan 13 for problem size 10 in 0.03080892562866211 s (HTN) and 0.1833 s (DI)
2022-04-08T03:13:24.263186 - INFO: Generated plan 1 for problem size 10 in 0.031891584396362305 s (HTN) and 0.1789 s (DI)
2022-04-08T03:13:24.358787 - INFO: Generated plan 10 for problem size 15 in 0.04904794692993164 s (HTN) and 0.2571 s (DI)
2022-04-08T03:13:24.418944 - INFO: Generated plan 6 for problem size 15 in 0.0703122615814209 s (HTN) and 0.2891 s (DI)
2022-04-08T03:13:24.430016 - INFO: Generated plan 2 for problem size 15 in 0.04851198196411133 s (HTN) and 0.2623 s (DI)
2022-04-08T03:13:24.453927 - INFO: Generated plan 14 for problem size 15 in 0.053685903549194336 s (HTN) and 0.2933 s (DI)
2022-04-08T03:13:24.474886 - INFO: Generated plan 4 for problem size 5 in 0.04087018966674805 s (HTN) and 0.0535 s (DI)
2022-04-08T03:13:24.499914 - WARN: Failed to find HTN solution for plan 13 problem size 5, retrying...
```

Once planning completes, you will find the following:

- All generated PDDL files will be in the **benchmarks** folder
- A file named **\<DOMAIN\>\_metrics\_\<TIMESTAMP>.csv** in helper-scripts containing summarized results (averages, stdev's, etc.)
- A file named **\<DOMAIN\>\_plan_data\_\<TIMESTAMP>.csv** in helper-scripts containing detailed information about each generated plan

# Notes

- You may see numerous WARN messages in the logs, this is expected as these are for acceptable issues that warrant a retry
- The logs will appear to be executed in no specific order, this is because of multithreading; this can be disabled by setting **USE_MULTITHREADING** to False in **runTests.py**
- The range of problems the planner executes in each domain can be modified by adjusting the **numTargetsArr** and **numBlocksArr** at the bottom of **runTests.py**
