import hashlib
import random

seed = hashlib.sha512("hoge".encode())
print(str(seed))
random.seed(int(seed.hexdigest(), 16))
print(random.randrange(0, 10))
print(random.randrange(0, 10))
print(random.randrange(0, 10))

seed = hashlib.sha512("hoge".encode())
print(str(seed))
random.seed(int(seed.hexdigest(), 16))
print(random.randrange(0, 10))
print(random.randrange(0, 10))
print(random.randrange(0, 10))
