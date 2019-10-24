# marathon-lb-autoscaler

docker container which designed to run inside metronome (or other cron like mesos framework) which takes the current # of connections per minutes from an ELB cloudwatch every X minutes in order to allow that metrics to be used to autoscale the marathon-lb tasks & public workers in a spotinst elstigroup.

required envs:
* AWS_ACCESS_KEY_ID
* AWS_SECRET_ACCESS_KEY
* AWS_DEFAULT_REGION (example: us-east-1)
* MARATHON_URL (example: master.mesos for use inside mesos)
* MARATHON_PORT (example: 8080)
* ELB_NAME (example: dcos-public-worker-elb)
* MIN_NUM_OF_LB
* LB_PER_X_CONNECTIONS
* SPOTINST_AUTH_TOKEN
* SPOTINST_ACCOUNT_ID
* ELASTIGROUP_ID
* APP_NAME (app name in marathon, defaults to "marathon-lb")


example metronome job config:
``````
{
  "id": "marathon-lb-autoscaler",
  "run": {
    "cmd": "docker pull vidazoohub/marathon-lb-autoscaler:latest && docker run --rm -e SPOTINST_AUTH_TOKEN=3c47...0a7 -e ELASTIGROUP_ID=sig-######## -e ELB_NAME=your_elb  -e LB_PER_X_CONNECTIONS=10000 -e AWS_ACCESS_KEY_ID=your_aws_Key -e AWS_SECRET_ACCESS_KEY=your_aws_secret -e MARATHON_URL=http://master.mesos -e AWS_DEFAULT_REGION=us-east-1 -e MARATHON_PORT=8080 -e MIN_NUM_OF_LB=4 vidazoohub/marathon-lb-autoscaler:latest",
    "cpus": 0.1,
    "mem": 256,
    "disk": 100
  },
  "schedules": [
    {
      "id": "default",
      "enabled": true,
      "cron": "*/10 * * * *",
      "timezone": "UTC",
      "concurrencyPolicy": "ALLOW",
      "startingDeadlineSeconds": 30
    }
  ]
}
```````