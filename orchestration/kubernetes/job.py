def prepare_job(kube_client, **task):

    container = kube_client.V1Container(**task)

    # Create and configurate a spec section
    template = kube_client.V1PodTemplateSpec(
        metadata=kube_client.V1ObjectMeta(labels={"app": "pi"}),
        spec=kube_client.V1PodSpec(restart_policy="Never", containers=[container]),
    )
    # Create the specification of deployment
    spec = kube_client.V1JobSpec(template=template, backoff_limit=4)
    # Instantiate the job object
    job = kube_client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=kube_client.V1ObjectMeta(name=JOB_NAME),
        spec=spec,
    )
    return job


def create_job(api_instance, job):
    api_response = api_instance.create_namespaced_job(body=job, namespace="default")
    print("Job created. status='%s'" % str(api_response.status))


def update_job(api_instance, job):
    # Update container image
    job.spec.template.spec.containers[0].image = "perl"
    api_response = api_instance.patch_namespaced_job(
        name=JOB_NAME, namespace="default", body=job
    )
    print("Job updated. status='%s'" % str(api_response.status))


def delete_job(api_instance):
    api_response = api_instance.delete_namespaced_job(
        name=JOB_NAME,
        namespace="default",
        body=client.V1DeleteOptions(
            propagation_policy="Foreground", grace_period_seconds=5
        ),
    )
    print("Job deleted. status='%s'" % str(api_response.status))
