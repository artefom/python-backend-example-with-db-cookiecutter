"""
Full API specification

Fully describes API of the application,
must not depend on any other modules
"""

import abc
import enum
import inspect
import logging
from contextlib import contextmanager
from functools import wraps
from typing import (
    Any,
    Callable,
    Generator,
    Generic,
    List,
    Tuple,
    Type,
    TypeVar,
    get_type_hints,
)
from uuid import uuid4

import fastapi
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T")

ErrorVariants = TypeVar("ErrorVariants")


class UserError(BaseModel, Generic[ErrorVariants]):
    """
    Error model for all user errors.
    Provides reason of error and details
    """

    error: ErrorVariants
    detail: str


class EchoResponse(BaseModel):
    text: str


class PostPayload(BaseModel):
    title: str
    main_content: str


class PostResponse(BaseModel):
    id: int
    title: str
    main_content: str


class PostsListResponse(BaseModel):
    data: list[PostResponse]


class EchoExampleError(Exception):
    status_code = 400

    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return f"Echo example error: {self.message}"


class PostNotFoundError(Exception):
    status_code = 404

    def __init__(self, post_id: int):
        self.post_id = post_id

    def __str__(self):
        return f"Post (id={self.post_id}) was not found"


async def default_validation_exception_handler(
    _: fastapi.Request, exc: RequestValidationError
):
    """
    Handler for FastAPI errors
    """
    return fastapi.Response(
        UserError(error=exc.__class__.__name__, detail=str(exc)).model_dump_json(),
        headers={"Content-Type": "application/json"},
        status_code=422,
    )


def _create_error_enum(name: str, errors: List[Type[Exception]]):
    variants = dict()
    for error in errors:
        error_type = error.__name__
        variants[error_type] = error_type
    return enum.Enum(f"{name}_errors", variants, type=str)


def expect_exceptions(func: Callable, exceptions: Tuple[Type[Exception], ...]):
    """
    Specifies which exceptions can function raise
    Only those exceptions will be handled
    """

    @wraps(func)
    async def _handle_exceptions(*args: Any, **kwargs: Any):
        try:
            return await func(*args, **kwargs)
        except exceptions as exc:
            return fastapi.Response(
                UserError(
                    error=exc.__class__.__name__, detail=str(exc)
                ).model_dump_json(),
                headers={"Content-Type": "application/json"},
                status_code=getattr(exc, "status_code"),
            )
        # Manually handle here internal server errors
        # Handling the error this way gives more concise stack trace
        # and also allows middleware such as CORS to correctly add headers
        # to the response
        except Exception:  # pylint: disable=broad-exception-caught
            error_uuid = str(uuid4())

            logger.exception("Unhandled exception occurred. Id %s", error_uuid)

            return fastapi.Response(
                UserError(
                    error="Internal server error",
                    detail=f"Find details in logs by this id: {error_uuid}",
                ).model_dump_json(),
                headers={"Content-Type": "application/json"},
                status_code=500,
            )

    errors_by_status_code = dict()

    for exception in exceptions:
        status_code = getattr(exception, "status_code")
        if status_code not in errors_by_status_code:
            errors_by_status_code[status_code] = list()
        errors_by_status_code[status_code].append(exception)

    additional_responses = dict()
    for status_code, errors in errors_by_status_code.items():
        additional_responses[status_code] = {
            "model": UserError[
                _create_error_enum(  # type: ignore
                    f"{func.__name__}{status_code}", errors
                )
            ]
        }

    additional_responses[422] = {
        "model": UserError[
            _create_error_enum(  # type: ignore
                f"{func.__name__}422", [RequestValidationError]
            )
        ]
    }

    _handle_exceptions.additional_responses = additional_responses  # type: ignore

    return _handle_exceptions


class Api(abc.ABC):
    """
    API interface for implementation definition
    """

    @abc.abstractmethod
    async def echo(self, request: str) -> EchoResponse:
        """
        Echo what user inputs.
        Raises error if request = 'error'
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def new_post(self, post: PostPayload) -> PostResponse:
        """
        Create a new post.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def view_posts(self) -> PostsListResponse:
        """
        View all posts.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def view_post(self, post_id: int) -> PostResponse:
        """
        View a specific post by ID.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def update_post(self, post_id: int, post: PostPayload) -> PostResponse:
        """
        Update a specific post by ID.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def delete_post(self, post_id: int) -> None:
        """
        Delete a specific post by ID.
        """
        raise NotImplementedError()


class ApiSection:
    """
    Helper method for registering methods
    Registers methods in given router with specified prefix and tag
    """

    def __init__(self, router: APIRouter, prefix: str, tag: str):
        self.router = router
        self.prefix = prefix
        self.tag = tag

    def register(
        self,
        method: str,
        path: str,
        endpoint: Any,
        *exceptions: Type[Exception],
        deprecated: bool = False,
    ):
        endpoint = expect_exceptions(endpoint, exceptions)
        response_model = get_type_hints(endpoint)["return"]

        if isinstance(response_model, type) and issubclass(
            response_model, fastapi.Response
        ):
            response_model = None

        additional_responses = getattr(endpoint, "additional_responses", None)

        path_with_prefix = f"{self.prefix.rstrip('/')}{'/' if path else ''}{path}"
        self.router.add_api_route(
            path_with_prefix,
            endpoint,
            methods=[method],
            tags=[self.tag],
            response_model=response_model,
            summary=inspect.getdoc(endpoint),
            description=None,
            responses=additional_responses,
            deprecated=deprecated,
        )


def make_router(api: Api) -> APIRouter:
    router = APIRouter()

    @contextmanager
    def section(prefix: str, tag: str) -> Generator[ApiSection, None, None]:
        yield ApiSection(router, prefix, tag)

    # Add new API routes here
    with section("/echo", "echo") as sec:
        sec.register("GET", "", api.echo, EchoExampleError)
    with section("/posts", "posts") as sec:
        sec.register("POST", "", api.new_post)
        sec.register("GET", "", api.view_posts)
        sec.register("GET", "{post_id}", api.view_post, PostNotFoundError)
        sec.register("PUT", "{post_id}", api.update_post, PostNotFoundError)
        sec.register("DELETE", "{post_id}", api.delete_post, PostNotFoundError)

    return router


def register_default_exception_handler(app: fastapi.FastAPI):
    app.add_exception_handler(
        RequestValidationError,
        default_validation_exception_handler,  # type: ignore
    )
