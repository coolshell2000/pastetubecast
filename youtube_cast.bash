#!/bin/bash
VAR_USER=$1
VAR_HOST=$2
VAR_URL=$3
VAR_OPTION=$4

VAR_LOCAL_DISPLAY=$(ssh -o ConnectTimeout=1 $VAR_USER@$VAR_HOST "w" | grep ^$VAR_USER | grep ":0" | awk '{print $3}')
if [[ -z $VAR_LOCAL_DISPLAY ]]; then
  echo "Error - remote X not ready. no VAR_LOCAL_DISPLAY=$VAR_LOCAL_DISPLAY"
  echo "attempt to play locally.."
  mpv $VAR_URL $VAR_OPTION> /dev/null 2>&1
else
  echo "play it remotely at $VAR_USER@$VAR_HOST .."
  #ssh $VAR_USER@$VAR_HOST "pkill mpv ;sleep 0.1; export DISPLAY=:0 ; mpv $VAR_URL $VAR_OPTION> /dev/null 2>&1 &"
  ssh $VAR_USER@$VAR_HOST "pkill mpv ;sleep 0.1; export DISPLAY=:0 ; mpv $VAR_URL $VAR_OPTION> /dev/null 2>&1"
fi
