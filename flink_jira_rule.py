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

import abc
import logging


class FlinkJiraRule:
    __metaclass__ = abc.ABCMeta

    def __init__(self, jira_client, config, is_dry_run):
        self.jira_client = jira_client
        self.is_dry_run = is_dry_run
        self.stale_days = config["stale_days"].get()
        self.warning_days = config["warning_days"].get()
        self.warning_label = config["warning_label"].get()
        self.done_label = config["done_label"].get()
        self.done_comment = config["done_comment"].get()
        self.warning_comment = config["warning_comment"].get()
        self.ticket_limit = config["ticket_limit"].get()

    def get_issues(self, jql_query, limit=10000):
        """Queries the JIRA PI for all issues that match the given JQL Query

        This method is necessary as requests tend to time out if the number of results reaches a certain number.
        So, this method requests the results in multiple queries and returns a final list of all issues.
        :param jql_query: the search query
        :param limit: the maximum number of issues that should returned
        :return: a list of issues matching the query
        """
        limit_per_api_request = min(100, limit)
        current = 0
        total = 1
        issues = []
        while current < min(total, limit):
            response = self.jira_client.jql(
                jql_query, limit=limit_per_api_request, start=current
            )
            total = response["total"]
            issues = issues + response["issues"]
            current = len(issues)
        logging.info(f'"{jql_query}" returned {len(issues)} issues')
        return issues[: min(limit, len(issues))]

    def has_recently_updated_subtask(self, parent, updated_within_days):
        find_subtasks_updated_within = (
            f"parent = {parent}  AND updated > startOfDay(-{updated_within_days}d)"
        )
        issues = self.get_issues(find_subtasks_updated_within, 1)
        return len(issues) > 0

    def add_label_with_comment(self, key, label, comment):
        if not self.is_dry_run:
            self.jira_client.edit_issue(
                key,
                {"labels": [{"add": label}], "comment": [{"add": {"body": comment}}]},
            )
        else:
            logging.info(f'DRY RUN ({key}): Adding label "{label}".')

    @abc.abstractmethod
    def run(self):
        return

    @abc.abstractmethod
    def handle_stale_ticket(self, key, warning_label, done_label, comment):
        return

    def mark_stale_tickets_stale(self, jql_query):

        logging.info(f"Looking for stale tickets.")
        issues = self.get_issues(jql_query)

        updated_issues_counter = 0
        i = 0
        while i < len(issues) and updated_issues_counter <= self.ticket_limit:
            issue = issues[i]
            key = issue["key"]

            if not self.has_recently_updated_subtask(key, self.stale_days):
                logging.info(
                    f"Found https://issues.apache.org/jira/browse/{key}. It is marked stale now."
                )
                formatted_comment = self.warning_comment.format(
                    stale_days=self.stale_days,
                    warning_days=self.warning_days,
                    warning_label=self.warning_label,
                )

                self.add_label_with_comment(key, self.warning_label, formatted_comment)

                updated_issues_counter += 1

            else:
                logging.info(
                    f"Found https://issues.apache.org/jira/browse/{key}, but is has recently updated Subtasks. "
                    f"Ignoring for now."
                )
            i += 1

    def handle_tickets_marked_stale(self, jql_query):
        logging.info(f"Looking for ticket previously marked as {self.warning_label}.")
        issues = self.get_issues(jql_query, self.ticket_limit)

        for issue in issues:
            key = issue["key"]
            logging.info(
                f"Found https://issues.apache.org/jira/browse/{key}. It is now processed as stale."
            )

            formatted_comment = self.done_comment.format(
                warning_days=self.warning_days,
                warning_label=self.warning_label,
                done_label=self.done_label,
            )

            self.handle_stale_ticket(
                key, self.warning_label, self.done_label, formatted_comment
            )
