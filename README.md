# Apache Flink Jira Bot

The Flink Jira Bot partially enforces the Apache Flink Jira process. Please see [Apache Flink Jira Process](https://cwiki.apache.org/confluence/display/FLINK/Flink+Jira+Process) for all the guidlines and conventions that we try to follow.

## Usage

```
./venv/bin/python3 flink_jira_bot.py --help
usage: flink_jira_bot.py [-h] [-d] [-c CONFIG]

Apache Flink Jira Bot

optional arguments:
  -h, --help            show this help message and exit
  -d, --dry-run         no action on Jira, only logging
  -c CONFIG, --config CONFIG
                        path to config file (default: config.yaml)
```

There are also `make` targets for the important actions:

### Run
```
make run
```

### Dry-Run

The dry-run does not make any changes to the Apache Flink Jira, but instead only logs the actions it would do.

```
make dry-run
```

### Configuration

Both `make run` and `make dry-run` look for the password of `flink-jira-bot` in an environment variable called `JIRA_PASSWORD`. 

The configuration of the rules can be found in [config.yaml](config.yaml). 

## About the Rules

### Rule 1 Tickets Need an Assignee or Discussion Eventually

Any ticket (except ones with priority "Not a Priority") needs an assignee, or an update within {stale_<blocker|critical|major|minor>.stale_days}, otherwise the priority will be reduced after a warning period of {stale_<blocker|critical|major>.warning_days} days.
An update of a Sub-Task counts as an update to the ticket. 
Before this happens the assignee/reporter/watchers are notified that the ticket is about to become stale and will be deprioritized. 
The time periods before warning differ based on the priority: 

### Rule 2: Unassign Stale Assigned Tickets

Assigned tickets without an update for {stale_assigned.stale_days} days are marked stale. The assignee is notified and asked for an update on the status of her contribution.

## About Apache Flink

Apache Flink is an open source project of The Apache Software Foundation (ASF).

Flink is a distributed data processing framework with powerful stream and batch processing capabilities. Learn more about Flink at http://flink.apache.org/

