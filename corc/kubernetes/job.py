from kubernetes import client


def prepare_job(container_kwargs=None, pod_spec_kwargs=None, job_spec_kwargs=None):

    if not container_kwargs:
        container_kwargs = {}

    if not pod_spec_kwargs:
        pod_spec_kwargs = {}

    if not job_spec_kwargs:
        job_spec_kwargs = {}

    if "name" not in container_kwargs:
        print("missing name from container_kwargs")
        return False

    container = client.V1Container(**container_kwargs)

    # Round robin
    # V1PodSpec Can use node_selector to target specific node
    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(generate_name=container_kwargs["name"]),
        spec=client.V1PodSpec(
            restart_policy="Never", containers=[container], **pod_spec_kwargs
        ),
    )
    # Create the specification of deployment
    spec = client.V1JobSpec(template=template, **job_spec_kwargs)
    # Instantiate the job object
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(generate_name=container_kwargs["name"]),
        spec=spec,
    )
    return job


def create_job(api_instance, job, namespace="default"):
    api_response = api_instance.create_namespaced_job(
        body=job, namespace=namespace
    ).to_dict()
    return api_response


# TODO, encode response so that datetime objects are converted to JSON formatable
def list_job(api_instance):
    jobs_list = api_instance.list_job_for_all_namespaces()
    jobs = jobs_list.items
    return jobs


# def update_job(api_instance, job):
#     # Update container image
#     job.spec.template.spec.containers[0].image = "perl"
#     api_response = api_instance.patch_namespaced_job(
#         name=JOB_NAME, namespace="default", body=job
#     )
#     print("Job updated. status='%s'" % str(api_response.status))


# def delete_job(api_instance):
#     api_response = api_instance.delete_namespaced_job(
#         name=JOB_NAME,
#         namespace="default",
#         body=client.V1DeleteOptions(
#             propagation_policy="Foreground", grace_period_seconds=5
#         ),
#     )
#     print("Job deleted. status='%s'" % str(api_response.status))
