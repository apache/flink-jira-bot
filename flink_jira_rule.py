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
            self.jira_client.set_issue_status(
                key, "Closed", fields={"resolution": {"name": "Auto Closed"}}
            )
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
