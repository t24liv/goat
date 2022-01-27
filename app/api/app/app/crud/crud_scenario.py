import io
import json
import os
import shutil
import time
from typing import Any

import geojson
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.sql import text
from starlette.responses import JSONResponse

from app.schemas.scenario import (
    ScenarioBase,
    ScenarioCreate,
    ScenarioDelete,
    ScenarioImport,
    ScenarioReadDeleted,
    ScenarioUpdate,
    ScenarioUpdateDeleted,
)

# TODO: Get scenario layer names from config table
translation_layers = {
    "ways": "deleted_ways",
    "pois": "deleted_pois",
    "buildings": "deleted_buildings",
}


class CRUDScenario:
    async def create_scenario(self, db: AsyncSession, *, obj_in: ScenarioCreate) -> Any:
        obj_in_data = jsonable_encoder(obj_in)
        sql = text(
            """INSERT INTO scenarios (userid, scenario_name) VALUES (:user_id, :scenario_name) RETURNING scenario_id;"""
        )
        result = await db.execute(sql, obj_in_data)
        for row in result:
            print(row)
        await db.commit()
        return {"scenario_id": result[0]}

    async def update_scenario(self, db: AsyncSession, *, obj_in: ScenarioUpdate) -> Any:
        obj_in_data = jsonable_encoder(obj_in)
        sql = text(
            """UPDATE scenarios SET scenario_name = :scenario_name WHERE scenario_id = CAST(:scenario_id AS bigint);"""
        )
        await db.execute(sql, obj_in_data)
        await db.commit()
        return {"msg": "Scenario updated."}

    async def delete_scenario(self, db: AsyncSession, *, obj_in: ScenarioBase) -> Any:
        obj_in_data = jsonable_encoder(obj_in)
        sql = text(
            """DELETE FROM scenarios WHERE scenario_id=:scenario_id;SELECT network_modification(:scenario_id);"""
        )
        await db.execute(sql, obj_in_data)
        await db.commit()
        return {"msg": "All changes are reverted."}

    async def import_scenario(self, db: AsyncSession, *, obj_in: ScenarioImport) -> JSONResponse:
        # TODO: scenario_id must be generated automatically in order to avoid conflicts
        obj_in_data = jsonable_encoder(obj_in)
        obj_in_data["payload"] = json.dumps(obj_in_data["payload"], separators=(",", ":"))
        sql = text(
            """SELECT import_changeset_scenario(:scenario_id,:user_id,jsonb_build_object(:layer_name,CAST(:payload as jsonb)))"""
        )
        result = await db.execute(sql, obj_in_data).fetchone()
        await db.commit()
        return JSONResponse(content=result[0])

    async def export_scenario(self, db: AsyncSession, *, obj_in: ScenarioBase) -> Any:
        obj_in_data = jsonable_encoder(obj_in)
        sql = text("""SELECT * FROM export_changeset_scenario(:scenario_id)""")
        result = await db.execute(sql, obj_in_data).fetchone()
        dicts = dict(result[0])
        dir_path = "/tmp/exports/{}/".format(time.strftime("%Y%m%d-%H%M%S"))
        os.makedirs(dir_path)
        for key in dicts.keys():
            with open(dir_path + "/{}.geojson".format(key), "w") as f:
                geojson.dump(dicts[key], f)
        file_name = "scenario_export_{}".format(time.strftime("%Y%m%d-%H%M%S"))
        shutil.make_archive(file_name, "zip", dir_path)
        with open(file_name + ".zip", "rb") as f:
            data = f.read()
        os.remove(file_name + ".zip")
        shutil.rmtree(dir_path[0 : len(dir_path) - 1])
        response = StreamingResponse(io.BytesIO(data), media_type="application/zip")
        response.headers["Content-Disposition"] = "attachment; filename={}.zip".format(file_name)

        return response

    async def upload_scenario(self, db: AsyncSession, *, obj_in: ScenarioBase) -> Any:
        obj_in_data = jsonable_encoder(obj_in)
        sql = text(
            """SELECT * FROM network_modification(:scenario_id);SELECT * FROM population_modification(:scenario_id);"""
        )
        await db.execute(sql, obj_in_data)
        await db.commit()
        return {"msg": "Scenarios are reflected."}

    async def delete_feature(self, db: AsyncSession, *, obj_in: ScenarioDelete) -> Any:
        obj_in_data = jsonable_encoder(obj_in)
        layer_name = obj_in_data["layer_name"]
        if not translation_layers.get(layer_name):
            raise HTTPException(status_code=404, detail=f"Layer {layer_name} not found.")
        scenario_layer = layer_name + "_modified"
        sql = text(
            f"""DELETE FROM {scenario_layer} WHERE scenario_id = CAST(:scenario_id AS bigint) AND original_id = ANY(:deleted_feature_ids);"""
        )
        await db.execute(sql, obj_in_data)
        await db.commit()
        return {
            "msg": "Feature delete successful.",
        }

    async def read_deleted_features(self, db: AsyncSession, *, obj_in: ScenarioReadDeleted) -> Any:
        obj_in_data = jsonable_encoder(obj_in)
        layer_name = obj_in_data["layer_name"]
        scenario_layer = translation_layers.get(layer_name)
        if not scenario_layer:
            raise HTTPException(status_code=404, detail=f"Layer {layer_name} not found.")

        sql = text(
            f"""SELECT {scenario_layer} AS deleted_feature_ids FROM scenarios WHERE scenario_id=:scenario_id;"""
        )
        result = await db.execute(sql, obj_in_data).fetchone()
        return result[0]

    async def update_deleted_features(
        self, db: AsyncSession, *, obj_in: ScenarioUpdateDeleted
    ) -> Any:
        obj_in_data = jsonable_encoder(obj_in)
        layer_name = obj_in_data["layer_name"]
        scenario_layer = translation_layers.get(layer_name)
        if not scenario_layer:
            raise HTTPException(status_code=404, detail=f"Layer {layer_name} not found.")

        sql = text(
            f"""UPDATE scenarios SET {scenario_layer} = CAST(:deleted_feature_ids AS bigint[]) WHERE scenario_id=:scenario_id;"""
        )

        await db.execute(sql, obj_in_data)
        await db.commit()
        return {
            "msg": "Feature delete update successful.",
        }

    async def delete_all_scenario(self, db: AsyncSession, *, obj_in: ScenarioBase) -> Any:
        obj_in_data = jsonable_encoder(obj_in)
        sql = text("""DELETE FROM scenarios WHERE scenario_id = :scenario_id;""")
        await db.execute(sql, obj_in_data)
        await db.commit()
        return {"msg": "Scenario deleted."}


scenario = CRUDScenario()