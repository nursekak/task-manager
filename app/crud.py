from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Task, TaskStatus, User
from app.schemas import TaskCreate, TaskUpdate, UserCreate


# --- User ---
def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalars().one_or_none()


def create_user(db: Session, user_in: UserCreate, hashed_password: str) -> User:
    user = User(email=user_in.email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# --- Task ---
def get_task(db: Session, task_id: int, user_id: int) -> Task | None:
    return db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    ).scalars().one_or_none()


def get_tasks(
    db: Session,
    user_id: int,
    *,
    status: TaskStatus | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    skip: int = 0,
    limit: int = 10,
) -> tuple[list[Task], int]:
    q = select(Task).where(Task.user_id == user_id)
    count_q = select(func.count()).select_from(Task).where(Task.user_id == user_id)

    if status is not None:
        q = q.where(Task.status == status)
        count_q = count_q.where(Task.status == status)
    if created_after is not None:
        q = q.where(Task.created_at >= created_after)
        count_q = count_q.where(Task.created_at >= created_after)
    if created_before is not None:
        q = q.where(Task.created_at <= created_before)
        count_q = count_q.where(Task.created_at <= created_before)

    total = db.execute(count_q).scalar() or 0
    q = q.order_by(Task.updated_at.desc()).offset(skip).limit(limit)
    items = list(db.execute(q).scalars().all())
    return items, total


def create_task(db: Session, task_in: TaskCreate, user_id: int) -> Task:
    task = Task(**task_in.model_dump(), user_id=user_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: Task, task_in: TaskUpdate) -> Task:
    data = task_in.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
