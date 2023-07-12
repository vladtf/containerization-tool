import docker


class RuleEntry:
    def __init__(self, command, chain, target, protocol, options, source, destination):
        self.command = command
        self.chain = chain
        self.target = target
        self.protocol = protocol
        self.options = options
        self.source = source
        self.destination = destination

    def to_dict(self):
        return {
            'command': self.command,
            'chain': self.chain,
            'target': self.target,
            'protocol': self.protocol,
            'options': self.options,
            'source': self.source,
            'destination': self.destination
        }

    def __str__(self):
        return f"Command: {self.command}, Chain: {self.chain}, Target: {self.target}, Protocol: {self.protocol}, Options: {self.options}, Source: {self.source}, Destination: {self.destination}"


def parse_iptables_rules(iptables_output) -> list[RuleEntry]:
    rules = iptables_output.strip().split('\n')
    nat_table: list[RuleEntry] = []
    chain = None

    for rule in rules:
        rule = rule.strip()
        if rule.startswith(':'):
            # Skip the counters line
            continue

        if rule.startswith('-A'):
            parts = rule.split(' ')
            chain = parts[1]
            rule_spec = parts[2:]

            # TODO: handle other chains
            if chain != 'OUTPUT':
                continue

            rule_entry = RuleEntry(
                command=rule,
                chain=chain,
                target=None,
                protocol=None,
                options=None,
                source=None,
                destination=None
            )

            # Extracting the target, protocol, options, source, and destination from the rule_spec
            for i, part in enumerate(rule_spec):
                if part == '-j':
                    rule_entry.target = rule_spec[i + 1]
                elif part == '-p':
                    rule_entry.protocol = rule_spec[i + 1]
                elif part == '-s':
                    rule_entry.source = rule_spec[i + 1]
                elif part == '-d':
                    rule_entry.destination = rule_spec[i + 1]
                elif part == '--to-destination':
                    rule_entry.destination = rule_spec[i + 1]

            # Add the rule to the nat table
            nat_table.append(rule_entry)

    return nat_table


def show_nat_table(container_id) -> list[RuleEntry]:
    client = docker.from_env()
    container = client.containers.get(container_id)

    exec_command = 'iptables-save -t nat'
    response = container.exec_run(exec_command, privileged=True)

    output = response.output.decode()

    nat_table = parse_iptables_rules(output)

    return nat_table
