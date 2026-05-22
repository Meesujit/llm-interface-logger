import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.folder import Folder
from app.models.conversation import Conversation
from app.schemas.folder import FolderCreate, FolderListResponse, FolderResponse, FolderUpdate

router = APIRouter()

@router.get("/folders", response_model=FolderListResponse)
async def list_folders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Folder).order_by(Folder.name.asc()))
    folders = list(result.scalars().all())
    responses = []
    for folder in folders:
        count_result = await db.execute(select(func.count(Conversation.id)).where(Conversation.folder_id == folder.id, Conversation.status == "active"))
        count = count_result.scalar() or 0
        responses.append(FolderResponse(id=folder.id, name=folder.name, created_at=folder.created_at, updated_at=folder.updated_at, conversation_count=count))
    return FolderListResponse(folders=responses)

@router.post("/folders", response_model=FolderResponse, status_code=201)
async def create_folder(data: FolderCreate, db: AsyncSession = Depends(get_db)):
    folder = Folder(id=uuid.uuid4(), name=data.name)
    db.add(folder); await db.commit(); await db.refresh(folder)
    return FolderResponse(id=folder.id, name=folder.name, created_at=folder.created_at, updated_at=folder.updated_at, conversation_count=0)

@router.patch("/folders/{folder_id}", response_model=FolderResponse)
async def update_folder(folder_id: str, data: FolderUpdate, db: AsyncSession = Depends(get_db)):
    try: fid = uuid.UUID(folder_id)
    except ValueError: raise HTTPException(status_code=400, detail="Invalid UUID")
    folder = await db.get(Folder, fid)
    if not folder: raise HTTPException(status_code=404, detail="Folder not found")
    folder.name = data.name; await db.commit(); await db.refresh(folder)
    count_result = await db.execute(select(func.count(Conversation.id)).where(Conversation.folder_id == fid))
    count = count_result.scalar() or 0
    return FolderResponse(id=folder.id, name=folder.name, created_at=folder.created_at, updated_at=folder.updated_at, conversation_count=count)

@router.delete("/folders/{folder_id}")
async def delete_folder(folder_id: str, db: AsyncSession = Depends(get_db)):
    try: fid = uuid.UUID(folder_id)
    except ValueError: raise HTTPException(status_code=400, detail="Invalid UUID")
    folder = await db.get(Folder, fid)
    if not folder: raise HTTPException(status_code=404, detail="Folder not found")
    await db.delete(folder); await db.commit()
    return {"status": "deleted", "id": folder_id}
