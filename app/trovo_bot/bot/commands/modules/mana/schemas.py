from pydantic import BaseModel, validator


class RocketRankPosition(BaseModel):
    nickname: str
    rank: int
    points: int
    is_live: bool
    channel_id: int

    @validator("rank", pre=True)
    def validate_rank(cls, v):  # noqa
        if isinstance(v, str):
            v = int(v) if v.isdigit() else 0
        return v


class RocketRankInfo(BaseModel):
    position: RocketRankPosition
    rank_list: list[RocketRankPosition]

    def get_offset(self, position_rank: int):
        # sourcery skip: reintroduce-else, use-named-expression
        target = list(filter(lambda x: x.rank == position_rank, self.rank_list))
        if not target:
            return

        return self.position.points - target[0].points
