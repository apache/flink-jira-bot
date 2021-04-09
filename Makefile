# define the name of the virtual environment directory
VENV := venv

# default target, when make executed without arguments
all: venv

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	./$(VENV)/bin/pip install -r requirements.txt

# venv is a shortcut target
venv: $(VENV)/bin/activate

help: venv
	./$(VENV)/bin/python3 flink_jira_bot.py --help

dry-run: venv
	./$(VENV)/bin/python3 flink_jira_bot.py -d

run: venv
	./$(VENV)/bin/python3 flink_jira_bot.py

format: venv
	./$(VENV)/bin/python3 -m black .

freeze: venv
	./$(VENV)/bin/pip freeze > requirements.txt

clean:
	rm -rf $(VENV)
	find . -type f -name '*.pyc' -delete



.PHONY: all venv run clean