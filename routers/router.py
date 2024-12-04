import os, io

from fastapi import UploadFile, APIRouter, HTTPException, Body

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


@stts_router.post("/audio/streaming", tags=["stream"]) #, response_model=ResponseGenerateSingleTTS)
async def generate_single_tts_play(file_name:str):
    try:
        # WAV 파일을 스트리밍하여 재생 가능하도록 반환
        with open(file_name, "rb") as f:
            wav_data = f.read()
        headers = {
            'Content-Disposition': 'inline; filename="output.wav"'
        }
        return StreamingResponse(io.BytesIO(wav_data), media_type="audio/wav", headers=headers)

    except Exception as e:
        stts_logger.add_error('generate_single_tts_play', e)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/download/file/{file_name}", tags=["download"])
async def download_file(file_name:str):
    file_path = ap.inner_output_path / file_name
    if not file_path.exists():
        stts_logger.add_error('generate_single_tts_file', 'File not found.')
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path, media_type='audio/wav', filename=file_name)