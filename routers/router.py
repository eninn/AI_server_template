from fastapi import UploadFile, APIRouter

from cores.coreClass import coreClass
from utils.environment import hp
from routers import ItemRequest, ItemResponse, sample_1

core = coreClass(device=hp.device)
router = APIRouter(prefix="/route")

@router.post("/mainTag/method", tags=["mainTag"], response_model=ItemResponse)
async def mainTag_method(file: UploadFile, item:ItemRequest):
    try:
        x, runtime = method(item.input_data)

        response_json = {"checkout": True,
                         "return_data": x,
                         "runtime": runtime,
                         "message": "Complete"}

    except Exception as e:
        response_json = {"checkout": False,
                         "return_data": None,
                         "runtime": None,
                         "message": f"Error: {e}"}

    response = ItemResponse(**response_json)

    return response
