#!/bin/bash

function run_test() {
	test=$1
	tmux new-session -d "echo \"Runnning $test\"; sleep 0.5; $test; echo $?; if [[ $? -eq 0 ]]; then bash; fi; killall wlms; killall wlnr"
	tmux split-window -p 90 bash -c "sleep 0.5; ./wlms --testuser"
	tmux split-window -p 90 bash -c "./wlnr"
	tmux select-pane -t 0
	tmux select-layout tiled
	tmux attach
}


GOPATH=`realpath .` go build github.com/widelands/widelands_metaserver/wlms
GOPATH=`realpath .` go build github.com/widelands/widelands_metaserver/wlnr

if [[ -n $1 ]]; then
	run_test $1
	exit
fi

for f in test_*.py; do
	run_test ./$f
done