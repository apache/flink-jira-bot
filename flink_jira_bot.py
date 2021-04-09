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

from atlassian import Jira
import logging
import confuse
import os
import abc
import sys
from argparse import ArgumentParser
from pathlib import Path


class FlinkJiraRule:
    __metaclass__ = abc.ABCMeta

    def __init__(self, jira_client, config, is_dry_run):
        self.jira_client = jira_client
        self.config = config
        self.is_dry_run = is_dry_run

    def has_recently_updated_subtask(self, parent, updated_within_days):
        find_subtasks_updated_within = (
            f"parent = {parent}  AND updated > startOfDay(-{updated_within_days}d)"
        )
        issues = self.jira_client.jql(find_subtasks_updated_within, limit=1)
        return issues["total"] > 0

    def add_label(self, issue, label):
        labels = issue["fields"]["labels"] + [label]
        fields = {"labels": labels}
        key = issue["key"]

        if not self.is_dry_run:
            self.jira.update_issue_field(key, fields)
        else:
            logging.info(f'DRY RUN ({key}): Adding label "{label}".')

    def replace_label(self, issue, old_label, new_label):
        labels = issue["fields"]["labels"] + [new_label]
        labels.remove(old_label)
        fields = {"labels": labels}
        key = issue["key"]

        if not self.is_dry_run:
            self.jira.update_issue_field(key, fields)
        else:
            logging.info(
                f'DRY RUN ({key}): Replace label "{old_label}" for "{new_label}".'
            )

    def add_comment(self, key, comment):
        if not self.is_dry_run:
            jira.issue_add_comment(key, comment)
        else:
            logging.info(f'DRY_RUN ({key}): Adding comment "{comment}".')

    def close_issue(self, key):
        if not self.is_dry_run:
            jira.issue_transition(key, "Closed")
        else:
            logging.info(f"DRY_RUN (({key})): Closing.")

    @abc.abstractmethod
    def run(self):
        return


class Rule3(FlinkJiraRule):
    def __init__(self, jira_client, config, is_dry_run):
        super().__init__(jira_client, config, is_dry_run)
        self.stale_days = config["stale_minor"]["stale_days"].get()
        self.warning_days = config["stale_minor"]["warning_days"].get()
        self.warning_label = config["stale_minor"]["warning_label"].get()
        self.done_label = config["stale_minor"]["done_label"].get()
        self.warning_comment = config["stale_minor"]["warning_comment"].get()

    def run(self):
        self.close_tickets_marked_stale()
        self.mark_stale_tickets_stale()

    def close_tickets_marked_stale(self):

        minor_tickets_marked_stale = f'project=FLINK AND Priority = Minor AND resolution = Unresolved AND labels in ("{self.warning_label}") AND updated < startOfDay(-{self.warning_days}d)'
        logging.info(
            f"Looking for minor tickets, which were previously marked as stale: {minor_tickets_marked_stale}"
        )
        issues = jira.jql(minor_tickets_marked_stale, limit=10000)

        for issue in issues["issues"]:
            key = issue["key"]
            logging.info(
                f"Found https://issues.apache.org/jira/browse/{key}. It is now closed due to inactivity."
            )

            formatted_comment = self.done_comment.format(
                warning_days=self.warning_days,
                warning_label=self.warning_label,
                done_label=self.done_label,
            )

            self.add_comment(key, formatted_comment)
            self.replace_label(issue, self.warning_label, self.done_label)
            self.close_issue(key)

    def mark_stale_tickets_stale(self):

        stale_minor_tickets = f"project = FLINK AND Priority = Minor AND resolution = Unresolved AND updated < startOfDay(-{self.stale_days}d)"
        logging.info(
            f"Looking for minor tickets, which are stale: {stale_minor_tickets}"
        )
        issues = self.jira_client.jql(stale_minor_tickets, limit=10000)

        for issue in issues["issues"]:
            key = issue["key"]
            issue = self.jira_client.get_issue(key)

            if not self.has_recently_updated_subtask(key, self.stale_days):
                logging.info(
                    f"Found https://issues.apache.org/jira/browse/{key}. It is marked stale now."
                )
                formatted_comment = self.warning_comment.format(
                    stale_days=self.stale_days,
                    warning_days=self.warning_days,
                    warning_label=self.warning_label,
                )

                self.add_label(issue, self.warning_label)
                self.add_comment(key, formatted_comment)

            else:
                logging.info(
                    f"Found https://issues.apache.org/jira/browse/{key}, but is has recently updated Subtasks. Ignoring for now."
                )


def is_dry_run():
    opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    return "-d" in opts


def get_args():
    parser = ArgumentParser(description="Apache Flink Jira Bot")
    parser.add_argument(
        "-d",
        "--dry-run",
        dest="dryrun",
        action="store_true",
        help="no action on Jira, only logging",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="path to config file (default: config.yaml)",
    )
    return parser.parse_args()


if __name__ == "__main__":

    logging.getLogger().setLevel(logging.INFO)

    args = get_args()

    config = confuse.Configuration("flink-jira-bot", __name__)
    config.set_file(args.config)

    jira = Jira(
        url="https://issues.apache.org/jira",
        username="flink-jira-bot",
        password=os.environ["JIRA_PASSWORD"],
    )

    rule_3 = Rule3(jira, config, args.dryrun)
    rule_3.run()
