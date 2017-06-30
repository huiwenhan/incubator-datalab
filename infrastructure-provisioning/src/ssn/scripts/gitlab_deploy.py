#!/usr/bin/python
# *****************************************************************************
#
# Copyright (c) 2016, EPAM SYSTEMS INC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ******************************************************************************


from ConfigParser import SafeConfigParser
from fabric.api import *
import argparse
import boto3
import sys
import os

parser = argparse.ArgumentParser()
parser.add_argument('--action', required=True, type=str, default='', choices=['create', 'terminate'],
                    help='Available options: create, terminate')
args = parser.parse_args()


def read_ini():
    try:
        head, tail = os.path.split(os.path.realpath(__file__))
        for filename in os.listdir(head):
            if filename.endswith('.ini'):
                config = SafeConfigParser()
                config.read(os.path.join(head, filename))
                for section in config.sections():
                    for option in config.options(section):
                        var = "{0}_{1}".format(section, option)
                        if var not in os.environ:
                            os.environ[var] = config.get(section, option)
    except Exception as err:
        print 'Failed to read conf file.', str(err)
        sys.exit(1)


def create_instance():
    try:
        local('mkdir -p ~/.aws')
        local('touch ~/.aws/config')
        local('echo "[default]" > ~/.aws/config')
        local('echo "region = {}" >> ~/.aws/config'.format(os.environ['aws_region']))
        ec2 = boto3.resource('ec2')
        security_groups_ids = []
        ami_id = get_ami_id('aws_{}_ami_name'.format(os.environ['conf_os_family']))
        for chunk in os.environ['aws_sg_ids'].split(','):
            security_groups_ids.append(chunk.strip())
        instances = ec2.create_instances(ImageId=ami_id, MinCount=1, MaxCount=1,
                                         KeyName=os.environ['conf_key_name'],
                                         SecurityGroupIds=security_groups_ids,
                                         InstanceType=os.environ['aws_instance_type'],
                                         SubnetId=os.environ['aws_subnet_id'])
        for instance in instances:
            print 'Waiting for instance {} become running.'.format(instance.id)
            instance.wait_until_running()
            node_name = '{0}-{1}'.format(os.environ['conf_service_base_name'], os.environ['conf_node_name'])
            instance.create_tags(Tags=[{'Key': 'Name', 'Value': node_name}])
            return instance.id
        return ''
    except Exception as err:
        print "Failed to create instance.", str(err)
        sys.exit(1)


def get_ami_id(ami_name):
    try:
        client = boto3.client('ec2')
        image_id = ''
        response = client.describe_images(
            Filters=[
                {
                    'Name': 'name',
                    'Values': [ami_name]
                },
                {
                    'Name': 'virtualization-type', 'Values': ['hvm']
                },
                {
                    'Name': 'state', 'Values': ['available']
                },
                {
                    'Name': 'root-device-name', 'Values': ['/dev/sda1']
                },
                {
                    'Name': 'root-device-type', 'Values': ['ebs']
                },
                {
                    'Name': 'architecture', 'Values': ['x86_64']
                }
            ])
        response = response.get('Images')
        for i in response:
            image_id = i.get('ImageId')
        if image_id == '':
            raise Exception("Unable to find image id with name: " + ami_name)
        return image_id
    except Exception as err:
        print "Failed to get AMI ID.", str(err)


def get_ec2_ip(instance_id):
    try:
        ec2 = boto3.resource('ec2')
        instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-id', 'Values': [instance_id]}])
        for instance in instances:
            return getattr(instance, 'public_dns_name')
    except Exception as e:
        print 'Failed to get instance IP.', str(e)
        sys.exit(1)


if __name__ == "__main__":
    if args.action == 'create':
        # Read all configs
        read_ini()

        instance_id = create_instance()
        print 'Instance {} created.'.format(instance_id)
        os.environ['instance_hostname'] = get_ec2_ip(instance_id)
        print 'Instance hostname: {}'.format(os.environ['instance_hostname'])

        keyfile = '{}'.format('{}{}.pem'.format(os.environ['conf_key_dir'], os.environ['conf_key_name']))
        params = '--keyfile {0} --instance_ip {1} --os_user {2}'.format(keyfile, os.environ['instance_hostname'], os.environ['conf_os_user'])
        local('configure_gitlab.py {}'.format(params))

    elif args.action == 'terminate':
        # TBD...
        pass
    else:
        print 'Unknown action. Try again.'