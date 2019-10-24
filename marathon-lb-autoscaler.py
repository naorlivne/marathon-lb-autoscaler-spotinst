import boto3
import datetime
import math
import os
import requests
from parse_it import ParseIt


parser = ParseIt()
marathon_url = parser.read_configuration_variable("marathon_url")
marathon_port = parser.read_configuration_variable("marathon_port")
elb_name = parser.read_configuration_variable("elb_name")
min_num_of_lb = parser.read_configuration_variable("min_num_of_lb")
lb_per_x_connections = parser.read_configuration_variable("lb_per_x_connections")
spotinst_auth_token = parser.read_configuration_variable("spotinst_auth_token")
spotinst_account_id = parser.read_configuration_variable("spotinst_account_id")
elastigroup_id = parser.read_configuration_variable("elastigroup_id")
app_name = parser.read_configuration_variable("app_name", default_value="marathon-lb")


def get_elb_requests(aws_elb_name):
    client = boto3.client(
        'cloudwatch'
    )

    cloudwatch_metric_data = client.get_metric_statistics(
        Period=300,
        StartTime=datetime.datetime.utcnow() - datetime.timedelta(minutes=6),
        EndTime=datetime.datetime.utcnow() - datetime.timedelta(minutes=1),
        MetricName='RequestCount',
        Namespace='AWS/ELB',
        Statistics=['Sum'],
        Dimensions=[{'Name': "LoadBalancerName", 'Value': aws_elb_name}],
        Unit="Count"
    )
    return int(cloudwatch_metric_data["Datapoints"][0]["Sum"] / 5)


def change_marathon_lb_size(marathon_host_url, marathon_host_port, new_size, marathon_app_name):
    url = marathon_host_url + ":" + marathon_host_port + "/v2/apps/" + marathon_app_name + "/"

    querystring = {"force": "true"}

    payload = "{\"instances\": " + str(new_size) + "}"
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'postman-token': "7b955bc7-d7ee-4b02-3821-95b57f151bca"
    }

    response = requests.request("PUT", url, data=payload, headers=headers, params=querystring)

    return response.status_code


def get_spotinst_instances(auth_token, elastigroup):
    url = "https://api.spotinst.io/aws/ec2/group/" + elastigroup + "/instanceHealthiness?accountId=" \
          + spotinst_account_id

    headers = {
        'authorization': "Bearer " + auth_token,
        'cache-control': "no-cache"
        }

    response = requests.request("GET", url, headers=headers)
    response_json = response.json()

    return int(response_json["response"]["count"])


def get_marathon_lb_tasks(marathon_host_url, marathon_host_port, marathon_app_name):
    url = marathon_host_url + ":" + marathon_host_port + "/v2/apps/" + marathon_app_name + "/tasks"

    headers = {
        'cache-control': "no-cache"
    }

    response = requests.request("GET", url, headers=headers)
    response_json = response.json()

    return int(len(response_json["tasks"]))


def set_spotinst_elastigroup_size(auth_token, elastigroup, instance_size):
    url = "https://api.spotinst.io/aws/ec2/group/" + elastigroup + "?accountId=" + spotinst_account_id

    payload = "{\"group\": { \"capacity\": { \"target\": " + str(instance_size) + ", \"minimum\": " \
              + str(instance_size) + ", \"maximum\":" + str(instance_size) + "}}}"
    headers = {
        'authorization': "Bearer " + auth_token,
        'content-type': "application/json",
        'cache-control': "no-cache"
    }

    response = requests.request("PUT", url, data=payload, headers=headers)

    return response.status_code


requests_last_minute = get_elb_requests(elb_name)
print("there was an average of " + str(requests_last_minute) + " requests per minute over the last 5 minutes")
marathon_lb_needed = int(math.ceil(requests_last_minute / lb_per_x_connections))
if int(marathon_lb_needed) < int(min_num_of_lb):
    marathon_lb_needed = int(min_num_of_lb)
print("there are " + str(marathon_lb_needed) + " marathon-lb instances needed")
current_spotinst_instances = get_spotinst_instances(spotinst_auth_token, elastigroup_id)
print("there are currently " + str(current_spotinst_instances) + " marathon-lb spot instances")
current_marathon_lb_tasks = get_marathon_lb_tasks(marathon_url, marathon_port, app_name)
print("there are currently " + str(current_marathon_lb_tasks) + " marathon-lb tasks")
if current_marathon_lb_tasks == current_spotinst_instances == marathon_lb_needed:
    print("no changes needed - exiting")
    exit(0)
else:
    print("scaling spot instances & marathon-lb tasks to " + str(marathon_lb_needed))
    spotinst_rescale_status_code = set_spotinst_elastigroup_size(spotinst_auth_token, elastigroup_id,
                                                                 marathon_lb_needed)
    marathon_rescale_status_code = change_marathon_lb_size(marathon_url, marathon_port, str(marathon_lb_needed),
                                                           app_name)
    if marathon_rescale_status_code != spotinst_rescale_status_code != 200:
        if marathon_rescale_status_code != 200:
            print("critical - failed to scale marathon-lb tasks")
        if spotinst_rescale_status_code != 200:
            print("critical - failed to scale spotinst elastigroup")
        exit(2)
