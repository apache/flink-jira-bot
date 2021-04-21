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
    An unresolved Minor ticket without an update for {stale_minor.stale_days} is closed after a warning period of
    {stale_minor.warning_days} with a comment that encourages users to watch, comment and simply reopen with a higher
    priority if the problem insists.
    """

    def __init__(self, jira_client, config, is_dry_run):
        super().__init__(jira_client, config, is_dry_run)

    def run(self):
        self.close_tickets_marked_stale()
        self.mark_stale_tickets_stale(
            f"project = FLINK AND Priority = Minor AND resolution = Unresolved "
            f"AND updated < startOfDay(-{self.stale_days}d)"
        )

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