import logging

from airflow.providers.http.hooks.http import HttpHook

LOGGER = logging.getLogger(__name__)


class MSTeamsHook(HttpHook):
    """
    This hook allows you to post messages to MS Teams using the Incoming Webhook connector.
    Takes both MS Teams webhook token directly and connection that has MS Teams webhook token.
    If both supplied, the webhook token will be appended to the host in the connection.
    :param http_conn_id: connection that has MS Teams webhook URL
    :type http_conn_id: str
    :param message: The message you want to send on MS Teams
    :type message: str
    :param subtitle: The subtitle of the message to send
    :type subtitle: str
    :param button_text: The text of the action button
    :type button_text: str
    :param button_url: The URL for the action button click
    :type button_url : str
    :param theme_color: Hex code of the card theme, without the #
    :type message: str
    """

    def __init__(
        self,
        http_conn_id="ms_teams_default",
        message="",
        subtitle="",
        button_text="",
        button_url="",
        theme_color="00FF00",
        *args,
        **kwargs,
    ):
        super(MSTeamsHook, self).__init__(http_conn_id=http_conn_id, *args, **kwargs)
        self.http_conn_id = http_conn_id
        self.message = message
        self.subtitle = subtitle
        self.button_text = button_text
        self.button_url = button_url
        self.theme_color = theme_color

    def build_message(self):
        card_json = """ {{
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "{3}",
            "summary": "{0}",
            "sections": [{{
                "activityTitle": "{1}",
                "activitySubtitle": "{2}",
                "markdown": true,
                "potentialAction": [
                    {{
                        "@type": "OpenUri",
                        "name": "{4}",
                        "targets": [
                            {{ "os": "default", "uri": "{5}" }}
                        ]
                    }}
                ]
            }}]
        }}"""

        message = card_json.format(
            self.message,
            self.message,
            self.subtitle,
            self.theme_color,
            self.button_text,
            self.button_url,
        )
        LOGGER.info(f"Formatted message:\n{message}")
        return message

    def execute(self):
        """
        Remote Popen (actually execute the webhook call)
        :param cmd: command to remotely execute
        :param kwargs: extra arguments to Popen (see subprocess.Popen)
        """
        self.run(
            endpoint="",  # it's actually part of the 'connection.host'
            data=self.build_message(),
            headers={"Content-type": "application/json"},
        )
