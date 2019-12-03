import time

count = 0

while True:
    time.sleep(1);

    print(count)

    count += 1

    if count > 60:
        break