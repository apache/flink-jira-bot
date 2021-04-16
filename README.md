# Apache Flink Jira Bot

The Flink Jira enforces some of the rules outlined in [the Apache Flink Confluence](https://cwiki.apache.org/confluence/display/FLINK/Flink+Jira+Process).

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

### Rule 1 (not implemented yet)

### Rule 2: Unassign Stale Assigned Tickets

Assigned tickets without an update for {stale_assigned.stale_days} are unassigned after a warning period of {stale_assigned.warning_days}. Before this happens the assignee is notified that this is about to happen and asked for an update on the status of her contribution.

### Rule 3: Close Stale Minor Tickets

An unresolved Minor ticket without an update for {stale_minor.stale_days} is closed after a warning period of {stale_minor.warning_days} with a comment that encourages users to watch, comment and simply reopen with a higher priority if the problem insists.

## About Apache Flink

Apache Flink is an open source project of The Apache Software Foundation (ASF).

Flink is distributed data processing framework with powerful stream and batch processing capabilities. Learn more about Flink at http://flink.apache.org/