# from kubernetes import client, config
# from kubernetes.stream import stream 
# import time
# from datetime import timedelta, datetime

# config.load_kube_config()
# client_apis = client.CoreV1Api()

# def test_can_crate_expected_namespaces():
#     expected_namespace_items = ['foo','bar','legacy']
#     actual_namespace_item = []
#     for ns in client_apis.list_namespace().items:
#          actual_namespace_item.append(ns.metadata.name)
#     assert all(elem in actual_namespace_item for elem in expected_namespace_items) == True
