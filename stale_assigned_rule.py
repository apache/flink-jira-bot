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
        self.handle_tickets_marked_stale(
            f"project=FLINK AND resolution = Unresolved AND labels in "
            f'("{self.warning_label}") AND updated < startOfDay(-{self.warning_days}d)'
        )
        self.mark_stale_tickets_stale(
            f"project = FLINK AND resolution = Unresolved AND assignee is not EMPTY "
            f"AND updated < startOfDay(-{self.stale_days}d)"
        )

    def handle_stale_ticket(self, key, warning_label, done_label, comment):
        self.unassign(key, warning_label, done_label, comment)

    def unassign(self, key, warning_label, done_label, comment):
        if not self.is_dry_run:
            if self.jira_client.get_issue_status(key) == "In Progress":
                self.jira_client.edit_issue(
                    key,
                    {"assignee": [{"set": {"name": self.jira_client.username}}]},
                    notify_users=False,
                )
                self.jira_client.set_issue_status(key, "Open")
            self.jira_client.edit_issue(
                key,
                {
                    "labels": [{"add": done_label}, {"remove": warning_label}],
                    "comment": [{"add": {"body": comment}}],
                    "assignee": [{"set": {"name": None}}],
                },
                notify_users=False,
            )
        else:
            logging.info(f"DRY_RUN (({key})): Unassigning.")
