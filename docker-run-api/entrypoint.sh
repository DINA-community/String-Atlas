#!/bin/sh
export PYTHONPATH="/app:${PYTHONPATH}"
export PYTHONPATH="/app:${PYTHONPATH}" && python normalizer/initialise/init_process_csaf_files.py
export PYTHONPATH="/app:${PYTHONPATH}" && python app.py
