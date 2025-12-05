import os
from environ import Env
import redis

env = Env()

REDIS_URL = env('REDIS_URL')

redis_client = redis.from_url(REDIS_URL, decode_responses=True)