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


class StaleMinorRule(FlinkJiraRule):
    """
    An unresolved Minor ticket without an update for {stale_minor.stale_days} or a fixVersion is closed after a warning period of
    {stale_minor.warning_days} with a comment that encourages users to watch, comment and simply reopen with a higher
    priority if the problem insists.
    """

    def __init__(self, jira_client, config, is_dry_run):
        super().__init__(jira_client, config, is_dry_run)

    def run(self):
        self.handle_tickets_marked_stale(
            f"project=FLINK AND Priority = Minor AND resolution = Unresolved "
            f'AND labels in ("{self.warning_label}") '
            f"AND updated < startOfDay(-{self.warning_days}d)"
        )
        self.mark_stale_tickets_stale(
            f'project = FLINK AND type != "Sub-Task" AND Priority = Minor AND resolution = Unresolved '
            f'AND updated < startOfDay(-{self.stale_days}d) AND fixVersion = null AND NOT labels in '
            f'("{self.warning_label}")'
        )

    def handle_stale_ticket(self, key, warning_label, done_label, comment):
        self.close_issue(key, warning_label, done_label, comment)

    def close_issue(self, key, warning_label, done_label, comment):
        if not self.is_dry_run:
            self.jira_client.edit_issue(
                key,
                {"labels": [{"add": done_label}, {"remove": warning_label}]},
                notify_users=False,
            )
            self.jira_client.set_issue_status(
                key,
                "Closed",
                fields={"resolution": {"name": "Auto Closed"}},
                update={"comment": [{"add": {"body": comment}}]},
            )
        else:
            logging.info(f"DRY_RUN (({key})): Closing.")
