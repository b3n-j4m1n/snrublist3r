import aiodns
import asyncio
from tqdm import tqdm


class DNSBruteForce:
    def __init__(self, tasks, nameservers, operating_system):
        self.operating_system = operating_system
        if operating_system == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        self.domains = []
        self.bruteforce_results = set()
        self.nameservers = nameservers
        self.tasks = tasks
        self.resolver = aiodns.DNSResolver(nameservers=self.nameservers , timeout=10, tries=5)
        self.task_list = []
        self.queue = asyncio.Queue()

    async def produce(self, domain_list):
        for domain in domain_list:
            self.queue.put_nowait(domain)
        for _ in range(self.tasks):
            task = asyncio.create_task(self.worker(self.queue))
            self.task_list.append(task)
        await self.queue.join()
        for task in self.task_list:
            task.cancel()
        await asyncio.gather(*self.task_list, return_exceptions=True)
        return(self.bruteforce_results)

    async def worker(self, queue):
        while not queue.empty():
            domain = await queue.get()
            try:
                await self.resolver.query(domain, "A")
                tqdm.write('\033[92m' + "[+] " + domain + '\033[1m')
                self.bruteforce_results.add(domain)
            except aiodns.error.DNSError as error:
                if error.args[0] != 1 and error.args[0] != 4:
                    self.timeout_bar.update()
            finally:
                self.progress_bar.update()
                queue.task_done()

    def run(self, domain_list):
        self.progress_bar = tqdm(desc="progress", total=len(domain_list), unit=" requests", maxinterval=0.1, mininterval=0, miniters=1, smoothing=0, colour='WHITE')
        self.timeout_bar = tqdm(desc="error", total=len(domain_list), unit=" errors", maxinterval=1, mininterval=1, colour='RED')
        self.resolver.loop.run_until_complete(self.produce(domain_list))
        return self.bruteforce_results