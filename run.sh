#!/bin/bash

WORK_PATH="./" # change your work path
python3 nuscene_tool.py \
        ${WORK_PATH}/sets/samples/LIDAR_TOP \
        ${WORK_PATH}/sets/v1.0-mini \
        ${WORK_PATH}/output/
