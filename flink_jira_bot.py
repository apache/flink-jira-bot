from atlassian import Jira
import logging
import confuse
import os
import abc


class FlinkJiraRule:
    __metaclass__ = abc.ABCMeta

    def __init__(self, jira_client, config):
        self.jira_client = jira_client
        self.config = config

    def has_recently_updated_subtask(self, parent, updated_within_days):
        find_subtasks_updated_within = (
            f"parent = {parent}  AND updated > startOfDay(-{updated_within_days}d)"
        )
        issues = self.jira_client.jql(find_subtasks_updated_within, limit=1)
        return issues["total"] > 0

    @abc.abstractmethod
    def run(self):
        return


class Rule3(FlinkJiraRule):
    def __init__(self, jira_client, config):
        super().__init__(jira_client, config)
        self.stale_days = config["stale_minor"]["stale_days"].get()
        self.warning_days = config["stale_minor"]["warning_days"].get()
        self.label = config["stale_minor"]["label"].get()
        self.comment = config["stale_minor"]["comment"].get()

    def run(self):
        self.close_tickets_marked_stale()
        self.mark_stale_tickets_stale()

    def close_tickets_marked_stale(self):

        minor_tickets_marked_stale = f'project=FLINK AND Priority = Minor AND resolution = Unresolved AND labels in ("{self.label}") AND updated < startOfDay(-{self.warning_days}d)'
        logging.info(
            f"Looking for minor tickets, which were previously marked as stale: {minor_tickets_marked_stale}"
        )
        issues = jira.jql(minor_tickets_marked_stale, limit=10000)

        for issue in issues["issues"]:
            key = issue["key"]
            logging.info(
                f"Found https://issues.apache.org/jira/browse/{key}. It is now closed due to inactivity."
            )

    def mark_stale_tickets_stale(self):

        stale_minor_tickets = f"project = FLINK AND Priority = Minor AND resolution = Unresolved AND updated < startOfDay(-{self.stale_days}d)"
        logging.info(
            f"Looking for minor tickets, which are stale: {stale_minor_tickets}"
        )
        issues = self.jira_client.jql(stale_minor_tickets, limit=10000)

        for issue in issues["issues"]:
            key = issue["key"]
            issue = self.jira_client.get_issue(key)

            if not self.has_recently_updated_subtask(key, self.stale_days):
                logging.info(
                    f"Found https://issues.apache.org/jira/browse/{key}. It is marked stale now."
                )

            else:
                logging.debug(
                    f"Found https://issues.apache.org/jira/browse/{key}, but is has recently updated Subtasks. Ignoring for now."
                )


if __name__ == "__main__":

    logging.getLogger().setLevel(logging.INFO)

    config = confuse.Configuration("flink-jira-bot", __name__)
    config.set_file("config.yaml")

    jira = Jira(
        url="https://issues.apache.org/jira",
        username="flink-jira-bot",
        password=os.environ["JIRA_PASSWORD"],
    )

    rule_3 = Rule3(jira, config)
    rule_3.run()
