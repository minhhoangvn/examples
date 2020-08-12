from kubernetes import client, config
from kubernetes.stream import stream 
import time
from datetime import timedelta, datetime

config.load_kube_config()
client_apis = client.CoreV1Api()

def test_can_send_request_via_mTLS_with_certificate():
    list_namespaces = ['foo','bar']
    wait_for_all_pods_ready(list_namespaces, "sleep")
    wait_for_all_pods_ready(list_namespaces, "httpbin")
    verify_can_send_request_via_mTLS_with_certificate(list_namespaces, "sleep")

def test_cannot_send_request_via_mTLS_with_certificate():
    list_namespaces = ['legacy']
    wait_for_all_pods_ready(list_namespaces, "sleep")
    wait_for_all_pods_ready(list_namespaces, "httpbin")
    verify_cannot_send_request_via_mTLS_without_certificate(list_namespaces, "sleep")

def verify_can_send_request_via_mTLS_with_certificate(list_namespaces: list, pod_name: str):
    verify_can_send_request_via_mTLS = []
    for src_namespace in list_namespaces:
        pod_list = client_apis.list_namespaced_pod(src_namespace)
        for pod in pod_list.items:
            if pod_name == pod.metadata.labels.get("app",""):
                verify_can_send_request_via_mTLS.extend(assert_request(pod, src_namespace, list_namespaces, lambda status_code: status_code == "200"))
    assert False not in verify_can_send_request_via_mTLS

def verify_cannot_send_request_via_mTLS_without_certificate(list_namespaces: list, pod_name: str):
    verify_cannot_send_request_via_mTLS = []
    for src_namespace in list_namespaces:     
        pod_list = client_apis.list_namespaced_pod(src_namespace)
        for pod in pod_list.items:
            if pod_name == pod.metadata.labels.get("app",""):
                verify_cannot_send_request_via_mTLS.extend(assert_request(pod, src_namespace, ["foo", "bar"], lambda status_code: status_code != "200"))
    assert False not in verify_cannot_send_request_via_mTLS

def assert_request(pod, src_namespace, list_namespaces, assert_function):
    assert_result = []
    for dest_namespace in list_namespaces:
        resp=stream(client_apis.connect_get_namespaced_pod_exec,name=pod.metadata.name,namespace=src_namespace,command=["curl","http://httpbin.{0}:8000/ip".format(dest_namespace),"-s","-o","/dev/null","-w","%{http_code}\n"],stderr=True,stdout=True,container="sleep")
        print("sleep.{0} to httpbin.{1}: {2}".format(src_namespace, dest_namespace, resp))
        assert_result.append(assert_function(str(resp)))
    return assert_result

def wait_for_all_pods_ready(list_namespaces: list ,pod_name: str):
    for src_namespace in list_namespaces:
        wait_for_pod_ready(src_namespace, pod_name)

def wait_for_pod_ready(namespace: str = "default", pod_name: str = ""):
    pod_list = client_apis.list_namespaced_pod(namespace)
    if len(pod_list.items) == 0:
        print("Namespace {0} does not exist!".format(namespace))
        return 
    ready_status = "Running"
    current_status = "Pending"
    pod_ready = current_status == ready_status
    start_time = datetime.now()
    total_waiting_time = (datetime.now() - start_time).total_seconds()
    while not pod_ready and total_waiting_time < 45.0 :
        for pod in pod_list.items:
            if pod_name == pod.metadata.labels.get("app",""):
                current_status = pod.status.phase
                print("namespace [{0}] with deployment [{1}] status: {2}..........!".format(namespace, pod_name, pod.status.phase))
        pod_list = client_apis.list_namespaced_pod(namespace)
        pod_ready = current_status == ready_status
        total_waiting_time = (datetime.now() - start_time).total_seconds()
        time.sleep(2)
    time.sleep(5)