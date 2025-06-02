#!/bin/bash


DEFECTS4J_HOME="/path/to/defects4j" # Replace this with the path to your cloned defects4j repo.
WORK_DIR="/Users/WORK_DIR" # Specify the path to the folder where you want to check out all Defects4J bugs.

if [ -z "$BASH_VERSION" ]; then
    echo "This script must be run with bash"
    exit 1
fi

PROJECTS=(
    "Chart 1-26"
    "Cli 1-5 7-40"
    "Closure 1-62 64-92 94-176"
    "Codec 1-18"
    "Collections 25-28"
    "Compress 1-47"
    "Csv 1-16"
    "Gson 1-18"
    "JacksonCore 1-26"
    "JacksonDatabind 1-112"
    "JacksonXml 1-6"
    "Jsoup 1-93"
    "JxPath 1-22"
    "Lang 1 3-65"
    "Math 1-106"
    "Mockito 1-38"
    "Time 1-20 22-27"
)

process_bug() {
  local project=$1
  local bug_id=$2

  echo "Processing $project-$bug_id"

  defects4j checkout -p $project -v ${bug_id}b -w $WORK_DIR/${project}_${bug_id}
}

for entry in "${PROJECTS[@]}"; do
  project=$(echo $entry | awk '{print $1}')
  bug_ranges=$(echo $entry | cut -d' ' -f2-)

  for range in $bug_ranges; do
    if [[ $range == *-* ]]; then
      start=$(echo $range | cut -d'-' -f1)
      end=$(echo $range | cut -d'-' -f2)
      for (( i=$start; i<=$end; i++ )); do
        process_bug $project $i
      done
    else
      process_bug $project $range
    fi
  done
done