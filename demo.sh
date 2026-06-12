#!/bin/bash
#
# This script provide the setup of the demo environment


## Default values
first=2010 ## Set the minimum year
start=2024 ## Set the default starting year 
end=2026   ## Set the default ending year for collecting documents


csaf_cisagov() {
  #git clone https://github.com/cisagov/CSAF
  #mkdir -p resources/CSAF/csaf_files/OT/white
  if check_response "Do you want to adjust the starting year (default: $start) for CSAF resources [y/N]?" "N"; then
    start=$(check_year)
    end=$(check_year $start)
  fi
  echo "CSAF files from $start to $end are used."
  for year in $(seq $start $end); do
    if [ -d "CSAF/csaf_files/OT/white/$year" ]; then
      cp -R "CSAF/csaf_files/OT/white/$year" "resources/CSAF/csaf_files/OT/white/$year"
    fi

  done
  rm -rf CSAF
}

ensure_compose() {
  # Prefer `docker compose` (v2). Fall back to `docker-compose` (v1) if available.
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    cd docker-run-api
    docker compose up
  elif command -v docker-compose >/dev/null 2>&1; then
    cd docker-run-api
    docker-compose up
  else
    error "Neither 'docker compose' nor 'docker-compose' is available."; exit 127
  fi
}

check_year(){
  local default_start=$start
  local default_end=$end
  local start_year="${1:-""}" # If empty default start, otherwise end years is asked
  while true; do
    if [ -z "$start_year" ]; then
      read -rp "Please provide the start year >= $first and <= $default_end: " reply </dev/tty
      if [ -z "$reply" ]; then
          echo "$default_start"
          echo "Default value $default_start is used." >&2
          return 0
      else
          if [[ "$reply" =~ ^20[1-9][0-9]$ ]] && (( reply <= default_end )) ; then
          echo "$reply"
          return 0
          fi
      fi
      echo "Please enter a year between $first and $default_end." >&2
    else # end year
      read -rp "Please provide the end year [$start_year - $default_end]: " reply </dev/tty
      if [ -z "$reply" ]; then
          echo "$default_end"
          echo "Default value $default_end end is used." >&2
          return 0
      fi
      if [[ "$reply" =~ ^20[1-9][0-9]$ ]] && (( reply >= start_year && reply <= default_end )); then
          echo "$reply"
          return 0
      fi 
    fi

    
  done
}


check_response() {
  local text="$1"
  local default_reply="${2:-None}" # Assign default reply if provided
  local reply
  while true; do
    read -rp "[INPUT] $text" reply </dev/tty
    if [ -z "$reply" ]; then
      reply="$default_reply"
    fi
    case "$reply" in
      [yY]|[yY][eE][sS]) return 0 ;;
      ""|[nN]|[nN][oO]) return 1 ;;
      *) echo "Please answer y or n." ;;
    esac
  done
}

main(){
  # get CSAF documents from cisagov
  csaf_cisagov
  ensure_compose
}



main "$@"
