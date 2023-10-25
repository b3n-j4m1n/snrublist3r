class Results:
    def __init__(self, source):
        self.data = {
            source: {
                "subdomains": set()
            }
        }