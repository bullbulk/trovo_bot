import asyncio
from functools import partial

import numpy as np


async def calc_dices_result(amount: int) -> dict[int, int]:
    return await asyncio.get_running_loop().run_in_executor(
        None, partial(calc_dices_result_sync, amount)
    )


def calc_dices_result_sync(amount: int) -> dict[int, int]:
    array = np.random.randint(1, 7, amount, dtype=np.int8)
    unique, counts = np.unique(array, return_counts=True)
    return dict(zip(unique, counts))
