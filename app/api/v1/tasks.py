from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, rate_limit_dep
from app.crud import (
    create_task,
    delete_task,
    get_task,
    get_tasks,
    update_task,
)
from app.db import get_db
from app.models import Task, TaskStatus, User
from app.schemas import PaginatedTasks, TaskCreate, TaskResponse, TaskUpdate

router = APIRouter()


def _parse_date(v: str | None) -> datetime | None:
    if not v:
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        return None


@router.get("/", response_model=PaginatedTasks)
def list_tasks(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(rate_limit_dep)],
    status_filter: TaskStatus | None = Query(None, alias="status"),
    created_after: str | None = Query(None, description="ISO date"),
    created_before: str | None = Query(None, description="ISO date"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
) -> PaginatedTasks:
    after_dt = _parse_date(created_after)
    before_dt = _parse_date(created_before)
    skip = (page - 1) * limit
    items, total = get_tasks(
        db,
        current_user.id,
        status=status_filter,
        created_after=after_dt,
        created_before=before_dt,
        skip=skip,
        limit=limit,
    )
    pages = (total + limit - 1) // limit if total else 1
    return PaginatedTasks(
        items=[TaskResponse.model_validate(t) for t in items],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task_endpoint(
    task_in: TaskCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(rate_limit_dep)],
) -> Task:
    return create_task(db, task_in, current_user.id)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_endpoint(
    task_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(rate_limit_dep)],
) -> Task:
    task = get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task_endpoint(
    task_id: int,
    task_in: TaskUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(rate_limit_dep)],
) -> Task:
    task = get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    old_status = task.status
    task = update_task(db, task, task_in)
    if task_in.status is not None and task.status != old_status:
        from app.tasks.notifications import send_notification
        send_notification.delay(task_id)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_endpoint(
    task_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(rate_limit_dep)],
) -> None:
    task = get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    delete_task(db, task)
