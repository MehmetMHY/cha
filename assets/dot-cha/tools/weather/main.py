from datetime import datetime, timezone
import time

from cha import utils


class UsersCurrentWeatherStats:
    def __init__(self):
        # NOTE: name and description of the external Cha tool
        self.name = "Your Weather"
        self.description = "Get the user's current weather data"

        # NOTE: Cha alias for this tool
        self.alias = "!weather"

        # NOTE: Weather or not, and how to, feed the user's pre-existing chat history into this tool's call
        #   - if set to False: the user's current chat history will NOT be included in this tool
        #   - if set to True: the user's complete current chat history WILL BE included in this tool
        self.include_history = True

        # NOTE: this is the timeout in seconds Cha uses to kill the tool if it's taking too long
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


# NOTE: the code below is just for testing
if __name__ == "__main__":
    # NOTE: this function just exists to make the final output shorter so your terminal does not get spammed
    def preview_segments(text, n_segments, segment_length):
        segment_size = len(text) // n_segments
        parts = []
        for i in range(n_segments):
            start = segment_size * i
            end = segment_size * (i + 1)
            segment = text[start:end][:segment_length].strip()
            parts.append(segment)
        return "... ".join(parts) + "... "

    start_time = time.time()

    tool = UsersCurrentWeatherStats()

    example_history = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."},
    ]

    message = f"{tool.alias} What is my weather today?"

    tool_output = tool.execute(chat_history=example_history, pipe_input=message)

    runtime = time.time() - start_time

    print("Calling Weather Tool")
    print("====================")
    print(f"Tool's Name:     {tool.name}")
    print(f"Tool's About:    {tool.description}")
    print(f"Call Name:       {tool.alias}")
    print(f"Include History: {tool.include_history}")
    print(f"Set Timeout:     {tool.timeout_sec} seconds")
    print(f"Pipe Input:      {tool.pipe_input}")
    print(f"Pipe Output:     {tool.pipe_output}")
    # print(f"Tool's Output    {tool_output}")
    print(f"Output Preview:  {preview_segments(tool_output, 3, 8)}")
    print(f"Output's Length: {len(str(tool_output))}")
    print(f"Tool Runtime:    {runtime} seconds")
