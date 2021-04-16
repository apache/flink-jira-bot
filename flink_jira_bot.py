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
from argparse import ArgumentParser
from pathlib import Path


class FlinkJiraRule:
    __metaclass__ = abc.ABCMeta

    def __init__(self, jira_client, config, is_dry_run):
        self.jira_client = jira_client
        self.config = config
        self.is_dry_run = is_dry_run

    def get_issues(self, jql_query):
        """Queries the JIRA PI for all issues that match the given JQL Query

        This method is necessary as requests tend to time out if the number of results reaches a certain number.
        So, this method requests the results in multiple queries and returns a final list of all issues.
        :param jql_query: the search query
        :return: a list of issues matching the query
        """
        limit = 200
        current = 0
        total = 1
        issues = []
        while current < total:
            response = self.jira_client.jql(jql_query, limit=limit, start=current)
            total = response["total"]
            issues = issues + response["issues"]
            current = len(issues)
        logging.info(f'"{jql_query}" returned {len(issues)} issues')
        return issues

    def has_recently_updated_subtask(self, parent, updated_within_days):
        find_subtasks_updated_within = (
            f"parent = {parent}  AND updated > startOfDay(-{updated_within_days}d)"
        )
        issues = self.get_issues(find_subtasks_updated_within)
        return len(issues) > 0

    def add_label(self, issue, label):
        labels = issue["fields"]["labels"] + [label]
        fields = {"labels": labels}
        key = issue["key"]

        if not self.is_dry_run:
            self.jira_client.update_issue_field(key, fields)
        else:
            logging.info(f'DRY RUN ({key}): Adding label "{label}".')

    def replace_label(self, issue, old_label, new_label):
        labels = issue["fields"]["labels"] + [new_label]
        labels.remove(old_label)
        fields = {"labels": labels}
        key = issue["key"]

        if not self.is_dry_run:
            self.jira_client.update_issue_field(key, fields)
        else:
            logging.info(
                f'DRY RUN ({key}): Replace label "{old_label}" for "{new_label}".'
            )

    def add_comment(self, key, comment):
        if not self.is_dry_run:
            self.jira_client.issue_add_comment(key, comment)
        else:
            logging.info(f'DRY_RUN ({key}): Adding comment "{comment}".')

    def close_issue(self, key):
        if not self.is_dry_run:
            self.jira_client.issue_transition(key, "Closed")
        else:
            logging.info(f"DRY_RUN (({key})): Closing.")

    def unassign(self, key):
        if not self.is_dry_run:
            self.jira_client.assign_issue(key, None)
        else:
            logging.info(f"DRY_RUN (({key})): Unassigning.")

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
        self.done_comment = config["stale_minor"]["done_comment"].get()
        self.warning_comment = config["stale_minor"]["warning_comment"].get()

    def run(self):
        self.close_tickets_marked_stale()
        self.mark_stale_tickets_stale()

    def close_tickets_marked_stale(self):

        minor_tickets_marked_stale = (
            f"project=FLINK AND Priority = Minor AND resolution = Unresolved AND labels in "
            f'("{self.warning_label}") AND updated < startOfDay(-{self.warning_days}d)'
        )
        logging.info(
            f"Looking for minor tickets, which were previously marked as {self.warning_label}."
        )
        issues = self.get_issues(minor_tickets_marked_stale)

        for issue in issues:
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

        stale_minor_tickets = (
            f"project = FLINK AND Priority = Minor AND resolution = Unresolved AND updated < "
            f"startOfDay(-{self.stale_days}d)"
        )
        logging.info(f"Looking for minor tickets, which are stale.")
        issues = self.get_issues(stale_minor_tickets)

        for issue in issues:
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
                    f"Found https://issues.apache.org/jira/browse/{key}, but is has recently updated Subtasks. "
                    f"Ignoring for now."
                )


class Rule2(FlinkJiraRule):
    def __init__(self, jira_client, config, is_dry_run):
        super().__init__(jira_client, config, is_dry_run)
        self.stale_days = config["stale_assigned"]["stale_days"].get()
        self.warning_days = config["stale_assigned"]["warning_days"].get()
        self.warning_label = config["stale_assigned"]["warning_label"].get()
        self.done_label = config["stale_assigned"]["done_label"].get()
        self.done_comment = config["stale_assigned"]["done_comment"].get()
        self.warning_comment = config["stale_assigned"]["warning_comment"].get()

    def run(self):
        self.unassign_tickets_marked_stale()
        self.mark_stale_tickets_stale()

    def unassign_tickets_marked_stale(self):

        assigned_tickets_marked_stale = (
            f"project=FLINK AND resolution = Unresolved AND labels in "
            f'("{self.warning_label}") AND updated < startOfDay(-{self.warning_days}d)'
        )
        logging.info(
            f"Looking for assigned tickets, which were previously marked as {self.warning_label}."
        )
        issues = self.get_issues(assigned_tickets_marked_stale)

        for issue in issues:
            key = issue["key"]
            logging.info(
                f"Found https://issues.apache.org/jira/browse/{key}. It is now unassigned due to inactivity."
            )

            formatted_comment = self.done_comment.format(
                warning_days=self.warning_days,
                warning_label=self.warning_label,
                done_label=self.done_label,
            )

            self.add_comment(key, formatted_comment)
            self.replace_label(issue, self.warning_label, self.done_label)
            self.unassign(key)

    def mark_stale_tickets_stale(self):

        stale_assigned_tickets = (
            f"project = FLINK AND resolution = Unresolved AND assignee is not EMPTY AND updated < "
            f"startOfDay(-{self.stale_days}d)"
        )
        logging.info(f"Looking for assigned tickets, which are stale.")
        issues = self.get_issues(stale_assigned_tickets)

        for issue in issues:
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
                    f"Found https://issues.apache.org/jira/browse/{key}, but is has recently updated Subtasks. "
                    f"Ignoring for now."
                )


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

    jira_bot_config = confuse.Configuration("flink-jira-bot", __name__)
    jira_bot_config.set_file(args.config)

    jira = Jira(
        url="https://issues.apache.org/jira",
        username="flink-jira-bot",
        password=os.environ["JIRA_PASSWORD"],
    )

    rule_2 = Rule2(jira, jira_bot_config, args.dryrun)
    rule_3 = Rule3(jira, jira_bot_config, args.dryrun)
    rule_2.run()
    rule_3.run()
