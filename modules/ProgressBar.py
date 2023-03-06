from time import sleep
class ProgressBar:
    pass

def progress(steps: int, prefix: str = "*") -> None:
    percents_per_step = 100 // steps
    for i in range(steps + 1):
        print(f"|{prefix * (percents_per_step * i): <100}| {i * percents_per_step:.2f}%", end="\r")
        sleep(0.1)
    print()