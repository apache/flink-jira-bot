################################################################################
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
# limitations under the License.
################################################################################


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