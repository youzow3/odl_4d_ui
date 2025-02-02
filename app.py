from openai import AsyncOpenAI
import chainlit as cl

from typing import Any


@cl.set_chat_profiles
async def chat_profile() -> list[cl.ChatProfile]:
    return [
        cl.ChatProfile(
            name="OpenAI GPT Series",
            markdown_description="Models from OpenAI"
        ),
        cl.ChatProfile(
            name="llama.cpp Compatible Models",
            markdown_description="Local LLM via llama.cpp"
        )
    ]


@cl.on_chat_start
async def on_chat_start() -> None:
    base_url: str = None
    api_key: str = None
    model: str = None
    timeout: int = None

    chat_profile: str = cl.user_session.get("chat_profile")
    if chat_profile == "OpenAI GPT Series":
        settings: cl.ChatSettings = await cl.ChatSettings(
            [
                cl.input_widget.TextInput(
                    id="api_key",
                    label="API key for OpenAI"
                ),
                cl.input_widget.TextInput(
                    id="model",
                    label="Model name to use",
                    initial="gpt-4o"
                )
            ]
        ).send()

        api_key = settings["api_key"]
        model = settings["model"]
        timeout = None
    elif chat_profile == "llama.cpp Compatible Models":
        settings: cl.ChatSettings = await cl.ChatSettings(
            [
                cl.input_widget.TextInput(
                    id="model",
                    label="Model name to use",
                    initial="phi-4"
                )
            ]
        ).send()
        base_url = "http://localhost:8080/v1/"
        api_key = "none"
        model = settings["model"]
        timeout = None

    cl.user_session.set("base_url", base_url)
    cl.user_session.set("api_key", api_key)
    cl.user_session.set("model", model)
    cl.user_session.set("timeout", timeout)

    # Setup initial state
    cl.user_session.set("client", None)
#   cl.user_session.set("target-data", None)
    cl.user_session.set("dialogue",
                        [{"role": "system",
                          "content": "You are an AI assistant."}])

    """
    files = None
    while files is None:
        files = await cl.AskFileMessage(
            content="Drop a file you want to analyze",
            accept=["text/csv"]
        ).send()

    with open(files[0], "r") as f:
        content: str = f.readall()
        cl.user_session.set("target-data", content)
    #"""


@cl.on_settings_update
async def on_settings_update(settings: dict[str, Any]) -> None:
    if "base_url" in settings.keys():
        cl.user_session.set("base_url", settings["base_url"])
    if "api_key" in settings.keys():
        cl.user_session.set("api_key", settings["api_key"])
    if "model" in settings.keys():
        cl.user_session.set("model", settings["model"])
    if "timeout" in settings.keys():
        cl.user_session.set("timeout", settings["timeout"])


def setup_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=cl.user_session.get("base_url"),
        api_key=cl.user_session.get("api_key"),
        timeout=cl.user_session.get("timeout")
    )


@cl.on_message
async def on_message(message: cl.Message) -> None:
    # Generate responses

    # message.elements[] can contain files and other resources
    # https://docs.chainlit.io/api-reference/message
    # https://docs.chainlit.io/api-reference/elements/file

    client: AsyncOpenAI = cl.user_session.get("client")
    if client is None:
        client = setup_client()
        cl.user_session.set("client", client)

    model: str = cl.user_session.get("model")

    dialogue: list[dict[str, str]] = cl.user_session.get("dialogue")
    dialogue.append({"role": "user", "content": message.content})

    stream = await client.chat.completions.create(
            messages=dialogue, model=model, stream=True)

    output: cl.Message = cl.Message(content="")
    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await output.stream_token(token)

    dialogue.append({"role": "assistant", "content": output.content})

    await output.update()


@cl.on_stop
def on_stop() -> None:
    # Destroy server resources?
    pass


@cl.on_chat_end
def on_chat_end() -> None:
    pass
