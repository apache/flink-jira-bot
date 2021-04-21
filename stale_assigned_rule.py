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

import logging

from flink_jira_rule import FlinkJiraRule


class StaleAssignedRule(FlinkJiraRule):
    """
    Assigned tickets without an update for {stale_assigned.stale_days} are unassigned after a warning period of
    {stale_assigned.warning_days}. Before this happens the assignee is notified that this is about to happen and
    asked for an update on the status of her contribution.
    """

    def __init__(self, jira_client, config, is_dry_run):
        super().__init__(jira_client, config, is_dry_run)

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
