from typing import Dict

import pytest
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src.core.config import settings
from src.schemas.geostore import request_examples
from src.tests.utils.geostores import create_sample_geostore

pytestmark = pytest.mark.asyncio


async def test_read_geostores_list(
    client: AsyncClient, superuser_token_headers: Dict[str, str], db: AsyncSession
) -> None:
    await create_sample_geostore(db=db)
    await create_sample_geostore(db=db)
    r = await client.get(
        f"{settings.API_V1_STR}/config/geostores", headers=superuser_token_headers
    )
    assert 200 <= r.status_code < 300
    geostores = r.json()
    assert len(geostores) > 1


async def test_get_geostores_by_id(
    client: AsyncClient, superuser_token_headers: Dict[str, str], db: AsyncSession
) -> None:
    geostore = await create_sample_geostore(db=db)
    r = await client.get(
        f"{settings.API_V1_STR}/config/geostores/{geostore.id}",
        headers=superuser_token_headers,
    )
    assert 200 <= r.status_code < 300
    retrieved_geostore = r.json()
    assert retrieved_geostore.get("id") == geostore.id


async def test_create_geostores(
    client: AsyncClient, superuser_token_headers: Dict[str, str], db: AsyncSession
) -> None:
    geostore = request_examples["geostore"]
    r = await client.post(
        f"{settings.API_V1_STR}/config/geostores",
        headers=superuser_token_headers,
        json=geostore,
    )
    assert 200 <= r.status_code < 300
    retrieved_geostore = r.json()
    assert retrieved_geostore.get("name") == geostore.get("name")
    assert retrieved_geostore.get("id")


async def test_update_geostores(
    client: AsyncClient, superuser_token_headers: Dict[str, str], db: AsyncSession
) -> None:
    geostore = await create_sample_geostore(db=db)
    geostore_id = geostore.id
    geostore.name += "_updated"
    r = await client.put(
        f"{settings.API_V1_STR}/config/geostores/{geostore_id}",
        headers=superuser_token_headers,
        json=jsonable_encoder(geostore),
    )
    assert 200 <= r.status_code < 300
    retrieved_geostore = r.json()
    assert retrieved_geostore.get("name") == geostore.name
    assert retrieved_geostore.get("id")


async def test_delete_geostore(
    client: AsyncClient, superuser_token_headers: Dict[str, str], db: AsyncSession
) -> None:
    geostore = await create_sample_geostore(db=db)
    r = await client.delete(
        f"{settings.API_V1_STR}/config/geostores/{geostore.id}",
        headers=superuser_token_headers,
    )

    assert 200 <= r.status_code < 300

    # Try to get
    r = await client.get(
        f"{settings.API_V1_STR}/config/geostores/{geostore.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    # Try to delete again

    r = await client.delete(
        f"{settings.API_V1_STR}/config/geostores/{geostore.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


# TODO: ADD GEOSTORE TO STUDY AREA
# TODO: LIST STUDY AREA GEOSTORES
# TODO: REMOVE GEOSTORE FROM STUDY AREA
