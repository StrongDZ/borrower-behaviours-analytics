from aggregator.borrower_aggregator import BorrowerAggregatorJob

class JobScheduler:
    def __init__(self):
        self.jobs = [BorrowerAggregatorJob()]

    def run(self):
        for job in self.jobs:
            job.run()