def prepare_job(kube_client, **task):

    container = client.V1Container(**task,)

    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "pi"}),
        spec=client.V1PodSpec(restart_policy="Never", containers=[container]),
    )
    # Create the specification of deployment
    spec = client.V1JobSpec(template=template, backoff_limit=4)
    # Instantiate the job object
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=JOB_NAME),
        spec=spec,
    )
    return job


def create_job(api_instance, job):
    api_response = api_instance.create_namespaced_job(body=job, namespace="default")
    print("Job created. status='%s'" % str(api_response.status))
