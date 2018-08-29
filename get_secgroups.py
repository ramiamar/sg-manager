import boto3


class SecurityGroup(object):
    def __init__(self, raw_sg):
        self.id = raw_sg['GroupId']
        self.tags = SecurityGroup.parse_tags(raw_sg.get('Tags', []))
        self.name = raw_sg.get('GroupName')
        self.incoming = []
        for r in raw_sg.get('IpPermissions', []):
            self.incoming.extend(SGRule.create_multiple(r))
        self.outgoing = []
        for r in raw_sg.get('IpPermissionsEgress', []):
            self.outgoing.extend(SGRule.create_multiple(r))

    def fill_in_names(self, all_sgs):
        for r in self.incoming + self.outgoing:
            r.fill_in_names(all_sgs)

    @staticmethod
    def parse_tags(tags):
        parsed = {}
        for k_v_pair in tags:
            parsed[k_v_pair['Key']] = k_v_pair['Value']
        return parsed

    @staticmethod
    def get_all():
        ec2 = boto3.client('ec2')
        res = ec2.describe_security_groups()
        sgs = {}
        for raw_sg in res['SecurityGroups']:
            new_sg = SecurityGroup(raw_sg)
            sgs[new_sg.id] = new_sg
        for sg in sgs.values():
            sg.fill_in_names(sgs)
        return sgs

    def __str__(self):
        return ' '.join(['%s=%s' % (k, v) for k, v in self.__dict__.items()])

    def __repr__(self):
        return self.__str__()


class SGRule(object):
    def __init__(self, port_range, protocol, cidr=None, sg=None):
        if cidr is None and sg is None:
            raise ValueError('Missing cidr and sg')
        if cidr and sg:
            raise ValueError('Cannot have cidr and sg together')
        self.port_range = port_range
        self.protocol = protocol
        self.cidr = cidr  # list([x.get('CidrIp') for x in raw_rule.get('IpRanges', [])])
        self.sg = sg  # list([SGRef(ref) for ref in raw_rule.get('UserIdGroupPairs')])

    def __str__(self):
        return ' '.join(['%s=%s' % (k, v) for k, v in self.__dict__.items()])

    def __repr__(self):
        return self.__str__()

    def fill_in_names(self, all_sgs):
        if self.sg is not None:
            self.sg.fill_in_name(all_sgs)

    @staticmethod
    def create_multiple(raw_rule):
        res = []
        port_range = PortRange(raw_rule.get('FromPort'), raw_rule.get('ToPort'))
        protocol = raw_rule.get('IpProtocol')
        for x in raw_rule.get('IpRanges', []):
            res.append(SGRule(port_range, protocol, cidr=x.get('CidrIp')))
        for x in raw_rule.get('UserIdGroupPairs', []):
            res.append(SGRule(port_range, protocol, sg=SGRef(x)))
        return res


class PortRange(object):
    def __init__(self, from_port, to_port):
        self.from_port = from_port
        self.to_port = to_port

    def __str__(self):
        if self.from_port is None and self.to_port is None:
            return '*'
        if self.from_port == self.to_port:
            return '%d' % self.from_port
        return '%d-%d' % (self.from_port, self.to_port)


class SGRef(object):
    def __init__(self, raw_sg_ref):
        self.id = raw_sg_ref['GroupId']
        self.name = raw_sg_ref.get('GroupName')
        self.vpc = raw_sg_ref.get('VpcId')
        self.vpcx_id = raw_sg_ref.get('VpcPeeringConnectionId')

    def fill_in_name(self, all_sgs):
        if self.name is not None:
            return
        if self.id in all_sgs:
            self.name = all_sgs[self.id].name

    def __str__(self):
        return self.name or self.id

    def __repr__(self):
        return self.__str__()


def print_all_rules_csv():
    for sg in SecurityGroup.get_all().values():
        for ir in sg.incoming:
            print('%s, %s, %s, %s' % (
                ir.cidr or ir.sg, sg.name, ir.protocol, ir.port_range))


if __name__ == '__main__':
    print_all_rules_csv()
