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

from flink_jira_rule import FlinkJiraRule


class StaleMajorOrAboveRule(FlinkJiraRule):
    """
    Tickets major and above need an assignee, or an update within {stale_<blocker|critical|major>.stale_days},
    otherwise the priority will be reduced after a warning period of {stale_<blocker|critical|major>.warning_days} days.
    An update of on of the Sub-Tasks counts as an update to the ticket.
    Before this happens the assignee/reporter/watchers are notified that the ticket is about to become stale and will
    be deprioritized.
    The time periods before warning differ based on the priority:
    """

    def __init__(self, jira_client, config, is_dry_run, priority, lower_priority):
        super().__init__(jira_client, config, is_dry_run)
        self.lower_priority = lower_priority
        self.priority = priority

    def run(self):
        self.handle_tickets_marked_stale(
            f"project=FLINK AND Priority = {self.priority} AND resolution = Unresolved "
            f'AND labels in ("{self.warning_label}") '
            f"AND updated < startOfDay(-{self.warning_days}d)"
        )
        self.mark_stale_tickets_stale(
            f"project=FLINK AND priority = {self.priority} AND resolution = Unresolved "
            f"AND assignee is empty AND updated < startOfDay(-{self.stale_days}d)"
        )

    def handle_stale_ticket(self, key):
        self.set_priority(key, self.lower_priority)
