play:
	cd clients/Linux; ./launch.sh

server:
	cd clients/Linux; ./teeworlds_srv -f server.cfg

# make run_ai map=1
run_ai:
	python controller.py maps/map$(map).csv
