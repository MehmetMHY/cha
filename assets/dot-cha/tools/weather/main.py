from datetime import datetime, timezone

from cha import utils


class UsersCurrentWeatherStats:
    def __init__(self):
        # NOTE: name and description of the external Cha tool
        self.name = "Current Weather Stats"
        self.description = "Get the user's current weather data"

        # NOTE: Cha alias for this tool
        self.alias = "!weather"

        # NOTE: Weather or not, and how to, feed the user's pre-existing chat history into this tool's call
        #   - if set to False: the user's current chat history will NOT be included in this tool
        #   - if set to True: the user's complete current chat history WILL BE included in this tool
        self.include_history = True

        self.timeout_sec = 30  # seconds

        # NOTE: Pipe the user's input into this tool, e.g. !weather will be it be sunny today
        self.pipe_input = True

        # NOTE: weather or not to just exist the current chat input in Cha after the tool is called or feed the context into the current chat as context
        self.pipe_output = True

    def execute(self, **kwargs):
        """
        Accepts arbitrary keyword arguments so input structure
        can change without updating the method signature.

        piped_input
        chat_history
        """

        piped_input = kwargs.get("piped_input")

        chat_history = kwargs.get("chat_history")
        if len(chat_history) > 2:
            chat_history = chat_history[-2:]
        elif len(chat_history) >= 1:
            chat_history = chat_history[-1:]
        else:
            chat_history = "Just tell me my weather"

        try:
            utc_time_stamp = f"{datetime.now(timezone.utc)} UTC"
            local_weather_data = utils.get_request("https://wttr.in?format=j1")
            local_weather_data = local_weather_data.json()
            return utils.rls(
                f"""
                Today's Date is {utc_time_stamp}

                The user's weather stats, using wttr.in, is the following:
                
                ```
                {str(local_weather_data)}
                ```

                With that in mind, answer the user's question:
                
                ```
                {piped_input}
                ```

                If the user did not provide a question, answer the question as best as you can based on previous messages the user sent during the conversations:
                ```
                {chat_history}
                ```
                """
            )
        except Exception as e:
            return None


if __name__ == "__main__":
    tool = UsersCurrentWeatherStats()

    print(f"Tool's Name:", tool.name)
    print(f"Tool's About:", tool.description)
    print(f"Include History:", tool.include_history)
    print(f"Call Name:", tool.alias)

    print()
    user_input = input(f"Enter {tool.alias} to continue... ")
    print()

    if user_input.strip().startswith(tool.alias) and len(user_input.split(" ")) > 1:
        pipe_input = " ".join(user_input.split(" ")[1:])
        output = tool.execute(piped_input=pipe_input)
        print("\nOUTPUT:")
        print(output)
    else:
        print("ERROR: Invalid input!")
