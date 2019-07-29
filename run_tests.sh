#!/bin/sh

pip --version 2>&1 > /dev/null
if [ $? -ne 0 ]; then
    echo "You have to install 'pip' using your system packet manager first"
    echo "Exit"
    exit 1
fi

base=`realpath "$(dirname "${BASH_SOURCE[0]}")"`
cd "$base"

host=`cat src/config_test.py 2>/dev/null | grep host | awk -F= '{print $2}' | xargs`
port=`cat src/config_test.py 2>/dev/null | grep port | awk -F= '{print $2}' | xargs`

if [ -z "$host" ] || [ -z "$port" ]; then
   echo "Configuration file is missing or corrupt"
   echo "Exit"
   exit 1
fi

if [ -z "$VIRTUAL_ENV" ]; then
    pip install --user virtualenv virtualenv-bin
    PATH=$PATH:~/.local/bin
    mkdir venv 2>/dev/null
    [ $? -eq 0 ] && virtualenv ./venv/ 2>/dev/null && VENV_CREATED="1"
fi

source ./venv/bin/activate
pip install -r requirements-dev.txt
rm src/db/test_db.sqlite 2>/dev/null
python3 ./tests/create_test_user.py

running=`lsof -Pi TCP@$host:$port -t`
if [ -z "$running" ]; then
    echo "Service is not running"
    echo "Trying to start"
    cd ./src/
    python3 app.py &
    sanic_pid=$!
    sanic_pgid=$(ps -o pgid= $sanic_pid | grep -o '[0-9]*')

    echo "Waiting 3 seconds to let sanic start..."
    sleep 3
    cd "$base"
fi

pyresttest "http://$host:$port" ./tests/*.yaml

([ $? -eq 0 ] && echo "Done!" ) || echo "Fail!"

if [ "$VENV_CREATED" == "1" ]; then
    deactivate
    rm -r ./venv
fi

# if the server has been started in this process, shut it down
# (there's probably a better way to do this, but I don't know it)
if [ -n "$sanic_pgid" ]; then
   kill -- -$sanic_pgid >/dev/null 2>&1
fi
