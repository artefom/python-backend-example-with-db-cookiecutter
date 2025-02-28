# pylint: disable=missing-module-docstring

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_echo(api_client: AsyncClient) -> None:
    response = await api_client.get("/echo?request=test")
    assert response.status_code == 200
    assert response.json() == {"text": "test"}


@pytest.mark.asyncio
async def test_new_post(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/posts", json={"title": "Test", "main_content": "This is a test post"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Test"


@pytest.mark.asyncio
async def test_view_posts(api_client: AsyncClient) -> None:
    response = await api_client.get("/posts")
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)


@pytest.mark.asyncio
async def test_view_post(api_client: AsyncClient) -> None:
    res = await api_client.post(
        "/posts", json={"title": "Test", "main_content": "This is a test post"}
    )
    assert res.status_code == 200
    post_id = res.json()["id"]
    response = await api_client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    assert response.json()["id"] == post_id
    assert response.json()["title"] == "Test"
    assert response.json()["main_content"] == "This is a test post"


@pytest.mark.asyncio
async def test_update_post(api_client: AsyncClient) -> None:
    res = await api_client.post(
        "/posts", json={"title": "Test", "main_content": "This is a test post"}
    )
    assert res.status_code == 200
    post_id = res.json()["id"]
    response = await api_client.put(
        f"/posts/{post_id}",
        json={"title": "Updated", "main_content": "Updated content"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["main_content"] == "Updated content"


@pytest.mark.asyncio
async def test_delete_post(api_client: AsyncClient) -> None:
    res = await api_client.post(
        "/posts", json={"title": "Test", "main_content": "This is a test post"}
    )
    assert res.status_code == 200
    post_id = res.json()["id"]
    response = await api_client.delete(f"/posts/{post_id}")
    assert response.status_code == 200
    response = await api_client.get(f"/posts/{post_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_view_post_not_found(api_client: AsyncClient) -> None:
    response = await api_client.get("/posts/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_post_not_found(api_client: AsyncClient) -> None:
    response = await api_client.put(
        "/posts/999999",
        json={"title": "Updated", "main_content": "Updated content"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_post_not_found(api_client: AsyncClient) -> None:
    response = await api_client.delete("/posts/999999")
    assert response.status_code == 404
