from airflow.providers.http.operators.http import SimpleHttpOperator
from ms_teams.ms_teams_hook import MSTeamsHook
import logging


class MSTeamsOperator(SimpleHttpOperator):
    """
    This operator allows you to post messages to MS Teams using the Incoming Webhooks connector.
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

    template_fields = (
        "message",
        "subtitle",
    )

    def __init__(
        self,
        http_conn_id="ms_teams_default",
        message="default message",
        subtitle="",
        button_text="ok",
        button_url="https://airflow.com",
        theme_color="00FF00",
        *args,
        **kwargs
    ):
        super(MSTeamsOperator, self).__init__(*args, **kwargs)
        self.hook = MSTeamsHook(
            http_conn_id, message, subtitle, button_text, button_url, theme_color
        )

    def execute(self, context):
        """
        Call the MsTeamsHook to send a message
        """
        self.hook.execute()
        logging.info("Webhook request sent to MS Teams")
