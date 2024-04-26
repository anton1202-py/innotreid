import asyncio


def synchronous_function(n, m):
    # Синхронная функция, которую вы хотите вызвать
    return n + m


async def async_wrapper():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, synchronous_function)
    synchronous_function()
    print(type(result))
    return result


async def async_function_calling_sync():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, synchronous_function, 5, 10)
    s = synchronous_function(5, 3)
    print(s, result)
    return result

asyncio.run(async_function_calling_sync())
