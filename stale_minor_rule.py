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
        self.handle_tickets_marked_stale(
            f"project=FLINK AND Priority = Minor AND resolution = Unresolved "
            f'AND labels in ("{self.warning_label}") '
            f"AND updated < startOfDay(-{self.warning_days}d)"
        )
        self.mark_stale_tickets_stale(
            f'project = FLINK AND type != "Sub-Task" AND Priority = Minor AND resolution = Unresolved '
            f'AND updated < startOfDay(-{self.stale_days}d)'
        )

    def handle_stale_ticket(self, key):
        self.close_issue(key)
