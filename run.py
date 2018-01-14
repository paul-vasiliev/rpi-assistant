import asyncio

loop = asyncio.get_event_loop()

def create_promise():
    print("Create promise")
    p = loop.create_future()
    def callback():
        print("Callback called")
        p.set_result("Test")

    loop.call_later(3, callback)
    return p

async def main():
    print("Start main")
    await create_promise()
    print("Stop main")

print("Start loop")
loop.create_task(main())
loop.run_forever()
print("Complete")