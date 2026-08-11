import asyncio
import time

async def waiting_task(name: str, seconds: float) -> None:
  print(f"started at {time.strftime('%X')}")
  await asyncio.sleep(seconds, name)
  print(f"finished at {time.strftime('%X')}")

async def blocking_task(name: str, seconds: float) -> None:
  print(f"started at {time.strftime('%X')}")
  await asyncio.sleep(seconds, name)
  print(f"finished at {time.strftime('%X')}")


# 1st there are no times when printed correctly or in general test doesn't return times
# 2nd I get that the waiting task is set to timeout which is handed to the event pool and
# there it is waiting until timeout will finish to actually respond wthat timeout is finished and can print
# out last statement
# in the second function we don't pass the time.sleep to anything but actually the thread is sleeping
# and therefore the whole app waits on the sleeping method
# still it questions who decides what is what ? is that written in the documentation ?
# and I think I just needed the https://docs.python.org/3/library/asyncio-task.html to pass the test
# I didn't need the - **Python Concurrency with asyncio** (Matthew Fowler) — the event-loop/coroutines chapters, already queued in `books.md` for this exact moment; the deeper "why" behind the timing numbers,
# to finish this task which is sad. In overall the task wasn't that hard but at the same time I don't think
# I learned much - okay I'll give it to you - this task clearly shows the delegation vs doing on own and therefore
# blocking the app but still I don't know - maybe that was all that we could've put in the task based on where we were
# at that moment but yea - maybe next time we should have a topic and then we take a book or documentation and from there
# think of a task/exercise ? Overall writing this review made me realise that what I don't like about the task is the feeling
# that I cheated and got lucky that the tests passed. I'm not entirely sure that by completing this exercise I have grasped the concept
