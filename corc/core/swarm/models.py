class Member:

    def __init__(self, name, **kwargs):
        self.name = name
        self.config = kwargs

    def print_state(self):
        print("Member name: {}, config: {}".format(self.name, self.config))

    def __str__(self):
        return "Member name: {}, config: {}".format(self.name, self.config)

    def asdict(self):
        return {
            "name": self.name,
            "config": self.config,
        }
