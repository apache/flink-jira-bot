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
from argparse import ArgumentParser
from pathlib import Path

from stale_assigned_rule import StaleAssignedRule
from stale_major_or_above_rule import StaleMajorOrAboveRule
from stale_minor_rule import StaleMinorRule


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

    stale_assigned_rule = StaleAssignedRule(jira, jira_bot_config, args.dryrun)
    stale_minor_rule = StaleMinorRule(jira, jira_bot_config, args.dryrun)
    stale_major_rule = StaleMajorOrAboveRule(
        jira, jira_bot_config, args.dryrun, "Major"
    )
    stale_critical_rule = StaleMajorOrAboveRule(
        jira, jira_bot_config, args.dryrun, "Critical"
    )
    stale_blocker_rule = StaleMajorOrAboveRule(
        jira, jira_bot_config, args.dryrun, "Blocker"
    )
    stale_assigned_rule.run()
    stale_minor_rule.run()
    stale_major_rule.run()
    stale_critical_rule.run()
    stale_blocker_rule.run()
