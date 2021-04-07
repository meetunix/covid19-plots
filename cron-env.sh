# short script which executes a python script within a virtual environment (venv)
# firt argument: full path to the bin directory inside the venv directory
# second argument: full path to the script
# example:
#
# ./cron-env.sh ~/project/.venv/bin ~/project/socript_to_execute.py

set -e

INTERPRETER="python3"

env_path=${1%/}
activate_path=$env_path/activate
interpreter_path=$env_path/$INTERPRETER

if [ ! -f $activate_path ] ; then
    echo "Unable to find \"$activate_path\", venv path provided?"
    exit 1
elif [ ! -f $interpreter_path ] ; then
    echo "Unable to find \"$interpreter_path\", is $INTERPRETER the valid interpreter?"
    exit 1
elif [ ! -f $2 ] ; then
    echo "Unable to find \"$2\"!"
    exit 1
fi

source $activate_path

eval $interpreter_path $2 $3

deactivate
