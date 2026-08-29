import asyncio

_handlers = []
def register(callback):
    _handlers.append(callback)

async def publish(message):
    for fn in _handlers:
        try:
            result = fn(message)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            print(f"[msg_bus] handler error: {e}")