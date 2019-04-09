#!/usr/bin/env python

from subprocess import check_output
import json


def get_latest_hive_image():
    # TODO: query quay api to obtain latest tag in
    # https://quay.io/repository/app-sre/hive?tab=tags that is not 'latest'
    return "quay.io/app-sre/hive:e9cfcb4"


def create_cluster_image_set(name, hive_image, release_image):
    cluster_image_set_name = "openshift-v{}".format(name)

    return {
        "apiVersion": "hive.openshift.io/v1alpha1",
        "kind": "ClusterImageSet",
        "metadata": {
            "name": cluster_image_set_name,
            "labels": {
                "hive.openshift.io/source": "nightly"
            }
        },
        "spec": {
            "hiveImage": hive_image,
            "releaseImage": release_image
        }
    }


def is_tag_valid(tag):
    annotations = tag['annotations']

    if annotations is None:
        return False

    name = annotations["release.openshift.io/name"]
    phase = annotations["release.openshift.io/phase"]

    if name != "4.0.0-0.nightly":
        return False

    if phase != "Accepted":
        return False

    return True


def generate_cluster_image_sets(release_info, hive_image):
    cluster_image_sets = []
    for tag in release_info['spec']['tags']:
        if not is_tag_valid(tag):
            continue

        annotations = tag['annotations']

        sha = annotations['release.openshift.io/hash']
        name = tag['name']

        release_image = "{}:{}".format(
            release_info['status']['publicDockerImageRepository'], name)

        cluster_image_set = create_cluster_image_set(
            name, hive_image, release_image)

        cluster_image_sets.append(cluster_image_set)

    return cluster_image_sets


if __name__ == "__main__":
    # oc login https://api.ci.openshift.org
    release_info_raw = check_output(
        ['oc', 'get', 'is/release', '-n', 'ocp', '-o', 'json'])

    hive_image = get_latest_hive_image()

    release_info = json.loads(release_info_raw.decode('utf-8'))

    cluster_image_sets = generate_cluster_image_sets(release_info, hive_image)

    print(json.dumps(cluster_image_sets))
