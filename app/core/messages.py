import typing

from starlette.requests import Request


def message(request: Request, message: typing.Any, category: str = "default") -> None:
    if "_messages" not in request.session:
        request.session["_messages"] = []
    request.session["_messages"].append({"message": message, "category": category})


def get_messages(request: Request) -> typing.List[str]:
    messages: typing.List[str]
    if "_messages" in request.session:
        messages = request.session.pop("_messages")
    else:
        messages = []
    return messages
