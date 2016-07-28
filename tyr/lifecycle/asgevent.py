import boto3
import logging

class ASGEvent(object):
    def __init__(self, hook_name=None,
                asg_name=None,
                transition='autoscaling:EC2_INSTANCE_LAUNCHING',
                role_name=None):

        self.log = logging.getLogger('Tyr.Lifecycle.ASGEvent')

        self.asg_name = asg_name
        self.hook_name = hook_name
        self.transition = transition 
        self.role_arn = self.get_role_arn(role_name)

    def get_role_arn(self, role_name):

        iam = boto3.client('iam')
        roles = iam.get_role(RoleName=role_name)

        self.log.info('Found role ARN for lifecycle[{arn}]'.format(arn=roles['Role']['Arn']))

        return roles['Role']['Arn']

    def create_event(self):
        client = boto3.client('autoscaling')

        self.log.info('Creating lifecycle hook name[{name}] asg[{asg}] transaction[{transition}]'.format(name=self.hook_name,
                        asg=self.asg_name,
                        transition=self.transition))

        response = client.put_lifecycle_hook(LifecycleHookName=self.hook_name,
                                                AutoScalingGroupName=self.asg_name,
                                                LifecycleTransition=self.transition
                                                )