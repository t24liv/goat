from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from app.core.config import settings
from app.db.models import base  # noqa: F401
from app.db.models.customer.customization import Customization as CustomizationDB
from app.db.session import staging_session
import yaml 
from rich import print
from sqlalchemy.future import select
from app.db.data_import import DataImport
# make sure all SQL Alchemy models are imported (app.db.base) before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly
# for more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28



async def init_db(db: AsyncSession) -> None:
    customization = await crud.check_data.table_is_empty(db, CustomizationDB)
    
    if customization["Success"] == True:
        print('INFO: There is no default customization. The default customization will be loaded.')

        with open("/app/config/customization.yaml", 'r') as stream:
            default_settings = yaml.load(stream, Loader=yaml.FullLoader)
        
        for role in default_settings:
            for setting in default_settings[role]:
                customization_create = schemas.customization.CustomizationCreate(
                    role_name = role,
                    type = setting,
                    default_setting = {setting : default_settings[role][setting]},
                )   
                await crud.customization.insert_default_customization(db, obj_in=customization_create)
                print('INFO: Default setting of parameter [bold magenta]%s[/bold magenta] for [bold magenta]%s[/bold magenta] added.' % (setting, role))

    imported_table = await DataImport().import_all_tables(db, staging_session())

        #user = await crud.user.create(db, obj_in=user_in)  # noqa: F841