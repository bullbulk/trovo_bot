from string import digits, ascii_uppercase

from aiohttp import ClientSession

from app.utils import get_rand_string
from .schemas import RocketRankPosition, RocketRankInfo

headers = {
    "accept": "*/*",
    "accept-language": "en-RU,en;q=0.9,ru-RU;q=0.8,ru;q=0.7,en-US;q=0.6",
    "content-type": "text/plain",
    "sec-ch-ua": '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "Referer": "https://cdn.trovo.live/",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36",
}


async def get_rocket_rank(target_channel_id) -> RocketRankInfo:
    target_channel_id = int(target_channel_id)

    body = [
        {
            "operationName": "commerce_StreamerSpellPointRankService_GetStreamerSpellPointRank",
            "variables": {
                "params": {
                    "rankType": 1,
                    "channelID": target_channel_id,
                    "previous": False,
                    "offset": 0,
                    "count": 7,
                }
            },
            "extensions": {},
        },
    ]

    async with ClientSession() as session:
        r = await session.request(
            "POST",
            f"https://api-web.trovo.live/graphql?qid={get_rand_string(10, digits + ascii_uppercase)}",
            json=body,
            headers=headers,
        )

    json = await r.json()
    data = json[0]["data"][
        "commerce_StreamerSpellPointRankService_GetStreamerSpellPointRank"
    ]

    rank_list = data["rankList"]
    rank_info = data["rankInfo"]

    result_rank_list = []

    for rank in rank_list:
        position = RocketRankPosition(
            nickname=rank["nickName"],
            rank=rank["displayRank"],
            is_live=rank["isLive"],
            points=rank["spellPoint"],
            channel_id=rank["uid"],
        )
        result_rank_list.append(position)

    return RocketRankInfo(
        position=RocketRankPosition(
            nickname=rank_info["nickName"],
            rank=rank_info["displayRank"],
            is_live=rank_info["isLive"],
            points=rank_info["spellPoint"],
            channel_id=rank_info["uid"],
        ),
        rank_list=result_rank_list,
    )


async def get_rank_message(channel_id: int | str):
    ranks = await get_rocket_rank(channel_id)
    top_points = sorted([x.points for x in ranks.rank_list], reverse=True)

    msg = f"Текущая позиция: {ranks.position.rank}. Очков: {ranks.position.points:,}. "
    if 0 < ranks.position.rank <= 6:
        msg += f"Отрыв от 7-го места: {ranks.get_offset(7):,} очков."
    else:
        msg += f"До 6-го места не хватает {abs(ranks.get_offset(6)):,} очков."

    top_points_numbered = [
        f"{index}. {item:,}" for index, item in enumerate(top_points, 1)
    ]
    msg += f" Топ: {'; '.join(top_points_numbered)}"

    return msg
