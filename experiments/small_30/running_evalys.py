from evalys.jobset import JobSet
import matplotlib.pyplot as plt

def main():
    js = JobSet.from_csv("_jobs.csv")
    js.plot(with_details=True)
    plt.show()

main()