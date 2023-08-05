import asyncio
from functools import partial

import numpy as np
from sqlalchemy.orm import Session
from unidecode import unidecode

from app import crud
from app.schemas import MassDiceEntry
from .api.trovo import schemas
from .commands.modules.cubes import MassBanController


async def calc_dices_result(amount: int) -> dict[int, int]:
    return await asyncio.get_running_loop().run_in_executor(
        None, partial(calc_dices_result_sync, amount)
    )


def calc_dices_result_sync(amount: int) -> dict[int, int]:
    array = np.random.randint(1, 7, amount, dtype=np.int8)
    unique, counts = np.unique(array, return_counts=True)
    return dict(zip(unique, counts))


def create_massban_entry(
    db: Session,
    message: schemas.Message,
    amount: int,
    trigger_text: str | None,
    target_role: str | None,
):
    if target_role:
        ascii_target_role = unidecode(target_role).lower()
    else:
        ascii_target_role = target_role
        
    crud.mass_dice_entry.create(
        db,
        obj_in=MassDiceEntry(
            issuer_id=message.sender_id,
            issuer_nickname=message.nick_name,
            amount=amount,
            trigger_text=trigger_text,
            target_role=target_role,
            ascii_target_role=ascii_target_role,
            channel_id=message.channel_id,
        ),
    )

    MassBanController.update_active_entries(db)
