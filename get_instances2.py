import boto3


class InstanceInfo(object):
    def __init__(self, instance):
        self.id = instance['InstanceId']
        self.machine_type = instance['InstanceType']
        self.tags = InstanceInfo.parse_tags(instance.get('Tags', []))
        self.client = self.tags.get('Client')
        self.name = self.tags.get('Name')
        self.deployer = self.tags.get('User')
        self.service_type = self.tags.get('Type')
        self.state = instance['State']['Name']
        self.launch_date = instance['LaunchTime']
        self.interfaces = list(
            [NetworkInterface(ni) for ni in
             instance['NetworkInterfaces']])
        self.raw = instance

    @staticmethod
    def parse_tags(tags):
        parsed = {}
        for k_v_pair in tags:
            parsed[k_v_pair['Key']] = k_v_pair['Value']
        return parsed

    @staticmethod
    def get_all():
        ec2 = boto3.client('ec2')
        res = ec2.describe_instances()
        instance_infos = []
        for r in res['Reservations']:
            for i in r['Instances']:
                instance_infos.append(InstanceInfo(i))
        return instance_infos

    def __str__(self):
        return ' '.join(['%s=%s' % (k, v) for k, v in self.__dict__.items()])

    def __repr__(self):
        return self.__str__()


class NetworkInterface(object):
    def __init__(self, network_interface):
        self.id = network_interface['NetworkInterfaceId']
        self.ip = network_interface['PrivateIpAddress']
        self.public_ip = network_interface.get('Association', {}).get(
            'PublicIp')
        self.subnet = network_interface['SubnetId']
        self.vpc = network_interface['VpcId']
        self.security_groups = list(
            [SecurityGroup(g) for g in network_interface['Groups']])

    def __str__(self):
        return '[NI id=%s ip=%s pub_ip=%s subnet=%s sgs=%s]' % (
            self.id, self.ip, self.public_ip, self.subnet,
            self.security_groups)

    def __repr__(self):
        return self.__str__()


class SecurityGroup(object):
    def __init__(self, group):
        self.name = group['GroupName']
        self.id = group['GroupId']

    def __str__(self):
        return self.name or self.id

    def __repr__(self):
        return self.__str__()


def list_nifs_csv():
    instance_infos = InstanceInfo.get_all()
    print('instance_id,state,nif_id,ip,pub_ip,sgs,tags')
    for i in instance_infos:
        for ni in i.interfaces:
            print('%s,%s,%s,%s,%s,%s,"%s"' % (
                i.id, i.state, ni.id, ni.ip, ni.public_ip,
                ' '.join([str(sg) for sg in ni.security_groups]),
                i.tags))


def list_machines_by_sg():
    instance_infos = InstanceInfo.get_all()
    print('sg,instance_id,instance_type,instance_name')
    instances_by_sg = {}
    for i in instance_infos:
        for ni in i.interfaces:
            for sg in ni.security_groups:
                if str(sg) not in instances_by_sg:
                    instances_by_sg[str(sg)] = set()
                instances_by_sg[str(sg)].add(i)
    for sg, instances in instances_by_sg.items():
        for i in instances:
            print('%s,%s,%s,%s' % (sg, i.id, i.service_type, i.name))


def list_client_machines():
    instance_infos = InstanceInfo.get_all()
    for i in instance_infos:
        if i.client is None:
            continue
        print('%s,%s,%s' % (i.id, i.client, i.service_type))


def list_cluster_machines_with_client_tag():
    instance_infos = InstanceInfo.get_all()
    # ec2resource = boto3.resource('ec2')
    for i in instance_infos:
        if i.client is None or i.service_type is None:
            continue
        print('%s,%s,%s,%s' % (i.id, i.name, i.client, i.service_type))
        # t = ec2resource.Tag(i.id, 'Client', i.client)
        # print('Deleting %r' % t)
        # t.delete()


if __name__ == '__main__':
    list_machines_by_sg()
    #list_nifs_csv()
