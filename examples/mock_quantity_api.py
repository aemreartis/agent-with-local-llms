from __future__ import annotations

from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel

app = FastAPI(title="Mock Quantity API")


class Item(BaseModel):
    name: str
    quantity: int


MOCK_ITEMS: List[Item] = [
    Item(name="alpha", quantity=50),
    Item(name="beta", quantity=120),
    Item(name="gamma", quantity=5),
    Item(name="delta", quantity=300),
]


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok"}


@app.get("/items/quantity")
async def get_quantities(
    name: Optional[str] = Query(default=None),
    min_quantity: Optional[int] = Query(default=None),
) -> Dict[str, Any]:
    items = MOCK_ITEMS

    if name:
        name_l = name.lower().strip()
        items = [i for i in items if name_l in i.name.lower()]

    if min_quantity is not None:
        items = [i for i in items if i.quantity >= min_quantity]

    return {"items": [i.model_dump() for i in items]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8099) 